from datetime import datetime

from fastapi import HTTPException, status, Request
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from sqlalchemy.orm import Session
from collections import defaultdict
from dotenv import load_dotenv
import base64
import json
import time
import os
from models import UserModel, ActiveSessionModel
from schemas import UserSchema, UserLoginSchema
from utils import (
    verify_password,
    create_access_token,
    decode_token,
    secure_compare,
    hash_password,
)

load_dotenv()

DEBUG_MODE = os.getenv("DEBUG_MODE", "0") == 1


class SecurityManager:
    def __init__(self):
        self.user_public_keys = {}
        self.failed_attempts = defaultdict(list)

    def check_brute_force(self, request: Request):
        client_ip = request.client.host
        now = time.time()

        recent_attempts = [
            t
            for t in self.failed_attempts[client_ip]
            if now - t < int(os.getenv("LOCKOUT_MINUTES", 5)) * 60
        ]
        self.failed_attempts[client_ip] = recent_attempts

        if len(recent_attempts) >= int(os.getenv("FAILED_ATTEMPT_LIMIT", 5)):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account locked for {os.getenv('LOCKOUT_MINUTES', 5)} minutes",
            )

    def encrypt_response(self, data: dict, current_user: str, db: Session) -> dict:
        public_key_pem = self.user_public_keys.get(current_user)
        if not public_key_pem:
            raise HTTPException(status_code=400, detail="Public key missing")

        try:
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
        encrypted = base64.b64encode(ciphertext).decode()

        if DEBUG_MODE:
            print(f"[DEBUG] Odszyfrowana wiadomość dla {current_user}: {data}")
            print(f"[DEBUG] Zaszyfrowana wiadomość dla {current_user}: {encrypted}")

        return {"encrypted": encrypted}

    @staticmethod
    async def validate_token(credentials):
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

    def register_user(self, user: UserSchema, db: Session):
        if db.query(UserModel).filter(UserModel.username == user.username).first():
            raise HTTPException(status_code=400, detail="Username already registered")

        new_user = UserModel(
            username=user.username,
            hashed_password=hash_password(user.password),
            public_key=user.public_key,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"status": "User registered successfully"}

    async def login(self, request: Request, user: UserSchema, db: Session):
        self.check_brute_force(request)

        if not (
            secure_compare(user.username, os.getenv("ADMIN_USERNAME"))
            and verify_password(user.password, os.getenv("ADMIN_PASSWORD"))
        ):
            self.failed_attempts[request.client.host].append(time.time())
            raise HTTPException(status_code=401, detail="Invalid credentials")

        try:
            self.user_public_keys[user.username] = user.public_key
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid public key format: {str(e)}"
            )

        access_token = create_access_token(data={"sub": user.username})
        return self.encrypt_response(
            {"access_token": access_token, "token_type": "bearer"}, user.username, db
        )

    def login_db(self, request: Request, user: UserLoginSchema, db: Session):
        self.check_brute_force(request)

        fetched_user = db.query(UserModel).filter(UserModel.username == user.username).first()
        if not fetched_user or not verify_password(user.password, fetched_user.hashed_password):
            self.failed_attempts[request.client.host].append(time.time())
            raise HTTPException(status_code=401, detail="Invalid credentials")

        self.user_public_keys[fetched_user.username] = fetched_user.public_key

        access_token = create_access_token(data={"sub": fetched_user.username})
        active_session = ActiveSessionModel(
            username=fetched_user.username,
            ip=request.client.host,
            timestamp=datetime.fromtimestamp(time.time())
        )
        db.add(active_session)
        db.commit()
        db.refresh(active_session)

        return self.encrypt_response(
            {"access_token": access_token, "token_type": "bearer"}, fetched_user.username, db
        )
