import azure.functions as func
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils import success_response

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/ok
    Simple health check endpoint that returns ok
    """
    try:
        return success_response({"status": "ok"}, 200)
    except Exception as e:
        logger.error(f"Error in ok endpoint: {str(e)}", exc_info=True)
        # Fallback to basic HttpResponse if there's an import error
        return func.HttpResponse(
            '{"status": "ok"}',
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
