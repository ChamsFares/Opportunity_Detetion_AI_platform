#!/usr/bin/env python3
"""
Simple database connection test for OpportunityDetection backend
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.config.database import db_manager
from core.config.settings import settings

async def test_database_connection():
    """Test MongoDB connection and basic operations"""
    
    print("🔍 Testing OpportunityDetection Database Connection...")
    print(f"Database: {settings.mongodb_database}")
    print(f"Connection URI: mongodb://localhost:27017 (default)")
    print("-" * 50)
    
    try:
        # Test connection
        print("1. Connecting to MongoDB...")
        await db_manager.connect()
        print("✅ Database connection successful!")
        
        # Test database access
        print("\n2. Testing database access...")
        db = db_manager.database
        
        # List collections
        print("\n3. Listing existing collections...")
        collections = await db.list_collection_names()
        print(f"📁 Found {len(collections)} collections:")
        for collection in collections:
            print(f"   - {collection}")
        
        # Test write operation
        print("\n4. Testing write operation...")
        test_collection = db.connection_test
        test_doc = {
            "test_id": "db_connection_test",
            "timestamp": datetime.utcnow(),
            "status": "testing_connection",
            "message": "Database connection test from OpportunityDetection backend"
        }
        
        result = await test_collection.insert_one(test_doc)
        print(f"✅ Document inserted with ID: {result.inserted_id}")
        
        # Test read operation
        print("\n5. Testing read operation...")
        found_doc = await test_collection.find_one({"test_id": "db_connection_test"})
        if found_doc:
            print("✅ Document retrieved successfully!")
            print(f"   - Test ID: {found_doc['test_id']}")
            print(f"   - Timestamp: {found_doc['timestamp']}")
            print(f"   - Message: {found_doc['message']}")
        else:
            print("❌ Failed to retrieve test document")
        
        # Test update operation
        print("\n6. Testing update operation...")
        update_result = await test_collection.update_one(
            {"test_id": "db_connection_test"},
            {"$set": {"status": "connection_verified", "last_updated": datetime.utcnow()}}
        )
        print(f"✅ Document updated. Modified count: {update_result.modified_count}")
        
        # Test count operation
        print("\n7. Testing count operation...")
        doc_count = await test_collection.count_documents({})
        print(f"✅ Total documents in test collection: {doc_count}")
        
        # Test aggregation
        print("\n8. Testing aggregation operation...")
        pipeline = [
            {"$match": {"test_id": "db_connection_test"}},
            {"$project": {"test_id": 1, "status": 1, "timestamp": 1}}
        ]
        async for doc in test_collection.aggregate(pipeline):
            print(f"✅ Aggregation result: {doc}")
        
        # Cleanup test document
        print("\n9. Cleaning up test data...")
        delete_result = await test_collection.delete_many({"test_id": "db_connection_test"})
        print(f"✅ Cleaned up {delete_result.deleted_count} test documents")
        
        print("\n" + "="*50)
        print("🎉 DATABASE CONNECTION TEST COMPLETED SUCCESSFULLY!")
        print("✅ All database operations working correctly")
        print("✅ MongoDB connection is healthy")
        print("✅ OpportunityDetection database is ready for use")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Database connection test failed!")
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        # Provide troubleshooting tips
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure MongoDB is running on localhost:27017")
        print("2. Check if the 'OpportunityDetection' database exists")
        print("3. Verify MongoDB connection string in .env file")
        print("4. Ensure no firewall is blocking the connection")
        
        return False
        
    finally:
        # Disconnect
        try:
            await db_manager.disconnect()
            print("\n🔌 Disconnected from database")
        except:
            pass


if __name__ == "__main__":
    print("Starting OpportunityDetection Database Test...")
    
    # Run the async test
    success = asyncio.run(test_database_connection())
    
    if success:
        print("\n🚀 Database is ready for OpportunityDetection backend!")
        sys.exit(0)
    else:
        print("\n⚠️  Database connection issues detected")
        sys.exit(1)
