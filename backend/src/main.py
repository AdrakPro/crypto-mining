from fastapi import FastAPI, Depends, Request
import random
from sqlalchemy.orm import Session
from . import database, client_service

app = FastAPI()

# Create database tables on startup
@app.on_event("startup")
def startup_event():
    database.create_tables()

# Dependency to get database session
def get_db():
    return next(database.get_db())

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

# ping od klienta
@app.post("/ping")
def ping(request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host
    # Zapisz lub zaktualizuj klienta w bazie danych
    client_service.update_client_ping(db, client_ip)
    return {"message": "Client is online"}

# Sprawdzenie rozwiązania
@app.post("/result")
def check_result(result: dict, request: Request, db: Session = Depends(get_db)):
    global current_task
    client_ip = request.client.host
    
    if not current_task:
        return {"status": "No active task"}
    
    client_sum = result.get("sum") # Sprawdzenie Poprawności
    expected_sum = current_task["expected_sum"]
    is_correct = client_sum == expected_sum
    
    # Aktualizacja statystyk klienta w bazie danych
    client_service.update_client_task_completion(db, client_ip, is_correct)

    if is_correct: # Odpowiedź
        response = {"status": "Correct!"}
    else:
        response = {"status": "Incorrect!", "expected": expected_sum}

    current_task = {} # Wysłanie
    return response

# Pobierz wszystkich klientów
@app.get("/clients")
def get_clients(db: Session = Depends(get_db)):
    clients = db.query(database.Client).all()
    return clients

# Pobierz konkretnego klienta po adresie IP
@app.get("/clients/{ip_address}")
def get_client(ip_address: str, db: Session = Depends(get_db)):
    client = client_service.get_client_by_ip(db, ip_address)
    if client:
        return client
    return {"error": "Client not found"}
