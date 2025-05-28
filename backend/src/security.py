from fastapi import HTTPException, status, Request
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from sqlalchemy.orm import Session
from collections import defaultdict
import base64
import json
import time
import os

from models import User
from schemas import UserCreate, UserCredentials, UserLogin
from utils import (
    verify_password,
    create_access_token,
    decode_token,
    secure_compare,
    hash_password,
)

class SecurityManager:
    def __init__(self):
        self.user_public_keys = {}
        self.failed_attempts = defaultdict(list)

    def check_brute_force(self, request: Request):
        client_ip = request.client.host
        now = time.time()

        recent_attempts = [
            t for t in self.failed_attempts[client_ip]
            if now - t < int(os.getenv("LOCKOUT_MINUTES", 5)) * 60
        ]
        self.failed_attempts[client_ip] = recent_attempts

        if len(recent_attempts) >= int(os.getenv("FAILED_ATTEMPT_LIMIT", 5)):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account locked for {os.getenv('LOCKOUT_MINUTES', 5)} minutes"
            )

    def encrypt_response(self, data: dict, username: str) -> dict:
        public_key_pem = self.user_public_keys.get(username)
        if not public_key_pem:
            raise HTTPException(status_code=400, detail="Public key missing")

        try:
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

    async def validate_token(self, credentials):
        try:
            payload = decode_token(credentials.credentials)
            if not payload:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            username: str = payload.get("sub")
            if not username:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            return username
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid credentials")

    def register_user(self, db: Session, user: UserCreate):
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

    async def login(self, request: Request, credentials: UserCredentials):
        self.check_brute_force(request)

        if not (secure_compare(credentials.username, os.getenv("ADMIN_USERNAME")) and
                verify_password(credentials.password, os.getenv("ADMIN_PASSWORD"))):
            self.failed_attempts[request.client.host].append(time.time())
            raise HTTPException(status_code=401, detail="Invalid credentials")

        try:
            self.user_public_keys[credentials.username] = credentials.public_key
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid public key format: {str(e)}")

        access_token = create_access_token(data={"sub": credentials.username})
        return self.encrypt_response(
            {"access_token": access_token, "token_type": "bearer"},
            credentials.username
        )

    def login_db(self, request: Request, credentials: UserLogin, db: Session):
        self.check_brute_force(request)

        user = db.query(User).filter(User.username == credentials.username).first()
        if not user or not verify_password(credentials.password, user.hashed_password):
            self.failed_attempts[request.client.host].append(time.time())
            raise HTTPException(status_code=401, detail="Invalid credentials")

        self.user_public_keys[credentials.username] = user.public_key
        access_token = create_access_token(data={"sub": credentials.username})

        return self.encrypt_response(
            {"access_token": access_token, "token_type": "bearer"},
            credentials.username
        )
