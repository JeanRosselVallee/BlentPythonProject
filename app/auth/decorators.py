# Authentication Decorators
# This module provides reusable decorators to secure API endpoints by verifying JWT tokens.

import app.app_utils as au  # Custom Library for token verification
from flask import request, jsonify
from functools import wraps  # Ensures decorated functions keep their original identity


def requires_authorization(target_function):
    """
    Decorator to protect API routes.
    It checks for a valid Bearer token in the 'Authorization' header.

    If valid: Injects the decrypted token data into the target function's arguments.
    If invalid: Returns a 401 Unauthorized error.
    """

    @wraps(target_function)
    def wrapper(*args, **kwargs):
        # 1. Retrieve the Authorization header (Expected: "Bearer <token>")
        auth_header = request.headers.get("authorization", "0")

        try:
            # 2. Extract the token string after the "Bearer " prefix
            # Example: "Bearer eyJhbG..." -> "eyJhbG..."
            token = auth_header.split(" ")[1]

            # 3. Verify the token validity and expiration using app utilities
            data_in_token = au.verify_token(token)

            if not data_in_token:
                return (
                    jsonify({"error": "Accès refusé : jeton invalide oue expiré"}),
                    401,
                )

            # 4. Inject the user information (id, role, etc.) into the function
            # This allows the route to know who is making the request.
            kwargs["data_in_token"] = data_in_token

            # 5. Execute the protected route function
            return target_function(*args, **kwargs)

        except IndexError:
            # Triggered if the header is missing or incorrectly formatted
            return (
                jsonify(
                    {
                        "error": "Format d'autorisation invalide. Utilisez 'Bearer <token>'"
                    }
                ),
                401,
            )

        except Exception as e:
            # Catch-all for internal processing errors
            message = f"{target_function.__name__}() - {str(e)}"
            return jsonify({"error": f"{message}"}), 400

    return wrapper
