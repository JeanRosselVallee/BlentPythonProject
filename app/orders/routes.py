# Orders API Routes
# This module manages the lifecycle of customer orders, including creation,
# retrieval, status updates, and order line item management.

import app.app_utils as au  # Custom utilities for app
from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.database.model import Produit, Commande, LigneCommande  #  DB Model Tables
from app.auth.decorators import requires_authorization
from sqlalchemy import text

# Blueprint of Routes for Orders
orders_bp = Blueprint("orders", __name__)  # id for routing  # current module's path

# --- ROUTES DEFINITION ---


@orders_bp.route("/commandes", methods=["POST"])
@requires_authorization
def create_order(data_in_token):
    """
    Creates a new order record.
    - For 'client' role: Automatically associates the order with their user ID.
    - For 'admin' role: Allows manual assignment of a user ID and delivery address.
    """
    # Get User Data from DB
    user_role = au.get_user_attribute_in_db(data_in_token, "role")
    user_id = au.get_user_attribute_in_db(data_in_token, "id")

    # Create Order as SQLALchemy Instance
    if user_role == "client":
        new_order = Commande(
            utilisateur_id=user_id,
            # adresse_livraison=submitted_data["adresse_livraison"],
        )
    else:
        # Get Order Data from Request
        submitted_data = request.get_json()
        missing_fields = not au.check_fields(
            submitted_data, {"user_id", "adresse_livraison"}
        )
        if missing_fields:
            return jsonify({"error": "Missing fields."}), 400

        new_order = Commande(
            utilisateur_id=submitted_data["user_id"],
            adresse_livraison=submitted_data["adresse_livraison"],
        )

    # Create Order in DB
    db.session.add(new_order)
    db.session.commit()

    # Return Order as a string
    return au.get_items(Commande, Commande.id, new_order.id)


@orders_bp.route("/commandes", methods=["GET"])
@requires_authorization
def get_orders(data_in_token):
    """
    Retrieves a list of orders.
    - Admins: Retrieve all orders in the system.
    - Clients: Retrieve only their personal order history.
    """
    # Get User Role & Id from DB
    user_role = au.get_user_attribute_in_db(data_in_token, "role")
    user_id = au.get_user_attribute_in_db(data_in_token, "id")

    # Admin gets all orders
    if user_role == "admin":
        return au.get_items(Commande)

    # Client gets only own orders
    return au.get_items(Commande, Commande.utilisateur_id, user_id)


@orders_bp.route("/commandes/<int:order_id>/lignes", methods=["POST"])
@requires_authorization
def add_order_item(order_id, data_in_token):
    """
    Adds a specific product to an existing order.
    - Verifies order ownership and that the order status is 'en_attente'.
    - Validates product existence and stock availability before adding.
    """
    # Get Order Data from Request
    submitted_data = request.get_json()
    missing_fields = not au.check_fields(submitted_data, {"produit_id", "quantite"})
    if missing_fields:
        return jsonify({"error": "Missing fields."}), 400

    # Get User Id from DB
    user_id = au.get_user_attribute_in_db(data_in_token, "id")

    # Check User's Pending Order exists
    order = Commande.query.filter_by(
        id=order_id, utilisateur_id=user_id, statut="en_attente"
    ).first()
    if not order:
        return jsonify({"error": "Order not found."}), 404

    # Check Product exists
    id = submitted_data["produit_id"]
    product = Produit.query.get(id)
    if not product:
        return jsonify({"error": "Product no;t found."}), 404

    # Check Product Stock
    quantity = submitted_data["quantite"]
    stock = product.quantite_stock
    if quantity > stock:
        return (
            jsonify({"error": f"{quantity} > stock of {stock} for product id {id}."}),
            400,
        )

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


@orders_bp.route("/commandes/<int:order_id>/lignes", methods=["GET"])
@requires_authorization
def get_order_items(order_id, data_in_token):
    """
    Retrieves all product lines associated with a specific order.
    Uses a JOIN query to combine order data with product names for display.
    """
    # Get User Data from DB
    user_id = au.get_user_attribute_in_db(data_in_token, "id")
    user_email = au.get_user_attribute_in_db(data_in_token, "email")
    user_role = au.get_user_attribute_in_db(data_in_token, "role")

    selection = """
        SELECT 
            lc.commande_id, 
            p.nom, 
            lc.quantite, 
            lc.prix_unitaire
        FROM ligne_commande lc
    """
    junction = " JOIN produit p ON lc.produit_id = p.id"
    where_clause = " WHERE lc.commande_id = :order_id"

    #  Get Order
    if user_role == "admin":

        # Admin can access any Order
        sql_params = {"order_id": order_id}

    else:
        junction += " JOIN commande c ON lc.commande_id = c.id"
        where_clause += " AND c.utilisateur_id = :user_id"
        sql_params = {"order_id": order_id, "user_id": user_id}

    # Execute the query
    sql_query = text(selection + junction + where_clause)
    # current_app.logger.debug(f"DEBUG: Executing SQL query for user role {user_role}: {sql_query} with parameters: {sql_params}")
    order_items = db.session.execute(sql_query, sql_params)

    # Get Data from Query Results
    table_headers = order_items.keys()
    table_rows = order_items.fetchall()  # rows contain values no field names

    # Check Order Items exist
    nb_items = len(table_rows)
    if nb_items == 0:
        return (
            jsonify(
                {
                    "error": f"No order items found for order id {order_id} for user {user_email}"
                }
            ),
            404,
        )

    # Convert the result rows into a list of dictionaries
    items_as_list = [dict(zip(table_headers, row_values)) for row_values in table_rows]

    # Return Order's Items
    return jsonify(items_as_list), 200


