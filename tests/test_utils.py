import requests
import json

HOST = "127.0.0.1"
PORT = "5000"

def check_response(resp, test_goal):
    """
    Validates the HTTP response and prints formatted output.
    """
    SUCCESS_CODES = [200, 201]
    goal = f"API '{test_goal}'"
    print (f"{goal} - URL {resp.url}")
    response_code = resp.status_code
    response_OK = (response_code in SUCCESS_CODES)
    if response_OK: 
        print(f"{goal} - Response OK")
    else:
        print(f"{goal} failed with status code {response_code}")
        print(f"{goal} failed : {resp.json().get('error')}")
    return response_OK

def authenticate(email, password):
    """
    Authenticates with the server and returns the token.
    """
    resp = requests.post(
        f"http://{HOST}:{PORT}/authenticate", 
        json={      "email": email,
                    "password": password})
    if check_response(resp, "Authenticate"):
        token = json.loads(resp.content)["token"]
        return token
    return None

def print_response(resp, test_goal, indented=False):
    print(f"API '{test_goal}' - Response :")
    if indented:
        print(resp.content.decode('utf-8'))
    else:
        print(json.loads(resp.content))

