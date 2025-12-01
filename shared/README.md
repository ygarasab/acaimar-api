# Shared Utilities

This directory contains standardized utilities for the Azure Functions API, organized by responsibility.

## Structure

```
shared/
├── utils/          # General utilities and HTTP responses
│   ├── helpers.py  # Data manipulation utilities
│   └── responses.py # HTTP response helpers
├── validators/     # Input validation utilities
├── services/       # Database operations and business logic
│   └── user_service.py  # User-related database operations
├── auth.py         # Authentication and authorization
└── db_connection.py # Database connection management
```

## Usage

### HTTP Responses (`shared.utils`)
```python
from shared.utils import (
    success_response,
    error_response,
    method_not_allowed_response,
    unauthorized_response,
    forbidden_response
)

return success_response(data, status_code=200)
return error_response("Error message", status_code=400)
```

### Validation (`shared.validators`)
```python
from shared.validators import (
    validate_email,
    validate_password,
    validate_required_fields,
    sanitize_email,
    sanitize_string
)

is_valid, error_msg = validate_email(email)
is_valid, error_msg = validate_password(password)
```

### User Service (`shared.services`)
```python
from shared.services import (
    get_all_users,
    find_user_by_email,
    user_exists,
    create_user,
    authenticate_user,
    update_user_role
)

users = get_all_users()
user = authenticate_user(email, password)
user = create_user(email, password, name, role='user')
```

### Utilities (`shared.utils`)
```python
from shared.utils import (
    convert_objectid_to_str,
    convert_objectids_in_list,
    sanitize_user_response
)

doc = convert_objectid_to_str(document)
docs = convert_objectids_in_list(document_list)
```

## Example

```python
from shared.utils import success_response, error_response
from shared.validators import validate_required_fields, validate_email
from shared.services import create_user, user_exists

def create_user_endpoint(req):
    req_body = req.get_json()
    
    # Validate
    is_valid, error_msg = validate_required_fields(req_body, ['email', 'name'])
    if not is_valid:
        return error_response(error_msg, 400)
    
    # Check if exists
    if user_exists(req_body['email']):
        return error_response("User already exists", 409)
    
    # Create user
    user = create_user(req_body['email'], req_body['password'], req_body['name'])
    return success_response(user, 201)
```
