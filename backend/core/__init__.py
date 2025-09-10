"""
Backend core module initialization
"""

from .config import (
    settings, 
    Settings,
    db_manager,
    get_database,
    Collections,
    create_indexes
)

__all__ = [
    "settings",
    "Settings", 
    "db_manager",
    "get_database",
    "Collections",
    "create_indexes"
]
