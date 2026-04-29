# Database Models
# This module defines the database schema using SQLAlchemy ORM.
# It establishes the tables, columns, and relationships for the e-commerce system.

from app.extensions import db
from datetime import datetime, timezone


class Utilisateur(db.Model):
    """
    Represents system users (Clients and Admins).
    - Stores credentials and roles.
    - Has a 'one-to-many' relationship with orders.
    """

    __tablename__ = "utilisateur"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(200), nullable=False)  # Hashed password
    nom = db.Column(db.String(100), nullable=False)
    role = db.Column(
        db.String(50), nullable=False, default="client"
    )  # 'client' or 'admin'
    date_creation = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Relationship: One user can have multiple orders
    commandes = db.relationship("Commande", backref="client", lazy=True)


class Produit(db.Model):
    """
    Represents items available for sale.
    - Tracks pricing and current inventory (quantite_stock).
    """

    __tablename__ = "produit"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    categorie = db.Column(db.String(100), nullable=True)
    prix = db.Column(db.Float, nullable=False)
    quantite_stock = db.Column(db.Integer, nullable=False, default=0)
    date_creation = db.Column(db.DateTime, default=datetime.now(timezone.utc))


class Commande(db.Model):
    """
    Represents a purchase transaction.
    - Links to a user (Foreign Key).
    - Tracks status (en_attente, validée, expédiée, annulée).
    - Contains multiple line items.
    """

    __tablename__ = "commande"
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id"), nullable=False
    )
    date_commande = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    adresse_livraison = db.Column(
        db.String(500), nullable=True
    )  # Populated during checkout
    statut = db.Column(db.String(50), nullable=False, default="en_attente")

    # Relationship: One order links to many line items (LigneCommande)
    lignes = db.relationship("LigneCommande", backref="commande_parent", lazy=True)


class LigneCommande(db.Model):
    """
    Represents a specific product within an order.
    - Captures the 'snapshot' price at the time of purchase.
    - Links a specific Order to a specific Product.
    """

    __tablename__ = "ligne_commande"
    id = db.Column(db.Integer, primary_key=True)
    commande_id = db.Column(db.Integer, db.ForeignKey("commande.id"), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey("produit.id"), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Float, nullable=False)  # Price at moment of sale
