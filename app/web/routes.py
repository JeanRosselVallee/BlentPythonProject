from flask import Blueprint, render_template
from app.database.model import Produit # DB Model Table

web_bp = Blueprint('web', __name__)

@web_bp.route("/catalog")
def show_catalog():

    # Fetch all products from DB
    all_products = Produit.query.all()

    # Render Products as webpage
    return render_template("products.html", products=all_products)