from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session, SQLModel

from app.main import app
from app.db.engine import engine
from app.db.session import get_session


@pytest.fixture(scope="session", autouse=True)
def create_test_schema():
    """
    Garante que as tabelas existem no Postgres antes de rodar a suíte.
    (Você já usa init_db no startup, mas isso deixa o pytest independente.)
    """
    SQLModel.metadata.create_all(engine)
    yield


@pytest.fixture()
def db_session():
    """
    Abre uma sessão por teste e limpa as tabelas no final.
    """
    session = Session(engine)
    try:
        yield session
    finally:
        # Limpa tudo para isolar testes (ordem importa por FK/relacionamentos)
        session.exec(text("TRUNCATE TABLE refresh_tokens RESTART IDENTITY CASCADE;"))
        session.exec(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE;"))
        session.commit()
        session.close()


@pytest.fixture()
def client(db_session: Session):
    """
    Override do Depends(get_session) para usar a mesma sessão do teste.
    Assim você consegue isolar e limpar com segurança.
    """
    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# Helpers (reutilizáveis nos testes)
@pytest.fixture()
def user_payload():
    return {"email": "eduardo@example.com", "password": "SenhaForte123"}


def _register(client: TestClient, email: str, password: str):
    return client.post("/auth/register", json={"email": email, "password": password})


def _login(client: TestClient, email: str, password: str):
    # login usa OAuth2PasswordRequestForm => x-www-form-urlencoded com "username"
    return client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


@pytest.fixture()
def registered_user(client: TestClient, user_payload):
    resp = _register(client, user_payload["email"], user_payload["password"])
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def tokens(client: TestClient, user_payload, registered_user):
    resp = _login(client, user_payload["email"], user_payload["password"])
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture()
def auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}
