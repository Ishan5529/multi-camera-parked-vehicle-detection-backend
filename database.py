"""Database configuration for local development and Render PostgreSQL."""

import os
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Yield a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables if they do not exist."""
    from db_models import ParkingConfiguration  # noqa: F401

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    if "parking_configurations" in inspector.get_table_names():
        column_names = {column["name"] for column in inspector.get_columns("parking_configurations")}
        if "vacant_lot" not in column_names:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE parking_configurations ADD COLUMN vacant_lot INTEGER NOT NULL DEFAULT 0")
                )
