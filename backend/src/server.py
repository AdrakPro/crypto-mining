from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional
from threading import Lock
from security import verify_password, create_access_token, decode_token, secure_compare, get_password_hash
from database import get_db
from models import User
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

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGINS")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
failed_attempts = defaultdict(list)
calculations = {}
tasks = {}
lock = Lock()
executor = ThreadPoolExecutor(max_workers=4)

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


# Security models
class UserCredentials(BaseModel):
    username: str
    password: str
    public_key: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    public_key: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    created_at: datetime


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
        t for t in failed_attempts[client_ip] if now - t < LOCKOUT_WINDOW
    ]
    failed_attempts[client_ip] = recent_attempts

    if len(recent_attempts) >= FAILED_ATTEMPT_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts",
        )


def encrypt_response(data: dict, username: str) -> dict:
    public_key_pem = data.get("public_key")
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
        raise HTTPException(
            status_code=400, detail=f"Invalid public key for username {username}: {e}"
        )

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
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        if not payload:
            raise credentials_exception
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception

        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise credentials_exception
        return user
    except Exception:
        raise credentials_exception


@app.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if username or email already exists
    result = await db.execute(
        select(User).where(
            (User.username == user_data.username) | 
            (User.email == user_data.email)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        public_key=user_data.public_key
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        is_admin=new_user.is_admin,
        created_at=new_user.created_at
    )


@app.post("/login")
async def login(
    request: Request, 
    credentials: UserCredentials,
    db: AsyncSession = Depends(get_db)
):
    check_brute_force(request)

    # Find user in database
    result = await db.execute(select(User).where(User.username == credentials.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        failed_attempts[request.client.host].append(time.time())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Update user's public key and last login time
    user.public_key = credentials.public_key
    user.last_login = datetime.utcnow()
    await db.commit()

    # Create access token
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "is_admin": user.is_admin
        }
    )

    return encrypt_response(
        {"access_token": access_token, "token_type": "bearer"},
        credentials.username
    )


@app.get("/task")
async def get_task(current_user: User = Depends(get_current_user)):
    with lock:
        if current_user.username not in tasks:
            a = secrets.randbelow(100) + 1
            b = secrets.randbelow(100) + 1
            tasks[current_user.username] = {"a": a, "b": b, "expected_sum": a + b}
        return encrypt_response(
            {"a": tasks[current_user.username]["a"], "b": tasks[current_user.username]["b"]}, current_user.username
        )


@app.post("/result")
async def submit_result(result: Result, current_user: User = Depends(get_current_user)):
    with lock:
        if current_user.username not in tasks:
            return encrypt_response({"status": "No active task"}, current_user.username)

        expected = tasks[current_user.username]["expected_sum"]
        response_data = (
            {"status": "Correct"}
            if result.sum == expected
            else {"status": "Incorrect", "expected": expected, "received": result.sum}
        )
        del tasks[current_user.username]
        return encrypt_response(response_data, current_user.username)


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
    """
    1. Regex pattern matching
    2. AST validation
    3. Additional safety checks
    """
    expression = expression.strip()

    # Strict regex pattern for "number + number"
    if not re.match(r"^\d+\s*\+\s*\d+$", expression):
        raise ValueError("Invalid format. Only simple addition (num + num) is allowed.")

    # AST validation to ensure only allowed operations
    try:
        tree = ast.parse(expression)
        if not is_safe_ast(tree):
            raise ValueError("Expression contains unsafe operations")
    except SyntaxError:
        raise ValueError("Invalid syntax in expression")

    # Ensure no variable names, function calls, or other potentially dangerous elements
    if any(
        keyword in expression
        for keyword in [
            "import",
            "eval",
            "exec",
            "compile",
            "open",
            "file",
            "globals",
            "locals",
            "__",
            "os",
            "sys",
            "subprocess",
        ]
    ):
        raise ValueError("Expression contains forbidden keywords")

    return True


@app.post("/calculation")
async def submit_calculation(
    calculation: Calculation, current_user: User = Depends(get_current_user)
):
    with lock:
        try:
            print(f"User {current_user.username} submitted a calculation request")

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
                logger.error(f"Calculation timeout from {current_user.username}")
                raise HTTPException(status_code=400, detail="Calculation timeout")
            except Exception as e:
                logger.error(f"Calculation error from {current_user.username}: {e}")
                raise HTTPException(status_code=400, detail="Calculation error")

            result = restricted_locals.get("result")
            if not isinstance(result, (int, float)):
                logger.error(f"Non-numeric result from {current_user.username}")
                raise HTTPException(status_code=400, detail="Invalid result type")

            print(f"Result {result}")

            return encrypt_response({"result": result}, current_user.username)

        except Exception as e:
            print(f"Error processing calculation: {str(e)}")
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
