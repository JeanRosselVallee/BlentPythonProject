import requests
from test_utils import check_response, authenticate, print_response, HOST, PORT

goal = "Get All Orders"

email = "clementthibaut@example.net"   # client gets own orders
#email = "olivier96@example.com"        # admin gets all orders

# Authenticate
my_token = authenticate(email, "blent")

if my_token:
    # Send request
    resp = requests.get(
        f"http://{HOST}:{PORT}/api/commandes", 
        headers={"authorization": my_token},
        json={"email": email}
    )
    if check_response(resp, goal):
        print_response(resp, goal, indented=True)