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
import tests.tests_utils as tu  # Custom Library


@pytest.fixture(scope="module", autouse=True)
def testing_wrapper():
    """
    Writes test data in DB, executes all tests & cleans up DB 
    - 'scope="module"' : runs only once (per module not per test)
    - 'autouse=True' : runs automatically (no call needed)
    """

    # Check app is running 
    tu.check_connection_to_server()

    try: 
        # SETUP TESTS
        logging.info("\n[Wrapper] Step 1 : Create test users in DB...")
        tu.create_test_users() 
        
        # RUN TESTS
        logging.info("\n[Wrapper] Step 2 : Run tests...")
        yield  # Tests are executed here

    finally:        
        # TEARDOWN TESTS
        logging.info("\n[Wrapper] Step 3 : Cleanup DB...")
        tu.delete_test_data()

@pytest.mark.parametrize("user", 
                         [tu.test_users["client"], tu.test_users["admin"]], 
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
        """
        Authenticate with the server & Get Token.
        """

        # Set Goals
        email = user['email']
        goal_1 = f"Authenticate user {email}"
        goal_2 = f"Get Token for user {email}"

        # Get Response
        response = requests.post(
            f"{tu.URL}/authenticate",
            json={"email": email, "password": user["password"]},
            # json={"email": email, "password": "blent"}, 
        )    

        # Check Response
        tu.assert_status(response, goal_1, tu.SUCCESS_CODES)

        # Initialize User's Token        
        data_in_response = json.loads(response.content)
        data_is_a_dict = (isinstance(data_in_response, dict))
        if data_is_a_dict:
            user["token"] = data_in_response["token"]

        # Pytest Assertion
        assert user["token"], f"{goal_2} failed."


    # Test Get Product by ID
    def test_get_product_by_id(self, user):

        # Set Goal
        goal = f"Search Product by ID for {user['email']}"

        # Get Response
        product_id = 2
        response = requests.get(
            f"{tu.URL}/api/produits/{product_id}",
            headers={"authorization": user["token"]},
        )

        # Check Response
        tu.assert_status(response, goal, tu.SUCCESS_CODES)


    # Test Get All Products
    def test_get_products(self, user):

        # Set Goal    
        goal = f"Get All Products for {user['email']}"

        # Get Response
        response = requests.get(
            f"{tu.URL}/api/produits", headers={"authorization": user["token"]}
        )

        # Check Response
        tu.assert_status(response, goal, tu.SUCCESS_CODES)


    # Test Create an Order
    def test_create_order(self, user):

        # Set Goal
        goal = f"Create Order for {user['email']}"

        # Get Response
        response = requests.post(
            f"{tu.URL}/api/commandes",
            headers={"authorization": user["token"]},
            json={
                "utilisateur_id": user["id"],
                "adresse_livraison": "123, rue de la Paix, Paris"
            }
        )

        # Check Response       
        tu.assert_status(response, goal, tu.SUCCESS_CODES)

        # Get Created Order from Response 
        orders_list = json.loads(response.content) # contains a list with a single order
        if orders_list:
            order = orders_list[0]

            # Store Order Id for other tests 
            user["order_ids"].append(order["id"])


    # Test Get Order by ID
    def test_get_order_by_id(self, user):

        # Test on 2 different owners' orders
        own_order_id = tu.get_last_user_order(user["email"])
        alien_order_id = 2
        for order_id in [own_order_id, alien_order_id]:

            # Seet Goal
            goal = f"Get Order with id {order_id} for {user['email']}"

            # Get expected statuses based on user's role & order's ownership
            expected_statuses = tu.get_expected_status(user["role"], order_id, own_order_id)

            # Get Response to Request
            response = requests.get(
                f"{tu.URL}/api/commandes/{order_id}",
                headers={"authorization": user["token"]}
            )
            
            # Check Response
            tu.assert_status(response, goal, expected_statuses)


    # Test Get Orders    
    def test_get_orders(self, user):

        # Set Goal
        goal = f"Get Orders for {user['email']}"

        # Get Response
        response = requests.get(
            f"{tu.URL}/api/commandes",
            headers={"authorization": user["token"]}
        )

        # Check Response
        tu.assert_status(response, goal, tu.SUCCESS_CODES)


    # Test Add Order Item
    def test_add_order_item(self, user):

        # Set Goal
        goal = f"Add Order Item for {user['email']}"

        # Get Order Id
        order_id = user["order_ids"][0]

        # Get Response
        response = requests.post(
            f"{tu.URL}/api/commandes/{order_id}/lignes",
            headers={"authorization": user["token"]},
            json={
                "produit_id": 1,
                "quantite": 2,
            }
        )

        # Check Response
        tu.assert_status(response, goal, tu.SUCCESS_CODES)


    # Test Get Order Items
    def test_get_order_items(self, user):

        # Get Client & Admin Order Id 
        client_order_id = tu.test_users["client"]["order_ids"][0]
        admin_order_id = tu.test_users["admin"]["order_ids"][0]

        # Get own Order Id
        own_order_id = user["order_ids"][0]
        
        # Test on 2 different orders
        for order_id in [client_order_id, admin_order_id]:

            # Set Goal
            goal = f"Get Items of Order id {order_id} for {user['email']}"

            # Get expected statuses based on user's role & order's ownership
            expected_statuses = tu.get_expected_status(user["role"], order_id, own_order_id)

            # Get Response to Request
            response = requests.get(
                f"{tu.URL}/api/commandes/{order_id}/lignes",
                headers={"authorization": user["token"]},
            )
        
            # Check Response
            tu.assert_status(response, goal, expected_statuses)


    # Test Update Order
    def test_update_order(self, user):

        # Get User's Order Id
        order_id = user["order_ids"][0]

        # Set Goal
        goal = f"Update Order with id {order_id} for {user['email']}"

        # Get Response to Request
        response = requests.patch(
            f"{tu.URL}/api/commandes/{order_id}",
            headers={"authorization": user["token"]},
            params={"email": user["email"]},
            json={
                "status": "validée"
            }
        )

        # Get expected statuses based on user's role
        if user["role"] == "admin":
            # Admin can update orders
            expected_statuses = tu.SUCCESS_CODES
        else:  
            # Clients can't update orders 
            expected_statuses = [403]

        # Check Response
        tu.assert_status(response, goal, expected_statuses) 

