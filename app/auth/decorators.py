import app.app_utils as au  # Custom Library

from flask import request, jsonify
from functools import wraps # Preserves distinct names of functions inside a decorator


# Authorization Decorator for routes
def requires_authorization(target_function):
    @wraps(target_function)  # Preserves target_function's internal name 
    def wrapper(*args, **kwargs):

        # Get Token
        auth_header = request.headers.get("authorization", "0")  # Gets Bearer <token>, default 0
        # print("auth_header=", auth_header)
        token = auth_header.split(" ")[1] # Extracts token from header 
        data_in_token = au.verify_token(token)        
        if not data_in_token:
            return jsonify({"error": "Authorization denied: invalid token"}), 401
        
        # Share data in token with target function
        kwargs['data_in_token'] = data_in_token
        
        # Run Target Function
        try:
            return target_function(*args, **kwargs)
        
        except Exception as e:
            message = f"{target_function.__name__}() - {str(e)}"
            return jsonify({"error": f"{message}"}), 400

    return wrapper