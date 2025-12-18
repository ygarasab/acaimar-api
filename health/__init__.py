import azure.functions as func
import logging
import json
import sys
import os
import traceback
from datetime import datetime

# Configure logging - Azure Functions uses root logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Also use print - Azure Functions always logs print statements
print("=" * 50)
print("MODULE LOAD: health/__init__.py")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"__file__: {__file__}")
print("=" * 50)

# Store import status
_import_errors = []
_db_functions_available = False
_response_functions_available = False

# Add parent directory to path
try:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    logger.info(f"Added to sys.path: {parent_dir}")
    print(f"INFO: Added to sys.path: {parent_dir}")
except Exception as path_error:
    error_msg = f"Error setting up sys.path: {str(path_error)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    print(f"ERROR: {traceback.format_exc()}")
    _import_errors.append(error_msg)

# Import shared modules with error handling - don't raise, store errors
try:
    from shared.db_connection import get_database, get_db_provider, get_collection
    logger.info("Successfully imported database functions")
    print("INFO: Successfully imported database functions")
    _db_functions_available = True
except ImportError as e:
    error_msg = f"Failed to import database functions: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    print(f"ERROR: {traceback.format_exc()}")
    _import_errors.append(error_msg)
except Exception as e:
    error_msg = f"Unexpected error importing database functions: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    print(f"ERROR: {traceback.format_exc()}")
    _import_errors.append(error_msg)

try:
    from shared.utils.responses import json_response, error_response
    logger.info("Successfully imported response utilities")
    print("INFO: Successfully imported response utilities")
    _response_functions_available = True
except ImportError as e:
    error_msg = f"Failed to import response utilities: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    print(f"ERROR: {traceback.format_exc()}")
    _import_errors.append(error_msg)
except Exception as e:
    error_msg = f"Unexpected error importing response utilities: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    print(f"ERROR: {traceback.format_exc()}")
    _import_errors.append(error_msg)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/health
    Health check endpoint - returns API and database status
    """
    print(f"INFO: health endpoint called, method: {req.method}")
    logger.info(f"health endpoint called, method: {req.method}")
    
    # If imports failed, return error immediately
    if _import_errors:
        error_details = "; ".join(_import_errors)
        print(f"ERROR: Import errors detected: {error_details}")
        logger.error(f"Import errors: {error_details}")
        
        # Try to use error_response if available, otherwise use basic HttpResponse
        if _response_functions_available:
            try:
                return error_response(
                    "Health check failed due to import errors",
                    500,
                    error_details
                )
            except:
                pass
        
        # Fallback to basic HttpResponse
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "error": "Health check failed due to import errors",
                "details": error_details,
                "import_errors": _import_errors
            }, ensure_ascii=False),
            status_code=500,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
    
    try:
        # Check if database functions are available
        if not _db_functions_available:
            return func.HttpResponse(
                json.dumps({
                    "status": "degraded",
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": "AÇAIMAR API",
                    "version": "1.0.0",
                    "checks": {
                        "api": {
                            "status": "ok",
                            "message": "API is running"
                        },
                        "database": {
                            "status": "error",
                            "message": "Database functions not available - import failed"
                        }
                    }
                }, ensure_ascii=False),
                status_code=503,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
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
        
        # Use json_response if available, otherwise basic HttpResponse
        if _response_functions_available:
            try:
                response = json_response(health_status, http_status)
                response.headers["Cache-Control"] = "no-cache"
                return response
            except Exception as resp_error:
                print(f"ERROR: json_response failed: {str(resp_error)}")
                logger.error(f"json_response failed: {str(resp_error)}")
        
        # Fallback to basic HttpResponse
        response = func.HttpResponse(
            json.dumps(health_status, indent=2, ensure_ascii=False),
            status_code=http_status,
            mimetype="application/json",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache"
            }
        )
        return response
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"ERROR: Critical error in health check endpoint: {error_msg}")
        print(f"ERROR: Traceback: {error_trace}")
        print(f"ERROR: Exception type: {type(e).__name__}")
        logger.error(f"Critical error in health check endpoint: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        
        # Try to use error_response if available
        if _response_functions_available:
            try:
                return error_response(
                    "Health check endpoint encountered an unexpected error",
                    500,
                    error_msg
                )
            except:
                pass
        
        # Fallback to basic HttpResponse
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "error": "Health check endpoint encountered an unexpected error",
                "details": error_msg,
                "traceback": error_trace
            }, ensure_ascii=False),
            status_code=500,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
