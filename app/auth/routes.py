# Authentication API Routes
# This module handles user registration and login logic, interacting with the database
# and managing security via password hashing and JWT token generation.

import app.app_utils as au  # Custom utilities for token generation and field validation
from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.database.model import Utilisateur
from werkzeug.security import check_password_hash, generate_password_hash

# Define the Blueprint for authentication
auth_bp = Blueprint(
    "auth", __name__  # ID for internal routing and URL prefixing  # Current module path
)

# --- ROUTES DEFINITION ---


@auth_bp.route("/register", methods=["POST"])
def register_user():
    """
    Handles new user account creation.
    1. Validates that all required fields (email, password, name) are present.
    2. Hashes the password for secure storage.
    3. Checks if the user already exists to prevent duplicates.
    4. Saves the new user to the database.
    """
    f_name = "register_user()"

    # Retrieve and validate incoming JSON data
    submitted_data = request.get_json()
    required_fields = {"email", "mot_de_passe", "nom"}

    if not au.check_fields(submitted_data, required_fields):
        return jsonify({"error": "Missing fields."}), 400

    # Secure the password using PBKDF2 hashing
    password_in_clear = submitted_data["mot_de_passe"]
    password_hashed = generate_password_hash(password_in_clear)

    # Prepare the new user record
    new_user = Utilisateur(
        email=submitted_data["email"],
        mot_de_passe=password_hashed,
        nom=submitted_data["nom"],
    )

    try:
        # Check database for existing email
        user_is_already_in_db = Utilisateur.query.filter_by(
            email=submitted_data["email"]
        ).first()
        if user_is_already_in_db:
            return (
                jsonify(
                    {"error": f"{f_name}: User {new_user.email} already exists in DB."}
                ),
                400,
            )

        # Commit to database
        db.session.add(new_user)
        db.session.commit()

    except Exception as e:
        return jsonify({"error": f"{f_name}: {str(e)}"}), 400

    # Return the newly created user data as a confirmation
    return au.get_items(Utilisateur, Utilisateur.email, new_user.email)


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticates existing users.
    1. Verifies that email and password are provided.
    2. Retrieves the user from the database by email.
    3. Verifies the hashed password.
    4. Generates a JWT token for subsequent authorized requests.
    """
    f_name = "login()"

    # Get credentials from request body
    submitted_data = request.get_json()
    if not au.check_fields(submitted_data, {"email", "password"}):
        return jsonify({"error": f"{f_name}: Missing credentials in request."}), 400

    submitted_email = submitted_data["email"]
    submitted_password = submitted_data["password"]

    # Locate user in DB
    user_in_db = Utilisateur.query.filter_by(email=submitted_email).first()
    if not user_in_db:
        return (
            jsonify({"error": f"{f_name}: User {submitted_email} not found in DB"}),
            404,
        )

    # Extract user data for verification
    password_in_db = user_in_db.mot_de_passe
    user_role = user_in_db.role

    # Compare submitted password with the hashed version in DB
    if not check_password_hash(password_in_db, submitted_password):
        return jsonify({"error": f"{f_name}: Invalid credentials"}), 401

    # Generate a signed JWT token for the session
    token = au.generate_json_token(submitted_email)

    # Return both the token and the role (admin/client) for frontend UI logic
    return jsonify({"token": token, "role": user_role}), 200
