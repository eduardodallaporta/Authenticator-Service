def test_login_returns_tokens(client, user_payload, registered_user):
    r = client.post(
        "/auth/login",
        data={"username": user_payload["email"], "password": user_payload["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    body = r.json()

    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0


def test_login_invalid_credentials(client, user_payload, registered_user):
    r = client.post(
        "/auth/login",
        data={"username": user_payload["email"], "password": "senhaErrada"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 401, r.text


def test_me_requires_auth(client):
    r = client.get("/auth/me")
    assert r.status_code == 401, r.text


def test_me_returns_user(client, tokens, auth_headers):
    r = client.get("/auth/me", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == 1
    assert "email" in body
