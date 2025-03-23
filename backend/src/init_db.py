import os
from dotenv import load_dotenv
from .database import create_tables

# Load environment variables
load_dotenv()

def init_database():
    """Initialize database tables"""
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully!")

if __name__ == "__main__":
    # When run directly, need to use absolute import
    from database import create_tables
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully!")