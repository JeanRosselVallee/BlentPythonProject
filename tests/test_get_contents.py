import requests
import json

print(requests.get("http://127.0.0.1:5000/cart").content.decode())

resp = requests.post("http://127.0.0.1:5000/authenticate", json={"password": "blent"})
print("test-authenticate", resp.status_code, json.loads(resp.content))
my_token = json.loads(resp.content)["token"]

resp = requests.get("http://127.0.0.1:5000/authorize", 
                     headers={"authorization": my_token})
print("test-authorize:", resp.status_code, json.loads(resp.content))