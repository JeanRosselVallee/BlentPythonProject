import app.app_utils as au  # Custom Library
import logging

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from functools import wraps # Preserves distinct names of functions inside a decorator
from config import Config  # Custom ../config.py

# Authorization Decorator for routes
def requires_authorization(target_function):
    @wraps(target_function)  # Preserves target_function's internal name 
    def wrapper(*args, **kwargs):

        # Get Token
        token = request.headers.get("authorization", "0")  # 0 by default
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


# DB instanciation
db = SQLAlchemy()


# Flask App Creation
def create_app():
    app = Flask(__name__)

    # Setup from ../config.py
    # Enable to debug SQL queries in front&backend output
    # app.config.from_object(Config) 

    # DB setup
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///digimarket.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    # DB R/W Access
    with app.app_context():
        # Import tables defined in ./database/model.py
        from .database.model import Produit, Commande, Utilisateur, LigneCommande

        # Create DB as a file
        db.create_all()  


    # ROUTES DEFINITION

    # Route Register User
    @app.route("/auth/register", methods=["POST"])
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
    
    
    # Route login
    @app.route("/auth/login", methods=["POST"])
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


    # Route Home
    @app.route("/", methods=["GET"])
    def home():

        # Fetch all products from DB
        all_products = Produit.query.all()

        # Render Products as webpage
        return render_template("products.html", products=all_products)


    # Route Create Product
    @app.route("/api/produits", methods=["POST"])
    @requires_authorization
    def create_product(data_in_token):

        # Get User Data from DB
        user_role = get_user_attribute_in_db(data_in_token, "role")

        # Reject non-Admin Users
        if user_role != "admin":  
            return jsonify({"error": "User {email} not authorized to create products."}), 403
        
        # Get Product Data from Request
        submitted_data = request.get_json()
        missing_fields = (not au.check_fields(
            submitted_data, 
            {"nom", 
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
    @app.route("/api/produits/<int:product_id>", methods=["PUT"])
    @requires_authorization
    def update_product(product_id, data_in_token):

        # Get User Data from DB
        user_email = get_user_attribute_in_db(data_in_token, "email")
        user_role = get_user_attribute_in_db(data_in_token, "role")

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
        app.logger.debug(f"update_product:\n {submitted_data.keys()}")
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
    @app.route("/api/produits/<int:product_id>", methods=["DELETE"])
    @requires_authorization
    def delete_product(product_id, data_in_token):

        # Get User Data from DB
        user_email = get_user_attribute_in_db(data_in_token, "email")
        user_role = get_user_attribute_in_db(data_in_token, "role")

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
    @app.route("/api/produits/<int:product_id>", methods=["GET"])
    @requires_authorization
    def get_product_by_id(product_id, data_in_token):
        return au.get_items(Produit, Produit.id, product_id)


    # Route Get All Products
    @app.route("/api/produits", methods=["GET"])
    def get_products():
        # try:
        #     return au.get_items(Produit)
        # except Exception as e:
        #     message = f"get_products() - {str(e)}"
        #     return jsonify({"error": f"{message}"}), 400


        # '''
        # Goals: Get all products from DB &
        # Search products by keywords (if any) in name & description
        # '''
        
        # Get Query Parameters
        # keywords = request.args.get('q')
        keywords = request.args.getlist('keywords')

        # TO DO
        # Add a filter + search button inside webpage ??

        if keywords:
            # Search products by keywords in name & description
            results = au.search_items(db, "Produit", "nom", "description", keywords)
            
        else:
            # Get all products from DB  
            results = au.get_items(Produit)
        
        return results




    # Route Create Order
    @app.route("/api/commandes", methods=["POST"])
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
    @app.route("/api/commandes", methods=["GET"])
    @requires_authorization
    def get_orders(data_in_token):

        # Get User Role & Id from DB
        user_role = get_user_attribute_in_db(data_in_token, "role")
        user_id = get_user_attribute_in_db(data_in_token, "id")

        # Admin gets all orders
        if user_role == "admin":            
            return au.get_items(Commande)

        # Client gets only own orders
        return au.get_items(Commande, Commande.utilisateur_id, user_id)


    # Route Add Order Item
    @app.route("/api/commandes/<int:order_id>/lignes", methods=["POST"])
    @requires_authorization
    def add_order_item(order_id, data_in_token):

        # Get Order Data from Request
        submitted_data = request.get_json()
        missing_fields = (not au.check_fields(submitted_data, {"produit_id", "quantite"}))
        if missing_fields:
            return jsonify({"error": "Missing fields."}), 400

        # Get User Id from DB
        user_id = get_user_attribute_in_db(data_in_token, "id")

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
    @app.route("/api/commandes/<int:order_id>/lignes", methods=["GET"])
    @requires_authorization
    def get_order_items(order_id, data_in_token):

        # Get User Data from DB
        user_id = get_user_attribute_in_db(data_in_token, "id")
        user_email = get_user_attribute_in_db(data_in_token, "email")
        user_role = get_user_attribute_in_db(data_in_token, "role")

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
    @app.route("/api/commandes/<int:order_id>", methods=["PATCH"])
    @requires_authorization
    def update_order_status(order_id, data_in_token):

        # Get User Data from DB
        user_email = get_user_attribute_in_db(data_in_token, "email")
        user_role = get_user_attribute_in_db(data_in_token, "role")

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
    @app.route("/api/commandes/<int:order_id>", methods=["GET"])
    @requires_authorization
    def get_order_by_id(order_id, data_in_token):

        # Get User Data from DB
        user_email = get_user_attribute_in_db(data_in_token, "email")
        user_role = get_user_attribute_in_db(data_in_token, "role")
        user_id = get_user_attribute_in_db(data_in_token, "id")

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


    def get_user_attribute_in_db(data_in_token, attribute_name):
        # Get User Role in DB
        email_in_token = data_in_token["login"]
        user_in_db = Utilisateur.query.filter_by(email=email_in_token).first()
        user_attribute = getattr(user_in_db, attribute_name, None)
        return user_attribute
    

    
    # Flask App created
    return app


# Flask App Initialization
app = create_app()


