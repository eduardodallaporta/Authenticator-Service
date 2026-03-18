from __future__ import annotations

from sqlmodel import SQLModel, create_engine

from app.core.config import settings

# Ex.: settings.DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/auth_db"
engine = create_engine(settings.DATABASE_URL, echo=True)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
