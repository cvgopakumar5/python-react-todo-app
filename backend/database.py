from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://appuser:apppassword@localhost:3309/python_react_db")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 