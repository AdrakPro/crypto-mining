# schemas.py
from pydantic import BaseModel


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
