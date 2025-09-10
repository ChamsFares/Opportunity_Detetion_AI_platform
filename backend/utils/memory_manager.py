"""
Enhanced Memory Manager for MCP Backend
Comprehensive memory management, monitoring, and optimization system.
"""

import gc
import psutil
import threading
import asyncio
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import weakref
import sys
import traceback
from functools import wraps
import warnings

# Local imports
from .logger import MCPLogger


@dataclass
class MemoryMetrics:
    """Memory metrics data structure."""
    
    timestamp: datetime = field(default_factory=datetime.utcnow)
    process_memory_mb: float = 0.0
    system_memory_percent: float = 0.0
    available_memory_mb: float = 0.0
    gc_collections: Dict[int, int] = field(default_factory=dict)
    object_counts: Dict[str, int] = field(default_factory=dict)
    cache_sizes: Dict[str, int] = field(default_factory=dict)
    active_threads: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "process_memory_mb": self.process_memory_mb,
            "system_memory_percent": self.system_memory_percent,
            "available_memory_mb": self.available_memory_mb,
            "gc_collections": self.gc_collections,
            "object_counts": self.object_counts,
            "cache_sizes": self.cache_sizes,
            "active_threads": self.active_threads
        }


@dataclass
class MemoryAlert:
    """Memory alert data structure."""
    
    alert_type: str
    severity: str  # low, medium, high, critical
    message: str
    metrics: MemoryMetrics
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "metrics": self.metrics.to_dict()
        }


