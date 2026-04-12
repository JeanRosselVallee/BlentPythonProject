import requests
from tests_utils import check_response, authenticate, print_response, HOST, PORT

goal = "Search Order Items by Order ID"

order_id = 4
email = "clementthibaut@example.net"

# Authenticate
my_token = authenticate(email, "blent")

if my_token:
    # Send request
    resp = requests.get(
        f"http://{HOST}:{PORT}/api/commandes/{order_id}/lignes",
        headers={"authorization": my_token},
    )
    if check_response(resp, goal):
        print_response(resp, goal, indented=True)
