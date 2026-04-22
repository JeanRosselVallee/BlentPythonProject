import requests
import json
import logging

from app import app, db
from app.database.model import Utilisateur, Produit, Commande, LigneCommande
from werkzeug.security import generate_password_hash


HOST = "127.0.0.1"
PORT = "5000"
URL = f"http://{HOST}:{PORT}"
SUCCESS_CODES = [200, 201]

testing_users = {
    "client": {
        "email": "customer@test.net",
        "password": "blent",
        "token": None,
        "id": None,
        "name": "Customer",
        "role": "client",
        "product_ids":[],
        "order_ids":[]
    },
    "admin": {
        "email": "admin@test.net",
        "password": "admin",
        "token": None,
        "id": None,
        "name": "Admin",
        "role": "admin",
        "product_ids":[],
        "order_ids":[]
    }
}

tested_clients = [
    {
        "email": "tested_client_1@test.net",
        "password": "blent",
        "name": "Tested Client 1",
    },
    {
        "email": "tested_client_2@test.net",
        "password": "blent",
        "name": "Tested Client 2",
    },
]

tested_product ={
        "nom": "Mouse wireless Microsoft",
        "description": "Black, rechargeable, USB-C radio emitter",
        "categorie": "Accessories",
        "prix": 45,
        "quantite_stock": 30
    }

def check_connection_to_server():
    """
    Check if Flask app is running before executing tests.
    """
    try: 
        requests.get(URL)
    except requests.exceptions.ConnectionError:
        raise Exception("ERROR: Flask app not running.")


# Get user instance from DB with his email
get_user = lambda email: Utilisateur.query.filter_by(email=email).first()

def create_testing_users():
    """
    Create test customer & admin users in DB.
    """
    with app.app_context():
        for user in testing_users.values():
            email = user["email"]

            # Avoid duplicates in DB
            user_instance = get_user(email)
            if user_instance:
                logging.info(f"User {email} already exists in DB.")
                continue

            # Create SQLAlchemy instance
            user_instance = Utilisateur(
                email=email,
                mot_de_passe=generate_password_hash(user["password"]),
                nom=user["name"],
                role=user["role"]
            )

            # Create user in DB
            db.session.add(user_instance)
            db.session.commit()
            logging.info(f"User {email} was created in DB.")

            # Store user's id for other tests
            db.session.refresh(user_instance)
            user["id"] = user_instance.id

def get_last_user_order(user_email):
    with app.app_context():
        user_instance = get_user(user_email)
        orders = Commande.query.filter_by(utilisateur_id=user_instance.id)
        orders_ids = [order.id for order in orders]
        logging.info(f"Ids of orders for user {user_email}: {orders_ids}")
        last_order_id = orders_ids[0]
        logging.info(f"Id of last order: {last_order_id}")
        return last_order_id
    
def get_expected_status_per_role(user_role):
    # Get expected statuses based on user's role
    if user_role == "admin":
        # Admin can create orders
        expected_statuses = SUCCESS_CODES
    else:  
        # Clients can't create products 
        expected_statuses = [403]
    return expected_statuses

def get_expected_status_for_order_ownership(user_role, current_order_id, last_own_order_id) :
    # Get expected statuses based on user's role & order's ownership
    user_is_admin = (user_role == "admin")
    order_is_own = (current_order_id == last_own_order_id)
    if user_is_admin or order_is_own:
        expected_statuses = [200, 201]
    else:  # Alien orders are hidden for non-admin users
        expected_statuses = [403, 404]
    return expected_statuses


def delete_test_data():
    """
    Delete test data in DB.
    """
    with app.app_context():
        # Clear test data in cascade

        for user in testing_users.values():
            user_instance = get_user(user["email"])

            if user_instance:
                # Get test users' orders
                orders = Commande.query.filter_by(utilisateur_id=user_instance.id)
                orders_ids = [order.id for order in orders]
                logging.info(f"Ids of orders for user {user['email']}: {orders_ids}")

                # Delete orders' items
                order_items = LigneCommande.query.filter(LigneCommande.commande_id.in_(orders_ids))
                order_items_ids = [item.id for item in order_items]
                logging.info(f"Ids of corresponding order items: {order_items_ids}")
                
                nb_order_items = order_items.delete()
                logging.info(f"Deleted {nb_order_items} corresponding order item(s)")

                # Delete orders
                nb_orders = orders.delete()
                logging.info(f"Deleted {nb_orders} corresponding order(s)")

                # Get testing users' products
                product_ids = user['product_ids']
                logging.info(f"Ids of products for user {user['email']}: {product_ids}")

                # Delete products
                products = Produit.query.filter(Produit.id.in_(product_ids))
                nb_products = products.delete()
                logging.info(f"Deleted {nb_products} corresponding product(s)")
                
                # Delete testing_users
                db.session.delete(user_instance)
                logging.info(f"Deleted user {user['email']}.")

                db.session.commit()  

        # Delete Tested Users
        for email in ["tested_client_1@test.net", "tested_client_2@test.net"]:
            user_instance = get_user(email)
            if user_instance:                 
                db.session.delete(user_instance)
                logging.info(f"Deleted user {email}.")
                db.session.commit()  

def assert_status_to_delete(response, test_goal, expected_statuses):
    """
    Validates the HTTP response and prints formatted output.
    """

    # Log Goal & URL
    logging.info(f"API '{test_goal}'")
    logging.info(f"URL {response.url}")
    
    # Get Status from Response Tuple
    status = response.status_code
    status_OK = (status in expected_statuses)

    # Check Status
    if status_OK:        
        logging.info("Response OK")
    else:
        logging.exception(f"{response.json().get('error')}")

    return status_OK


def assert_status(response, test_goal, expected_statuses):
    """
    Check Response Tuple 
    """    

   # Log Goal & URL
    logging.info(f"API '{test_goal}'")
    logging.info(f"URL {response.url}")
     
    # Get Status & Payload from Response Tuple
    status = response.status_code
    status_OK = (status in expected_statuses)
    # Get indented string (from binary response.content)
    content = response.content.decode('utf-8') 

    # Log Error if any
    error_message = f"{test_goal} got status code {response.status_code} but expected {expected_statuses}"
    if not status_OK:
        error_message = f"{error_message}. {response.json()['error']}"
        logging.error(error_message)

    # Log Data in Response
    logging.info(f"Response : {content}")         
    
    # Pytest Assertion
    assert status_OK, error_message

    # Return Response as [{...}]
    return json.loads(response.content)
    
    
    
