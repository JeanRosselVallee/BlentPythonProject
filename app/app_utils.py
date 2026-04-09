import jwt

from datetime import datetime, timedelta, timezone
from flask import jsonify

SECRET_PHRASE = "d3fb12750c2eff92120742e1b334479e"

# Token Generation for Authentication
def generate_token(username):
    now = datetime.now(timezone.utc)
    expire_time = now + timedelta(hours=1)
    token = jwt.encode(
        {   'expire_time': expire_time.timestamp(),
            'user': username}, 
        SECRET_PHRASE, 
        algorithm='HS256'   # singular
        )
    return token

# Token Validity Check for Authorization
def verify_token(token):
    try:
        ret = jwt.decode(
            token,
            SECRET_PHRASE,
            algorithms=["HS256"]  # plural
        )
        return ret  
    except Exception:
        print("Invalid JWT token.")
        return

# Get items from DB for Routes Definition
def get_items(table, field=None, item_id=None):
    """
    Fetch items from DB, optionally filtered, & returned as JSON
    parameters:
    - table: DB table
    - field (optional): filter DB column
    - item_id (optional): filter value 
    """
    if item_id:
        target_items = table.query.filter(field==item_id)
        nb_items = target_items.count()
    else:
        target_items = table.query.all()
        nb_items = len(target_items)
    if target_items and nb_items > 0:    
        items = [
            {c.name: getattr(o, c.name) for c in o.__table__.columns} 
            for o in target_items
        ]
        return jsonify(items), 200
    else:
        return jsonify({'error': 'No records found'}), 404       

# OBSOLETE Format SQLAlchemy object as JSON-serializable dict
# def sqla_to_dict(sqla_object):
#     if not sqla_object: return None
#     columns = sqla_object.__table__.columns
#     obj_as_dict = {column.name: getattr(sqla_object, column.name) for column in columns}
#     return jsonify(obj_as_dict)

# called in init.py
        # target_product = Produit.query.get(product_id)
        # if target_product:
        #     return sqla_to_dict(target_product), 200
        # return jsonify({'error': 'Target product not found'}), 404

def check_fields(body, fields):
    """
    Check availability of required fields in request's body
    """
    required_fields = set(fields)    
    available_fields = set(body.keys())
    required_fields_availability = (required_fields <= available_fields)
    return required_fields_availability