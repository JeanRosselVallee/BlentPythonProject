# Application Utility Functions
# This module contains shared logic for JWT authentication, generic database 
# retrieval, keyword searching, and data validation used across all blueprints.

import os
import jwt

from datetime import datetime, timedelta, timezone
from flask import jsonify, current_app
from sqlalchemy import text
from dotenv import load_dotenv
from app.database.model import Utilisateur

# Load SECRET_PHRASE from .env
load_dotenv()
SECRET_PHRASE = os.getenv("SECRET_PHRASE")


# Token Generation for Authentication
def generate_json_token(user_login):
    """
    Generates a JWT for a successfully authenticated user.
    Includes the login identity and an expiration timestamp (1 hour).
    """
    now = datetime.now(timezone.utc)
    expire_time = now + timedelta(hours=1)
    token = jwt.encode(
        {   "expire_time": expire_time.timestamp(), 
            "login": user_login
        },
        SECRET_PHRASE,
        algorithm="HS256",  # singular
    )
    #return jsonify({"token": token})
    return token


# Token Validity Check for Authorization
def verify_token(token):
    """
    Decodes and validates a provided JWT.
    returns payload = data stored in token 
    """
    try:
        # current_app.logger.debug(f"DEBUG: Token received for verification: '{token}'")
        payload = jwt.decode(token, SECRET_PHRASE, algorithms=["HS256"])  # plural
        return payload
    except Exception as e:
        current_app.logger.error(f"ERROR in verify_token(): {e}")
        return None

# Get Email from Token
def get_email_from_token(token):
    """
    Extracts the user login/email directly from a token payload.
    """
    payload = verify_token(token)
    user_email = payload.login
    return user_email

# Get items from DB for Routes Definition
def get_items(table, field=None, item_id=None):
    """
    Fetch items from DB, optionally filtered, & returned as JSON
    Parameters:
    - table: DB table (SQLAlchemy Model)
    - field (optional): filter DB column
    - item_id (optional): filter value
    Return: JSON string of items and HTTP status code
    """
           
    if item_id:
        # Filtered query (e.g., specific ID or User ID)
        target_items = table.query.filter(field == item_id)
        nb_items = target_items.count()
        
    else:
        # Unfiltered query for all records
        target_items = table.query.all()
        nb_items = len(target_items)
        
    if target_items and nb_items > 0:
        # Convert SQLAlchemy objects into serializable dictionaries
        items = [
            {c.name: getattr(i, c.name) for c in i.__table__.columns}
            for i in target_items
        ]
        return jsonify(items), 200
    else:
        return jsonify({"error": "No records found"}), 404


def search_items(db, table, field_1, field_2, keywords):
        """
        Performs a multi-keyword search across two database fields.
        Each word must be present in the concatenated result of both fields.
        """
        
        f_name = "search_items()"
        sql_conditions = []
        params = {}

        # Get 1 condition per keyword to ensure all keywords match (AND logic)
        for i, word in enumerate(keywords):
            sql_concatenation = f"{field_1} || ' ' || {field_2}"
            sql_text = f"LOWER({sql_concatenation})"
            sql_condition = f"\n\t{sql_text} LIKE :word_{i}"
            sql_conditions.append(sql_condition)
            params[f"word_{i}"] = f"%{word.lower()}%"

        # Get SQL Clause with all conditions joined by AND
        sql_clause = ' AND '.join(sql_conditions)

        # Set SQL Query as a string
        select_query = f"SELECT * FROM {table} WHERE {sql_clause}"
        current_app.logger.debug(f"{f_name}:\n {select_query}")

        # Get Results from DB using raw SQL execution
        results = db.session.execute(text(select_query), params)
        nb_items = results.returns_rows
        
        if not nb_items :  # Case Undefined
            return jsonify({"error": "DB error"}), 404
        if nb_items > 0:   # Case OK : Products Found
            items = results.fetchall()
            # Mapping rows to dictionaries for JSON response
            items_as_dicts = [dict(row._mapping) for row in items]
            return jsonify(items_as_dicts), 200
        else:              # Case OK : No Product found
            return jsonify({f"message": f"No records contain {keywords}"}), 204


def check_fields(body, fields):
    """
    Validates that the required keys are present in a dictionary (typically request.get_json()).
    Returns True if all required fields are available.
    """
    required_fields = set(fields)
    available_fields = set(body.keys())
    required_fields_availability = required_fields <= available_fields
    return required_fields_availability


def get_user_attribute_in_db(data_in_token, attribute_name):
    """
    Retrieves a specific attribute (like 'role' or 'id') for a user based on 
     the identity stored in the JWT payload.
    """
    # Get User login from Token and find record in DB
    email_in_token = data_in_token["login"]
    user_in_db = Utilisateur.query.filter_by(email=email_in_token).first()
    
    # Use getattr to dynamically retrieve the requested field
    user_attribute = getattr(user_in_db, attribute_name, None)
    return user_attribute