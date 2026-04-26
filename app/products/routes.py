import app.app_utils as au # Custom utilities for app

from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.database.model import Produit  #  DB Model Table
from app.auth.decorators import requires_authorization

# Bluprint of Routes for Products
products_bp = Blueprint(
    'products',  # id for routing
    __name__ # current module's path
    )


 # ROUTES DEFINITION

# Route Create Product
@products_bp.route("/produits", methods=["POST"])
@requires_authorization
def create_product(data_in_token):

    # Get User Data from DB
    user_role = au.get_user_attribute_in_db(data_in_token, "role")

    # Reject non-Admin Users
    if user_role != "admin":  
        return jsonify({"error": "User {email} not authorized to create products."}), 403
    
    # Get Product Data from Request
    submitted_data = request.get_json()
    missing_fields = (not au.check_fields(
        submitted_data, {
            "nom", 
            "description",
            "categorie",
            "prix",
            "quantite_stock",
            }
    ))
    if missing_fields:
        return jsonify({"error": "Missing fields."}), 400
    new_product = Produit(
        nom=submitted_data["nom"],
        description=submitted_data["description"],
        categorie=submitted_data["categorie"],
        prix=submitted_data["prix"],
        quantite_stock=submitted_data["quantite_stock"]
    )

    # Create Product in DB
    db.session.add(new_product)
    db.session.commit()

    # Return Product as a string
    return au.get_items(Produit, Produit.id, new_product.id)


# Route Update Product
@products_bp.route("/produits/<int:product_id>", methods=["PUT"])
@requires_authorization
def update_product(product_id, data_in_token):

    # Get User Data from DB
    user_email = au.get_user_attribute_in_db(data_in_token, "email")
    user_role = au.get_user_attribute_in_db(data_in_token, "role")

    # Check User is Admin
    if user_role != "admin":
        return jsonify({"error": f"User {user_email} not authorized to update products."}), 403
    
    # Get Product Data from Request
    submitted_data = request.get_json()
    
    # Check Product exists in DB
    product = Produit.query.get(product_id)
    if not product:
        return jsonify({"error": f"Product with id {product_id} not found."}), 404
    
    # Get Submitted Fields        
    current_app.logger.debug(f"update_product:\n {submitted_data.keys()}")
    all_fields = {"nom", "description", "categorie", "prix", "quantite_stock"}
    for field in all_fields:
        field_is_available = au.check_fields(submitted_data, {field})
        
        # Update Submitted Field in DB
        if field_is_available:
            setattr(product, field, submitted_data[field])

    db.session.commit()

    # Return Updated Product
    return get_product_by_id(product_id)


# Route Delete Product
@products_bp.route("/produits/<int:product_id>", methods=["DELETE"])
@requires_authorization
def delete_product(product_id, data_in_token):

    # Get User Data from DB
    user_email = au.get_user_attribute_in_db(data_in_token, "email")
    user_role = au.get_user_attribute_in_db(data_in_token, "role")

    # Reject non-Admin Users
    if user_role != "admin":  
        return jsonify({"error": f"User {user_email} not authorized to delete products."}), 403

    # Check Product in DB before deletion
    product = Produit.query.get(product_id)
    if not product:
        return jsonify({"error": f"Product with id {product_id} not found."}), 404
    
    # Delete Product in DB
    db.session.delete(product)

    db.session.commit()

    # Check Product in DB after deletion
    product = Produit.query.get(product_id)
    if not product:
        return jsonify({"info": f"Product with id {product_id} has been deleted."}), 200
    else:
        return jsonify({"error": f"Product with id {product_id} could not be deleted."}), 404


# Route Get Product by ID
@products_bp.route("/produits/<int:product_id>", methods=["GET"])
@requires_authorization
def get_product_by_id(product_id, data_in_token):
    return au.get_items(Produit, Produit.id, product_id)


# Route Get All Products
@products_bp.route("/produits", methods=["GET"])
def get_products():
    '''
    Goals: Get all products from DB &
    Search products by keywords (if any) in name & description
    '''
    
    # Get Query Parameters
    keywords = request.args.getlist('keywords')

    if keywords:

        # Search products by keywords in name & description
        results = au.search_items(db, "Produit", "nom", "description", keywords)
        
    else:

        # Get all products from DB  
        results = au.get_items(Produit)
    
    return results

