def test_logout_revokes_refresh_token(client, tokens):
    refresh = tokens["refresh_token"]

    r1 = client.post("/auth/logout", json={"refresh_token": refresh})
    assert r1.status_code == 204, r1.text

    # tentar usar depois => 401
    r2 = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 401, r2.text


def test_logout_all_revokes_all_refresh_tokens(client, tokens, auth_headers):
    # cria uma segunda sessão (segundo refresh) via login novo
    r_login2 = client.post(
        "/auth/login",
        data={"username": "eduardo@example.com", "password": "SenhaForte123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r_login2.status_code == 200, r_login2.text
    refresh2 = r_login2.json()["refresh_token"]

    # logout-all
    r1 = client.post("/auth/logout-all", headers=auth_headers)
    assert r1.status_code == 204, r1.text

    # refresh antigo falha
    r2 = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r2.status_code == 401, r2.text

    # refresh da segunda sessão também falha
    r3 = client.post("/auth/refresh", json={"refresh_token": refresh2})
    assert r3.status_code == 401, r3.text
