"""Auth flow tests (signup, login, protected-route guards)."""

SIGNUP = {
    "user_name": "Jane",
    "email": "jane@example.com",
    "organization_name": "Jane Co",
    "password": "password123",
}


async def test_signup_creates_user_and_org(client):
    resp = await client.post("/api/signup", json=SIGNUP)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user"]["email"] == "jane@example.com"
    assert body["organization_id"]
    # APP_ENV=development auto-verifies and sends no email.
    assert body["email_sent"] is False
    assert body["verification_required"] is False


async def test_signup_duplicate_email_fails(client):
    first = await client.post("/api/signup", json=SIGNUP)
    assert first.status_code == 200, first.text
    second = await client.post("/api/signup", json=SIGNUP)
    assert second.status_code == 409


async def test_login_success(client):
    await client.post("/api/signup", json=SIGNUP)
    resp = await client.post(
        "/api/login",
        json={"email": SIGNUP["email"], "password": SIGNUP["password"]},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["access_token"]


async def test_login_wrong_password(client):
    await client.post("/api/signup", json=SIGNUP)
    resp = await client.post(
        "/api/login",
        json={"email": SIGNUP["email"], "password": "wrong-password"},
    )
    assert resp.status_code == 401


async def test_protected_route_without_token_returns_401(client):
    resp = await client.get("/api/projects")
    assert resp.status_code == 401


async def test_protected_route_with_invalid_token_returns_401(client):
    resp = await client.get(
        "/api/projects", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401
