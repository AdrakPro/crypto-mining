from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

app = FastAPI()


# Start (musisz odpalic w tym samym folderze co main): uvicorn main:app --host 127.0.0.1 --port 8080 --reload
@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

# Endpoint, ktory po prostu sprawdza polaczenie z baza danych, ale nie robi nic wiecej
@app.get("/db_check")
async def db_check(db: AsyncSession = Depends(get_db)):
    try:
        return {"message": "Połączenie z bazą danych jest aktywne!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nie udało się połączyć z bazą danych: {str(e)}")
