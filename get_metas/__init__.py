import azure.functions as func
import logging
import json
from bson import ObjectId
import sys
import os
import traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add parent directory to path to import shared modules
try:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    logger.info(f"Added to sys.path: {parent_dir}")
except Exception as path_error:
    logger.error(f"Error setting up sys.path: {str(path_error)}", exc_info=True)

# Import shared modules with error handling
try:
    from shared.db_connection import get_collection
    logger.info("Successfully imported get_collection")
except ImportError as e:
    logger.error(f"Failed to import get_collection: {str(e)}", exc_info=True)
    raise

try:
    from shared.auth import require_auth
    logger.info("Successfully imported require_auth")
except ImportError as e:
    logger.error(f"Failed to import require_auth: {str(e)}", exc_info=True)
    raise

try:
    from shared.utils.responses import error_response, success_response
    logger.info("Successfully imported response utilities")
except ImportError as e:
    logger.error(f"Failed to import response utilities: {str(e)}", exc_info=True)
    raise


@require_auth()
def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/metas
    Retrieve all metas from the database
    """
    try:
        try:
            collection = get_collection('metas')
            metas = list(collection.find({}))
            
            # Convert ObjectId to string
            for meta in metas:
                meta['_id'] = str(meta['_id'])
            
            return success_response(metas, 200)
        except Exception as db_error:
            error_msg = str(db_error)
            error_trace = traceback.format_exc()
            logger.error(f"Database error retrieving metas: {error_msg}")
            logger.error(f"Traceback: {error_trace}")
            logger.error(f"Exception type: {type(db_error).__name__}")
            return error_response("Failed to retrieve metas from database", 500, error_msg)
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error retrieving metas: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response("Failed to retrieve metas", 500, error_msg)
