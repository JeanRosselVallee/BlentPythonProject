import requests
import json
import logging

from app import app, db
from app.database.model import Utilisateur, Produit, Commande, LigneCommande
from werkzeug.security import generate_password_hash


HOST = "127.0.0.1"
PORT = "5000"
URL = f"http://{HOST}:{PORT}"
users = {
    "admin": {
        "email": "admin@test.net",
        "password": "admin",
        "name": "Admin",
        "role": "admin"
    },
    "client": {
        "email": "customer@test.net",
        "password": "blent",
        "name": "Customer",
        "role": "client"
    }
}


def check_connection_to_server():
    """
    Checks if the Flask app is running before executing tests.
    """
    try: 
        requests.get(URL)
    except requests.exceptions.ConnectionError:
        raise Exception("ERROR: Flask app not running.")


def authenticate(email, password, goal):
    """
    Authenticates with the server and returns the token.
    """
    resp = requests.post(
        f"http://{HOST}:{PORT}/authenticate",
        json={"email": email, "password": password},
    )
    if check_response(resp, goal):
        token = json.loads(resp.content)["token"]
        return token
    return None


# Get user instance from DB with his email
get_user = lambda email: Utilisateur.query.filter_by(email=email).first()

    
def get_user_id(email):
    """
    Retrieves user's ID from DB with his email.
    """
    with app.app_context():
        user = get_user(email)
        return user.id

def create_users():
    """
    Create test customer & admin users in DB.
    """
    with app.app_context():
        for user in users.values():
            user_instance = get_user(user["email"])
            if user_instance:
                logging.info(f"User {user['email']} already exists in DB.")
                continue
            # Create SQLAlchemy instance
            user_instance = Utilisateur(
                email=user["email"],
                mot_de_passe=generate_password_hash(user["password"]),
                nom=user["name"],
                role=user["role"]
            )
            # Create user in DB
            db.session.add(user_instance)
            db.session.commit()
            logging.info(f"User {user['email']} was created in DB.")

            # Store user's id for requests' testing
            db.session.refresh(user_instance)
            user["id"] = user_instance.id


def delete_test_data():
    """
    Deletes test data in DB.
    """
    with app.app_context():
        # Clear test data in cascade

        for user in users.values():
            user_instance = get_user(user["email"])

            if user_instance:

                # Delete orders and order items
                nb_orders = Commande.query.filter_by(utilisateur_id=user_instance.id).delete()
                logging.info(f"{nb_orders} orders of user {user['email']} were deleted.")
                
                # Delete users
                db.session.delete(user_instance)
                db.session.commit()  
                logging.info(f"User {user['email']} was deleted from DB.")


def check_response(resp, test_goal):
    """
    Validates the HTTP response and prints formatted output.
    """
    SUCCESS_CODES = [200, 201]
    goal = f"API '{test_goal}'"
    logging.info(f"{goal} - URL {resp.url}")
    response_code = resp.status_code
    response_OK = response_code in SUCCESS_CODES
    if response_OK:
        logging.info(f"{goal} - Response OK")
    else:
        logging.info(f"{goal} failed with status code {response_code}")
        logging.info(f"{goal} failed : {resp.json().get('error')}")
    return response_OK


def print_response(resp, test_goal, indented=False):
    logging.info(f"API '{test_goal}' - Response :")
    if indented:
        logging.info(resp.content.decode("utf-8"))
    else:
        logging.info(json.loads(resp.content))


def check_resp_status(resp, test_goal, expected_statuses):
    """
    Check response & status
    """    
    if check_response(resp, test_goal):
        print_response(resp, test_goal, indented=True)

    assert resp.status_code in expected_statuses, f"{test_goal} failed for {user['email']}."