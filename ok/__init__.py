import azure.functions as func
import logging
import json
import traceback

# Configure logging - Azure Functions uses root logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Also use print - Azure Functions always logs print statements
print("=" * 50)
print("MODULE LOAD: ok/__init__.py")
print("=" * 50)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/ok
    Simple health check endpoint that returns ok
    """
    print(f"INFO: ok endpoint called, method: {req.method}")
    logger.info(f"ok endpoint called, method: {req.method}")
    try:
        print("INFO: Creating success response")
        response = func.HttpResponse(
            json.dumps({"status": "ok"}, ensure_ascii=False),
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
        print("INFO: Successfully created response")
        return response
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"ERROR: Error in ok endpoint: {error_msg}")
        print(f"ERROR: Traceback: {error_trace}")
        print(f"ERROR: Exception type: {type(e).__name__}")
        logger.error(f"Error in ok endpoint: {error_msg}", exc_info=True)
        # Even if json.dumps fails, return something
        return func.HttpResponse(
            '{"status": "ok"}',
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
