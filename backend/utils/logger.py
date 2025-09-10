"""
Enhanced Logger Utility for MCP Backend
Comprehensive logging system with structured logging and monitoring capabilities.
"""

import logging
import logging.handlers
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from contextlib import contextmanager
import asyncio
import inspect
from functools import wraps

# Third-party imports
try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


class MCPLoggerConfig:
    """Configuration for MCP logger."""
    
    def __init__(
        self,
        log_level: str = "INFO",
        log_format: str = "json",
        enable_file_logging: bool = True,
        enable_console_logging: bool = True,
        log_directory: str = "logs",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        enable_async_logging: bool = True,
        enable_metrics: bool = True,
        sensitive_fields: Optional[List[str]] = None
    ):
        self.log_level = log_level.upper()
        self.log_format = log_format
        self.enable_file_logging = enable_file_logging
        self.enable_console_logging = enable_console_logging
        self.log_directory = Path(log_directory)
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.enable_async_logging = enable_async_logging
        self.enable_metrics = enable_metrics
        self.sensitive_fields = sensitive_fields or [
            "password", "token", "secret", "key", "auth", "credential"
        ]


class MCPLogger:
    """Enhanced logger for MCP backend with structured logging and monitoring."""
    
    _instance = None
    _logger = None
    _config = None
    _metrics = {}
    
    def __new__(cls, config: Optional[MCPLoggerConfig] = None):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(config or MCPLoggerConfig())
        return cls._instance
    
    def _initialize(self, config: MCPLoggerConfig):
        """Initialize the logger with configuration."""
        self._config = config
        self._setup_directories()
        self._setup_logger()
        self._setup_metrics()
    
    def _setup_directories(self):
        """Create necessary directories for logging."""
        self._config.log_directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_logger(self):
        """Setup the main logger with handlers."""
        # Create base logger
        self._logger = logging.getLogger("mcp_backend")
        self._logger.setLevel(getattr(logging, self._config.log_level))
        
        # Clear existing handlers
        self._logger.handlers.clear()
        
        # Setup formatters
        if self._config.log_format == "json":
            formatter = self._create_json_formatter()
        else:
            formatter = self._create_standard_formatter()
        
        # Console handler
        if self._config.enable_console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)
        
        # File handler
        if self._config.enable_file_logging:
            file_handler = logging.handlers.RotatingFileHandler(
                self._config.log_directory / "mcp_backend.log",
                maxBytes=self._config.max_file_size,
                backupCount=self._config.backup_count
            )
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
            
            # Error-specific file handler
            error_handler = logging.handlers.RotatingFileHandler(
                self._config.log_directory / "mcp_errors.log",
                maxBytes=self._config.max_file_size,
                backupCount=self._config.backup_count
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            self._logger.addHandler(error_handler)
    
    def _create_json_formatter(self):
        """Create JSON formatter for structured logging."""
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                    "thread": record.thread,
                    "process": record.process
                }
                
                # Add extra fields if present
                if hasattr(record, "extra_data"):
                    log_entry.update(record.extra_data)
                
                # Add exception information if present
                if record.exc_info:
                    log_entry["exception"] = {
                        "type": record.exc_info[0].__name__,
                        "message": str(record.exc_info[1]),
                        "traceback": traceback.format_exception(*record.exc_info)
                    }
                
                return json.dumps(log_entry, default=str)
        
        return JSONFormatter()
    
    def _create_standard_formatter(self):
        """Create standard formatter for human-readable logging."""
        return logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s"
        )
    
    def _setup_metrics(self):
        """Setup logging metrics tracking."""
        if self._config.enable_metrics:
            self._metrics = {
                "total_logs": 0,
                "error_count": 0,
                "warning_count": 0,
                "info_count": 0,
                "debug_count": 0,
                "start_time": datetime.utcnow(),
                "last_error": None,
                "most_frequent_errors": {},
                "performance_logs": []
            }
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data from log entries."""
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self._config.sensitive_fields):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized
    
    def _update_metrics(self, level: str, extra_data: Optional[Dict[str, Any]] = None):
        """Update logging metrics."""
        if not self._config.enable_metrics:
            return
        
        self._metrics["total_logs"] += 1
        
        level_key = f"{level.lower()}_count"
        if level_key in self._metrics:
            self._metrics[level_key] += 1
        
        if level == "ERROR" and extra_data:
            error_type = extra_data.get("error_type", "Unknown")
            self._metrics["most_frequent_errors"][error_type] = (
                self._metrics["most_frequent_errors"].get(error_type, 0) + 1
            )
            self._metrics["last_error"] = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": error_type,
                "message": extra_data.get("message", "")
            }
    
    def _log(self, level: str, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Internal logging method."""
        if not self._logger:
            return
        
        # Sanitize extra data
        if extra_data:
            extra_data = self._sanitize_data(extra_data)
        
        # Update metrics
        self._update_metrics(level, extra_data)
        
        # Create log record with extra data
        if extra_data:
            self._logger.log(
                getattr(logging, level),
                message,
                extra={"extra_data": extra_data}
            )
        else:
            self._logger.log(getattr(logging, level), message)
    
    # Public logging methods
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log("DEBUG", message, kwargs if kwargs else None)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log("INFO", message, kwargs if kwargs else None)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log("WARNING", message, kwargs if kwargs else None)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception."""
        extra_data = kwargs.copy() if kwargs else {}
        
        if error:
            extra_data.update({
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc()
            })
        
        self._log("ERROR", message, extra_data)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log critical message with optional exception."""
        extra_data = kwargs.copy() if kwargs else {}
        
        if error:
            extra_data.update({
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc()
            })
        
        self._log("CRITICAL", message, extra_data)
    
    # MCP-specific logging methods
    def mcp_tool_call(self, tool_name: str, parameters: Dict[str, Any], duration: float = None):
        """Log MCP tool call."""
        self.info(
            f"MCP tool called: {tool_name}",
            tool_name=tool_name,
            parameters=parameters,
            duration=duration,
            category="mcp_tool_call"
        )
    
    def mcp_tool_result(self, tool_name: str, success: bool, result_size: int = None, duration: float = None):
        """Log MCP tool result."""
        self.info(
            f"MCP tool result: {tool_name}",
            tool_name=tool_name,
            success=success,
            result_size=result_size,
            duration=duration,
            category="mcp_tool_result"
        )
    
    def api_request(self, method: str, endpoint: str, status_code: int, duration: float = None, user_id: str = None):
        """Log API request."""
        self.info(
            f"API request: {method} {endpoint}",
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration=duration,
            user_id=user_id,
            category="api_request"
        )
    
    def database_operation(self, operation: str, collection: str, duration: float = None, record_count: int = None):
        """Log database operation."""
        self.info(
            f"Database operation: {operation} on {collection}",
            operation=operation,
            collection=collection,
            duration=duration,
            record_count=record_count,
            category="database_operation"
        )
    
    def performance_log(self, operation: str, duration: float, metadata: Optional[Dict[str, Any]] = None):
        """Log performance metrics."""
        log_data = {
            "operation": operation,
            "duration": duration,
            "category": "performance"
        }
        
        if metadata:
            log_data.update(metadata)
        
        if self._config.enable_metrics and duration is not None:
            self._metrics["performance_logs"].append({
                "operation": operation,
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Keep only last 1000 performance logs
            if len(self._metrics["performance_logs"]) > 1000:
                self._metrics["performance_logs"] = self._metrics["performance_logs"][-1000:]
        
        self.info(f"Performance: {operation}", **log_data)
    
    @contextmanager
    def performance_context(self, operation: str, **metadata):
        """Context manager for performance logging."""
        start_time = datetime.utcnow()
        try:
            yield
        finally:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.performance_log(operation, duration, metadata)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current logging metrics."""
        if not self._config.enable_metrics:
            return {"metrics_disabled": True}
        
        return self._metrics.copy()
    
    def reset_metrics(self):
        """Reset logging metrics."""
        if self._config.enable_metrics:
            self._setup_metrics()


def log_function_calls(logger_instance: Optional[MCPLogger] = None):
    """Decorator to log function calls and performance."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = logger_instance or MCPLogger()
            func_name = f"{func.__module__}.{func.__name__}"
            
            with logger.performance_context(f"function_call:{func_name}"):
                try:
                    logger.debug(
                        f"Calling function: {func_name}",
                        function=func_name,
                        args_count=len(args),
                        kwargs_count=len(kwargs)
                    )
                    result = await func(*args, **kwargs)
                    logger.debug(f"Function completed: {func_name}", function=func_name)
                    return result
                except Exception as e:
                    logger.error(
                        f"Function failed: {func_name}",
                        error=e,
                        function=func_name
                    )
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = logger_instance or MCPLogger()
            func_name = f"{func.__module__}.{func.__name__}"
            
            with logger.performance_context(f"function_call:{func_name}"):
                try:
                    logger.debug(
                        f"Calling function: {func_name}",
                        function=func_name,
                        args_count=len(args),
                        kwargs_count=len(kwargs)
                    )
                    result = func(*args, **kwargs)
                    logger.debug(f"Function completed: {func_name}", function=func_name)
                    return result
                except Exception as e:
                    logger.error(
                        f"Function failed: {func_name}",
                        error=e,
                        function=func_name
                    )
                    raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Global logger instance
mcp_logger = MCPLogger()


def get_logger(name: Optional[str] = None) -> MCPLogger:
    """Get the global logger instance (for backward compatibility)."""
    return mcp_logger


# Convenience functions
def debug(message: str, **kwargs):
    """Global debug logging function."""
    mcp_logger.debug(message, **kwargs)

def info(message: str, **kwargs):
    """Global info logging function."""
    mcp_logger.info(message, **kwargs)

def warning(message: str, **kwargs):
    """Global warning logging function."""
    mcp_logger.warning(message, **kwargs)

def error(message: str, error_obj: Optional[Exception] = None, **kwargs):
    """Global error logging function."""
    mcp_logger.error(message, error=error_obj, **kwargs)

def critical(message: str, error_obj: Optional[Exception] = None, **kwargs):
    """Global critical logging function."""
    mcp_logger.critical(message, error=error_obj, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    # Configure logger
    config = MCPLoggerConfig(
        log_level="DEBUG",
        log_format="json",
        enable_metrics=True
    )
    
    logger = MCPLogger(config)
    
    # Test logging
    logger.info("MCP backend logger initialized", version="1.0.0")
    logger.mcp_tool_call("test_tool", {"param1": "value1"}, duration=0.5)
    logger.api_request("GET", "/api/v1/test", 200, duration=0.1)
    
    # Test performance context
    with logger.performance_context("test_operation"):
        import time
        time.sleep(0.1)
    
    # Get metrics
    metrics = logger.get_metrics()
    print(f"Logger metrics: {json.dumps(metrics, indent=2, default=str)}")
