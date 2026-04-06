import datetime

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import jwt
from datetime import datetime, timedelta, timezone

SECRET_PHRASE = "d3fb12750c2eff92120742e1b334479e"

db = SQLAlchemy()




def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///digimarket.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)

    with app.app_context():
        from .database import model   # DB model defines tables
        from .database.model import Produit
        db.create_all()                 # Creates DB file
        
    @app.route('/')
    def home():
        # Fetch all products from DB
        all_products = Produit.query.all()
        # Pass the products to the 'home.html' file
        return render_template('home.html', products=all_products)

    @app.route('/cart')
    def cart():
        return "Empty cart !"

    @app.route('/authenticate', methods=['POST'])
    def generate_token():
        body = request.get_json()
        if body and body.get('password', '') == 'blent':
            now_ts = datetime.now(timezone.utc)
            token = jwt.encode(
                {   'expire_time': (now_ts + timedelta(hours=1)).timestamp(),
                    'user': 'blentia'}, 
                SECRET_PHRASE, 
                algorithm='HS256'   # singular
                )
            return jsonify({'token': token}), 200
        return jsonify({'error': 'Invalid credentials'}), 401

    @app.route('/authorize', methods=['GET'])
    @requires_authentication
    def authorize():
        return jsonify({'message': 'OK!'}), 200


    return app

def decode_token(token):
    try:
        ret = jwt.decode(
            token,
            SECRET_PHRASE,
            algorithms=["HS256"]  # plural
        )
        # print("ret=", ret)
        return ret  
    except Exception:
        print("Invalid JWT token.")
        return
    

def requires_authentication(target_function):
    def wrapper(*args, **kwargs):
        token = request.headers.get('authorization', '0')
        if decode_token(token):
            return target_function(*args, **kwargs)
        else:
            return jsonify({'error': 'Unauthorized: invalid token'}), 401
    return wrapper

app = create_app()
