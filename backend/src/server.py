from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from pydantic import BaseModel
from typing import Optional
from threading import Lock
from security import verify_password, create_access_token, decode_token, secure_compare
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
import re

load_dotenv()

app = FastAPI()

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
user_public_keys = {}
failed_attempts = defaultdict(list)
tasks = {}
calculations = {}
lock = Lock()

# Security models
class UserCredentials(BaseModel):
    username: str
    password: str
    public_key: str

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

# Security functions
def check_brute_force(request: Request):
    client_ip = request.client.host
    now = time.time()

    # Clean old attempts
    recent_attempts = [
        t for t in failed_attempts[client_ip]
        if now - t < int(os.getenv("LOCKOUT_MINUTES", 5)) * 60
    ]
    failed_attempts[client_ip] = recent_attempts

    if len(recent_attempts) >= int(os.getenv("FAILED_ATTEMPT_LIMIT", 5)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked for {os.getenv('LOCKOUT_MINUTES', 5)} minutes"
        )

def encrypt_response(data: dict, username: str) -> dict:
    public_key_pem = user_public_keys.get(username)
    if not public_key_pem:
        raise HTTPException(status_code=400, detail="Public key missing")

    try:
        # Add proper PEM headers if missing
        if "BEGIN PUBLIC KEY" not in public_key_pem:
            public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{public_key_pem}\n-----END PUBLIC KEY-----"

        public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid public key: {str(e)}")

    payload = json.dumps(data).encode()
    ciphertext = public_key.encrypt(
        payload,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return {"encrypted": base64.b64encode(ciphertext).decode()}

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        if not payload:
            raise credentials_exception
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

# Endpoints
@app.post("/login")
async def login(request: Request, credentials: UserCredentials):
    check_brute_force(request)

    # Verify credentials
    if not (secure_compare(credentials.username, os.getenv("ADMIN_USERNAME")) and
            verify_password(credentials.password, os.getenv("ADMIN_PASSWORD"))):
        failed_attempts[request.client.host].append(time.time())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Store public key with proper formatting
    try:
        user_public_keys[credentials.username] = credentials.public_key
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid public key format: {str(e)}")

    # Create token
    access_token = create_access_token(data={"sub": credentials.username})

    # Return encrypted response
    return encrypt_response({
        "access_token": access_token,
        "token_type": "bearer"
    }, credentials.username)

@app.get("/task")
async def get_task(current_user: str = Depends(get_current_user)):
    with lock:
        if current_user not in tasks:
            a = secrets.randbelow(100) + 1
            b = secrets.randbelow(100) + 1
            tasks[current_user] = {
                "a": a,
                "b": b,
                "expected_sum": a + b
            }
        return encrypt_response({
            "a": tasks[current_user]["a"],
            "b": tasks[current_user]["b"]
        }, current_user)

@app.post("/result")
async def submit_result(result: Result, current_user: str = Depends(get_current_user)):
    with lock:
        if current_user not in tasks:
            return encrypt_response({"status": "No active task"}, current_user)

        expected = tasks[current_user]["expected_sum"]
        response_data = {"status": "Correct"} if result.sum == expected else {
            "status": "Incorrect",
            "expected": expected,
            "received": result.sum
        }
        del tasks[current_user]
        return encrypt_response(response_data, current_user)

#check if string is valid
def is_valid_sum(expression: str) -> bool:
    pattern = r'^\s*\d+\s*\+\s*\d+\s*$'
    return re.match(pattern, expression) is not None

#performing calculation by exec and sending data
@app.post("/calculation")
async def submit_calculation(calculation:  Calculation,current_user: str = Depends(get_current_user)):
    with lock:
        print(f"Użytkownik {current_user} wysłał kalkulację: {calculation.calculation}")
        if not is_valid_sum(calculation.calculation):
            raise HTTPException(
            status_code=400,
            detail="Invalid calculation format. Expected format: number + number"
            )
        try:
            allowed_globals = {"__builtins__": None, "sum": sum}
            result = exec(f"result = {calculation.calculation}", allowed_globals)
            return encrypt_response({"Calculation Result": allowed_globals["result"]},current_user)

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error in calculation: {str(e)}"
            )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVER_PORT", 8080)),
    )
