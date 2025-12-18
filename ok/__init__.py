import azure.functions as func
import logging
import json

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/ok
    Simple health check endpoint that returns ok
    """
    try:
        return func.HttpResponse(
            json.dumps({"status": "ok"}, ensure_ascii=False),
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        logger.error(f"Error in ok endpoint: {str(e)}", exc_info=True)
        # Even if json.dumps fails, return something
        return func.HttpResponse(
            '{"status": "ok"}',
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
