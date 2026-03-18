from sqlmodel import SQLModel

from app.db.engine import engine

# IMPORTANTE: importe os models aqui para o metadata "conhecer" as tabelas
from app.models.user import User  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
