"""Health endpoint: reports DB + Redis connectivity and a version."""


async def test_health_returns_ok(client):
    resp = await client.get("/health")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["database"] == "connected"
    assert body["redis"] == "connected"
    assert body["version"]


async def test_health_is_unprotected(client):
    # No Authorization header -> still reachable (not a 401).
    resp = await client.get("/health")
    assert resp.status_code != 401
