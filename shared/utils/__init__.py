"""
General utility functions and HTTP responses
"""
import logging
import traceback

logger = logging.getLogger(__name__)
print(f"INFO: Loading shared.utils.__init__.py")

# Import responses first (no dependencies)
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

# Import helpers lazily - only when needed (has bson dependency)
# Don't fail if helpers can't be imported - they're only needed for some functions
_helpers_available = False
try:
    from .helpers import (
        convert_objectid_to_str,
        convert_objectids_in_list,
        exclude_fields,
        sanitize_user_response
    )
    print("INFO: Successfully imported helpers")
    _helpers_available = True
except Exception as e:
    print(f"WARNING: Failed to import helpers (bson may not be available): {str(e)}")
    print(f"WARNING: Helper functions will not be available")
    # Don't raise - helpers are optional for response functions
    # Create stub functions that raise helpful errors
    def convert_objectid_to_str(doc):
        raise ImportError("bson module not available. Install pymongo to use this function.")
    def convert_objectids_in_list(docs):
        raise ImportError("bson module not available. Install pymongo to use this function.")
    def exclude_fields(doc, fields):
        raise ImportError("bson module not available. Install pymongo to use this function.")
    def sanitize_user_response(user):
        raise ImportError("bson module not available. Install pymongo to use this function.")

__all__ = [
    # Responses (always available)
    'json_response',
    'error_response',
    'success_response',
    'method_not_allowed_response',
    'not_found_response',
    'unauthorized_response',
    'forbidden_response',
    # Helpers (may not be available if bson/pymongo not installed)
    'convert_objectid_to_str',
    'convert_objectids_in_list',
    'exclude_fields',
    'sanitize_user_response'
]
