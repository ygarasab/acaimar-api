import azure.functions as func
import logging
import json
from bson import ObjectId
import sys
import os

# Add parent directory to path to import shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_connection import get_collection
from shared.auth import require_auth

logger = logging.getLogger(__name__)


@require_auth()
def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/metas
    Retrieve all metas from the database
    """
    try:
        collection = get_collection('metas')
        metas = list(collection.find({}))
        
        # Convert ObjectId to string
        for meta in metas:
            meta['_id'] = str(meta['_id'])
        
        return func.HttpResponse(
            json.dumps(metas, ensure_ascii=False),
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        logger.error(f"Error retrieving metas: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to retrieve metas", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
