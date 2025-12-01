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
    DELETE /api/metas/{id}
    Delete a meta
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
        result = collection.delete_one({"_id": ObjectId(meta_id)})
        
        if result.deleted_count == 0:
            return func.HttpResponse(
                json.dumps({"error": "Meta not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        return func.HttpResponse(
            json.dumps({"message": "Meta deleted successfully"}),
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        logger.error(f"Error deleting meta: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to delete meta", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
