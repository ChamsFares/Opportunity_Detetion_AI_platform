"""
Centralized settings management for OpportunityDetection backend
"""

import os
from typing import List, Dict, Any
from dataclasses import dataclass, field

# Load from environment or use defaults
def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean value from environment variable"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')

def get_env_list(key: str, default: List[str] = None) -> List[str]:
    """Get list value from environment variable"""
    if default is None:
        default = []
    value = os.getenv(key, '')
    return [item.strip() for item in value.split(',') if item.strip()] or default

def get_env_int(key: str, default: int = 0) -> int:
    """Get integer value from environment variable"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default

def get_env_float(key: str, default: float = 0.0) -> float:
    """Get float value from environment variable"""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


@dataclass
class Settings:
    """Application settings"""
    
    # App Info
    app_name: str = "OpportunityDetection Backend"
    app_version: str = "2.0.0"
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = get_env_bool("DEBUG", True)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log_to_file: bool = get_env_bool("LOG_TO_FILE", False)
    
    # Server
    host: str = os.getenv("SERVER_HOST", "localhost")
    port: int = get_env_int("SERVER_PORT", 8000)
    reload: bool = get_env_bool("SERVER_RELOAD", True)
    workers: int = get_env_int("SERVER_WORKERS", 1)
    
    # MCP Server
    mcp_server_name: str = os.getenv("MCP_SERVER_NAME", "OpportunityDetection MCP Server")
    mcp_server_description: str = os.getenv(
        "MCP_SERVER_DESCRIPTION", 
        "Enhanced MCP server for AI-powered market opportunity detection"
    )
    mcp_server_version: str = os.getenv("MCP_SERVER_VERSION", "2.0.0")
    mcp_enable_discovery: bool = get_env_bool("MCP_ENABLE_DISCOVERY", True)
    mcp_enable_context: bool = get_env_bool("MCP_ENABLE_CONTEXT", True)
    mcp_max_context_size: int = get_env_int("MCP_MAX_CONTEXT_SIZE", 10000)
    
    # Database
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "OpportunityDetection")
    mongodb_max_connections: int = get_env_int("MONGODB_MAX_CONNECTIONS", 50)
    mongodb_timeout: int = get_env_int("MONGODB_TIMEOUT", 5000)
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_db: int = get_env_int("REDIS_DB", 0)
    redis_timeout: int = get_env_int("REDIS_TIMEOUT", 5000)
    
    # AI Providers
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # AI Models
    default_ai_provider: str = os.getenv("DEFAULT_AI_PROVIDER", "gemini")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    access_token_expire_minutes: int = get_env_int("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    refresh_token_expire_days: int = get_env_int("REFRESH_TOKEN_EXPIRE_DAYS", 7)
    
    # CORS
    cors_origins: List[str] = field(default_factory=lambda: get_env_list("CORS_ORIGINS", ["*"]))
    cors_allow_credentials: bool = get_env_bool("CORS_ALLOW_CREDENTIALS", False)
    cors_allow_methods: List[str] = field(default_factory=lambda: get_env_list("CORS_ALLOW_METHODS", ["*"]))
    cors_allow_headers: List[str] = field(default_factory=lambda: get_env_list("CORS_ALLOW_HEADERS", ["*"]))
    
    # File Upload
    max_file_size: int = get_env_int("MAX_FILE_SIZE", 10 * 1024 * 1024)  # 10MB
    upload_directory: str = os.getenv("UPLOAD_DIRECTORY", "./uploads")
    allowed_file_types: List[str] = field(default_factory=lambda: get_env_list(
        "ALLOWED_FILE_TYPES", 
        ["pdf", "txt", "doc", "docx", "csv", "xlsx"]
    ))
    
    # Rate Limiting
    rate_limit_requests: int = get_env_int("RATE_LIMIT_REQUESTS", 100)
    rate_limit_period: int = get_env_int("RATE_LIMIT_PERIOD", 3600)
    
    # Cache
    cache_ttl: int = get_env_int("CACHE_TTL", 3600)
    cache_max_size: int = get_env_int("CACHE_MAX_SIZE", 1000)
    
    # Monitoring
    enable_metrics: bool = get_env_bool("ENABLE_METRICS", True)
    enable_tracing: bool = get_env_bool("ENABLE_TRACING", True)
    metrics_port: int = get_env_int("METRICS_PORT", 9090)


# Global settings instance
settings = Settings()
