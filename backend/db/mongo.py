"""
MongoDB Database Configuration and Connection Management
Async MongoDB client with Motor driver for MCP-enabled backend.
"""

import os
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from utils.logger import get_logger

load_dotenv()
logger = get_logger("mongo")

# Environment configuration
MONGO_URI = os.getenv("MONGO_DB_URL", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "OpportunityDetection")
MAX_POOL_SIZE = int(os.getenv("MONGO_MAX_POOL_SIZE", "10"))
SERVER_SELECTION_TIMEOUT = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT", "30000"))


class MongoDBManager:
    """
    MongoDB connection manager with async support and connection pooling.
    Provides database access for MCP tools and API routes.
    """
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.is_connected = False
    
    async def connect(self) -> bool:
        """
        Establish connection to MongoDB with error handling and retry logic.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = AsyncIOMotorClient(
                MONGO_URI,
                serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                retryWrites=True,
                maxPoolSize=MAX_POOL_SIZE,
                waitQueueTimeoutMS=30000,
                # Additional reliability settings
                retryReads=True,
                w='majority',
                readPreference='primary',
                heartbeatFrequencyMS=30000,
            )
            
            self.database = self.client[DB_NAME]
            
            # Test connection
            await self.client.admin.command("ping")
            
            # Create indexes for better performance
            await self._create_indexes()
            
            self.is_connected = True
            logger.info(f"✅ Connected to MongoDB at {MONGO_URI}, using DB: {DB_NAME}")
            logger.info(f"📊 Connection pool size: {MAX_POOL_SIZE}, timeout: {SERVER_SELECTION_TIMEOUT}ms")
            
            return True
            
        except PyMongoError as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during MongoDB connection: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Close MongoDB connection gracefully."""
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("📴 MongoDB connection closed")
    
    async def _create_indexes(self):
        """
        Create database indexes for optimal performance.
        Called during connection establishment.
        """
        try:
            # Extracted infos collection indexes
            await self.database.extracted_infos.create_index("session_id")
            await self.database.extracted_infos.create_index("company_name")
            await self.database.extracted_infos.create_index("created_at")
            
            # Confirmed infos collection indexes
            await self.database.confirmed_infos.create_index("session_id")
            await self.database.confirmed_infos.create_index("company_name")
            await self.database.confirmed_infos.create_index("created_at")
            
            # Confirmations collection indexes
            await self.database.confirmations.create_index("prompt_id")
            await self.database.confirmations.create_index("session_id")
            await self.database.confirmations.create_index("timestamp")
            await self.database.confirmations.create_index("is_confirmed")
            
            # Competitors collection indexes
            await self.database.competitors.create_index([("company_name", 1), ("analysis_session", 1)], unique=True)
            await self.database.competitors.create_index("relevance_score")
            await self.database.competitors.create_index("created_at")
            await self.database.competitors.create_index("market_position")
            
            # Market news collection indexes
            await self.database.market_news.create_index([("title", 1), ("source", 1)])
            await self.database.market_news.create_index("analysis_sessions")
            await self.database.market_news.create_index("published_date")
            await self.database.market_news.create_index("category")
            await self.database.market_news.create_index("keywords_matched")
            await self.database.market_news.create_index("relevance_score")
            await self.database.market_news.create_index("sentiment")
            
            # Market trends collection indexes
            await self.database.market_trends.create_index("analysis_session")
            await self.database.market_trends.create_index("category")
            await self.database.market_trends.create_index("impact_level")
            await self.database.market_trends.create_index("confidence_score")
            await self.database.market_trends.create_index("time_horizon")
            await self.database.market_trends.create_index("created_at")
            
            # Market analyses collection indexes
            await self.database.market_analyses.create_index("analysis_session", unique=True)
            await self.database.market_analyses.create_index([("company", 1), ("sector", 1), ("service", 1)])
            await self.database.market_analyses.create_index("created_at")
            await self.database.market_analyses.create_index("analysis_type")
            await self.database.market_analyses.create_index("data_size")
            
            # Crawled infos collection indexes (for web scraping data)
            await self.database.crawled_infos.create_index("session_id")
            await self.database.crawled_infos.create_index("company_name")
            await self.database.crawled_infos.create_index("url")
            await self.database.crawled_infos.create_index("created_at")
            
            # Charts collection indexes (for chart data storage)
            await self.database.charts.create_index("session_id")
            await self.database.charts.create_index("user_id")
            await self.database.charts.create_index("chart_type")
            await self.database.charts.create_index("created_at")
            await self.database.charts.create_index("generation_source")
            
            # Progress tracking collection indexes
            await self.database.progress_tracking.create_index("session_id", unique=True)
            await self.database.progress_tracking.create_index("status")
            await self.database.progress_tracking.create_index("created_at")
            await self.database.progress_tracking.create_index("company")
            
            logger.info("📈 Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to create some database indexes: {e}")
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """
        Get the database instance for use by MCP tools and API routes.
        
        Returns:
            AsyncIOMotorDatabase: The database instance
            
        Raises:
            RuntimeError: If database is not connected
        """
        if not self.is_connected or not self.database:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        return self.database
    
    async def health_check(self) -> dict:
        """
        Perform database health check.
        
        Returns:
            dict: Health status information
        """
        try:
            if not self.is_connected:
                return {
                    "status": "disconnected",
                    "error": "Database not connected"
                }
            
            # Ping the database
            result = await self.client.admin.command("ping")
            
            # Get server status
            server_status = await self.client.admin.command("serverStatus")
            
            # Get database stats
            db_stats = await self.database.command("dbStats")
            
            return {
                "status": "healthy",
                "connected": True,
                "ping_result": result,
                "database_name": DB_NAME,
                "connection_uri": MONGO_URI.split('@')[-1] if '@' in MONGO_URI else MONGO_URI,
                "pool_size": MAX_POOL_SIZE,
                "server_version": server_status.get("version"),
                "uptime_seconds": server_status.get("uptime"),
                "collections_count": len(await self.database.list_collection_names()),
                "database_size_mb": round(db_stats.get("dataSize", 0) / (1024 * 1024), 2),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def get_collection_stats(self) -> dict:
        """
        Get statistics for all collections in the database.
        
        Returns:
            dict: Collection statistics
        """
        try:
            collections = await self.database.list_collection_names()
            stats = {}
            
            for collection_name in collections:
                collection = self.database[collection_name]
                count = await collection.count_documents({})
                
                # Get sample document to understand structure
                sample = await collection.find_one()
                
                stats[collection_name] = {
                    "document_count": count,
                    "has_data": count > 0,
                    "sample_fields": list(sample.keys()) if sample else [],
                    "estimated_size": "unknown"  # Could add collStats for more details
                }
            
            return {
                "total_collections": len(collections),
                "collections": stats,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


# Global database manager instance
db_manager = MongoDBManager()


# Legacy compatibility - provides direct database access
class DatabaseWrapper:
    """
    Wrapper to provide legacy-style database access for backward compatibility.
    """
    
    def __getattr__(self, name):
        """
        Dynamically return database collections.
        
        Args:
            name: Collection name
            
        Returns:
            AsyncIOMotorCollection: The requested collection
        """
        if not db_manager.is_connected:
            raise RuntimeError("Database not connected")
        
        return getattr(db_manager.database, name)


# Create global database instance for backward compatibility
db = DatabaseWrapper()


async def init_database():
    """
    Initialize database connection.
    Should be called during application startup.
    
    Returns:
        bool: True if successful, False otherwise
    """
    return await db_manager.connect()


async def close_database():
    """
    Close database connection.
    Should be called during application shutdown.
    """
    await db_manager.disconnect()


async def get_database_health():
    """
    Get database health status.
    
    Returns:
        dict: Health status information
    """
    return await db_manager.health_check()


async def get_database_stats():
    """
    Get database collection statistics.
    
    Returns:
        dict: Collection statistics
    """
    return await db_manager.get_collection_stats()


# For direct access to database instance
def get_db() -> AsyncIOMotorDatabase:
    """
    Get database instance for dependency injection.
    
    Returns:
        AsyncIOMotorDatabase: The database instance
    """
    return db_manager.get_database()
