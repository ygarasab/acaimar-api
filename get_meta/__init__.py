import azure.functions as func
import logging
import json
from bson import ObjectId
import sys
import os
import traceback

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
    from shared.db_connection import get_collection
    logger.info("Successfully imported get_collection")
except ImportError as e:
    logger.error(f"Failed to import get_collection: {str(e)}", exc_info=True)
    raise

try:
    from shared.utils.responses import error_response, success_response, not_found_response
    logger.info("Successfully imported response utilities")
except ImportError as e:
    logger.error(f"Failed to import response utilities: {str(e)}", exc_info=True)
    raise


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/metas/{id}
    Retrieve a specific meta by ID
    """
    try:
        meta_id = req.route_params.get('id')
        
        if not meta_id:
            return error_response("Meta ID is required in the route path", 400)
        
        try:
            collection = get_collection('metas')
            meta = collection.find_one({"_id": ObjectId(meta_id)})
        except Exception as db_error:
            error_msg = str(db_error)
            error_trace = traceback.format_exc()
            logger.error(f"Database error retrieving meta: {error_msg}")
            logger.error(f"Traceback: {error_trace}")
            logger.error(f"Exception type: {type(db_error).__name__}")
            return error_response("Failed to retrieve meta from database", 500, error_msg)
        
        if not meta:
            return not_found_response("Meta")
        
        meta['_id'] = str(meta['_id'])
        
        return success_response(meta, 200)
    except ValueError as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Invalid meta ID format: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        return error_response("Invalid meta ID format", 400, error_msg)
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error retrieving meta: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response("Failed to retrieve meta", 500, error_msg)
