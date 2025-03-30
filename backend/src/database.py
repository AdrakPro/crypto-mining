from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment variable or use default
DATABASE_URL = os.getenv("DATABASE_URL")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

# Define Client model
class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    password = Column(String)
    ip_address = Column(String, index=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    tasks_completed = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)


# Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# Check if database exists
def database_exists():
    """
    Check if the database defined in DATABASE_URL exists.
    Returns True if the database exists, False otherwise.
    """
    from sqlalchemy.exc import OperationalError, ProgrammingError
    from urllib.parse import urlparse
    
    # Extract database name from URL
    parsed_url = urlparse(DATABASE_URL)
    db_name = parsed_url.path.lstrip('/')
    
    try:
        # Try to connect to the database
        with engine.connect() as connection:
            # Execute a simple query that should work on any database
            connection.execute("SELECT 1")
            return True
    except (OperationalError, ProgrammingError) as e:
        # Check error message to determine if it's about database existence
        error_msg = str(e).lower()
        if "database" in error_msg and ("does not exist" in error_msg or "not found" in error_msg):
            return False
        else:
            # Re-raise if it's a different type of error (server down, auth failed, etc.)
            raise
    except Exception as e:
        # Re-raise unexpected errors
        raise