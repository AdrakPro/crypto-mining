import requests
import time

BASE_URL = "http://127.0.0.1:8080"

while True:
    try:
        response = requests.post(f"{BASE_URL}/ping")  # Wysyłamy POST
        print("Server response:", response.json())

        task_response = requests.get(f"{BASE_URL}/task") #Pobranie Zadania
        task = task_response.json()

        a, b = task["a"], task["b"] #Rozwiązanie Zadania przez klienta
        print(f"Received task: {a} + {b}")
        result = {"sum": a + b}

        response = requests.post(f"{BASE_URL}/result", json=result) #Wysłanie Odpowiedzi
        server_reply = response.json()
        print("Server response:", server_reply)



    except requests.exceptions.Timeout:
        print("Server timeout, retrying...")
    except requests.exceptions.RequestException as e:
        print("Server unreachable:", e)
    time.sleep(5)