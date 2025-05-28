from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import secrets

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str):
    return pwd_context.hash(password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=int(os.getenv("JWT_EXPIRE_MINUTES", 30))
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        os.getenv("JWT_SECRET_KEY"),
        algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
    )


def decode_token(token: str):
    try:
        return jwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY"),
            algorithms=[os.getenv("JWT_ALGORITHM", "HS256")],
        )
    except JWTError:
        return None


def secure_compare(val1: str, val2: str) -> bool:
    return secrets.compare_digest(val1.encode(), val2.encode())
