import azure.functions as func
import logging
import json
from bson import ObjectId
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_connection import get_collection

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/metas/{id}
    Retrieve a specific meta by ID
    """
    try:
        meta_id = req.route_params.get('id')
        
        if not meta_id:
            return func.HttpResponse(
                json.dumps({"error": "Meta ID is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        collection = get_collection('metas')
        meta = collection.find_one({"_id": ObjectId(meta_id)})
        
        if not meta:
            return func.HttpResponse(
                json.dumps({"error": "Meta not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        meta['_id'] = str(meta['_id'])
        
        return func.HttpResponse(
            json.dumps(meta, ensure_ascii=False),
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        logger.error(f"Error retrieving meta: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to retrieve meta", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
