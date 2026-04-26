# Web Routes for Frontend Pages (HTML Templates)

from flask import Blueprint, render_template
#from app.database.model import Produit # DB Model Table

web_bp = Blueprint('web', __name__)


# ROUTES DEFINITION

@web_bp.route("/catalog")
def catalog():
    """Main product view for all users."""
    return render_template("catalog.html")

@web_bp.route("/login")
def login():
    return render_template("login.html")

@web_bp.route("/register")
def register():
    return render_template("register.html")

@web_bp.route("/cart")
def cart():
    return render_template("cart.html")

@web_bp.route("/orders")
def orders():
    return render_template("orders.html")

    # Fetch all products from DB
#    all_products = Produit.query.all()

    # Render Products as webpage
#    return render_template("products.html", products=all_products)