from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional
from threading import Lock
from security import verify_password, create_access_token, decode_token, secure_compare
import os
from dotenv import load_dotenv
import secrets

load_dotenv()

app = FastAPI()
security = HTTPBearer()

# Brute Force Protection
FAILED_ATTEMPT_LIMIT = 5  # Max allowed failed attempts
LOCKOUT_MINUTES = 5  # Lockout duration in minutes
failed_attempts = defaultdict(list)  # {ip: [timestamp1, timestamp2]}


def check_brute_force(request: Request):
    """Check if IP has exceeded failed attempt limit"""
    client_ip = request.client.host
    now = time.time()

    # Remove attempts older than lockout window
    recent_attempts = [
        t for t in failed_attempts[client_ip] if now - t < LOCKOUT_MINUTES * 60
    ]
    failed_attempts[client_ip] = recent_attempts

    if len(recent_attempts) >= FAILED_ATTEMPT_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many attempts. Try again in {LOCKOUT_MINUTES} minutes",
        )


# Models
class UserCredentials(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class Task(BaseModel):
    a: int
    b: int


class Result(BaseModel):
    sum: int


# State
tasks = {}
lock = Lock()


# Authentication
async def get_current_user(token: str = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token.credentials)
    if not payload:
        raise credentials_exception
    username: str = payload.get("sub")
    if not username:
        raise credentials_exception
    return username


# Endpoints
@app.post("/login", response_model=Token)
def login(credentials: UserCredentials):
    # Brute force check
    check_brute_force(request)

    if not (
        secure_compare(credentials.username, os.getenv("ADMIN_USERNAME"))
        and verify_password(credentials.password, os.getenv("ADMIN_PASSWORD"))
    ):
        # Record failed attempt
        failed_attempts[request.client.host].append(time.time())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Reset on successful login
    if request.client.host in failed_attempts:
        del failed_attempts[request.client.host]

    access_token = create_access_token(data={"sub": credentials.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/ping")
def ping(current_user: str = Depends(get_current_user)):
    return {"message": f"Client {current_user} is online"}


@app.get("/task")
def get_task(current_user: str = Depends(get_current_user)):
    with lock:
        if current_user not in tasks:
            a = secrets.randbelow(100) + 1
            b = secrets.randbelow(100) + 1
            tasks[current_user] = {"a": a, "b": b, "expected_sum": a + b}
        return {"a": tasks[current_user]["a"], "b": tasks[current_user]["b"]}


@app.post("/result")
def submit_result(result: Result, current_user: str = Depends(get_current_user)):
    with lock:
        if current_user not in tasks:
            return {"status": "No active task"}

        expected = tasks[current_user]["expected_sum"]
        if result.sum == expected:
            response = {"status": "Correct!"}
        else:
            response = {
                "status": "Incorrect!",
                "expected": expected,
                "received": result.sum,
            }
        del tasks[current_user]
        return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.getenv("SERVER_HOST"), port=int(os.getenv("SERVER_PORT")))
