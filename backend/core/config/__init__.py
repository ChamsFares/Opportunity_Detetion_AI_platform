"""
Core configuration module initialization
"""

from .settings import settings, Settings
from .database import (
    DatabaseManager,
    db_manager,
    get_database,
    get_database_config,
    Collections,
    DATABASE_INDEXES,
    create_indexes
)

__all__ = [
    # Settings
    "settings",
    "Settings",
    
    # Database
    "DatabaseManager",
    "db_manager", 
    "get_database",
    "get_database_config",
    "Collections",
    "DATABASE_INDEXES",
    "create_indexes"
]
