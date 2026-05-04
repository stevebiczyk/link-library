from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

DATABASE_URL = "sqlite:///./linklibrary.db" # SQLite database URL.

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) # Create a SQLAlchemy engine for the SQLite database. The connect_args parameter is used to allow multiple threads to access the database.

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # Create a session factory that will be used to create database sessions.

class Base(DeclarativeBase):
    pass # Base class for SQLAlchemy models. This is used to define the database schema.

def get_db() -> Generator[Session, None, None]: # Dependency function to get a database session. This will be used in FastAPI endpoints to interact with the database.
    db = SessionLocal() # Create a new database session.
    try:
        yield db # Yield the session to be used in the endpoint.
    finally:
        db.close() # Ensure that the database session is closed after the request is processed.