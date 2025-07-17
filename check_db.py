#!/usr/bin/env python3
"""
Simple script to test MySQL database connection
"""
import os
from sqlalchemy import create_engine, text

def test_connection():
    # Database URL
    DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://appuser:apppassword@localhost:3309/python_react_db")
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            
            # Check if tables exist
            result = connection.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            print(f"📋 Tables in database: {tables}")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    test_connection() 