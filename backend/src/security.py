#from passlib.context import CryptContext
from jose.exceptions import JWTError
from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import secrets
import hashlib

load_dotenv()

# Password Hashing
#pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_sha256_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

#def verify_password(plain_password: str, hashed_password: str) -> bool:
#    return pwd_context.verify(plain_password, hashed_password)


#def get_password_hash(password: str) -> str:
#    return pwd_context.hash(password)


# JWT Utilities
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=int(os.getenv("JWT_EXPIRE_MINUTES", 30))
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, os.getenv("JWT_SECRET_KEY"), algorithm=os.getenv("JWT_ALGORITHM")
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, os.getenv("JWT_SECRET_KEY"), algorithms=[os.getenv("JWT_ALGORITHM")]
        )
    except JWTError:
        return None


# Secure Comparison
def secure_compare(val1: str, val2: str) -> bool:
    return secrets.compare_digest(val1.encode(), val2.encode())
