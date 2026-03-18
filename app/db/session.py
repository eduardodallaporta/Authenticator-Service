from sqlmodel import Session
from app.db.engine import engine


def get_session():
    return Session(engine)