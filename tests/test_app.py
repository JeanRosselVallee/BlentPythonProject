# Syntax
# Run all tests on terminal: 
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
from tests_utils import create_users, delete_test_data, check_response, print_response, \
                        authenticate, check_connection_to_server, get_user_id, \
                        URL, users
import logging

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
        create_users() 
        
        # RUN TESTS
        logging.info("\n[Wrapper] Step 2 : Run tests...")
        yield  # Tests are executed here

    finally:        
        # TEARDOWN TESTS
        logging.info("\n[Wrapper] Step 3 : Cleanup DB...")
        delete_test_data()

@pytest.mark.parametrize("user", 
                         [users["client"], users["admin"]], 
                         ids=["CLIENT", "ADMIN"])

class Test_app:
    # Test Authenticate
    def test_authenticate(self, user):
        goal = f"Authenticate User {user['email']}"

        user["token"] = authenticate(user["email"], user["password"], goal)
        assert user["token"], f"{goal} failed for {user['email']}."

    # Test Create an Order
    def test_create_order(self, user):
        goal = f"Create Order for {user['email']}"
        resp = requests.post(
            f"{URL}/api/commandes",
            headers={"authorization": user["token"]},
            json={
                "utilisateur_id": get_user_id(user["email"]),
                "adresse_livraison": "123, rue de la Paix, Paris",
            },
        )
        if check_response(resp, goal):
            print_response(resp, goal, indented=True)
        assert resp.status_code in [200, 201], f"{goal} failed for {user['email']}."

    # Test Get Orders    
    def test_get_orders(self, user):
        goal = f"Get Orders for {user['email']}"
        resp = requests.get(
            f"{URL}/api/commandes",
            headers={"authorization": user["token"]},
            json={"email": user["email"]},
        )
        if check_response(resp, goal):
            print_response(resp, goal, indented=True)

        assert resp.status_code in [200, 201], f"{goal} failed for {user['email']}."


    # Test Get Order by ID
    def test_get_order_by_id(self, user):
        goal = f"Get Order by ID for {user['email']}"
        order_id = 2
        resp = requests.get(
            f"{URL}/api/commandes/{order_id}",
            headers={"authorization": user["token"]},
        )
        if check_response(resp, goal):
            print_response(resp, goal, indented=True)

        assert resp.status_code in [200, 201], f"{goal} failed for {user['email']}."


    # Test Get Order Items
    def test_get_order_items(self, user):
        goal = f"Get Order by ID for {user['email']}"
        order_id = 4
        resp = requests.get(
            f"{URL}/api/commandes/{order_id}/lignes",
            headers={"authorization": user["token"]},
        )
        if check_response(resp, goal):
            print_response(resp, goal, indented=True)

        assert resp.status_code in [200, 201], f"{goal} failed for {user['email']}."


    # Test Update Order
    def test_update_order(self, user):
        goal = f"Update Order for {user['email']}"
        order_id = 4
        resp = requests.patch(
            f"{URL}/api/commandes/{order_id}",
            headers={"authorization": user["token"]},
            params={"email": user["email"]},
            json={
                "status": "validée"
                # "status": "en attente"
            },
        )
        if check_response(resp, goal):
            print_response(resp, goal, indented=True)

        if user["role"] == "admin":
            expected_statuses = [200, 201]
        else:
            expected_statuses = [403]  # Forbidden for non-admin users

        assert resp.status_code in expected_statuses, f"{goal} failed for {user['email']}."

    # Test Get All Products
    def test_get_products(self, user):
        goal = f"Get All Products for {user['email']}"
        resp = requests.get(
            f"{URL}/api/produits", headers={"authorization": user["token"]}
        )
        if check_response(resp, goal):
            print_response(resp, goal)  # , indented=True)

        assert resp.status_code in [200, 201], f"{goal} failed for {user['email']}."


    # Test Get Product by ID
        def test_get_product_by_id(self, user):
            goal = f"Search Product by ID for {user['email']}"
            product_id = 2
            resp = requests.get(
                f"{URL}/api/produits/{product_id}",
                headers={"authorization": user["token"]},
            )
            if check_response(resp, goal):
                print_response(resp, goal, indented=True)

            assert resp.status_code in [200, 201], f"{goal} failed for {user['email']}."