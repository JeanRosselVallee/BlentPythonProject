import app.app_utils as au # Custom utilities for app

from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.database.model import Produit, Commande, LigneCommande #  DB Model Tables
from app.auth.decorators import requires_authorization

# Bluprint of Routes for Orders
orders_bp = Blueprint(
    'orders',  # id for routing
    __name__ # current module's path
    )


# Route Create Order
@orders_bp.route("/commandes", methods=["POST"])
@requires_authorization
def create_order(data_in_token):

    # Get Order Data from Request
    submitted_data = request.get_json()
    missing_fields = (not au.check_fields(submitted_data, {"utilisateur_id", "adresse_livraison"}))
    if missing_fields:
        return jsonify({"error": "Missing fields."}), 400
    new_order = Commande(
        utilisateur_id=submitted_data["utilisateur_id"],
        adresse_livraison=submitted_data["adresse_livraison"],
    )

    # Create Order in DB
    db.session.add(new_order)
    db.session.commit()

    # Return Order as a string
    return au.get_items(Commande, Commande.id, new_order.id)


# Route Get Orders
@orders_bp.route("/commandes", methods=["GET"])
@requires_authorization
def get_orders(data_in_token):

    # Get User Role & Id from DB
    user_role = au.get_user_attribute_in_db(data_in_token, "role")
    user_id = au.get_user_attribute_in_db(data_in_token, "id")

    # Admin gets all orders
    if user_role == "admin":            
        return au.get_items(Commande)

    # Client gets only own orders
    return au.get_items(Commande, Commande.utilisateur_id, user_id)


# Route Add Order Item
@orders_bp.route("/commandes/<int:order_id>/lignes", methods=["POST"])
@requires_authorization
def add_order_item(order_id, data_in_token):

    # Get Order Data from Request
    submitted_data = request.get_json()
    missing_fields = (not au.check_fields(submitted_data, {"produit_id", "quantite"}))
    if missing_fields:
        return jsonify({"error": "Missing fields."}), 400

    # Get User Id from DB
    user_id = au.get_user_attribute_in_db(data_in_token, "id")

    # Check User's Pending Order exists
    order = Commande.query.filter_by(
        id=order_id,
        utilisateur_id=user_id,
        statut="en_attente"
        ).first()
    if not order:
        return jsonify({"error": "Order not found."}), 404

    # Check Product exists
    id = submitted_data["produit_id"]
    product = Produit.query.get(id)
    if not product:
        return jsonify({"error": "Product not found."}), 404

    # Check Product Stock
    quantity = submitted_data["quantite"]
    stock = product.quantite_stock
    if quantity > stock:
        return jsonify({"error": f"{quantity} > stock of {stock} for product id {id}."}), 400

    # Create Order's Item in DB
    new_item = LigneCommande(
        commande_id=order_id,
        produit_id=submitted_data["produit_id"],
        quantite=submitted_data["quantite"],
        prix_unitaire=product.prix,
    )
    db.session.add(new_item)
    db.session.commit()

    # Return Order's Items
    return get_order_items(order_id)


# Route Get Order Items
@orders_bp.route("/commandes/<int:order_id>/lignes", methods=["GET"])
@requires_authorization
def get_order_items(order_id, data_in_token):

    # Get User Data from DB
    user_id = au.get_user_attribute_in_db(data_in_token, "id")
    user_email = au.get_user_attribute_in_db(data_in_token, "email")
    user_role = au.get_user_attribute_in_db(data_in_token, "role")

    #  Get Order
    if user_role == "admin":
        
        # Pending Order for Admin
        order = Commande.query.get(order_id)

    else:
        
        # Client's Pending Order 
        order = Commande.query.filter_by(
            id=order_id,
            utilisateur_id=user_id
        ).first()

    # Check Order exists
    if not order:
        return jsonify({"error": f"No order found with id {order_id} for user {user_email}"}), 404

    # Return Order's Items
    return au.get_items(LigneCommande, LigneCommande.commande_id, order_id)


# Route Update Order
@orders_bp.route("/commandes/<int:order_id>", methods=["PATCH"])
@requires_authorization
def update_order_status(order_id, data_in_token):

    # Get User Data from DB
    user_email = au.get_user_attribute_in_db(data_in_token, "email")
    user_role = au.get_user_attribute_in_db(data_in_token, "role")

    # Check User is Admin
    if user_role != "admin":
        return jsonify({"error": f"User {user_email} not authorized to update orders."}), 403
    
    # Get Order Data from Request
    submitted_data = request.get_json()
    status_is_missing = not au.check_fields(submitted_data, {"status"})
    if status_is_missing:
        return jsonify({"error": "Missing status."}), 400
    
    # Check Order exists in DB
    order = Commande.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found."}), 404

    # Update Order in DB
    order.statut = submitted_data["status"]

    # Check Order was updated in DB
    order = Commande.query.get(order_id)
    if order.statut != submitted_data["status"]: 
        return jsonify({"error": f"Order with id {order_id} could not be updated in DB."}), 404

    # Case of Order's Validdation
    validation_requested = (order.statut == "en_attente") and (submitted_data["status"] == "validée")
    if validation_requested:
    
        # Update Stocks of products in the order

        # Scan Order Items
        order_items = LigneCommande.query.filter_by(commande_id=order_id).all()
        for item in order_items:

            # Get Product Id & Quantity 
            id = item.produit_id 
            quantity = item.quantite

            # Get Product in DB                
            product = Produit.query.get(id)

            # Check Product Stock
            if not product or (product.quantite >= quantity):
                return jsonify({"error": f"No stock for product with id {id}."}), 400
            
            # Update Product Stock 
            product.quantite -= quantity

    # Update whole transaction in DB            
    db.session.commit()


    # Return Updated Order
    return get_order_by_id(order_id)


# Route Get Order by ID
@orders_bp.route("/commandes/<int:order_id>", methods=["GET"])
@requires_authorization
def get_order_by_id(order_id, data_in_token):

    # Get User Data from DB
    user_email = au.get_user_attribute_in_db(data_in_token, "email")
    user_role = au.get_user_attribute_in_db(data_in_token, "role")
    user_id = au.get_user_attribute_in_db(data_in_token, "id")

    #  Get Order
    if user_role == "admin":
        
        # Admin access to any order
        order = Commande.query.get(order_id)

    else:
        
        # Client access only to own order 
        order = Commande.query.filter_by(
            id=order_id,
            utilisateur_id=user_id
        ).first()

    # Check Order exists
    if not order:
        return jsonify({"error": f"No order found with id {order_id} for user {user_email}"}), 404

    # Return Order
    order_as_string = au.get_items(Commande, Commande.id, order_id)
    return order_as_string

