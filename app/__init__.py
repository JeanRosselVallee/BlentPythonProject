from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from functools import wraps # Preserves distinct names of functions inside a decorator
from .app_utils import generate_json_token, verify_token, get_items, check_fields


# Authorization Decorator for routes
def requires_authorization(target_function):
    @wraps(target_function)  # Preserves target_function's internal name 
    def wrapper(*args, **kwargs):

        # Get Token
        token = request.headers.get("authorization", "0")  # 0 by default
        data_in_token = verify_token(token)        
        if not data_in_token:
            return jsonify({"error": "Authorization denied: invalid token"}), 401
        
        # Share data in token with target function
        kwargs['data_in_token'] = data_in_token
        
        # Run Target Function
        return target_function(*args, **kwargs)

    return wrapper


# DB instanciation
db = SQLAlchemy()


# Flask App Creation
def create_app():
    app = Flask(__name__)


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

    # Route Authenticate
    @app.route("/authenticate", methods=["POST"])
    def authenticate():
        f_name = "authenticate()"

        # Get credentials from request
        submitted_data = request.get_json()
        request_is_incomplete = (not check_fields(submitted_data, {"email", "password"}))
        if request_is_incomplete:
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
        token = generate_json_token(email_in_db)
        return token, 200


    # Route Home
    @app.route("/", methods=["GET"])
    def home():

        # Fetch all products from DB
        all_products = Produit.query.all()

        # Render Products as webpage
        return render_template("products.html", products=all_products)


    # Route Get All Products
    @app.route("/api/produits", methods=["GET"])
    @requires_authorization
    def get_products(data_in_token):
        return get_items(Produit)


    # Route Get Product by ID
    @app.route("/api/produits/<int:product_id>", methods=["GET"])
    @requires_authorization
    def get_product_by_id(product_id, data_in_token):
        return get_items(Produit, Produit.id, product_id)


    # Route Create Order
    @app.route("/api/commandes", methods=["POST"])
    @requires_authorization
    def create_order(data_in_token):
        try:
            submitted_data = request.get_json()
            if not check_fields(submitted_data, {"utilisateur_id", "adresse_livraison"}):
                return jsonify({"error": "Missing fields."}), 400
            new_order = Commande(
                utilisateur_id=submitted_data["utilisateur_id"],
                adresse_livraison=submitted_data["adresse_livraison"],
            )
            db.session.add(new_order)
            db.session.commit()

            return get_items(Commande, Commande.id, new_order.id)

        except Exception as e:
            #return jsonify({"error": "create_order()"}), 400
            return jsonify({"error": f"create_order() - {str(e)}"}), 400


    # Route Get Orders
    @app.route("/api/commandes", methods=["GET"])
    @requires_authorization
    def get_orders(data_in_token):
        submitted_data = request.get_json()
        if not check_fields(submitted_data, {"email"}):
            return jsonify({"error": "Missing email address."}), 400
        user_in_db = Utilisateur.query.filter_by(email=submitted_data["email"]).first()
        if user_in_db.role == "admin":
            return get_items(Commande)
        else:
            return get_items(Commande, Commande.utilisateur_id, user_in_db.id)


    # Route Get Order by ID
    @app.route("/api/commandes/<int:order_id>", methods=["GET"])
    @requires_authorization
    def get_order_by_id(order_id, data_in_token):
        submitted_data = request.get_json()
        if not check_fields(submitted_data, {"email"}):
            return jsonify({"error": "Missing email address."}), 400

        all_orders = Commande.query.all()
        all_orders_ids = [order.id for order in all_orders]
        order_exists = order_id in all_orders_ids
        if not order_exists:
            return jsonify({"error": "Order not found."}), 404

        user_in_db = Utilisateur.query.filter_by(email=submitted_data["email"]).first()
        user_orders = Commande.query.filter_by(utilisateur_id=user_in_db.id)

        user_orders_ids = [order.id for order in user_orders]
        order_is_own = (order_id in user_orders_ids)
        user_is_admin = (user_in_db.role == "admin")
        if order_is_own or user_is_admin:
            return get_items(Commande, Commande.id, order_id)
        else:
            return jsonify({"error": "User not authorized to view this order."}), 404


    @app.route("/api/commandes/<int:order_id>", methods=["PATCH"])
    @requires_authorization
    def update_order(order_id, data_in_token):
        try:
            email = request.args.get("email")
            user_in_db = Utilisateur.query.filter_by(email=email).first()
            if user_in_db.role != "admin":
                return jsonify({"error": "User {email} not authorized to update orders."}), 403
            submitted_data = request.get_json()
            status_is_missing = not check_fields(submitted_data, {"status"})
            if status_is_missing:
                return jsonify({"error": "Missing status."}), 400
            order = Commande.query.get(order_id)
            if not order:
                return jsonify({"error": "Order not found."}), 404
            order.statut = submitted_data["status"]
            db.session.commit()
            return get_order_by_id(order_id)

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/api/commandes/<int:order_id>/lignes", methods=["GET"])
    @requires_authorization
    def get_order_items(order_id, data_in_token):
        return get_items(LigneCommande, LigneCommande.commande_id, order_id)


    @app.route("/api/commandes/<int:order_id>/lignes", methods=["POST"])
    @requires_authorization
    def add_order_item(order_id, data_in_token):
        try:
            submitted_data = request.get_json()
            if not check_fields(submitted_data, {"produit_id", "quantite"}):
                return jsonify({"error": "Missing fields."}), 400
                
            all_orders = Commande.query.all()
            all_orders_ids = [order.id for order in all_orders]
            order_exists = (order_id in all_orders_ids)
            if not order_exists:
                return jsonify({"error": "Order not found."}), 404

            produit = Produit.query.filter_by(id=submitted_data["produit_id"]).first()
            if not produit:
                return jsonify({"error": "Product not found."}), 404
            new_item = LigneCommande(
                commande_id=order_id,
                produit_id=submitted_data["produit_id"],
                quantite=submitted_data["quantite"],
                prix_unitaire=produit.prix,
            )
            db.session.add(new_item)
            db.session.commit()
            return get_order_items(order_id)
        except Exception as e:
            return jsonify({"error": str(e)}), 400


    # Flask App created
    return app


# Flask App Initialization
app = create_app()
