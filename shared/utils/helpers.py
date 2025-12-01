"""
General utility functions
"""
from bson import ObjectId
from typing import Any, Dict, List


def convert_objectid_to_str(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert MongoDB ObjectId to string in a document
    
    Args:
        doc: MongoDB document
    
    Returns:
        Document with _id converted to string
    """
    if doc and '_id' in doc and isinstance(doc['_id'], ObjectId):
        doc['_id'] = str(doc['_id'])
    return doc


def convert_objectids_in_list(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert ObjectIds to strings in a list of documents
    
    Args:
        docs: List of MongoDB documents
    
    Returns:
        List of documents with _id fields converted to strings
    """
    return [convert_objectid_to_str(doc) for doc in docs]


def exclude_fields(doc: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """
    Exclude specified fields from a document
    
    Args:
        doc: Document to process
        fields: List of field names to exclude
    
    Returns:
        Document with specified fields removed
    """
    return {k: v for k, v in doc.items() if k not in fields}


def sanitize_user_response(user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize user document for API response (remove password, convert ObjectId)
    
    Args:
        user: User document from database
    
    Returns:
        Sanitized user document
    """
    user = convert_objectid_to_str(user)
    return exclude_fields(user, ['password_hash'])

