import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add src directory to PATH
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path.absolute()))

# Load environment variables
load_dotenv()

# Import after setting path
from src.database import create_tables

def init_database():
    """Initialize database tables"""
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database()