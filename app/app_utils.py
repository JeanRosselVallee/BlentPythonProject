import jwt

from datetime import datetime, timedelta, timezone
from flask import jsonify, current_app
from sqlalchemy import text

SECRET_PHRASE = "d3fb12750c2eff92120742e1b334479e"


# Token Generation for Authentication
def generate_json_token(user_login):
    now = datetime.now(timezone.utc)
    expire_time = now + timedelta(hours=1)
    token = jwt.encode(
        {   "expire_time": expire_time.timestamp(), 
            "login": user_login, 
        },
        SECRET_PHRASE,
        algorithm="HS256",  # singular
    )
    return jsonify({"token": token})


# Token Validity Check for Authorization
def verify_token(token):
    """
    returns payload = data stored in token 
    """
    try:
        payload = jwt.decode(token, SECRET_PHRASE, algorithms=["HS256"])  # plural
        return payload
    except Exception as e:
        print(f"ERROR in verify_token(): {e}")
        return None

# Get Email from Token
def get_email_from_token(token):
    payload = verify_token(token)
    user_email = payload.login
    return user_email

# Get items from DB for Routes Definition
def get_items(table, field=None, item_id=None):
    """
    Fetch items from DB, optionally filtered, & returned as JSON
    Parameters:
    - table: DB table
    - field (optional): filter DB column
    - item_id (optional): filter value
    Return: string of items
    """
           
    if item_id:
        target_items = table.query.filter(field == item_id)
        nb_items = target_items.count()
        
    else:
        target_items = table.query.all()
        nb_items = len(target_items)
    if target_items and nb_items > 0:
        items = [
            {c.name: getattr(i, c.name) for c in i.__table__.columns}
            for i in target_items
        ]
        return jsonify(items), 200
    else:
        return jsonify({"error": "No records found"}), 404



    # TO Do
    # Update Function description & Clean up function
def search_items(db, table, field_1, field_2, keywords):
        '''
        Each word should be present in at least one of the fields
        '''
        
        f_name = "search_items()"
        conditions = []
        params = {}

        # Get 1 condition per keyword
        for i, word in enumerate(keywords):
            concatenated_fields = f"{field_1} || ' ' || {field_2}"
            condition = f"\n\t{concatenated_fields} LIKE :word_{i}"
            conditions.append(condition)
            params[f"word_{i}"] = f"%{word}%"

        # Get SQL Clause with all conditions
        sql_clause = ' AND '.join(conditions)

        # Set SQL Query as a string
        select_query = f"SELECT * FROM {table} WHERE {sql_clause}"
        current_app.logger.debug(f"{f_name}:\n {select_query}")

        # Get Results from DB
        results = db.session.execute(text(select_query), params)
        nb_items = results.returns_rows
        
        if not nb_items :  # Case Undefined
            return jsonify({"error": "DB error"}), 404
        if nb_items > 0:   # Case OK : Products Found
            items = results.fetchall()
            items_as_dicts = [dict(row._mapping) for row in items]
            return jsonify(items_as_dicts), 200
        else:              # Case OK : No Product found
            return jsonify({f"message": "No records contain {keywords}"}), 204


def check_fields(body, fields):
    """
    Check availability of required fields in request's body
    """
    required_fields = set(fields)
    available_fields = set(body.keys())
    required_fields_availability = required_fields <= available_fields
    return required_fields_availability
