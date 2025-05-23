# schemas.py
from pydantic import BaseModel
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str
    public_key: str


class UserLogin(BaseModel):
    username: str
    password: str


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


class Message(BaseModel):
    to_user: str
    content: str

class TaskHistoryCreate(BaseModel):
    action: str
    details: str

class TaskHistoryOut(BaseModel):
    id: int
    user_id: int
    action: str
    details: str
    timestamp: datetime

    class Config:
        from_attributes = True
