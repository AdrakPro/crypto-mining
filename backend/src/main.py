from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import Session
from security import SecurityManager
from session import SessionManager
from message import MessageManager
from db import get_db, Base, engine, SessionLocal
from schemas import UserSchema, Message, UserLoginSchema

#Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def truncate_sessions():
    db: Session = SessionLocal()
    try:
        db.execute(text("TRUNCATE TABLE active_sessions RESTART IDENTITY;"))
        db.commit()
    finally:
        db.close()

security_manager = SecurityManager()
session_manager = SessionManager()
message_manager = MessageManager()


async def get_current_user(credentials=Depends(HTTPBearer())):
    return await SecurityManager.validate_token(credentials)

@app.post("/register")
async def register(user: UserSchema, db: Session = Depends(get_db)):
    return security_manager.register_user(user, db)

@app.post("/login")
async def login(request: Request, user: UserSchema, db: Session = Depends(get_db)):
    return await security_manager.login(request, user, db)

@app.post("/login-db")
def login_db(request: Request, user: UserLoginSchema, db: Session = Depends(get_db)):
    return security_manager.login_db(request, user, db)

@app.get("/task")
async def get_task(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    task = session_manager.create_task(current_user, db)
    return security_manager.encrypt_response(task, current_user, db)

@app.post("/task/{task_id}/result")
async def submit_result(
    task_id: int, result: int, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)
):
    response = session_manager.validate_task_result(task_id, result, current_user, db)

    if response.get("status") == "Task not found":
        raise HTTPException(status_code=404, detail="Task not found")
    if response.get("status") == "Task already submitted":
        raise HTTPException(status_code=400, detail="Task already submitted")

    return security_manager.encrypt_response(response, current_user, db)

@app.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    return session_manager.list_active_sessions(db)

@app.post("/send")
def send_message(message: Message, db: Session = Depends(get_db)):
    return message_manager.send_message(message, security_manager, db)

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
