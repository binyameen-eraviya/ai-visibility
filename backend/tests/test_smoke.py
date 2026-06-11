"""Smoke tests: prove the DB harness and ASGI client boot before writing real tests."""


async def test_db_session_roundtrip(db_session):
    from backend.database.models.organization import Organization
    org = await Organization.create(db_session, name="Smoke Org")
    fetched = await Organization.find_by_id(db_session, org.id)
    assert fetched.name == "Smoke Org"


async def test_db_session_is_isolated(db_session):
    # The org from the previous test must NOT leak in (per-test rollback).
    from sqlalchemy import select
    from backend.database.migrations.organization import Organization as OrgTable
    rows = (await db_session.execute(select(OrgTable))).scalars().all()
    assert rows == []


async def test_client_serves_openapi(client):
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["title"]  # FastAPI default schema is present
