from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

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

    return app

app = create_app()
