def test_refresh_rotates_tokens(client, tokens):
    old_refresh = tokens["refresh_token"]

    r = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 200, r.text
    new_body = r.json()

    assert new_body["access_token"] != tokens["access_token"]
    assert new_body["refresh_token"] != old_refresh
    assert new_body["expires_in"] > 0


def test_refresh_old_token_revoked_after_rotation(client, tokens):
    # 1) Rotaciona (revoga o antigo)
    old_refresh = tokens["refresh_token"]
    r1 = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert r1.status_code == 200, r1.text

    # 2) Tenta usar o antigo => deve negar
    r2 = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert r2.status_code == 401, r2.text
    detail = r2.json().get("detail", "")
    assert "revoked" in detail.lower() or "reuse" in detail.lower() or "invalid" in detail.lower()


def test_refresh_reuse_detection_revokes_all_sessions(client, tokens):
    """
    Opção A: se tentar usar um refresh já revogado, revoga todos do usuário.
    Cenário:
    - usa refresh uma vez (gera novo e revoga o velho)
    - tenta usar o velho novamente => dispara reuse detection (revoga todos)
    - tenta usar o novo => também deve falhar (porque logout-all implícito)
    """
    old_refresh = tokens["refresh_token"]

    r1 = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert r1.status_code == 200, r1.text
    new_refresh = r1.json()["refresh_token"]

    # reuse do antigo
    r2 = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert r2.status_code == 401, r2.text

    # depois do reuse detection, o new_refresh deve estar revogado também
    r3 = client.post("/auth/refresh", json={"refresh_token": new_refresh})
    assert r3.status_code == 401, r3.text
