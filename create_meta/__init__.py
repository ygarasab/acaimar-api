import azure.functions as func
import logging
import json
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
    from shared.utils.responses import error_response, success_response
    logger.info("Successfully imported response utilities")
except ImportError as e:
    logger.error(f"Failed to import response utilities: {str(e)}", exc_info=True)
    raise


@require_auth(require_role='admin')
def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/metas
    Create a new meta
    """
    try:
        req_body = req.get_json()
        
        if not req_body:
            return error_response("Request body is required", 400)
        
        # Validate required fields
        required_fields = ['titulo', 'descricao']
        missing_fields = [field for field in required_fields if field not in req_body]
        if missing_fields:
            return error_response(f"Missing required fields: {', '.join(missing_fields)}", 400)
        
        # Set default status if not provided
        if 'status' not in req_body:
            req_body['status'] = 'pendente'
        
        try:
            collection = get_collection('metas')
            result = collection.insert_one(req_body)
            
            # Retrieve the created document
            created_meta = collection.find_one({"_id": result.inserted_id})
            if not created_meta:
                return error_response("Meta was created but could not be retrieved", 500)
            
            created_meta['_id'] = str(created_meta['_id'])
            
            return success_response(created_meta, 201)
        except Exception as db_error:
            error_msg = str(db_error)
            error_trace = traceback.format_exc()
            logger.error(f"Database error creating meta: {error_msg}")
            logger.error(f"Traceback: {error_trace}")
            logger.error(f"Exception type: {type(db_error).__name__}")
            return error_response("Failed to create meta in database", 500, error_msg)
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error creating meta: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response("Failed to create meta", 500, error_msg)
