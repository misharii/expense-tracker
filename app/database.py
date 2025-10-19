import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Explicitly load .env from the project root
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(dotenv_path=env_path)

# Read DATABASE_URL strictly from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Fail fast if missing
if not DATABASE_URL:
    raise RuntimeError(
        "❌ DATABASE_URL not found. Please define it in a .env file at the project root."
    )

# Create SQLAlchemy engine (PostgreSQL or other)
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency to provide a database session per request"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize tables on startup"""
    Base.metadata.create_all(bind=engine)