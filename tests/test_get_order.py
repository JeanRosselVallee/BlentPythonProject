import requests
from test_utils import check_response, authenticate, print_response, HOST, PORT

goal = "Get Order by ID"

email = "clementthibaut@example.net"
order_id = 2

# Authenticate
my_token = authenticate(email, "blent")

if my_token:
    # Send request
    resp = requests.get(
        f"http://{HOST}:{PORT}/api/commandes/{order_id}", 
        headers={"authorization": my_token}
    )
    if check_response(resp, goal):
        print_response(resp, goal, indented=True)