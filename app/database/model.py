from .. import db

from datetime import datetime

class Utilisateur(db.Model):
    __tablename__ = 'utilisateur'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(200), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='client')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to link orders to a user
    commandes = db.relationship('Commande', backref='client', lazy=True)


class Produit(db.Model):
    __tablename__ = "produit"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    categorie = db.Column(db.String(100), nullable=True)
    prix = db.Column(db.Float, nullable=False)
    quantite_stock = db.Column(db.Integer, nullable=False, default=0)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)


class Commande(db.Model):
    __tablename__ = 'commande'
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    date_commande = db.Column(db.DateTime, default=datetime.utcnow)
    adresse_livraison = db.Column(db.String(500), nullable=False)
    statut = db.Column(db.String(50), nullable=False, default='en_attente')
    
    # Relationship to link items to an order
    lignes = db.relationship('LigneCommande', backref='commande_parent', lazy=True)

class LigneCommande(db.Model):
    __tablename__ = 'ligne_commande'
    id = db.Column(db.Integer, primary_key=True)
    commande_id = db.Column(db.Integer, db.ForeignKey('commande.id'), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey('produit.id'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Float, nullable=False)
