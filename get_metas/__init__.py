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
from shared.utils.responses import error_response, success_response

logger = logging.getLogger(__name__)


@require_auth()
def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/metas
    Retrieve all metas from the database
    """
    try:
        try:
            collection = get_collection('metas')
            metas = list(collection.find({}))
            
            # Convert ObjectId to string
            for meta in metas:
                meta['_id'] = str(meta['_id'])
            
            return success_response(metas, 200)
        except Exception as db_error:
            logger.error(f"Database error retrieving metas: {str(db_error)}")
            return error_response("Failed to retrieve metas from database", 500, str(db_error))
    except Exception as e:
        logger.error(f"Error retrieving metas: {str(e)}", exc_info=True)
        return error_response("Failed to retrieve metas", 500, str(e))
