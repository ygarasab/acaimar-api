"""
Database connection utility for Azure Functions
Supports MongoDB (pymongo) and CosmosDB SQL API (azure-cosmos) via DB_PROVIDER environment variable
"""
import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Global connection cache
_client = None
_database = None
_provider = None

# Import providers conditionally
_pymongo_client = None
_cosmos_client = None
_cosmos_database = None


def get_db_provider():
    """Get the database provider (mongodb or cosmosdb)"""
    global _provider
    if _provider is None:
        _provider = os.environ.get('DB_PROVIDER', 'mongodb').lower()
        if _provider not in ['mongodb', 'cosmosdb']:
            logger.warning(f"Unknown DB_PROVIDER '{_provider}', defaulting to 'mongodb'")
            _provider = 'mongodb'
    return _provider


def get_mongo_client():
    """Get or create MongoDB client connection (for MongoDB provider)"""
    global _pymongo_client
    
    if _pymongo_client is None:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
        
        connection_string = os.environ.get('MONGODB_CONNECTION_STRING')
        if not connection_string:
            raise ValueError("MONGODB_CONNECTION_STRING environment variable is not set")
        
        try:
            _pymongo_client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            # Test connection
            _pymongo_client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    return _pymongo_client


def get_cosmos_client():
    """Get or create CosmosDB SQL API client connection"""
    global _cosmos_client
    
    if _cosmos_client is None:
        from azure.cosmos import CosmosClient, exceptions
        
        endpoint = os.environ.get('COSMOSDB_ENDPOINT') or os.environ.get('COSMOSDB_CONNECTION_STRING')
        key = os.environ.get('COSMOSDB_KEY')
        
        if not endpoint or not key:
            raise ValueError("COSMOSDB_ENDPOINT and COSMOSDB_KEY environment variables are required")
        
        try:
            _cosmos_client = CosmosClient(endpoint, key)
            logger.info("Successfully connected to CosmosDB SQL API")
        except Exception as e:
            logger.error(f"Failed to connect to CosmosDB SQL API: {e}")
            raise
    
    return _cosmos_client


def get_database():
    """Get database instance (provider-agnostic)"""
    global _database
    
    if _database is None:
        provider = get_db_provider()
        
        if provider == 'cosmosdb':
            client = get_cosmos_client()
            db_name = os.environ.get('COSMOSDB_DATABASE') or os.environ.get('MONGODB_DATABASE', 'acaimar')
            _database = client.get_database_client(db_name)
            logger.info(f"Using CosmosDB SQL API database: {db_name}")
        else:
            client = get_mongo_client()
            db_name = os.environ.get('MONGODB_DATABASE', 'acaimar')
            _database = client[db_name]
            logger.info(f"Using MongoDB database: {db_name}")
    
    return _database


