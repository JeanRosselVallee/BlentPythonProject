import random
from datetime import datetime, timedelta
from faker import Faker
from app import app, db   # imports Flask app & SQLAlchemy db from init.py
from app.database.model import Utilisateur, Produit, Commande, LigneCommande

# Initialize Faker with French locale for realistic French names/addresses
fake = Faker('fr_FR')

def seed_database():
    with app.app_context():
        print("Cleaning up the database...")
        # Delete records in reverse order of dependencies to avoid Foreign Key constraints
        db.session.query(LigneCommande).delete()
        db.session.query(Commande).delete()
        db.session.query(Produit).delete()
        db.session.query(Utilisateur).delete()
        
        # 1. Generate 50 Users
        print("Generating users...")
        utilisateurs = []
        for _ in range(50):
            user = Utilisateur(
                nom=fake.name(),
                email=fake.unique.email(),
                mot_de_passe="pbkdf2:sha256:250000$hash_example", # Placeholder hash
                role=random.choice(['client', 'client', 'admin']),
                date_creation=fake.date_time_between(start_date='-1y', end_date='now')
            )
            utilisateurs.append(user)
            db.session.add(user)
        
        # 2. Setup IT Hardware Data
        print("Generating IT hardware products...")
        DATA_INFO = {
            'Processeur': ['Intel Core i9', 'AMD Ryzen 7', 'Intel Core i5', 'Apple M2'],
            'Carte Graphique': ['NVIDIA RTX 4080', 'AMD Radeon RX 7900', 'NVIDIA GTX 1650'],
            'Stockage': ['SSD NVMe 1To', 'Disque Dur 4To', 'SSD Externe USB-C'],
            'Mémoire RAM': ['DDR5 32Go', 'DDR4 16Go 3200MHz', 'Kit Dual Channel 64Go'],
            'Écran': ['Moniteur 27" 4K', 'Dalle OLED 144Hz', 'Écran Incurvé 34"'],
            'Accessoire': ['Clavier Mécanique RGB', 'Souris Sans Fil', 'Casque Audio 7.1']
        }

        produits = []
        for _ in range(50):
            # Pick a random category from our dictionary keys
            cat_info = random.choice(list(DATA_INFO.keys()))
            
            # Build a realistic name: Category + Brand + Model
            brand = random.choice(['ASUS', 'MSI', 'Corsair', 'Logitech', 'Samsung', 'Gigabyte'])
            model = random.choice(DATA_INFO[cat_info])
            final_name = f"{cat_info} {brand} - {model}"
            
            # Create a technical description in French (since the site is for a French audience)
            tech_description = (
                f"High-performance {cat_info} hardware. "
                f"Ideal for gaming and professional video editing. "
                f"Manufacturer warranty included. Specs: {fake.word()} {random.randint(10, 99)} Plus."
            )

            prod = Produit(
                nom=final_name,
                description=tech_description,
                categorie=cat_info,
                prix=round(random.uniform(20.0, 1500.0), 2),
                quantite_stock=random.randint(0, 50),
                date_creation=fake.date_time_between(start_date='-60d', end_date='now')
            )
            produits.append(prod)
            db.session.add(prod)

        # Flush to get product & user IDs for the order lines
        db.session.flush() # < commit

        # 3. Generate 50 Orders
        print("Generating orders...")
        commandes = []
        for _ in range(50):
            random_user = random.choice(utilisateurs)
            cmd = Commande(
                utilisateur_id=random_user.id,
                date_commande=fake.date_time_between(start_date='-30d', end_date='now'),
                adresse_livraison=fake.address().replace('\n', ' '),
                statut=random.choice(['pending', 'paid', 'shipped', 'delivered'])
            )
            commandes.append(cmd)
            db.session.add(cmd)

        # Flush to get Order IDs for the line items
        db.session.flush() # < commit

        # 4. Generate 50 Order Line Items
        print("Generating order line items...")
        for _ in range(50):
            random_cmd = random.choice(commandes)
            random_prod = random.choice(produits)
            
            line = LigneCommande(
                commande_id=random_cmd.id,
                produit_id=random_prod.id,
                quantite=random.randint(1, 5),
                prix_unitaire=random_prod.prix  # Snapshot of product price at time of purchase
            )
            db.session.add(line)

        # Final commit to save all changes permanently
        db.session.commit()
        print("Success! The database has been populated with 50 rows per table.")

if __name__ == "__main__":
    seed_database()