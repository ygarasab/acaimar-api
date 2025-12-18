import azure.functions as func
import logging
import sys
import os
import json
import traceback

# Configure logging to show all levels
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add parent directory to path
try:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    logger.info(f"Added to sys.path: {parent_dir}")
except Exception as path_error:
    logger.error(f"Error setting up sys.path: {str(path_error)}", exc_info=True)

# Import shared modules
success_response = None
try:
    from shared.utils import success_response
    logger.info("Successfully imported success_response from shared.utils")
except ImportError as import_error:
    logger.error(f"Import error: {str(import_error)}", exc_info=True)
    logger.error(f"sys.path: {sys.path}")
    logger.error(f"Current working directory: {os.getcwd()}")
    logger.error(f"__file__: {__file__}")
    logger.error(f"Parent dir: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
    # Don't raise - let the function handle it


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/ok
    Simple health check endpoint that returns ok
    """
    logger.info("ok endpoint called")
    try:
        if success_response is None:
            logger.warning("success_response not imported, using fallback")
            raise ImportError("success_response not available")
        
        logger.debug("Creating success response")
        response = success_response({"status": "ok"}, 200)
        logger.info("Successfully created response")
        return response
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error in ok endpoint: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        
        # Fallback to basic HttpResponse
        try:
            return func.HttpResponse(
                json.dumps({
                    "status": "ok",
                    "warning": "Fallback response used due to error",
                    "error": error_msg
                }),
                status_code=200,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {str(fallback_error)}")
            return func.HttpResponse(
                '{"status": "error", "message": "Internal server error"}',
                status_code=500,
                mimetype="application/json"
            )
