"""API-bearing criterion: Authentication and session security.

Verifies login sets an httpOnly session cookie, /auth/me reflects the Super Admin
identity, logout clears the session, and invalid credentials are rejected.
"""
import httpx  # noqa: F401 kept for type consistency with client fixtures


def test_login_sets_session_and_me_returns_identity(client):
    resp = client.post("/auth/login", json={"email": "admin@crm.co.id", "password": "Password123"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["email"] == "admin@crm.co.id"
    assert body["role"] == "SUPER_ADMIN"

    set_cookie = resp.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie, f"expected HttpOnly cookie, got: {set_cookie}"

    cookies = resp.cookies
    me = client.get("/auth/me", cookies=cookies)
    assert me.status_code == 200, me.text
    me_body = me.json()
    assert me_body["email"] == "admin@crm.co.id"
    assert me_body["role"] == "SUPER_ADMIN"


def test_logout_clears_session(client):
    login = client.post("/auth/login", json={"email": "admin@crm.co.id", "password": "Password123"})
    assert login.status_code == 200
    cookies = login.cookies

    logout = client.post("/auth/logout", cookies=cookies)
    assert logout.status_code in (200, 204), logout.text

    # after logout the session cookie should no longer authenticate /auth/me
    me_after = client.get("/auth/me", cookies=logout.cookies)
    assert me_after.status_code in (401, 403), me_after.text


def test_invalid_credentials_rejected(client):
    resp = client.post("/auth/login", json={"email": "admin@crm.co.id", "password": "wrong-password"})
    assert resp.status_code in (401, 400), resp.text
