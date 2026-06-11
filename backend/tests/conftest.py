"""Shared test fixtures.

Strategy (see docs/superpowers/plans/2026-06-11-test-infrastructure.md):
- A separate Postgres database ({POSTGRES_DB}_test) in the same container.
- Schema created once per session via a synchronous psycopg2 engine.
- Each test gets an AsyncSession bound to an outer transaction with
  join_transaction_mode="create_savepoint"; one outer rollback isolates tests
  even though the query classes commit internally.
"""

import os
import uuid
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from httpx import AsyncClient, ASGITransport

from backend.database.db import Base, get_db


# --- Connection URLs -------------------------------------------------------

PG_USER = os.environ["POSTGRES_USER"]
PG_PASS = os.environ["POSTGRES_PASSWORD"]
# Mirror backend/database/db.py: "db" service host in-container, else localhost.
PG_HOST = "db" if os.getenv("ENVIRONMENT") == "production" else "localhost"
ADMIN_DB = os.getenv("POSTGRES_DB", "postgres")
TEST_DB = os.getenv("TEST_DATABASE_NAME", f"{ADMIN_DB}_test")

SYNC_ADMIN_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@{PG_HOST}:5432/{ADMIN_DB}"
SYNC_TEST_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@{PG_HOST}:5432/{TEST_DB}"
ASYNC_TEST_URL = f"postgresql+asyncpg://{PG_USER}:{PG_PASS}@{PG_HOST}:5432/{TEST_DB}"


def _import_all_table_models() -> None:
    """Import every migration module so all tables register on Base.metadata.

    Mirrors backend/alembic/env.py:import_all_migration_models without importing
    the alembic env (which requires an alembic runtime context).
    """
    migrations_dir = Path(__file__).resolve().parents[1] / "database" / "migrations"
    for model_file in migrations_dir.glob("*.py"):
        if model_file.name.startswith("_"):
            continue
        import_module(f"backend.database.migrations.{model_file.stem}")


@pytest.fixture(scope="session", autouse=True)
def _prepare_test_database():
    """Create the test database (if missing) and (re)build its schema once."""
    _import_all_table_models()

    # CREATE DATABASE cannot run in a transaction -> AUTOCOMMIT on the admin db.
    admin_engine = create_engine(SYNC_ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DB},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB}"'))
    admin_engine.dispose()

    sync_engine = create_engine(SYNC_TEST_URL)
    # Drop first so a re-run starts from a clean schema (also drops enums).
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    sync_engine.dispose()

    yield


@pytest_asyncio.fixture
async def db_session():
    """An AsyncSession isolated per test via an outer-transaction rollback."""
    engine = create_async_engine(ASYNC_TEST_URL)
    async with engine.connect() as connection:
        await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await connection.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """httpx client driving the real app with get_db -> the test session."""
    from main import app

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# --- Data fixtures (built via the real async query classes) ----------------

@pytest_asyncio.fixture
async def test_org(db_session):
    from backend.database.models.organization import Organization
    return await Organization.create(db_session, name="Test Org")


@pytest_asyncio.fixture
async def test_user(db_session, test_org):
    from backend.database.models.user import User
    from backend.service.auth_handler import AuthHandler
    from backend.utils.enums import UserRole
    return await User.create(
        db_session,
        name="Test User",
        email="owner@example.com",
        organization_id=test_org.id,
        password=AuthHandler.get_password_hash("password123"),
        signup_token="seed-token",
        role=UserRole.ADMIN.value,
        verified_at=datetime.now(timezone.utc),
    )


@pytest_asyncio.fixture
async def auth_headers(test_user):
    from backend.service.auth_handler import AuthHandler
    token = AuthHandler.generate_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def other_org_headers(db_session):
    """A second org+user, for cross-tenant (404) assertions."""
    from backend.database.models.organization import Organization
    from backend.database.models.user import User
    from backend.service.auth_handler import AuthHandler
    from backend.utils.enums import UserRole
    org = await Organization.create(db_session, name="Other Org")
    user = await User.create(
        db_session,
        name="Other User",
        email="intruder@example.com",
        organization_id=org.id,
        password=AuthHandler.get_password_hash("password123"),
        signup_token="seed-token-2",
        role=UserRole.ADMIN.value,
        verified_at=datetime.now(timezone.utc),
    )
    token = AuthHandler.generate_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_project(db_session, test_org):
    from backend.database.models.project import Project
    return await Project.create(
        db_session, organization_id=test_org.id,
        name="Test Project", website_url="https://example.com",
    )


@pytest_asyncio.fixture
async def test_brand(db_session, test_project):
    from backend.database.models.brand import Brand
    return await Brand.create(
        db_session, project_id=test_project.id, name="Acme", is_primary=True,
    )


@pytest_asyncio.fixture
async def test_prompt(db_session, test_project):
    from backend.database.models.prompt import Prompt
    return await Prompt.create(
        db_session, project_id=test_project.id, text="best crm software",
    )


@pytest_asyncio.fixture
async def seed_reference(db_session):
    """Seed one platform ('perplexity') and one country ('US')."""
    from backend.database.migrations.platform import Platform as PlatformTable
    from backend.database.migrations.country import Country as CountryTable
    from backend.utils.enums import AdapterType
    platform = PlatformTable(
        id=uuid.uuid4(), name="perplexity", display_name="Perplexity",
        adapter_type=AdapterType.SCRAPER, is_active=True,
    )
    country = CountryTable(
        id=uuid.uuid4(), code="US", name="United States", is_active=True,
    )
    db_session.add_all([platform, country])
    await db_session.commit()
    return {"platform": platform, "country": country}
