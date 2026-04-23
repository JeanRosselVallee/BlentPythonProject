import app.app_utils as au  # Custom Library
import logging

from flask import Flask
# from config import Config  # debug SQLAlchemy queries cf. ../config.py

# Blueprints for Authentication & API Routes
from .auth.routes import auth_bp
from .products.routes import products_bp
from .orders.routes import orders_bp
from .web.routes import web_bp

# DB as App Extension
from .extensions import db


# Flask App Creation
def create_app():
    app = Flask(__name__)

    # DB setup
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///digimarket.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    # app.config.from_object(Config)     # DEBUG: SQL Queries automatically printed

    
    # Blueprint Routes Registration

    # - Routes for Authentication: Register & Login
    app.register_blueprint(auth_bp, url_prefix='/auth')  

    # - Routes for Products
    app.register_blueprint(products_bp, url_prefix='/api')

    # - Routes for Orders
    app.register_blueprint(orders_bp, url_prefix='/api')

    # - Routes for Frontend Web Pages
    app.register_blueprint(web_bp, url_prefix='/web')


    # DB R/W Access
    with app.app_context():

        # Create DB as a file
        db.create_all()  

    
    # Flask App created
    return app


# Flask App Initialization
app = create_app()


