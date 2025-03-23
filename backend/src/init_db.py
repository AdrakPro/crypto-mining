import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError
from urllib.parse import urlparse
from .database import create_tables, DATABASE_URL

# Load environment variables
load_dotenv()

def database_exists():
    """
    Check if the database defined in DATABASE_URL exists.
    Returns True if the database exists, False otherwise.
    """
    engine = create_engine(DATABASE_URL)
    
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

def init_database():
    """Initialize database tables"""
    if database_exists():
        print("Database exists, creating/updating tables...")
        create_tables()
        print("Database tables created/updated successfully!")
    else:
        print("Database does not exist. Please create the database first.")
        print(f"Current DATABASE_URL: {DATABASE_URL}")
        raise Exception("Database does not exist")

if __name__ == "__main__":
    # When run directly, need to use absolute import
    from database import create_tables, DATABASE_URL
    init_database()