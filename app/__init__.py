from functools import wraps

from flask import Flask, render_template, request, jsonify
from werkzeug.security import check_password_hash
from flask_sqlalchemy import SQLAlchemy
from .app_utils import generate_token, verify_token, get_items, check_fields

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Database setup
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///digimarket.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        from .database import model   # DB model defines tables
        from .database.model import Produit, Commande, Utilisateur, LigneCommande
        db.create_all()                 # Creates DB file
        
    # Routes definition
    @app.route('/', methods=['GET'])
    def home():
        # Fetch all products from DB
        all_products = Produit.query.all()
        # Render Products as webpage
        return render_template('products.html', products=all_products)  

    @app.route('/api/produits', methods=['GET'])
    @requires_authorization
    def get_all_products():
        return get_items(Produit)
    
    @app.route('/api/produits/<int:product_id>', methods=['GET'])
    @requires_authorization
    def get_product_by_id(product_id):
        return get_items(Produit, Produit.id, product_id)
    
    @app.route('/api/commandes', methods=['GET'])
    @requires_authorization
    def get_all_orders():    
        body = request.get_json()            
        if not check_fields(body, {'email'}):
            return jsonify({'error': "Missing email address."}), 400
        user_in_db = Utilisateur.query.filter_by(email=body['email']).first()
        if user_in_db.role == 'admin':
            return get_items(Commande)
        else:
            return get_items(Commande, Commande.utilisateur_id, user_in_db.id)
    
    @app.route('/api/commandes/<int:order_id>', methods=['GET'])
    @requires_authorization
    def get_order_by_id(order_id):
        return get_items(Commande, Commande.id, order_id)

    @app.route('/api/commandes/<int:order_id>/lignes', methods=['GET'])
    @requires_authorization
    def get_order_items_by_id(order_id):
        return get_items(LigneCommande, LigneCommande.commande_id, order_id)

    @app.route('/api/commandes', methods=['POST'])
    def create_order():
        try:
            body = request.get_json()            
            if not check_fields(body, {'utilisateur_id', 'adresse_livraison'}):
                return jsonify({'error': "Missing fields."}), 400            
            new_order = Commande(
                utilisateur_id=body['utilisateur_id'],
                adresse_livraison=body['adresse_livraison']
            )
            db.session.add(new_order)
            db.session.commit()
            return get_order_by_id(new_order.id)
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/commandes/<int:order_id>', methods=['PATCH'])
    def update_order(order_id):
        try:
            email = request.args.get('email')
            user_in_db = Utilisateur.query.filter_by(email=email).first()
            if user_in_db.role != 'admin':
                return jsonify({'error': 'User not authorized to update orders.'}), 403
            body = request.get_json()
            status_is_missing = (not check_fields(body, {'status'}))            
            if status_is_missing:
                return jsonify({'error': "Missing status."}), 400            
            order = Commande.query.get(order_id)
            if not order:
                return jsonify({'error': 'Order not found.'}), 404
            order.statut = body['status']
            db.session.commit()
            return get_order_by_id(order_id) 
                
        except Exception as e:
            return jsonify({'error': str(e)}), 400
            
    @app.route('/authenticate', methods=['POST'])
    def authenticate():
        body = request.get_json()
        credentials_are_missing = (not check_fields(body, {'email', 'password'}))
        if credentials_are_missing:
            return jsonify({'error': "Missing credentials."}), 400
        email_in_request = body['email']
        passw_in_request = body['password']
        # Get Password in DB
        user_in_db = Utilisateur.query.filter_by(email=email_in_request).first()
        if not user_in_db:
            return jsonify({'error': f'User {email_in_request} not found in DB'}), 404
        login = user_in_db.email
        passw = user_in_db.mot_de_passe
        # Check Password
        passwords_are_identical = (check_password_hash(passw, passw_in_request))
        if passwords_are_identical:
            token = generate_token(login)
            return jsonify({'token': token}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
        
    # Flask App created
    return app 

# Authorization Decorator for routes
def requires_authorization(target_function):
    @wraps(target_function)   
    def wrapper(*args, **kwargs):
        token = request.headers.get('authorization', '0')  # 0 by default
        if verify_token(token):
            return target_function(*args, **kwargs)
        else:
            return jsonify({'error': 'Unauthorized: invalid token'}), 401
    return wrapper


# Flask App Initialization 
app = create_app()