class MemoryCache:
    """Thread-safe memory cache with TTL and size limits."""
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
        cleanup_interval: int = 300
    ):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cleanup_interval = cleanup_interval
        
        self._cache = {}
        self._access_times = {}
        self._lock = threading.RLock()
        self._last_cleanup = datetime.utcnow()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str, default=None):
        """Get item from cache."""
        with self._lock:
            self._cleanup_if_needed()
            
            if key in self._cache:
                entry_time, value = self._cache[key]
                if datetime.utcnow() - entry_time <= timedelta(seconds=self.ttl_seconds):
                    self._access_times[key] = datetime.utcnow()
                    self._hits += 1
                    return value
                else:
                    # Expired
                    del self._cache[key]
                    del self._access_times[key]
            
            self._misses += 1
            return default
    
    def set(self, key: str, value: Any):
        """Set item in cache."""
        with self._lock:
            current_time = datetime.utcnow()
            
            # Check size limit
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            self._cache[key] = (current_time, value)
            self._access_times[key] = current_time
    
    def delete(self, key: str):
        """Delete item from cache."""
        with self._lock:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
    
    def clear(self):
        """Clear all cache."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    def size(self) -> int:
        """Get cache size."""
        return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "ttl_seconds": self.ttl_seconds
        }
    
    def _cleanup_if_needed(self):
        """Cleanup expired entries if needed."""
        current_time = datetime.utcnow()
        if current_time - self._last_cleanup >= timedelta(seconds=self.cleanup_interval):
            self._cleanup_expired()
            self._last_cleanup = current_time
    
    def _cleanup_expired(self):
        """Remove expired entries."""
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, (entry_time, _) in self._cache.items()
            if current_time - entry_time > timedelta(seconds=self.ttl_seconds)
        ]
        
        for key in expired_keys:
            del self._cache[key]
            del self._access_times[key]
    
    def _evict_lru(self):
        """Evict least recently used item."""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        del self._cache[lru_key]
        del self._access_times[lru_key]


class MCPMemoryManager:
    """Comprehensive memory manager for MCP backend."""
    
    def __init__(
        self,
        memory_threshold_percent: float = 80.0,
        process_memory_limit_mb: float = 2048.0,
        monitoring_interval: int = 60,
        enable_auto_gc: bool = True,
        enable_alerts: bool = True,
        logger: Optional[MCPLogger] = None
    ):
        self.memory_threshold_percent = memory_threshold_percent
        self.process_memory_limit_mb = process_memory_limit_mb
        self.monitoring_interval = monitoring_interval
        self.enable_auto_gc = enable_auto_gc
        self.enable_alerts = enable_alerts
        
        self.logger = logger or MCPLogger()
        self._monitoring = False
        self._monitor_task = None
        self._lock = threading.RLock()
        
        # Memory tracking
        self._metrics_history = deque(maxlen=1000)
        self._alerts = deque(maxlen=100)
        self._caches = {}
        self._object_pools = {}
        self._weak_refs = weakref.WeakSet()
        
        # Statistics
        self._gc_triggered_count = 0
        self._peak_memory_mb = 0.0
        self._memory_warnings_count = 0
        
        # Alert callbacks
        self._alert_callbacks = []
        
        # Business info store for compatibility
        self.business_info_store = {}
        
        # Initialize monitoring
        self._setup_monitoring()
    
    def _setup_monitoring(self):
        """Setup memory monitoring."""
        # Set up garbage collection callbacks
        if self.enable_auto_gc:
            gc.set_debug(gc.DEBUG_STATS)
        
        self.logger.info(
            "Memory manager initialized",
            threshold_percent=self.memory_threshold_percent,
            process_limit_mb=self.process_memory_limit_mb,
            auto_gc=self.enable_auto_gc
        )
    
    def start_monitoring(self):
        """Start memory monitoring loop."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring loop."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
        self.logger.info("Memory monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._monitoring:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Error in memory monitoring loop", error=e)
                await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_metrics(self):
        """Collect current memory metrics."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()
            
            metrics = MemoryMetrics(
                process_memory_mb=memory_info.rss / 1024 / 1024,
                system_memory_percent=system_memory.percent,
                available_memory_mb=system_memory.available / 1024 / 1024,
                gc_collections={i: gc.get_count()[i] for i in range(3)},
                object_counts=self._get_object_counts(),
                cache_sizes={name: cache.size() for name, cache in self._caches.items()},
                active_threads=threading.active_count()
            )
            
            # Update peak memory
            if metrics.process_memory_mb > self._peak_memory_mb:
                self._peak_memory_mb = metrics.process_memory_mb
            
            # Store metrics
            self._metrics_history.append(metrics)
            
            # Check for alerts
            await self._check_memory_alerts(metrics)
            
            # Log metrics periodically
            if len(self._metrics_history) % 10 == 0:  # Every 10 collections
                self.logger.performance_log(
                    "memory_metrics",
                    metrics.process_memory_mb,
                    metadata=metrics.to_dict()
                )
            
        except Exception as e:
            self.logger.error("Error collecting memory metrics", error=e)
    
    def _get_object_counts(self) -> Dict[str, int]:
        """Get counts of different object types."""
        counts = defaultdict(int)
        for obj in gc.get_objects():
            obj_type = type(obj).__name__
            counts[obj_type] += 1
        
        # Return top 10 most common objects
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    async def _check_memory_alerts(self, metrics: MemoryMetrics):
        """Check for memory-related alerts."""
        if not self.enable_alerts:
            return
        
        alerts = []
        
        # Process memory limit alert
        if metrics.process_memory_mb > self.process_memory_limit_mb:
            alerts.append(MemoryAlert(
                alert_type="process_memory_limit",
                severity="critical",
                message=f"Process memory ({metrics.process_memory_mb:.1f}MB) exceeds limit ({self.process_memory_limit_mb}MB)",
                metrics=metrics
            ))
        
        # System memory threshold alert
        if metrics.system_memory_percent > self.memory_threshold_percent:
            severity = "critical" if metrics.system_memory_percent > 95 else "high"
            alerts.append(MemoryAlert(
                alert_type="system_memory_high",
                severity=severity,
                message=f"System memory usage ({metrics.system_memory_percent:.1f}%) above threshold",
                metrics=metrics
            ))
        
        # Low available memory alert
        if metrics.available_memory_mb < 500:  # Less than 500MB available
            alerts.append(MemoryAlert(
                alert_type="low_available_memory",
                severity="high",
                message=f"Low available memory: {metrics.available_memory_mb:.1f}MB",
                metrics=metrics
            ))
        
        # Process alerts
        for alert in alerts:
            await self._process_alert(alert)
    
    async def _process_alert(self, alert: MemoryAlert):
        """Process a memory alert."""
        self._alerts.append(alert)
        self._memory_warnings_count += 1
        
        self.logger.warning(
            f"Memory alert: {alert.message}",
            alert_type=alert.alert_type,
            severity=alert.severity,
            process_memory_mb=alert.metrics.process_memory_mb,
            system_memory_percent=alert.metrics.system_memory_percent
        )
        
        # Trigger automatic garbage collection for critical alerts
        if alert.severity == "critical" and self.enable_auto_gc:
            await self._trigger_garbage_collection()
        
        # Call registered alert callbacks
        for callback in self._alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                self.logger.error("Error in alert callback", error=e)
    
    async def _trigger_garbage_collection(self):
        """Trigger garbage collection."""
        try:
            collected = gc.collect()
            self._gc_triggered_count += 1
            
            self.logger.info(
                "Garbage collection triggered",
                objects_collected=collected,
                generation_counts=gc.get_count()
            )
            
        except Exception as e:
            self.logger.error("Error during garbage collection", error=e)
    
    def create_cache(self, name: str, max_size: int = 1000, ttl_seconds: int = 3600) -> MemoryCache:
        """Create a managed memory cache."""
        with self._lock:
            cache = MemoryCache(max_size, ttl_seconds)
            self._caches[name] = cache
            
            self.logger.info(
                f"Created memory cache: {name}",
                max_size=max_size,
                ttl_seconds=ttl_seconds
            )
            
            return cache
    
    def get_cache(self, name: str) -> Optional[MemoryCache]:
        """Get an existing cache."""
        return self._caches.get(name)
    
    def delete_cache(self, name: str):
        """Delete a cache."""
        with self._lock:
            if name in self._caches:
                self._caches[name].clear()
                del self._caches[name]
                self.logger.info(f"Deleted memory cache: {name}")
    
    def clear_all_caches(self):
        """Clear all managed caches."""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()
            self.logger.info("Cleared all memory caches")
    
    def register_alert_callback(self, callback: Callable[[MemoryAlert], Union[None, Any]]):
        """Register a callback for memory alerts."""
        self._alert_callbacks.append(callback)
    
    def get_current_metrics(self) -> Optional[MemoryMetrics]:
        """Get the most recent metrics."""
        return self._metrics_history[-1] if self._metrics_history else None
    
    def get_metrics_history(self, limit: int = 100) -> List[MemoryMetrics]:
        """Get recent metrics history."""
        return list(self._metrics_history)[-limit:]
    
    def get_alerts(self, limit: int = 50) -> List[MemoryAlert]:
        """Get recent alerts."""
        return list(self._alerts)[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory manager statistics."""
        current_metrics = self.get_current_metrics()
        
        return {
            "monitoring_active": self._monitoring,
            "peak_memory_mb": self._peak_memory_mb,
            "gc_triggered_count": self._gc_triggered_count,
            "memory_warnings_count": self._memory_warnings_count,
            "total_alerts": len(self._alerts),
            "active_caches": len(self._caches),
            "cache_stats": {name: cache.stats() for name, cache in self._caches.items()},
            "current_metrics": current_metrics.to_dict() if current_metrics else None,
            "configuration": {
                "memory_threshold_percent": self.memory_threshold_percent,
                "process_memory_limit_mb": self.process_memory_limit_mb,
                "monitoring_interval": self.monitoring_interval,
                "enable_auto_gc": self.enable_auto_gc,
                "enable_alerts": self.enable_alerts
            }
        }
    
    def optimize_memory(self):
        """Perform memory optimization."""
        self.logger.info("Starting memory optimization")
        
        # Clear all caches
        self.clear_all_caches()
        
        # Force garbage collection
        collected_objects = gc.collect()
        
        # Get updated metrics
        process = psutil.Process()
        memory_after = process.memory_info().rss / 1024 / 1024
        
        self.logger.info(
            "Memory optimization completed",
            collected_objects=collected_objects,
            memory_after_mb=memory_after
        )
        
        return {
            "collected_objects": collected_objects,
            "memory_after_mb": memory_after,
            "caches_cleared": len(self._caches)
        }
    
    # Chat history methods for compatibility
    def get_full_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get full chat history for a session."""
        cache_name = f"chat_history_{session_id}"
        cache = self.get_cache(cache_name)
        if cache:
            history = cache.get("history", [])
            return history if isinstance(history, list) else []
        return []
    
    def get_long_term_memory(self, session_id: str) -> Dict[str, Any]:
        """Get long-term memory for a session."""
        cache_name = f"long_term_memory_{session_id}"
        cache = self.get_cache(cache_name)
        if cache:
            memory = cache.get("memory", {})
            return memory if isinstance(memory, dict) else {}
        return {}
    
    def add_to_chat_history(self, session_id: str, message: Dict[str, Any]):
        """Add a message to chat history."""
        cache_name = f"chat_history_{session_id}"
        cache = self.get_cache(cache_name)
        if not cache:
            cache = self.create_cache(cache_name, max_size=1000, ttl_seconds=3600)
        
        history = cache.get("history", [])
        if not isinstance(history, list):
            history = []
        
        history.append(message)
        # Keep only last 100 messages
        if len(history) > 100:
            history = history[-100:]
        
        cache.set("history", history)
    
    def update_long_term_memory(self, session_id: str, memory_data: Dict[str, Any]):
        """Update long-term memory for a session."""
        cache_name = f"long_term_memory_{session_id}"
        cache = self.get_cache(cache_name)
        if not cache:
            cache = self.create_cache(cache_name, max_size=100, ttl_seconds=7200)
        
        current_memory = cache.get("memory", {})
        if not isinstance(current_memory, dict):
            current_memory = {}
        
        current_memory.update(memory_data)
        cache.set("memory", current_memory)
    
    def get_chat_history(self, session_id: str):
        """Get chat history manager for a session."""
        return ChatHistoryManager(self, session_id)
    
    def get_chart_preferences(self, session_id: str) -> Dict[str, Any]:
        """Get chart preferences for a session."""
        cache = self.get_cache("memory")
        if not cache:
            return {}
        
        key = f"{session_id}_chart_prefs"
        preferences = cache.get(key)
        if preferences is None:
            # Return default chart preferences
            return {
                "chart_type": "auto",
                "color_scheme": "default",
                "animation": True,
                "responsive": True,
                "grid": True,
                "legend": True
            }
        return preferences if isinstance(preferences, dict) else {}
    
    def set_chart_preferences(self, session_id: str, preferences: Dict[str, Any]):
        """Set chart preferences for a session."""
        cache = self.get_cache("memory")
        if not cache:
            cache = self.create_cache("memory")
        
        key = f"{session_id}_chart_prefs"
        cache.set(key, preferences)
    
    def update_long_term_memory_with_prompt(self, session_id: str, prompt: str, response: str):
        """Update long-term memory with prompt and response."""
        memory_data = {
            "last_prompt": prompt,
            "last_response": response,
            "last_updated": datetime.now().isoformat()
        }
        self.update_long_term_memory(session_id, memory_data)


class ChatHistoryManager:
    """Manages chat history for a specific session."""
    
    def __init__(self, memory_manager: MCPMemoryManager, session_id: str):
        self.memory_manager = memory_manager
        self.session_id = session_id
    
    def add_user_message(self, message: str):
        """Add a user message to chat history."""
        message_data = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        self.memory_manager.add_to_chat_history(self.session_id, message_data)
    
    def add_ai_message(self, message: str):
        """Add an AI message to chat history."""
        message_data = {
            "role": "assistant", 
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        self.memory_manager.add_to_chat_history(self.session_id, message_data)


def memory_profile(manager: Optional[MCPMemoryManager] = None):
    """Decorator to profile memory usage of functions."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            mem_manager = manager or MCPMemoryManager()
            func_name = f"{func.__module__}.{func.__name__}"
            
            # Get memory before
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024
            
            try:
                result = await func(*args, **kwargs)
                
                # Get memory after
                memory_after = process.memory_info().rss / 1024 / 1024
                memory_diff = memory_after - memory_before
                
                mem_manager.logger.performance_log(
                    f"memory_profile:{func_name}",
                    memory_diff,
                    metadata={
                        "memory_before_mb": memory_before,
                        "memory_after_mb": memory_after,
                        "memory_diff_mb": memory_diff,
                        "function": func_name
                    }
                )
                
                return result
            except Exception as e:
                mem_manager.logger.error(
                    f"Memory profiled function failed: {func_name}",
                    error=e
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            mem_manager = manager or MCPMemoryManager()
            func_name = f"{func.__module__}.{func.__name__}"
            
            # Get memory before
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024
            
            try:
                result = func(*args, **kwargs)
                
                # Get memory after
                memory_after = process.memory_info().rss / 1024 / 1024
                memory_diff = memory_after - memory_before
                
                mem_manager.logger.performance_log(
                    f"memory_profile:{func_name}",
                    memory_diff,
                    metadata={
                        "memory_before_mb": memory_before,
                        "memory_after_mb": memory_after,
                        "memory_diff_mb": memory_diff,
                        "function": func_name
                    }
                )
                
                return result
            except Exception as e:
                mem_manager.logger.error(
                    f"Memory profiled function failed: {func_name}",
                    error=e
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Global memory manager instance
mcp_memory_manager = MCPMemoryManager()

# Alias for backward compatibility
memory_manager = mcp_memory_manager
MemoryManager = MCPMemoryManager


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_memory_manager():
        """Test memory manager functionality."""
        manager = MCPMemoryManager(
            memory_threshold_percent=70.0,
            monitoring_interval=5
        )
        
        # Start monitoring
        manager.start_monitoring()
        
        # Create a test cache
        cache = manager.create_cache("test_cache", max_size=100)
        
        # Add some data to cache
        for i in range(50):
            cache.set(f"key_{i}", f"value_{i}")
        
        # Wait for monitoring
        await asyncio.sleep(10)
        
        # Get statistics
        stats = manager.get_statistics()
        print(f"Memory manager stats: {stats}")
        
        # Stop monitoring
        manager.stop_monitoring()
    
    asyncio.run(test_memory_manager())
