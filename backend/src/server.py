from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from threading import Lock
from security import verify_password, create_access_token, decode_token, secure_compare, verify_signature
import os
from dotenv import load_dotenv
import secrets
from collections import defaultdict
import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64
import json
from fastapi.middleware.cors import CORSMiddleware
import ast
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGINS")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
user_public_keys = {}
failed_attempts = defaultdict(list)
calculations = {}
tasks = {}
lock = Lock()
executor = ThreadPoolExecutor(max_workers=4)

# Simple in-memory user database
user_db = {
    os.getenv("ADMIN_USERNAME"): {
        "password_hash": os.getenv("ADMIN_PASSWORD_HASH"),
        "public_key": None
    }
}

ALLOWED_NODE_TYPES = {
    ast.Module,
    ast.Expr,
    ast.BinOp,
    ast.Add,
    ast.Num,
    ast.Constant,
    ast.Load,
}

LOCKOUT_WINDOW = int(os.getenv("LOCKOUT_MINUTES", 5)) * 60
FAILED_ATTEMPT_LIMIT = int(os.getenv("FAILED_ATTEMPT_LIMIT", 5))

DEBUG_MODE = os.getenv("DEBUG_MODE", "0") == "1"

# Security models
class UserCredentials(BaseModel):
    username: str
    password: str
    public_key: str
    signature: str  # base64 podpis cyfrowy (username+public_key)

class Token(BaseModel):
    access_token: str
    token_type: str

class Task(BaseModel):
    a: int
    b: int

class Result(BaseModel):
    sum: int

class Calculation(BaseModel):
    calculation: str

def check_brute_force(request: Request):
    client_ip = request.client.host
    now = time.time()
    recent_attempts = [t for t in failed_attempts[client_ip] if now - t < LOCKOUT_WINDOW]
    failed_attempts[client_ip] = recent_attempts
    if len(recent_attempts) >= FAILED_ATTEMPT_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts",
        )

def encrypt_response(data: dict, username: str) -> dict:
    public_key_pem = user_public_keys.get(username)
    if not public_key_pem:
        raise HTTPException(status_code=400, detail="Public key missing")
    try:
        if "BEGIN PUBLIC KEY" not in public_key_pem:
            public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{public_key_pem}\n-----END PUBLIC KEY-----"
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode(), backend=default_backend()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid public key for username {username}: {e}")
    payload = json.dumps(data).encode()
    ciphertext = public_key.encrypt(
        payload,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    encrypted = base64.b64encode(ciphertext).decode()
    if DEBUG_MODE:
        print(f"[DEBUG] Odszyfrowana wiadomość dla {username}: {data}")
        print(f"[DEBUG] Zaszyfrowana wiadomość dla {username}: {encrypted}")
    return {"encrypted": encrypted}

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        if not payload:
            raise credentials_exception
        if payload.get("iss") != "trusted-auth-server":
            raise HTTPException(status_code=403, detail="Untrusted token issuer")
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
        return username
    except Exception:
        raise credentials_exception

@app.post("/login")
async def login(request: Request, credentials: UserCredentials):
    check_brute_force(request)
    # Weryfikacja podpisu cyfrowego
    message = (credentials.username + credentials.public_key).encode()
    if not verify_signature(credentials.public_key, message, credentials.signature):
        failed_attempts[request.client.host].append(time.time())
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Weryfikacja hasła
    user_entry = user_db.get(credentials.username)
    if not user_entry or not verify_password(credentials.password, user_entry["password_hash"]):
        failed_attempts[request.client.host].append(time.time())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    # Aktualizacja klucza publicznego
    user_public_keys[credentials.username] = credentials.public_key
    user_db[credentials.username]["public_key"] = credentials.public_key

    # Tworzenie tokenu
    access_token = create_access_token(data={"sub": credentials.username})

    # Odpowiedź zaszyfrowana
    return encrypt_response({"access_token": access_token, "token_type": "bearer"}, credentials.username)

@app.get("/task")
async def get_task(current_user: str = Depends(get_current_user)):
    with lock:
        if current_user not in tasks:
            a = secrets.randbelow(100) + 1
            b = secrets.randbelow(100) + 1
            tasks[current_user] = {"a": a, "b": b, "expected_sum": a + b}
        return encrypt_response(
            {"a": tasks[current_user]["a"], "b": tasks[current_user]["b"]}, current_user
        )

@app.post("/result")
async def submit_result(result: Result, current_user: str = Depends(get_current_user)):
    with lock:
        if current_user not in tasks:
            return encrypt_response({"status": "No active task"}, current_user)
        expected = tasks[current_user]["expected_sum"]
        response_data = (
            {"status": "Correct"}
            if result.sum == expected
            else {"status": "Incorrect", "expected": expected, "received": result.sum}
        )
        del tasks[current_user]
        return encrypt_response(response_data, current_user)

def is_safe_ast(tree):
    class NodeVisitor(ast.NodeVisitor):
        def __init__(self):
            self.safe = True
        def generic_visit(self, node):
            if type(node) not in ALLOWED_NODE_TYPES:
                self.safe = False
            super().generic_visit(node)
    visitor = NodeVisitor()
    visitor.visit(tree)
    return visitor.safe

def validate_expression(expression):
    expression = expression.strip()
    if not re.match(r"^\d+\s*\+\s*\d+$", expression):
        raise ValueError("Invalid format. Only simple addition (num + num) is allowed.")
    try:
        tree = ast.parse(expression)
        if not is_safe_ast(tree):
            raise ValueError("Expression contains unsafe operations")
    except SyntaxError:
        raise ValueError("Invalid syntax in expression")
    if any(
        keyword in expression
        for keyword in [
            "import", "eval", "exec", "compile", "open", "file", "globals", "locals", "__", "os", "sys", "subprocess",
        ]
    ):
        raise ValueError("Expression contains forbidden keywords")
    return True

@app.post("/calculation")
async def submit_calculation(
    calculation: Calculation, current_user: str = Depends(get_current_user)
):
    with lock:
        try:
            if DEBUG_MODE:
                print(f"[DEBUG] Otrzymano żądanie obliczenia od {current_user}: {calculation.calculation}")
            expression = calculation.calculation
            try:
                validate_expression(expression)
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid calculation: {str(e)}"
                )
            restricted_globals = {
                "__builtins__": {
                    "int": int,
                    "float": float,
                }
            }
            restricted_locals = {}
            try:
                future = executor.submit(
                    exec,
                    f"result = {expression}",
                    restricted_globals,
                    restricted_locals,
                )
                future.result(timeout=2)
            except TimeoutError:
                raise HTTPException(status_code=400, detail="Calculation timeout")
            except Exception as e:
                raise HTTPException(status_code=400, detail="Calculation error")
            result = restricted_locals.get("result")
            if not isinstance(result, (int, float)):
                raise HTTPException(status_code=400, detail="Invalid result type")
            if DEBUG_MODE:
                print(f"[DEBUG] Wynik obliczenia: {result}")
            return encrypt_response({"result": result}, current_user)
        except Exception as e:
            if DEBUG_MODE:
                print(f"[DEBUG] Błąd przetwarzania kalkulacji: {str(e)}")
            raise HTTPException(
                status_code=500, detail="An error occurred processing the calculation"
            )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVER_PORT", 8080)),
    )
