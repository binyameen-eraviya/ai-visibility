"""Queue-status admin endpoint (SUPER_ADMIN only)."""

from datetime import datetime, timezone

import pytest_asyncio


@pytest_asyncio.fixture
async def super_admin_headers(db_session, test_org):
    from backend.database.models.user import User
    from backend.service.auth_handler import AuthHandler
    from backend.utils.enums import UserRole
    user = await User.create(
        db_session,
        name="Super Admin",
        email="super@example.com",
        organization_id=test_org.id,
        password=AuthHandler.get_password_hash("password123"),
        signup_token="seed-super",
        role=UserRole.SUPER_ADMIN.value,
        verified_at=datetime.now(timezone.utc),
    )
    token = AuthHandler.generate_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


async def test_queue_status_requires_super_admin(client, auth_headers):
    # auth_headers is a plain ADMIN -> rejected.
    resp = await client.get("/api/admin/queue-status", headers=auth_headers)
    assert resp.status_code == 401


async def test_queue_status_unauth(client):
    resp = await client.get("/api/admin/queue-status")
    assert resp.status_code == 401


async def test_queue_status_returns_structure(client, super_admin_headers):
    resp = await client.get("/api/admin/queue-status", headers=super_admin_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Shape must be present; worker count depends on whether the worker profile
    # is up in this environment (>= 0 either way).
    assert isinstance(body["workers"], int) and body["workers"] >= 0
    assert isinstance(body["worker_names"], list)
    assert isinstance(body["active_tasks"], int)
    assert isinstance(body["reserved_tasks"], int)
    assert isinstance(body["scheduled_tasks"], int)
    assert set(body["queues"].keys()) == {"scrape", "parse", "aggregate", "celery"}
