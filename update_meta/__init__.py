import azure.functions as func
import logging
import json
from bson import ObjectId
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_connection import get_collection
from shared.auth import require_auth
from shared.utils.responses import error_response, success_response, not_found_response

logger = logging.getLogger(__name__)


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
            logger.error(f"Invalid meta ID format: {str(ve)}")
            return error_response("Invalid meta ID format", 400, str(ve))
        except Exception as db_error:
            logger.error(f"Database error updating meta: {str(db_error)}")
            return error_response("Failed to update meta in database", 500, str(db_error))
    except Exception as e:
        logger.error(f"Error updating meta: {str(e)}", exc_info=True)
        return error_response("Failed to update meta", 500, str(e))
