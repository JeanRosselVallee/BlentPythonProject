# Application Factory and Initialization
# This script initializes the Flask application, configures the database,
# registers all functional blueprints, and
# ensures the database tables are created.

# import logging

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
    """
    Factory function to create and configure the Flask app.
    Sets up SQLite URI, initializes extensions, and registers blueprints.
    """
    app = Flask(__name__)

    # DB setup
    # Configuring the SQLite database location and disabling overhead tracking
    db_uri = "sqlite:///digimarket.db"  # ~URL to DB file
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    # DEBUG: SQL Queries automatically printed
    # app.config.from_object(Config)

    # Blueprint Routes Registration

    # - Routes for Authentication: Register & Login (prefixed with /auth)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # - Routes for Products (prefixed with /api)
    app.register_blueprint(products_bp, url_prefix="/api")

    # - Routes for Orders (prefixed with /api)
    app.register_blueprint(orders_bp, url_prefix="/api")

    # - Routes for Frontend Web Pages (Main site routes, no prefix)
    app.register_blueprint(web_bp)  # No prefix

    # DB R/W Access
    with app.app_context():
        """
        Ensures that database tables defined in model.py are created
        within the application context if they do not already exist.
        """
        # Create DB as a file
        db.create_all()

    # Flask App created
    return app


# Flask App Initialization
# Creating the final app instance to be used by the server or CLI tools
app = create_app()
