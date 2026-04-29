# Web Routes for Frontend Pages (HTML Templates)
# This module handles the routing for the user interface, serving the Jinja2 templates.

from flask import Blueprint, render_template

# Define the blueprint for web-related routes
web_bp = Blueprint("web", __name__)

# --- ROUTES DEFINITION ---


@web_bp.route("/")
def index():
    """
    Redirects to the catalog page.
    """
    return render_template("catalog.html")


@web_bp.route("/catalog")
def catalog():
    """
    Main product view for all users.
    Serves the catalog page where clients can browse products
    and admins can access management tools.
    """
    return render_template("catalog.html")


@web_bp.route("/login")
def login():
    """
    User authentication page.
    Provides the interface for existing users to sign in.
    """
    return render_template("login.html")


@web_bp.route("/register")
def register():
    """
    New account creation page.
    Provides the form for guests to create a new client account.
    """
    return render_template("register.html")


@web_bp.route("/cart")
def cart():
    """
    Shopping cart page.
    Displays the current items selected by the client before checkout.
    """
    return render_template("cart.html")


@web_bp.route("/orders")
def orders():
    """
    Order history and management page.
    Clients see their past purchases, while admins see all orders to manage status.
    """
    return render_template("orders.html")
