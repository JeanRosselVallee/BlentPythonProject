import requests
from tests_utils import check_response, authenticate, print_response, HOST, PORT

goal = "Update Order"

order_id = 11
# email = "clementthibaut@example.net"   # client can't update status
email = "olivier96@example.com"  # admin can update status

# Authenticate
my_token = authenticate(email, "blent")

if my_token:
    # Send request
    resp = requests.patch(
        f"http://{HOST}:{PORT}/api/commandes/{order_id}",
        headers={"authorization": my_token},
        params={"email": email},
        json={
            "status": "validée"
            # "status": "en attente"
        },
    )
    if check_response(resp, goal):
        print_response(resp, goal, indented=True)
