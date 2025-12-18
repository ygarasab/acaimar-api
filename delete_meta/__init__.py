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
    DELETE /api/metas/{id}
    Delete a meta
    """
    try:
        meta_id = req.route_params.get('id')
        
        if not meta_id:
            return error_response("Meta ID is required in the route path", 400)
        
        try:
            collection = get_collection('metas')
            result = collection.delete_one({"_id": ObjectId(meta_id)})
            
            if result.deleted_count == 0:
                return not_found_response("Meta")
            
            return success_response({"message": "Meta deleted successfully"}, 200)
        except ValueError as ve:
            logger.error(f"Invalid meta ID format: {str(ve)}")
            return error_response("Invalid meta ID format", 400, str(ve))
        except Exception as db_error:
            logger.error(f"Database error deleting meta: {str(db_error)}")
            return error_response("Failed to delete meta from database", 500, str(db_error))
    except Exception as e:
        logger.error(f"Error deleting meta: {str(e)}", exc_info=True)
        return error_response("Failed to delete meta", 500, str(e))
