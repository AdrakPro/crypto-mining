from pydantic import BaseModel


class UserSchema(BaseModel):
    username: str
    password: str
    public_key: str

class UserLoginSchema(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class Task(BaseModel):
    a: int
    b: int


class Message(BaseModel):
    to_user: str
    content: str
