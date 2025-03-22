import requests
import time

BASE_URL = "http://127.0.0.1:8080"

while True:
    try:
        response = requests.post(f"{BASE_URL}/ping")
        print("Server response:", response.json())
    except requests.exceptions.RequestException as e:
        print("Server unreachable:", e)
    time.sleep(5)