import app.app_utils as au # Custom utilities for app

from flask import Blueprint, request, jsonify
from app.extensions import db
from app.database.model import Utilisateur
from werkzeug.security import check_password_hash

# Definimos el Blueprint
auth_bp = Blueprint(
    'auth',  # id for routing & url prefix
    __name__ # current module's path
    )

@auth_bp.route("/register", methods=["POST"])
def register_user():
    f_name = "register_user()"

    # Get User Data from Request
    submitted_data = request.get_json()
    missing_fields = (not au.check_fields(
        submitted_data, 
        {"email", 
            "mot_de_passe",
            "nom"
            }
    ))
    if missing_fields:
        return jsonify({"error": "Missing fields."}), 400

    # Create User in DB
    new_user = Utilisateur(
        email=submitted_data["email"],
        mot_de_passe=submitted_data["mot_de_passe"],
        nom=submitted_data["nom"]
    )
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        return jsonify({"error": f"{f_name}: {str(e)}"}), 400

    # Return User as a string
    return au.get_items(Utilisateur, Utilisateur.email, new_user.email)

@auth_bp.route("/login", methods=["POST"])
def login():
    f_name = "login()"

    # Get credentials from request
    submitted_data = request.get_json()
    missing_fields = (not au.check_fields(submitted_data, {"email", "password"}))
    if missing_fields:
        return jsonify({"error": f"{f_name}: Missing credentials in request."}), 400
    submitted_email = submitted_data["email"]
    submitted_password = submitted_data["password"]
    
    # Get credentials from DB
    user_in_db = Utilisateur.query.filter_by(email=submitted_email).first()
    if not user_in_db:
        return jsonify({"error": f"{f_name}: User {submitted_email} not found in DB"}), 404
    email_in_db = user_in_db.email
    password_in_db = user_in_db.mot_de_passe
    
    # Check credentials
    passwords_are_different = not check_password_hash(password_in_db, submitted_password)
    if passwords_are_different:
        return jsonify({"error": f"{f_name}: Invalid credentials"}), 401
    
    # Generate Token
    token = au.generate_json_token(email_in_db)
    return token, 200