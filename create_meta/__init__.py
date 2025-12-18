import azure.functions as func
import logging
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_connection import get_collection
from shared.auth import require_auth
from shared.utils.responses import error_response, success_response

logger = logging.getLogger(__name__)


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
            logger.error(f"Database error creating meta: {str(db_error)}")
            return error_response("Failed to create meta in database", 500, str(db_error))
    except Exception as e:
        logger.error(f"Error creating meta: {str(e)}", exc_info=True)
        return error_response("Failed to create meta", 500, str(e))
