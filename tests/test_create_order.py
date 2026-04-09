import requests
from test_utils import check_response, authenticate, print_response, HOST, PORT

goal = "Create Order"

email = "clementthibaut@example.net"

# Authenticate
my_token = authenticate(email, "blent")

if my_token:
    # Send request
    resp = requests.post(
        f"http://{HOST}:{PORT}/api/commandes", 
        headers={"authorization": my_token},
        json={
            "utilisateur_id": 1,
            "adresse_livraison": "123, rue de la Paix, Paris",
        }
    )
    if check_response(resp, goal):
        print_response(resp, goal, indented=True)