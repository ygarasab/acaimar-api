"""
MongoDB connection utility for Azure Functions
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging

logger = logging.getLogger(__name__)

# Global connection cache
_client = None
_db = None


def get_mongo_client():
    """Get or create MongoDB client connection"""
    global _client
    
    if _client is None:
        connection_string = os.environ.get('MONGODB_CONNECTION_STRING')
        
        if not connection_string:
            raise ValueError("MONGODB_CONNECTION_STRING environment variable is not set")
        
        try:
            _client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            # Test connection
            _client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    return _client


def get_database():
    """Get database instance"""
    global _db
    
    if _db is None:
        client = get_mongo_client()
        db_name = os.environ.get('MONGODB_DATABASE', 'acaimar')
        _db = client[db_name]
        logger.info(f"Using database: {db_name}")
    
    return _db


def get_collection(collection_name):
    """Get a specific collection from the database"""
    db = get_database()
    return db[collection_name]


def close_connection():
    """Close MongoDB connection (useful for cleanup)"""
    global _client, _db
    
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")
