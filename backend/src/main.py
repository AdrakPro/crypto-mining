from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

app = FastAPI()


# Start (musisz odpalic w tym samym folderze co main): uvicorn main:app --host 127.0.0.1 --port 8080 --reload
@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

#ping od klienta
@app.post("/ping")
def ping():
    return {"message": "Client is online"}