class CosmosCollectionWrapper:
    """Wrapper to provide MongoDB-like interface for CosmosDB SQL API containers"""
    
    def __init__(self, container_client):
        self.container = container_client
    
    def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one document matching the filter"""
        from azure.cosmos import exceptions
        
        try:
            # Convert MongoDB filter to SQL query
            query = self._build_query(filter_dict)
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            if items:
                doc = items[0]
                # Convert 'id' to '_id' for compatibility
                if 'id' in doc and '_id' not in doc:
                    doc['_id'] = str(doc.pop('id'))
                elif 'id' in doc:
                    doc['_id'] = str(doc['id'])
                    del doc['id']
                return doc
            return None
        except exceptions.CosmosResourceNotFoundError:
            return None
    
    def find(self, filter_dict: Optional[Dict[str, Any]] = None, projection: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Find documents matching the filter"""
        from azure.cosmos import exceptions
        
        try:
            if filter_dict is None:
                filter_dict = {}
            
            query = self._build_query(filter_dict)
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            # Convert 'id' to '_id' for compatibility
            for item in items:
                if 'id' in item and '_id' not in item:
                    item['_id'] = str(item.pop('id'))
                elif 'id' in item:
                    item['_id'] = str(item['id'])
                    del item['id']
            
            # Apply projection if specified
            if projection:
                items = self._apply_projection(items, projection)
            
            return items
        except exceptions.CosmosResourceNotFoundError:
            return []
    
    def insert_one(self, document: Dict[str, Any]) -> Any:
        """Insert one document"""
        from azure.cosmos import exceptions
        
        # Convert '_id' to 'id' for CosmosDB
        doc = document.copy()
        if '_id' in doc:
            doc['id'] = str(doc.pop('_id'))
        elif 'id' not in doc:
            import uuid
            doc['id'] = str(uuid.uuid4())
        
        try:
            created_item = self.container.create_item(body=doc)
            # Return a result-like object
            class InsertResult:
                def __init__(self, item_id):
                    self.inserted_id = item_id
            return InsertResult(created_item['id'])
        except exceptions.CosmosAccessConditionFailedError as e:
            logger.error(f"Failed to insert document: {e}")
            raise
    
    def update_one(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Any:
        """Update one document"""
        from azure.cosmos import exceptions
        
        # Find the document first
        doc = self.find_one(filter_dict)
        if not doc:
            class UpdateResult:
                modified_count = 0
            return UpdateResult()
        
        # Apply update operations
        if '$set' in update_dict:
            doc.update(update_dict['$set'])
        
        # Convert '_id' back to 'id' for CosmosDB
        if '_id' in doc:
            doc['id'] = str(doc.pop('_id'))
        
        try:
            self.container.replace_item(item=doc['id'], body=doc)
            class UpdateResult:
                modified_count = 1
            return UpdateResult()
        except exceptions.CosmosAccessConditionFailedError as e:
            logger.error(f"Failed to update document: {e}")
            raise
    
    def delete_one(self, filter_dict: Dict[str, Any]) -> Any:
        """Delete one document"""
        from azure.cosmos import exceptions
        
        doc = self.find_one(filter_dict)
        if not doc:
            class DeleteResult:
                deleted_count = 0
            return DeleteResult()
        
        doc_id = doc.get('_id') or doc.get('id')
        try:
            self.container.delete_item(item=str(doc_id), partition_key=str(doc_id))
            class DeleteResult:
                deleted_count = 1
            return DeleteResult()
        except exceptions.CosmosResourceNotFoundError:
            class DeleteResult:
                deleted_count = 0
            return DeleteResult()
    
    def count_documents(self, filter_dict: Dict[str, Any]) -> int:
        """Count documents matching the filter"""
        items = self.find(filter_dict)
        return len(items)
    
    def _build_query(self, filter_dict: Dict[str, Any]) -> str:
        """Convert MongoDB filter to SQL query"""
        if not filter_dict:
            return "SELECT * FROM c"
        
        def escape_string(value):
            """Escape single quotes in SQL strings"""
            if isinstance(value, str):
                return value.replace("'", "''")
            return value
        
        conditions = []
        for key, value in filter_dict.items():
            # Handle _id field mapping to id for CosmosDB
            if key == '_id':
                key = 'id'
            
            if isinstance(value, dict):
                # Handle operators like $gte, $lte, etc.
                for op, op_value in value.items():
                    escaped_value = escape_string(op_value)
                    if op == '$gte':
                        if isinstance(op_value, str):
                            conditions.append(f"c.{key} >= '{escaped_value}'")
                        else:
                            conditions.append(f"c.{key} >= {op_value}")
                    elif op == '$lte':
                        if isinstance(op_value, str):
                            conditions.append(f"c.{key} <= '{escaped_value}'")
                        else:
                            conditions.append(f"c.{key} <= {op_value}")
                    elif op == '$gt':
                        if isinstance(op_value, str):
                            conditions.append(f"c.{key} > '{escaped_value}'")
                        else:
                            conditions.append(f"c.{key} > {op_value}")
                    elif op == '$lt':
                        if isinstance(op_value, str):
                            conditions.append(f"c.{key} < '{escaped_value}'")
                        else:
                            conditions.append(f"c.{key} < {op_value}")
                    elif op == '$ne':
                        if isinstance(op_value, str):
                            conditions.append(f"c.{key} != '{escaped_value}'")
                        else:
                            conditions.append(f"c.{key} != {op_value}")
            else:
                # Simple equality
                escaped_value = escape_string(value)
                if isinstance(value, str):
                    conditions.append(f"c.{key} = '{escaped_value}'")
                elif value is None:
                    conditions.append(f"c.{key} = null")
                else:
                    conditions.append(f"c.{key} = {value}")
        
        where_clause = " AND ".join(conditions)
        return f"SELECT * FROM c WHERE {where_clause}"
    
    def _apply_projection(self, items: List[Dict], projection: Dict[str, Any]) -> List[Dict]:
        """Apply MongoDB-style projection"""
        result = []
        exclude_fields = [k for k, v in projection.items() if v == 0]
        
        for item in items:
            filtered_item = {k: v for k, v in item.items() if k not in exclude_fields}
            result.append(filtered_item)
        
        return result


def get_collection(collection_name: str):
    """Get a specific collection/container from the database (provider-agnostic)"""
    provider = get_db_provider()
    database = get_database()
    
    if provider == 'cosmosdb':
        # CosmosDB SQL API uses containers
        # Try to get the container, create if it doesn't exist
        try:
            container_client = database.get_container_client(collection_name)
            # Try to read container properties to verify it exists
            container_client.read()
        except Exception:
            # Container doesn't exist, create it
            from azure.cosmos import PartitionKey
            logger.info(f"Creating container '{collection_name}' in CosmosDB")
            # For serverless accounts, don't specify offer_throughput
            database.create_container(
                id=collection_name,
                partition_key=PartitionKey(path="/id")
            )
            container_client = database.get_container_client(collection_name)
        
        return CosmosCollectionWrapper(container_client)
    else:
        # MongoDB uses collections
        return database[collection_name]


def close_connection():
    """Close database connection (useful for cleanup)"""
    global _client, _database, _provider, _pymongo_client, _cosmos_client, _cosmos_database
    
    provider = get_db_provider()
    
    if provider == 'cosmosdb' and _cosmos_client:
        # CosmosDB client doesn't need explicit close, but we'll clear the reference
        _cosmos_client = None
        _cosmos_database = None
        logger.info("CosmosDB SQL API connection closed")
    elif provider == 'mongodb' and _pymongo_client:
        _pymongo_client.close()
        _pymongo_client = None
        logger.info("MongoDB connection closed")
    
    _client = None
    _database = None
    _provider = None
