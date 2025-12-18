"""
General utility functions and HTTP responses
"""
import logging
import traceback

logger = logging.getLogger(__name__)
print(f"INFO: Loading shared.utils.__init__.py")

try:
    from .helpers import (
        convert_objectid_to_str,
        convert_objectids_in_list,
        exclude_fields,
        sanitize_user_response
    )
    print("INFO: Successfully imported helpers")
except Exception as e:
    print(f"ERROR: Failed to import helpers: {str(e)}")
    print(f"ERROR: {traceback.format_exc()}")
    raise

try:
    from .responses import (
        json_response,
        error_response,
        success_response,
        method_not_allowed_response,
        not_found_response,
        unauthorized_response,
        forbidden_response
    )
    print("INFO: Successfully imported responses")
except Exception as e:
    print(f"ERROR: Failed to import responses: {str(e)}")
    print(f"ERROR: {traceback.format_exc()}")
    raise

__all__ = [
    # Helpers
    'convert_objectid_to_str',
    'convert_objectids_in_list',
    'exclude_fields',
    'sanitize_user_response',
    # Responses
    'json_response',
    'error_response',
    'success_response',
    'method_not_allowed_response',
    'not_found_response',
    'unauthorized_response',
    'forbidden_response'
]
