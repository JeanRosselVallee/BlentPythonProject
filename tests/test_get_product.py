import requests
from test_utils import check_response, authenticate, print_response, HOST, PORT

goal = "Search Product by ID"

product_id = 2

# Authenticate
my_token = authenticate("olivier96@example.com", "blent")

if my_token:
    # Send request
    resp = requests.get(
        f"http://{HOST}:{PORT}/api/produits/{product_id}", 
        headers={"authorization": my_token}
    )
    if check_response(resp, goal):
        print_response(resp, goal, indented=True)