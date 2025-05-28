from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from threading import Lock
from security import (
    verify_password,
    create_access_token,
    decode_token,
    secure_compare,
    hash_password,
)
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

from sqlalchemy.orm import Session
from db import SessionLocal,  Base, engine
from models import User, ActiveSession
from schemas import UserCreate, UserLogin, UserCredentials, Token, Task, Result, Message
from jose import JWTError

Base.metadata.create_all(bind=engine)
load_dotenv()

app = FastAPI()

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_sessions = []

security = HTTPBearer()
user_public_keys = {}
failed_attempts = defaultdict(list)
tasks = {}
lock = Lock()


# Security functions
def check_brute_force(request: Request):
    client_ip = request.client.host
    now = time.time()

    # Clean old attempts
    recent_attempts = [
        t
        for t in failed_attempts[client_ip]
        if now - t < int(os.getenv("LOCKOUT_MINUTES", 5)) * 60
    ]
    failed_attempts[client_ip] = recent_attempts

    if len(recent_attempts) >= int(os.getenv("FAILED_ATTEMPT_LIMIT", 5)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked for {os.getenv('LOCKOUT_MINUTES', 5)} minutes",
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
            public_key_pem.encode(), backend=default_backend()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid public key: {str(e)}")

    payload = json.dumps(data).encode()
    ciphertext = public_key.encrypt(
        payload,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return {"encrypted": base64.b64encode(ciphertext).decode()}


# Authentication dependency
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
    if not (
        secure_compare(credentials.username, os.getenv("ADMIN_USERNAME"))
        and verify_password(credentials.password, os.getenv("ADMIN_PASSWORD"))
    ):
        failed_attempts[request.client.host].append(time.time())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Store public key with proper formatting
    try:
        user_public_keys[credentials.username] = credentials.public_key
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid public key format: {str(e)}"
        )

    # Create token
    access_token = create_access_token(data={"sub": credentials.username})

    # Return encrypted response
    return encrypt_response(
        {"access_token": access_token, "token_type": "bearer"}, credentials.username
    )


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


##########################################3
@app.post("/register")
def register(user: UserCreate):
    db: Session = SessionLocal()
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = User(
        username=user.username,
        hashed_password=hash_password(user.password),
        public_key=user.public_key,
        sent_tasks=0,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "User registered successfully"}


@app.post("/login-db")
def login_db(request: Request, credentials: UserLogin):
    check_brute_force(request)

    db: Session = SessionLocal()
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        failed_attempts[request.client.host].append(time.time())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Zapisz sesję w pamięci
    client_ip = request.client.host
    active_sessions.append(
        {"username": user.username, "ip": client_ip, "timestamp": time.time()}
    )

    # Pobierz klucz publiczny
    public_key_pem = user.public_key
    if not public_key_pem:
        raise HTTPException(status_code=400, detail="Public key missing in database")

    user_public_keys[credentials.username] = public_key_pem
    access_token = create_access_token(data={"sub": credentials.username})

    return encrypt_response(
        {"access_token": access_token, "token_type": "bearer"}, credentials.username
    )


@app.get("/sessions")
def list_sessions():
    return [
        {
            "username": s["username"],
            "ip": s["ip"],
            "timestamp": time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(s["timestamp"])
            ),
        }
        for s in active_sessions
    ]


# Pamięciowy inbox dla każdego użytkownika
user_inboxes = {}


@app.post("/send")
def send_message(message: Message):
    if message.to_user not in user_public_keys:
        raise HTTPException(status_code=404, detail="User not available")

    encrypted_msg = encrypt_response({"message": message.content}, message.to_user)

    # Zapisz wiadomość w "skrzynce odbiorczej"
    if message.to_user not in user_inboxes:
        user_inboxes[message.to_user] = []

    user_inboxes[message.to_user].append(encrypted_msg)

    return {"status": "message stored"}


@app.post("/get-message")
async def get_message(current_user: str = Depends(get_current_user)):
    if current_user not in user_inboxes or not user_inboxes[current_user]:
        return {"message": None}  # lub np. {"status": "no_message"}

    return user_inboxes[current_user].pop(0)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVER_PORT", 8080)),
    )

@app.post("/register")
def register(user: UserCreate):
    db: Session = SessionLocal()
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = User(
        username=user.username,
        hashed_password=hash_password(user.password),
        public_key=user.public_key
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "User registered successfully"}


@app.post("/login-db")
def login_db(request: Request, credentials: UserLogin):
    check_brute_force(request)

    db: Session = SessionLocal()
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        failed_attempts[request.client.host].append(time.time())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Zapisz sesję w pamięci
    client_ip = request.client.host
    active_sessions.append({
        "username": user.username,
        "ip": client_ip,
        "timestamp": time.time()
    })

    # Pobierz klucz publiczny
    public_key_pem = user.public_key
    if not public_key_pem:
        raise HTTPException(status_code=400, detail="Public key missing in database")

    user_public_keys[credentials.username] = public_key_pem
    access_token = create_access_token(data={"sub": credentials.username})

    return encrypt_response({
        "access_token": access_token,
        "token_type": "bearer"
    }, credentials.username)


@app.get("/sessions")
def list_sessions():
    return [
        {
            "username": s["username"],
            "ip": s["ip"],
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(s["timestamp"]))
        }
        for s in active_sessions
    ]

# Pamięciowy inbox dla każdego użytkownika
user_inboxes = {}

@app.post("/send")
def send_message(message: Message):
    if message.to_user not in user_public_keys:
        raise HTTPException(status_code=404, detail="User not available")

    encrypted_msg = encrypt_response({"message": message.content}, message.to_user)

    # Zapisz wiadomość w "skrzynce odbiorczej"
    if message.to_user not in user_inboxes:
        user_inboxes[message.to_user] = []

    user_inboxes[message.to_user].append(encrypted_msg)

    return {"status": "message stored"}
from fastapi import Request

@app.post("/get-message")
async def get_message(current_user: str = Depends(get_current_user)):
    if current_user not in user_inboxes or not user_inboxes[current_user]:
        return {"message": None}  # lub np. {"status": "no_message"}

    return user_inboxes[current_user].pop(0)

