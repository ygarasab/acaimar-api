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
    from shared.auth import require_auth
    logger.info("Successfully imported require_auth")
except ImportError as e:
    logger.error(f"Failed to import require_auth: {str(e)}", exc_info=True)
    raise

try:
    from shared.utils.responses import error_response, success_response, not_found_response
    logger.info("Successfully imported response utilities")
except ImportError as e:
    logger.error(f"Failed to import response utilities: {str(e)}", exc_info=True)
    raise


@require_auth(require_role='admin')
def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    PUT /api/metas/{id}
    Update an existing meta
    """
    try:
        meta_id = req.route_params.get('id')
        
        if not meta_id:
            return error_response("Meta ID is required in the route path", 400)
        
        req_body = req.get_json()
        
        if not req_body:
            return error_response("Request body is required", 400)
        
        if not req_body or len(req_body) == 0:
            return error_response("Request body cannot be empty. Provide at least one field to update", 400)
        
        # Remove _id from update body if present
        req_body.pop('_id', None)
        
        try:
            collection = get_collection('metas')
            result = collection.update_one(
                {"_id": ObjectId(meta_id)},
                {"$set": req_body}
            )
            
            if result.matched_count == 0:
                return not_found_response("Meta")
            
            # Retrieve the updated document
            updated_meta = collection.find_one({"_id": ObjectId(meta_id)})
            if not updated_meta:
                return error_response("Meta was updated but could not be retrieved", 500)
            
            updated_meta['_id'] = str(updated_meta['_id'])
            
            return success_response(updated_meta, 200)
        except ValueError as ve:
            error_msg = str(ve)
            error_trace = traceback.format_exc()
            logger.error(f"Invalid meta ID format: {error_msg}")
            logger.error(f"Traceback: {error_trace}")
            return error_response("Invalid meta ID format", 400, error_msg)
        except Exception as db_error:
            error_msg = str(db_error)
            error_trace = traceback.format_exc()
            logger.error(f"Database error updating meta: {error_msg}")
            logger.error(f"Traceback: {error_trace}")
            logger.error(f"Exception type: {type(db_error).__name__}")
            return error_response("Failed to update meta in database", 500, error_msg)
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error updating meta: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response("Failed to update meta", 500, error_msg)
