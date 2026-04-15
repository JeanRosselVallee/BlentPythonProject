# Syntax
# Run all tests on terminal: 
#    python -m pytest -sv --tb=short <file_path>
# Run single test on terminal: 
#    python -m pytest -sv --tb=short <file_path>
# Options :
#    -m searches modules from root dir rather than library files
#    -s displays stdout & SQL queries
#    -v displays names of tested module & user
#    --tb=short : traceback, shows lines in error
#    -k runs only certain tests on certain users:
#    python ... -k "(authenticate or create_order) and CLIENT"
# Log outpout on ./pytest.log

# Goal : Test REST API responses for all routes

import pytest
import requests
import logging
import json
# import test_utils as tu
from tests_utils import create_test_users, delete_test_data, check_resp_status, \
                        authenticate, check_connection_to_server, get_user_id, get_last_user_order, get_expected_status, \
                        URL, test_users


@pytest.fixture(scope="module", autouse=True)
def testing_wrapper():
    """
    Writes test data in DB, executes all tests & cleans up DB 
    - 'scope="module"' : runs only once (per module not per test)
    - 'autouse=True' : runs automatically (no call needed)
    """

    # Check app is running 
    check_connection_to_server()

    try: 
        # SETUP TESTS
        logging.info("\n[Wrapper] Step 1 : Create test users in DB...")
        create_test_users() 
        
        # RUN TESTS
        logging.info("\n[Wrapper] Step 2 : Run tests...")
        yield  # Tests are executed here

    finally:        
        # TEARDOWN TESTS
        logging.info("\n[Wrapper] Step 3 : Cleanup DB...")
        delete_test_data()

@pytest.mark.parametrize("user", 
                         [test_users["client"], test_users["admin"]], 
                         ids=["CLIENT", "ADMIN"])
class Test_app:
    '''
    A class is required to apply a Pytest decorator to each method
    Decorator arguments
    - variable "user": shared with each class method
    - list of values: every method is run once per value in the list
    - ids: list of use cases for logging & pytest's target selection
    '''
    # Test Authenticate
    def test_authenticate(self, user):
        goal = f"Authenticate User {user['email']}"

        user["token"] = authenticate(user["email"], user["password"], goal)
        assert user["token"], f"{goal} failed."


    # Test Get All Products
    def test_get_products(self, user):
        goal = f"Get All Products for {user['email']}"
        resp = requests.get(
            f"{URL}/api/produits", headers={"authorization": user["token"]}
        )
        check_resp_status(resp, goal, [200, 201])


    # Test Get Product by ID
    def test_get_product_by_id(self, user):
        goal = f"Search Product by ID for {user['email']}"
        product_id = 2
        resp = requests.get(
            f"{URL}/api/produits/{product_id}",
            headers={"authorization": user["token"]},
        )
        check_resp_status(resp, goal, [200, 201])


    # Test Create an Order
    def test_create_order(self, user):
        goal = f"Create Order for {user['email']}"
        resp = requests.post(
            f"{URL}/api/commandes",
            headers={"authorization": user["token"]},
            json={
                "utilisateur_id": user["id"],
                "adresse_livraison": "123, rue de la Paix, Paris"
            }
        )

        # Store order id for other tests        
        orders_list = check_resp_status(resp, goal, [200, 201])
        order = orders_list[0]
        user["order_ids"].append(order["id"])


    # Test Add Order Item
    def test_add_order_item(self, user):
        goal = f"Add Order Item for {user['email']}"
        order_id = get_last_user_order(user["email"])
        resp = requests.post(
            f"{URL}/api/commandes/{order_id}/lignes",
            headers={"authorization": user["token"]},
            json={
                "produit_id": 1,
                "quantite": 2,
            }
        )
        check_resp_status(resp, goal, [200, 201])


    # Test Get Orders    
    def test_get_orders(self, user):
        goal = f"Get Orders for {user['email']}"
        resp = requests.get(
            f"{URL}/api/commandes",
            headers={"authorization": user["token"]},
            json={"email": user["email"]},
        )
        check_resp_status(resp, goal, [200, 201])


    # Test Get Order by ID
    def test_get_order_by_id(self, user):

        # Test on 2 different owners' orders
        own_order_id = get_last_user_order(user["email"])
        alien_order_id = 2
        for order_id in [own_order_id, alien_order_id]:
            goal = f"Get Order with id {order_id} for {user['email']}"

            # Get expected statuses based on user's role & order's ownership
            expected_statuses = get_expected_status(user["role"], order_id, own_order_id)

            # Send request
            resp = requests.get(
                f"{URL}/api/commandes/{order_id}",
                headers={"authorization": user["token"]},
                json={"email": user["email"]},
            )
            
            # Check response
            check_resp_status(resp, goal, expected_statuses)


    # Test Get Order Items
    def test_get_order_items(self, user):
        order_id = 4
        goal = f"Get Items of Order id {order_id} for {user['email']}"
        resp = requests.get(
            f"{URL}/api/commandes/{order_id}/lignes",
            headers={"authorization": user["token"]},
        )
        check_resp_status(resp, goal, [200, 201])


    # Test Update Order
    def test_update_order(self, user):
        order_id = 4
        goal = f"Update Order with id {order_id} for {user['email']}"
        resp = requests.patch(
            f"{URL}/api/commandes/{order_id}",
            headers={"authorization": user["token"]},
            params={"email": user["email"]},
            json={
                "status": "validée"
                # "status": "en attente"
            },
        )
        if user["role"] == "admin":
            expected_statuses = [200, 201]
        else:  # Forbidden for non-admin users
            expected_statuses = [403]
            check_resp_status(resp, goal, expected_statuses) 

