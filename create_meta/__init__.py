import azure.functions as func
import logging
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_connection import get_collection
from shared.auth import require_auth

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
            return func.HttpResponse(
                json.dumps({"error": "Request body is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Validate required fields
        required_fields = ['titulo', 'descricao']
        for field in required_fields:
            if field not in req_body:
                return func.HttpResponse(
                    json.dumps({"error": f"Field '{field}' is required"}),
                    status_code=400,
                    mimetype="application/json"
                )
        
        # Set default status if not provided
        if 'status' not in req_body:
            req_body['status'] = 'pendente'
        
        collection = get_collection('metas')
        result = collection.insert_one(req_body)
        
        # Retrieve the created document
        created_meta = collection.find_one({"_id": result.inserted_id})
        created_meta['_id'] = str(created_meta['_id'])
        
        return func.HttpResponse(
            json.dumps(created_meta, ensure_ascii=False),
            status_code=201,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        logger.error(f"Error creating meta: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to create meta", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
