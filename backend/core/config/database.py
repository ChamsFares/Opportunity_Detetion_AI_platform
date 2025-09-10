"""
Database configuration for OpportunityDetection backend
"""

import logging
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .settings import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection manager"""
    
    def __init__(self):
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self) -> None:
        """Connect to MongoDB"""
        try:
            self._client = AsyncIOMotorClient(
                settings.mongodb_url,
                maxPoolSize=settings.mongodb_max_connections,
                serverSelectionTimeoutMS=settings.mongodb_timeout,
                connectTimeoutMS=settings.mongodb_timeout,
            )
            
            # Test connection
            await self._client.admin.command('ping')
            self._database = self._client[settings.mongodb_database]
            
            logger.info(f"Connected to MongoDB database: {settings.mongodb_database}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        if self._client:
            self._client.close()
            logger.info("Disconnected from MongoDB")
    
    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if self._database is None:
            raise RuntimeError("Database not connected")
        return self._database
    
    @property
    def client(self) -> AsyncIOMotorClient:
        """Get client instance"""
        if self._client is None:
            raise RuntimeError("Database not connected")
        return self._client


# Global database manager
db_manager = DatabaseManager()


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return db_manager.database


def get_database_config() -> Dict[str, Any]:
    """Get database configuration"""
    return {
        "url": settings.mongodb_url,
        "database": settings.mongodb_database,
        "max_connections": settings.mongodb_max_connections,
        "timeout": settings.mongodb_timeout
    }


# Collection names
class Collections:
    """Database collection names"""
    USERS = "users"
    ANALYSES = "analyses"
    REPORTS = "reports"
    COMPANIES = "companies"
    COMPETITORS = "competitors"
    TRENDS = "trends"
    SESSIONS = "sessions"
    CACHE = "cache"
    METRICS = "metrics"


# Database indexes
DATABASE_INDEXES = {
    Collections.USERS: [
        {"key": "email", "unique": True},
        {"key": "created_at"},
    ],
    Collections.ANALYSES: [
        {"key": "user_id"},
        {"key": "company_name"},
        {"key": "analysis_type"},
        {"key": "created_at"},
        {"key": "status"},
    ],
    Collections.REPORTS: [
        {"key": "analysis_id"},
        {"key": "user_id"},
        {"key": "created_at"},
    ],
    Collections.COMPANIES: [
        {"key": "name", "unique": True},
        {"key": "industry"},
        {"key": "size"},
        {"key": "location"},
    ],
    Collections.COMPETITORS: [
        {"key": "company_id"},
        {"key": "competitor_name"},
        {"key": "similarity_score"},
    ],
    Collections.TRENDS: [
        {"key": "industry"},
        {"key": "region"},
        {"key": "trend_type"},
        {"key": "date"},
    ],
    Collections.SESSIONS: [
        {"key": "user_id"},
        {"key": "session_id", "unique": True},
        {"key": "expires_at", "expireAfterSeconds": 0},
    ],
    Collections.CACHE: [
        {"key": "cache_key", "unique": True},
        {"key": "expires_at", "expireAfterSeconds": 0},
    ],
    Collections.METRICS: [
        {"key": "metric_type"},
        {"key": "timestamp"},
        {"key": "user_id"},
    ]
}


async def create_indexes():
    """Create database indexes"""
    try:
        database = await get_database()
        
        for collection_name, indexes in DATABASE_INDEXES.items():
            collection = database[collection_name]
            
            for index_config in indexes:
                key = index_config["key"]
                options = {k: v for k, v in index_config.items() if k != "key"}
                
                await collection.create_index(key, **options)
                logger.info(f"Created index on {collection_name}.{key}")
                
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")
        raise
