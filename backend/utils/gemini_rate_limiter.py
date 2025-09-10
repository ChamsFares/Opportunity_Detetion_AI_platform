"""
Enhanced Gemini Rate Limiter for MCP Backend
Comprehensive rate limiting and API management for Google Gemini API.
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import deque, defaultdict
import json

from .logger import MCPLogger


class QuotaExhaustedException(Exception):
    """Exception raised when API quota is exhausted."""
    
    def __init__(self, quota_type: str, message: str = None):
        self.quota_type = quota_type
        self.message = message or f"Quota exhausted: {quota_type}"
        super().__init__(self.message)


class FallbackStrategies(str, Enum):
    """Fallback strategies when quota is exhausted."""
    WAIT = "wait"
    SKIP = "skip"
    ERROR = "error"
    ALTERNATIVE_MODEL = "alternative_model"


class RateLimitType(str, Enum):
    """Types of rate limits."""
    PER_SECOND = "per_second"
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    CONCURRENT = "concurrent"
    TOKEN_BASED = "token_based"


@dataclass
class RateLimit:
    """Rate limit configuration."""
    
    limit_type: RateLimitType
    max_requests: int
    time_window: timedelta
    priority: int = 1  # Higher number = higher priority
    enabled: bool = True
    description: str = ""
    
    def __post_init__(self):
        """Validate rate limit configuration."""
        if self.max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if self.time_window.total_seconds() <= 0:
            raise ValueError("time_window must be positive")


@dataclass
class ApiQuota:
    """API quota tracking."""
    
    quota_type: str
    total_quota: int
    used_quota: int = 0
    reset_time: Optional[datetime] = None
    warning_threshold: float = 0.8  # Warn at 80% usage
    
    @property
    def remaining_quota(self) -> int:
        """Get remaining quota."""
        return max(0, self.total_quota - self.used_quota)
    
    @property
    def usage_percentage(self) -> float:
        """Get quota usage percentage."""
        return (self.used_quota / self.total_quota) * 100 if self.total_quota > 0 else 0
    
    @property
    def is_exhausted(self) -> bool:
        """Check if quota is exhausted."""
        return self.remaining_quota <= 0
    
    @property
    def is_near_limit(self) -> bool:
        """Check if quota is near limit."""
        return self.usage_percentage >= (self.warning_threshold * 100)


@dataclass
class RequestRecord:
    """Record of an API request."""
    
    timestamp: datetime
    endpoint: str
    request_id: str
    tokens_used: int = 0
    response_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "endpoint": self.endpoint,
            "request_id": self.request_id,
            "tokens_used": self.tokens_used,
            "response_time": self.response_time,
            "success": self.success,
            "error_message": self.error_message,
            "retry_count": self.retry_count
        }


class MCPGeminiRateLimiter:
    """Comprehensive rate limiter for Gemini API with MCP integration."""
    
    def __init__(
        self,
        logger: Optional[MCPLogger] = None,
        default_limits: Optional[Dict[RateLimitType, RateLimit]] = None
    ):
        self.logger = logger or MCPLogger()
        self._lock = threading.RLock()
        
        # Rate limiting storage
        self._rate_limits = {}
        self._request_history = deque(maxlen=10000)  # Keep last 10k requests
        self._endpoint_history = defaultdict(lambda: deque(maxlen=1000))
        self._quota_tracking = {}
        
        # Concurrent request tracking
        self._active_requests = set()
        self._max_concurrent = 10
        self._concurrent_semaphore = asyncio.Semaphore(self._max_concurrent)
        
        # Statistics
        self._statistics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited_requests": 0,
            "average_response_time": 0.0,
            "start_time": datetime.utcnow(),
            "peak_concurrent_requests": 0,
            "quota_warnings_sent": 0
        }
        
        # Default Gemini API limits
        self._setup_default_limits(default_limits)
        
        # Callback functions
        self._rate_limit_callbacks = []
        self._quota_warning_callbacks = []
        
        self.logger.info("Gemini rate limiter initialized")
    
    def _setup_default_limits(self, custom_limits: Optional[Dict[RateLimitType, RateLimit]] = None):
        """Setup default rate limits for Gemini API."""
        default_limits = {
            RateLimitType.PER_SECOND: RateLimit(
                limit_type=RateLimitType.PER_SECOND,
                max_requests=2,
                time_window=timedelta(seconds=1),
                priority=10,
                description="Gemini API requests per second"
            ),
            RateLimitType.PER_MINUTE: RateLimit(
                limit_type=RateLimitType.PER_MINUTE,
                max_requests=60,
                time_window=timedelta(minutes=1),
                priority=8,
                description="Gemini API requests per minute"
            ),
            RateLimitType.PER_HOUR: RateLimit(
                limit_type=RateLimitType.PER_HOUR,
                max_requests=1000,
                time_window=timedelta(hours=1),
                priority=6,
                description="Gemini API requests per hour"
            ),
            RateLimitType.PER_DAY: RateLimit(
                limit_type=RateLimitType.PER_DAY,
                max_requests=50000,
                time_window=timedelta(days=1),
                priority=4,
                description="Gemini API requests per day"
            ),
            RateLimitType.CONCURRENT: RateLimit(
                limit_type=RateLimitType.CONCURRENT,
                max_requests=10,
                time_window=timedelta(seconds=1),  # Not used for concurrent
                priority=12,
                description="Concurrent Gemini API requests"
            )
        }
        
        # Override with custom limits if provided
        if custom_limits:
            default_limits.update(custom_limits)
        
        self._rate_limits = default_limits
        
        # Setup default quotas
        self._quota_tracking = {
            "daily_tokens": ApiQuota(
                quota_type="daily_tokens",
                total_quota=1000000,  # 1M tokens per day
                warning_threshold=0.8
            ),
            "monthly_requests": ApiQuota(
                quota_type="monthly_requests",
                total_quota=100000,  # 100k requests per month
                warning_threshold=0.9
            )
        }
    
    async def acquire_permission(
        self,
        endpoint: str = "default",
        tokens_estimate: int = 0,
        priority: int = 1,
        timeout: float = 30.0
    ) -> str:
        """
        Acquire permission to make an API request.
        
        Args:
            endpoint: API endpoint identifier
            tokens_estimate: Estimated tokens for the request
            priority: Request priority (higher = more important)
            timeout: Maximum wait time for permission
            
        Returns:
            Request ID for tracking
        """
        request_id = f"req_{int(time.time() * 1000)}_{id(asyncio.current_task())}"
        start_time = time.time()
        
        self.logger.debug(
            f"Requesting API permission: {endpoint}",
            request_id=request_id,
            endpoint=endpoint,
            tokens_estimate=tokens_estimate,
            priority=priority
        )
        
        try:
            # Check quotas first
            await self._check_quotas(tokens_estimate)
            
            # Wait for rate limits
            await self._wait_for_rate_limits(endpoint, timeout)
            
            # Acquire concurrent request slot
            await asyncio.wait_for(
                self._concurrent_semaphore.acquire(),
                timeout=timeout - (time.time() - start_time)
            )
            
            # Track active request
            with self._lock:
                self._active_requests.add(request_id)
                current_concurrent = len(self._active_requests)
                if current_concurrent > self._statistics["peak_concurrent_requests"]:
                    self._statistics["peak_concurrent_requests"] = current_concurrent
            
            self.logger.debug(
                f"API permission granted: {endpoint}",
                request_id=request_id,
                wait_time=time.time() - start_time,
                active_requests=len(self._active_requests)
            )
            
            return request_id
            
        except asyncio.TimeoutError:
            self.logger.warning(
                f"API permission timeout: {endpoint}",
                request_id=request_id,
                timeout=timeout
            )
            raise
        except Exception as e:
            self.logger.error(
                f"API permission failed: {endpoint}",
                request_id=request_id,
                error=e
            )
            raise
    
    async def release_permission(
        self,
        request_id: str,
        endpoint: str = "default",
        tokens_used: int = 0,
        response_time: float = 0.0,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Release API request permission and record usage.
        
        Args:
            request_id: Request ID from acquire_permission
            endpoint: API endpoint identifier
            tokens_used: Actual tokens used
            response_time: Request response time
            success: Whether request was successful
            error_message: Error message if failed
        """
        with self._lock:
            # Record request
            record = RequestRecord(
                timestamp=datetime.utcnow(),
                endpoint=endpoint,
                request_id=request_id,
                tokens_used=tokens_used,
                response_time=response_time,
                success=success,
                error_message=error_message
            )
            
            self._request_history.append(record)
            self._endpoint_history[endpoint].append(record)
            
            # Update statistics
            self._statistics["total_requests"] += 1
            if success:
                self._statistics["successful_requests"] += 1
            else:
                self._statistics["failed_requests"] += 1
            
            # Update average response time
            total_time = (
                self._statistics["average_response_time"] * (self._statistics["total_requests"] - 1) +
                response_time
            )
            self._statistics["average_response_time"] = total_time / self._statistics["total_requests"]
            
            # Update quota usage
            if tokens_used > 0:
                for quota in self._quota_tracking.values():
                    if quota.quota_type == "daily_tokens":
                        quota.used_quota += tokens_used
                        if quota.is_near_limit:
                            await self._send_quota_warning(quota)
            
            # Remove from active requests
            self._active_requests.discard(request_id)
        
        # Release concurrent semaphore
        self._concurrent_semaphore.release()
        
        self.logger.debug(
            f"API permission released: {endpoint}",
            request_id=request_id,
            tokens_used=tokens_used,
            response_time=response_time,
            success=success
        )
    
    async def _check_quotas(self, tokens_estimate: int):
        """Check if request would exceed quotas."""
        for quota in self._quota_tracking.values():
            if quota.is_exhausted:
                raise QuotaExhaustedException(quota.quota_type, f"Quota exhausted: {quota.quota_type}")
            
            if quota.quota_type == "daily_tokens" and tokens_estimate > 0:
                if quota.used_quota + tokens_estimate > quota.total_quota:
                    raise QuotaExhaustedException(
                        quota.quota_type, 
                        f"Request would exceed {quota.quota_type} quota"
                    )
    
    async def _wait_for_rate_limits(self, endpoint: str, timeout: float):
        """Wait for rate limits to allow request."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check all rate limits
            max_wait = 0.0
            
            for rate_limit in self._rate_limits.values():
                if not rate_limit.enabled:
                    continue
                
                wait_time = await self._check_rate_limit(rate_limit, endpoint)
                max_wait = max(max_wait, wait_time)
            
            if max_wait <= 0:
                return  # All limits satisfied
            
            # Wait for the longest required time (but not more than remaining timeout)
            wait_time = min(max_wait, timeout - (time.time() - start_time))
            if wait_time > 0:
                self.logger.debug(f"Rate limit wait: {wait_time:.2f}s for {endpoint}")
                await asyncio.sleep(wait_time)
        
        raise asyncio.TimeoutError("Rate limit timeout")
    
    async def _check_rate_limit(self, rate_limit: RateLimit, endpoint: str) -> float:
        """
        Check a specific rate limit and return wait time needed.
        
        Returns:
            Wait time in seconds (0 if no wait needed)
        """
        current_time = datetime.utcnow()
        
        if rate_limit.limit_type == RateLimitType.CONCURRENT:
            # Concurrent limit is handled by semaphore
            return 0.0
        
        # Count requests in the time window
        window_start = current_time - rate_limit.time_window
        
        if endpoint == "default":
            # Check all requests
            recent_requests = [
                record for record in self._request_history
                if record.timestamp >= window_start
            ]
        else:
            # Check endpoint-specific requests
            recent_requests = [
                record for record in self._endpoint_history[endpoint]
                if record.timestamp >= window_start
            ]
        
        if len(recent_requests) < rate_limit.max_requests:
            return 0.0  # Under limit
        
        # Find when the oldest request in the window will expire
        oldest_request = min(recent_requests, key=lambda r: r.timestamp)
        wait_until = oldest_request.timestamp + rate_limit.time_window
        wait_time = (wait_until - current_time).total_seconds()
        
        return max(0.0, wait_time)
    
    async def _send_quota_warning(self, quota: ApiQuota):
        """Send quota warning if threshold exceeded."""
        if quota.is_near_limit:
            self._statistics["quota_warnings_sent"] += 1
            
            self.logger.warning(
                f"Quota warning: {quota.quota_type}",
                quota_type=quota.quota_type,
                usage_percentage=quota.usage_percentage,
                remaining=quota.remaining_quota
            )
            
            # Call registered callbacks
            for callback in self._quota_warning_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(quota)
                    else:
                        callback(quota)
                except Exception as e:
                    self.logger.error("Error in quota warning callback", error=e)
    
    def add_rate_limit(self, rate_limit: RateLimit):
        """Add or update a rate limit."""
        with self._lock:
            self._rate_limits[rate_limit.limit_type] = rate_limit
        
        self.logger.info(
            f"Added rate limit: {rate_limit.limit_type}",
            max_requests=rate_limit.max_requests,
            time_window=rate_limit.time_window.total_seconds()
        )
    
    def remove_rate_limit(self, limit_type: RateLimitType):
        """Remove a rate limit."""
        with self._lock:
            self._rate_limits.pop(limit_type, None)
        
        self.logger.info(f"Removed rate limit: {limit_type}")
    
    def update_quota(self, quota_type: str, total_quota: int, used_quota: int = 0):
        """Update quota information."""
        with self._lock:
            if quota_type in self._quota_tracking:
                self._quota_tracking[quota_type].total_quota = total_quota
                self._quota_tracking[quota_type].used_quota = used_quota
            else:
                self._quota_tracking[quota_type] = ApiQuota(
                    quota_type=quota_type,
                    total_quota=total_quota,
                    used_quota=used_quota
                )
        
        self.logger.info(
            f"Updated quota: {quota_type}",
            total_quota=total_quota,
            used_quota=used_quota
        )
    
    def register_quota_warning_callback(self, callback: Callable[[ApiQuota], Any]):
        """Register a callback for quota warnings."""
        self._quota_warning_callbacks.append(callback)
    
    def register_rate_limit_callback(self, callback: Callable[[str, float], Any]):
        """Register a callback for rate limit events."""
        self._rate_limit_callbacks.append(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        uptime = (datetime.utcnow() - self._statistics["start_time"]).total_seconds()
        
        with self._lock:
            return {
                **self._statistics,
                "uptime_seconds": uptime,
                "requests_per_second": self._statistics["total_requests"] / max(uptime, 1),
                "success_rate": (
                    self._statistics["successful_requests"] / 
                    max(self._statistics["total_requests"], 1)
                ),
                "active_requests": len(self._active_requests),
                "quota_status": {
                    quota_type: {
                        "total": quota.total_quota,
                        "used": quota.used_quota,
                        "remaining": quota.remaining_quota,
                        "usage_percentage": quota.usage_percentage,
                        "is_near_limit": quota.is_near_limit
                    }
                    for quota_type, quota in self._quota_tracking.items()
                },
                "rate_limits": {
                    limit_type.value: {
                        "max_requests": limit_config.max_requests,
                        "time_window_seconds": limit_config.time_window.total_seconds(),
                        "enabled": limit_config.enabled
                    }
                    for limit_type, limit_config in self._rate_limits.items()
                }
            }
    
    def get_request_history(self, limit: int = 100, endpoint: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent request history."""
        with self._lock:
            if endpoint:
                history = list(self._endpoint_history[endpoint])
            else:
                history = list(self._request_history)
        
        # Return most recent requests
        recent_history = history[-limit:] if len(history) > limit else history
        return [record.to_dict() for record in recent_history]
    
    async def reset_quotas(self, quota_types: Optional[List[str]] = None):
        """Reset quota usage counters."""
        with self._lock:
            if quota_types:
                for quota_type in quota_types:
                    if quota_type in self._quota_tracking:
                        self._quota_tracking[quota_type].used_quota = 0
            else:
                for quota in self._quota_tracking.values():
                    quota.used_quota = 0
        
        self.logger.info(f"Reset quotas: {quota_types or 'all'}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on rate limiter."""
        with self._lock:
            health_status = {
                "healthy": True,
                "issues": [],
                "active_requests": len(self._active_requests),
                "quotas_ok": True,
                "rate_limits_ok": True
            }
            
            # Check quotas
            for quota_type, quota in self._quota_tracking.items():
                if quota.is_exhausted:
                    health_status["healthy"] = False
                    health_status["quotas_ok"] = False
                    health_status["issues"].append(f"Quota exhausted: {quota_type}")
                elif quota.is_near_limit:
                    health_status["issues"].append(f"Quota near limit: {quota_type}")
            
            # Check for high concurrent usage
            if len(self._active_requests) >= self._max_concurrent * 0.9:
                health_status["issues"].append("High concurrent request usage")
            
            return health_status


# Context manager for automatic permission management
class GeminiRequestContext:
    """Context manager for Gemini API requests with automatic rate limiting."""
    
    def __init__(
        self,
        rate_limiter: MCPGeminiRateLimiter,
        endpoint: str = "default",
        tokens_estimate: int = 0,
        priority: int = 1,
        timeout: float = 30.0
    ):
        self.rate_limiter = rate_limiter
        self.endpoint = endpoint
        self.tokens_estimate = tokens_estimate
        self.priority = priority
        self.timeout = timeout
        self.request_id = None
        self.start_time = None
    
    async def __aenter__(self):
        """Enter the context and acquire permission."""
        self.start_time = time.time()
        self.request_id = await self.rate_limiter.acquire_permission(
            endpoint=self.endpoint,
            tokens_estimate=self.tokens_estimate,
            priority=self.priority,
            timeout=self.timeout
        )
        return self.request_id
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and release permission."""
        response_time = time.time() - self.start_time if self.start_time else 0.0
        success = exc_type is None
        error_message = str(exc_val) if exc_val else None
        
        await self.rate_limiter.release_permission(
            request_id=self.request_id,
            endpoint=self.endpoint,
            response_time=response_time,
            success=success,
            error_message=error_message
        )


# Global rate limiter instance
mcp_gemini_rate_limiter = MCPGeminiRateLimiter()


def get_rate_limiter() -> MCPGeminiRateLimiter:
    """Get the global rate limiter instance."""
    return mcp_gemini_rate_limiter


# Convenience functions
async def acquire_gemini_permission(
    endpoint: str = "default",
    tokens_estimate: int = 0,
    priority: int = 1,
    timeout: float = 30.0
) -> str:
    """Global function to acquire Gemini API permission."""
    return await mcp_gemini_rate_limiter.acquire_permission(
        endpoint, tokens_estimate, priority, timeout
    )


async def release_gemini_permission(
    request_id: str,
    endpoint: str = "default",
    tokens_used: int = 0,
    response_time: float = 0.0,
    success: bool = True,
    error_message: Optional[str] = None
):
    """Global function to release Gemini API permission."""
    await mcp_gemini_rate_limiter.release_permission(
        request_id, endpoint, tokens_used, response_time, success, error_message
    )


def gemini_rate_limited(
    endpoint: str = "default",
    tokens_estimate: int = 0,
    priority: int = 1,
    timeout: float = 30.0
):
    """Decorator for automatic Gemini API rate limiting."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with GeminiRequestContext(
                mcp_gemini_rate_limiter,
                endpoint,
                tokens_estimate,
                priority,
                timeout
            ):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_rate_limiter():
        """Test rate limiter functionality."""
        limiter = MCPGeminiRateLimiter()
        
        # Test basic permission acquisition
        request_id = await limiter.acquire_permission("test_endpoint", tokens_estimate=100)
        print(f"Acquired permission: {request_id}")
        
        # Simulate request processing
        await asyncio.sleep(0.1)
        
        # Release permission
        await limiter.release_permission(
            request_id=request_id,
            endpoint="test_endpoint",
            tokens_used=95,
            response_time=0.1,
            success=True
        )
        
        # Get statistics
        stats = limiter.get_statistics()
        print(f"Statistics: {json.dumps(stats, indent=2, default=str)}")
        
        # Test context manager
        async with GeminiRequestContext(limiter, "context_test", 50):
            print("Processing request in context...")
            await asyncio.sleep(0.05)
    
    asyncio.run(test_rate_limiter())
