def test_register_creates_user(client, user_payload):
    r = client.post("/auth/register", json=user_payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["id"] == 1
    assert body["email"] == user_payload["email"]


def test_register_rejects_duplicate_email(client, user_payload):
    r1 = client.post("/auth/register", json=user_payload)
    assert r1.status_code == 201, r1.text

    r2 = client.post("/auth/register", json=user_payload)
    assert r2.status_code == 400, r2.text
    assert r2.json()["detail"] in ("Email already registered", "email already registered")
