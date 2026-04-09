import requests
from test_utils import check_response, authenticate, print_response, HOST, PORT

goal = "Get All Products"

email = "clementthibaut@example.net"

# Authenticate
my_token = authenticate(email, "blent")

if my_token:
    # Send request
    resp = requests.get(
        f"http://{HOST}:{PORT}/api/produits",
        headers={"authorization": my_token}
    )
    if check_response(resp, goal):
        print_response(resp, goal)#, indented=True)