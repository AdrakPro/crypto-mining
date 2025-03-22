from fastapi import FastAPI
import random

app = FastAPI()

current_task = {} # Do przechowywania zadań klienta

# Start (musisz odpalic w tym samym folderze co main): uvicorn main:app --host 127.0.0.1 --port 8080 --reload
@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

# Wysłanie zadania obliczeniowego
@app.get("/task")
def task():
    global current_task
    if not current_task:
        a = random.randint(1,100)
        b = random.randint(1,100)
        current_task = {"a": a, "b": b, "expected_sum": a + b}
    return {"a": current_task["a"], "b": current_task["b"]}

#ping od klienta
@app.post("/ping")
def ping():
    return {"message": "Client is online"}

#Sprawdzenie rozwiązania
@app.post("/result")
def check_result(result: dict):
    global current_task
    if not current_task:
        return {"status": "No active task"}
    
    client_sum = result.get("sum") #Spradzenie Poprawności
    expected_sum = current_task["expected_sum"]

    if client_sum == expected_sum: #Odpowiedź
        response = {"status": "Correct!"}
    else:
        response = {"status": "Incorrect!", "expected": expected_sum}

    current_task = {} #Wysłanie
    return response



