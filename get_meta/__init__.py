import azure.functions as func
import logging
import json
from bson import ObjectId
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_connection import get_collection
from shared.utils.responses import error_response, success_response, not_found_response

logger = logging.getLogger(__name__)


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
            logger.error(f"Database error retrieving meta: {str(db_error)}")
            return error_response("Failed to retrieve meta from database", 500, str(db_error))
        
        if not meta:
            return not_found_response("Meta")
        
        meta['_id'] = str(meta['_id'])
        
        return success_response(meta, 200)
    except ValueError as e:
        logger.error(f"Invalid meta ID format: {str(e)}")
        return error_response("Invalid meta ID format", 400, str(e))
    except Exception as e:
        logger.error(f"Error retrieving meta: {str(e)}", exc_info=True)
        return error_response("Failed to retrieve meta", 500, str(e))
