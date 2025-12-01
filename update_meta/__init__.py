import azure.functions as func
import logging
import json
from bson import ObjectId
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_connection import get_collection
from shared.auth import require_auth

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
            return func.HttpResponse(
                json.dumps({"error": "Meta ID is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        req_body = req.get_json()
        
        if not req_body:
            return func.HttpResponse(
                json.dumps({"error": "Request body is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Remove _id from update body if present
        req_body.pop('_id', None)
        
        collection = get_collection('metas')
        result = collection.update_one(
            {"_id": ObjectId(meta_id)},
            {"$set": req_body}
        )
        
        if result.matched_count == 0:
            return func.HttpResponse(
                json.dumps({"error": "Meta not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        # Retrieve the updated document
        updated_meta = collection.find_one({"_id": ObjectId(meta_id)})
        updated_meta['_id'] = str(updated_meta['_id'])
        
        return func.HttpResponse(
            json.dumps(updated_meta, ensure_ascii=False),
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        logger.error(f"Error updating meta: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to update meta", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
