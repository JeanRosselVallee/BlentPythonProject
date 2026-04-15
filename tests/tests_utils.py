import requests
import json
import logging

from app import app, db
from app.database.model import Utilisateur, Produit, Commande, LigneCommande
from werkzeug.security import generate_password_hash


HOST = "127.0.0.1"
PORT = "5000"
URL = f"http://{HOST}:{PORT}"
test_users = {
    "client": {
        "email": "customer@test.net",
        "password": "blent",
        "name": "Customer",
        "role": "client",
        "order_ids":[]
    },
    "admin": {
        "email": "admin@test.net",
        "password": "admin",
        "name": "Admin",
        "role": "admin",
        "order_ids":[]
    }
}


def check_connection_to_server():
    """
    Check if Flask app is running before executing tests.
    """
    try: 
        requests.get(URL)
    except requests.exceptions.ConnectionError:
        raise Exception("ERROR: Flask app not running.")


def authenticate(email, password, goal):
    """
    Authenticate with the server and return token.
    """
    
    # Get Response
    response = requests.post(
        f"http://{HOST}:{PORT}/authenticate",
        json={"email": email, "password": password},
    )    
    response_not_OK = (not check_response(response, goal, [200, 201]))
    if response_not_OK:
        return None
    
    # Get Token
    token = json.loads(response.content)["token"]
    return token
    

# Get user instance from DB with his email
get_user = lambda email: Utilisateur.query.filter_by(email=email).first()

    
def get_user_id(email):
    """
    Retrieve user's ID from DB with his email.
    """
    with app.app_context():
        user = get_user(email)
        return user.id

def create_test_users():
    """
    Create test customer & admin users in DB.
    """
    with app.app_context():
        for user in test_users.values():
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
    
def get_expected_status(user_role, current_order_id, last_own_order_id) :
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

        for user in test_users.values():
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
                
                # Delete test_users
                db.session.delete(user_instance)
                logging.info(f"Deleted user {user['email']}.")

                db.session.commit()  


def check_response(resp, test_goal, expected_statuses):
    """
    Validates the HTTP response and prints formatted output.
    """
    goal = f"API '{test_goal}'"
    logging.info(f"{goal}")
    logging.info(f"URL {resp.url}")
    response_code = resp.status_code
    response_OK = response_code in expected_statuses
    if response_OK:
        logging.info("Response OK")
    else:
        #logging.info(f"{goal} failed with status code {response_code}")
        #logging.info(f"json.loads(resp.content)={resp.content.decode('utf-8')}")
        logging.info(f"{resp.json().get('error')}")
    return response_OK


def print_response(resp, test_goal, indented=False):
    logging.info(f"Response :")
    #if indented:
    #    logging.info(f"Response : {resp.content.decode('utf-8')}") # gets a string
    #else:
    #    logging.info(f"Response : {json.loads(resp.content)}") # gets a list of dicts
    logging.info(f"Response : {resp.content.decode('utf-8')}") # gets a string

def check_resp_status(resp, test_goal, expected_statuses):
    """
    Check response & status
    """    

    # Check Response
    status_OK = (check_response(resp, test_goal, expected_statuses))
    
    # Pytest Assertion
    assert status_OK, f"{test_goal}: got status code {resp.status_code} but expected {expected_statuses}"

    # Check Status
    if not status_OK:
        return None

    # Print Response
    print_response(resp, test_goal, indented=True)

    # Return Response as [{...}]
    return json.loads(resp.content)
