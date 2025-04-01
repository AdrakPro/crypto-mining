import requests
import time
import sys
from dotenv import load_dotenv
import os
from security import get_password_hash

load_dotenv()
# jeden klucz prywatny na serwerze, wiele dla użytkowników, kazdy klient i serwer jeden klucz prywatny i jeden publiczny, hashowanie json result, haslo na klucz prywatny, klucz generowac w locie? serwer tworzy klucz podczas startu i zapomina go, https bez cerytfikatu?

class APIClient:
    def __init__(self):
        self.base_url = os.getenv("SERVER_BASE_URL")
        self.token = None
        self.username = os.getenv("CLIENT_USERNAME")
        self.password = os.getenv("CLIENT_PASSWORD")


    def authenticate(self):
        try:
            response = requests.post(
                f"{self.base_url}/login",
                json={"username": self.username, "password": self.password},
            )
            response.raise_for_status()
            self.token = response.json()["access_token"]
            return True
        except requests.exceptions.RequestException as e:
            print(f"Authentication failed: {e}")
            return False

    def make_request(self, method, endpoint, **kwargs):
        if not self.token and endpoint != "/login":
            if not self.authenticate():
                return None

        headers = kwargs.get("headers", {})
        if self.token:
            headers.update({"Authorization": f"Bearer {self.token}"})
        kwargs["headers"] = headers

        try:
            response = requests.request(method, f"{self.base_url}{endpoint}", **kwargs)

            if response.status_code == 401:  # Token expired
                if self.authenticate():
                    return self.make_request(method, endpoint, **kwargs)
                return None

            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None


def main():
    client = APIClient()

    while True:
        try:
            # Ping
            ping_res = client.make_request("POST", "/ping")
            if ping_res:
                print("Server response:", ping_res.json())

            # Get task
            task_res = client.make_request("GET", "/task")
            if task_res:
                task = task_res.json()
                a, b = task["a"], task["b"]
                print(f"Received task: {a} + {b}")

                # Calculate and submit result
                result = {"sum": a + b}
                result_res = client.make_request("POST", "/result", json=result)
                if result_res:
                    print("Server response:", result_res.json())

        except KeyboardInterrupt:
            print("\nClient shutting down...")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(5)


if __name__ == "__main__":
    main()
