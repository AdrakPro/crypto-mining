from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Construct database URL from environment variables
DATABASE_URL = "postgresql+asyncpg://{}:{}@{}:{}/{}".format(
    os.getenv("DB_USER", "user"),
    os.getenv("DB_PASSWORD", "password"),
    os.getenv("DB_HOST", "localhost"),
    os.getenv("DB_PORT", "5432"),
    os.getenv("DB_NAME", "cryptomining")
)

# Create async engine
engine = create_async_engine(DATABASE_URL)

# Create async session factory
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Dependency to get database session
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()