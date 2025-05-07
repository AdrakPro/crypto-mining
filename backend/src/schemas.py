# schemas.py
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    public_key: str

class UserLogin(BaseModel):
    username: str
    password: str