@orders_bp.route("/commandes/<int:order_id>", methods=["PATCH"])
@requires_authorization
def update_order(order_id, data_in_token):
    """
    Updates order details:
    - Clients: Can update the 'adresse_livraison' for their own orders.
    - Admins: Can update the 'statut' (status).

    If an order moves from 'en_attente' to 'validée', the system
    automatically decrements the product stock levels.
    """
    # Get Order Data from Request
    submitted_data = request.get_json()

    # Check field provision
    address_provided = au.check_fields(submitted_data, {"adresse_livraison"})
    status_provided = au.check_fields(submitted_data, {"status"})
    required_field_provided = address_provided or status_provided
    if not required_field_provided:
        return jsonify({"error": "Missing field."}), 400

    # Case Update Delivery Address

    if address_provided:

        # Get User Data from DB
        user_id = au.get_user_attribute_in_db(data_in_token, "id")

        # Check Order is owned by User
        order = Commande.query.filter(
            Commande.id == order_id, Commande.utilisateur_id == user_id
        ).first()
        if not order:
            return jsonify({"error": "Order not found."}), 404

        # Update Order in DB
        order.adresse_livraison = submitted_data["adresse_livraison"]

        # Check Order was updated in DB
        order = Commande.query.get(order_id)
        if order.adresse_livraison != submitted_data["adresse_livraison"]:
            return (
                jsonify(
                    {"error": f"Order with id {order_id} could not be updated in DB."}
                ),
                404,
            )

    # Case Update Status

    if status_provided:

        # Get User Data from DB
        user_email = au.get_user_attribute_in_db(data_in_token, "email")
        user_role = au.get_user_attribute_in_db(data_in_token, "role")

        # Check User is Admin
        if user_role != "admin":
            return (
                jsonify(
                    {"error": f"User {user_email} not authorized to update orders."}
                ),
                403,
            )

        # Check Order exists in DB
        order = Commande.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found."}), 404

        # Update Order in DB
        previous_status_in_db = order.statut
        order.statut = submitted_data["status"]

        # Check Order was updated in DB
        order = Commande.query.get(order_id)
        new_status_in_db = order.statut
        if new_status_in_db != submitted_data["status"]:
            return (
                jsonify(
                    {"error": f"Order with id {order_id} could not be updated in DB."}
                ),
                404,
            )

        # Case of Order's Validation
        validation_requested = (previous_status_in_db == "en_attente") and (
            new_status_in_db == "validée"
        )
        if validation_requested:

            # Update Stocks of products in the order

            # Scan Order Items
            order_items = LigneCommande.query.filter_by(commande_id=order_id).all()
            for item in order_items:

                # Get Product Id & Quantity
                id = item.produit_id
                quantity_in_order = item.quantite

                # Get Product in DB
                product = Produit.query.get(id)

                # Check Product Stock
                if not product or (product.quantite_stock < quantity_in_order):
                    return (
                        jsonify({"error": f"No stock for product with id {id}."}),
                        400,
                    )

                # Update Product Stock
                product.quantite_stock -= quantity_in_order

    # Update whole transaction in DB
    db.session.commit()

    # Return Updated Order
    return au.get_items(Commande, Commande.id, order_id)


@orders_bp.route("/commandes/<int:order_id>", methods=["GET"])
@requires_authorization
def get_order_by_id(order_id, data_in_token):
    """
    Retrieves a single order by its ID.
    Enforces security by ensuring clients can only view their own orders.
    """
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
        order = Commande.query.filter_by(id=order_id, utilisateur_id=user_id).first()

    # Check Order exists
    if not order:
        return (
            jsonify(
                {"error": f"No order found with id {order_id} for user {user_email}"}
            ),
            404,
        )

    # Return Order
    order_as_string = au.get_items(Commande, Commande.id, order_id)
    return order_as_string
