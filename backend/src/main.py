from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from threading import Lock
from datetime import datetime
import os
import time
from dotenv import load_dotenv

from security import SecurityManager
from session import SessionManager
from message import MessageManager
from db import get_db, Base, engine
from models import User
from schemas import UserCreate, UserLogin, UserCredentials, Result, Message, Task

Base.metadata.create_all(bind=engine)
load_dotenv()

app = FastAPI()

security_manager = SecurityManager()
session_manager = SessionManager()
message_manager = MessageManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tasks: Dict[str, Dict[str, int]] = {}
lock = Lock()

async def get_current_user(
    credentials = Depends(HTTPBearer())
) -> str:
    return await security_manager.validate_token(credentials)

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    return security_manager.register_user(db, user)

@app.post("/login")
async def login(request: Request, credentials: UserCredentials):
    return await security_manager.login(request, credentials)

@app.post("/login-db")
def login_db(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    return security_manager.login_db(request, credentials, db)

@app.get("/task")
async def get_task(current_user: str = Depends(get_current_user)):
    task = session_manager.get_or_create_task(current_user)
    return security_manager.encrypt_response(task, current_user)

@app.post("/result")
async def submit_result(
    result: Result,
    current_user: str = Depends(get_current_user)
):
    response = session_manager.validate_task_result(current_user, result)
    return security_manager.encrypt_response(response, current_user)

@app.get("/sessions")
def list_sessions() -> List[Dict[str, str]]:
    return session_manager.list_active_sessions()

@app.post("/send")
def send_message(
    message: Message,
    current_user: str = Depends(get_current_user)
):
    return message_manager.send_message(message, security_manager)

@app.post("/get-message")
async def get_message(current_user: str = Depends(get_current_user)):
    return message_manager.get_message(current_user)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVER_PORT", 8080)),
    )
