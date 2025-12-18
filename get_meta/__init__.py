import azure.functions as func
import logging
import json
import sys
import os
import traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Bootstrap shared robustness helpers (safe imports + fallback responses)
_import_errors = []
try:
    from shared.function_bootstrap import (
        ensure_app_root_on_syspath,
        get_response_fns,
        maybe_attach_import_errors,
        safe_import,
    )
except Exception:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from shared.function_bootstrap import (
        ensure_app_root_on_syspath,
        get_response_fns,
        maybe_attach_import_errors,
        safe_import,
    )

ensure_app_root_on_syspath(__file__, logger=logger)
responses = get_response_fns(logger=logger, errors=_import_errors)
error_response = responses.error_response
success_response = responses.success_response
not_found_response = responses.not_found_response

_, _db_attrs = safe_import(
    "shared.db_connection",
    ["get_collection"],
    logger=logger,
    errors=_import_errors,
    label="db connection",
)
get_collection = _db_attrs.get("get_collection")

_, _bson_attrs = safe_import(
    "bson",
    ["ObjectId"],
    logger=logger,
    errors=_import_errors,
    label="bson",
)
ObjectId = _bson_attrs.get("ObjectId")


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/metas/{id}
    Retrieve a specific meta by ID
    """
    try:
        if _import_errors or not get_collection or not ObjectId:
            payload = maybe_attach_import_errors(
                {"error": "Get meta service unavailable (import errors)"}, _import_errors
            )
            return func.HttpResponse(
                json.dumps(payload, ensure_ascii=False),
                status_code=503,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"},
            )

        meta_id = req.route_params.get('id')
        
        if not meta_id:
            return error_response("Meta ID is required in the route path", 400)
        
        try:
            collection = get_collection('metas')
            meta = collection.find_one({"_id": ObjectId(meta_id)})
        except Exception as db_error:
            error_msg = str(db_error)
            error_trace = traceback.format_exc()
            logger.error(f"Database error retrieving meta: {error_msg}")
            logger.error(f"Traceback: {error_trace}")
            logger.error(f"Exception type: {type(db_error).__name__}")
            return error_response("Failed to retrieve meta from database", 500, error_msg)
        
        if not meta:
            return not_found_response("Meta")
        
        meta['_id'] = str(meta['_id'])
        
        return success_response(meta, 200)
    except ValueError as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Invalid meta ID format: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        return error_response("Invalid meta ID format", 400, error_msg)
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error retrieving meta: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response("Failed to retrieve meta", 500, error_msg)
