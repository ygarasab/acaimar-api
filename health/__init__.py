import azure.functions as func
import logging
import json
import sys
import os
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add parent directory to path
try:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    logger.info(f"Added to sys.path: {parent_dir}")
except Exception as path_error:
    logger.error(f"Error setting up sys.path: {str(path_error)}", exc_info=True)

# Import shared modules with error handling
try:
    from shared.db_connection import get_database, get_db_provider, get_collection
    logger.info("Successfully imported database functions")
except ImportError as e:
    logger.error(f"Failed to import database functions: {str(e)}", exc_info=True)
    raise

try:
    from shared.utils.responses import json_response, error_response
    logger.info("Successfully imported response utilities")
except ImportError as e:
    logger.error(f"Failed to import response utilities: {str(e)}", exc_info=True)
    raise


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/health
    Health check endpoint - returns API and database status
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "AÇAIMAR API",
            "version": "1.0.0",
            "checks": {
                "api": {
                    "status": "ok",
                    "message": "API is running"
                },
                "database": {
                    "status": "unknown",
                    "message": "Not checked"
                }
            }
        }
        
        http_status = 200
        
        # Check database connection (MongoDB or CosmosDB SQL API)
        try:
            provider = get_db_provider()
            db = get_database()
            
            # Test connection by querying a collection
            test_collection = get_collection('users')
            
            # Try to query (this will fail if connection is bad)
            test_collection.find({})
            
            # Get basic stats
            if provider == 'cosmosdb':
                # For CosmosDB, get database info
                db_name = os.environ.get('COSMOSDB_DATABASE') or os.environ.get('MONGODB_DATABASE', 'acaimar')
                # Count collections by trying to access common ones
                collections = ['users', 'metas', 'sensor_data']
                collection_count = 0
                for coll_name in collections:
                    try:
                        coll = get_collection(coll_name)
                        coll.find({})  # Test access
                        collection_count += 1
                    except Exception as coll_error:
                        logger.debug(f"Could not access collection {coll_name}: {str(coll_error)}")
                        pass
                
                health_status["checks"]["database"] = {
                    "status": "ok",
                    "message": "Database connection successful",
                    "provider": "COSMOSDB_SQL_API",
                    "database": db_name,
                    "collections_accessible": collection_count
                }
            else:
                # For MongoDB, use native stats
                try:
                    from shared.db_connection import get_mongo_client
                    client = get_mongo_client()
                    client.admin.command('ping')
                    db_stats = db.command("dbStats")
                    health_status["checks"]["database"] = {
                        "status": "ok",
                        "message": "Database connection successful",
                        "provider": "MONGODB",
                        "database": db.name,
                        "collections": db_stats.get("collections", 0),
                        "dataSize": db_stats.get("dataSize", 0)
                    }
                except Exception as stats_error:
                    # Fallback if stats command fails
                    logger.debug(f"Stats command failed, using fallback: {str(stats_error)}")
                    health_status["checks"]["database"] = {
                        "status": "ok",
                        "message": "Database connection successful",
                        "provider": "MONGODB",
                        "database": "acaimar"
                    }
            
            logger.info(f"Health check: All systems operational ({provider.upper()})")
            
        except Exception as db_error:
            provider = get_db_provider()
            health_status["status"] = "degraded"
            health_status["checks"]["database"] = {
                "status": "error",
                "message": f"Database connection failed: {str(db_error)}",
                "provider": provider.upper(),
                "error_details": str(db_error)
            }
            http_status = 503  # Service Unavailable
            logger.error(f"Health check: Database connection failed ({provider.upper()}) - {str(db_error)}")
        
        response = json_response(health_status, http_status)
        response.headers["Cache-Control"] = "no-cache"
        return response
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Critical error in health check endpoint: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response(
            "Health check endpoint encountered an unexpected error",
            500,
            error_msg
        )
