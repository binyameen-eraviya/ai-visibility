# Backend Test Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a pytest + pytest-asyncio test harness against a real Postgres test database and write integration tests covering the existing auth, project, brand, prompt, tracking-config, scrape, storage, and account-pool code (Section 4 of the hardening spec).

**Architecture:** Tests run inside the `api` container (`docker compose exec api pytest`), against a separate `*_test` Postgres database in the same `db` container. Schema is created once per session by a synchronous (psycopg2) fixture that mirrors Alembic's `import_all_migration_models()` + `Base.metadata.create_all`. Each test gets a function-scoped async engine + an `AsyncSession` bound to an outer connection transaction with `join_transaction_mode="create_savepoint"`, so the query classes' internal `commit()` calls become SAVEPOINT releases and a single outer `rollback()` gives per-test isolation. API tests drive the app through `httpx.AsyncClient` + `ASGITransport` with `get_db` overridden to the test session; auth is exercised with real JWTs minted via `AuthHandler`. External services (Playwright adapters) are mocked at the `get_adapter` seam; storage writes to a `tmp_path`.

**Tech Stack:** pytest 8.3.4, pytest-asyncio 0.24.0 (auto mode), pytest-cov 6.0.0, httpx 0.28.1 (already present), SQLAlchemy 2.0.44 async, asyncpg + psycopg2 (both already present), FastAPI 0.119.

---

## Why these design choices (read before starting)

- **Separate Postgres DB, not SQLite.** Models use `gen_random_uuid()` server defaults and Postgres `ENUM`/`JSON` types; SQLite can't run them. The spec's recommended option.
- **Savepoint isolation, not truncate.** The repository's query classes (e.g. `Project.create`) call `await db.commit()` internally. A plain transaction rollback would be defeated by those commits. SQLAlchemy 2.0's `join_transaction_mode="create_savepoint"` turns each inner `commit()` into a SAVEPOINT release inside one outer transaction that we roll back after every test. This also faithfully reproduces production semantics for `run_scrape` (which relies on a committed run row surviving a later `pool.checkout()` rollback).
- **Everything async is function-scoped.** Schema setup is a synchronous session fixture (no event loop). The async engine/session/client are function-scoped so they always run on the same per-test event loop — this sidesteps every pytest-asyncio "attached to a different loop" pitfall without needing custom `event_loop` overrides.
- **No factory-boy for data.** factory-boy's session model is synchronous and fights async SQLAlchemy. We build fixtures with the existing async query classes instead — less ceremony, exact-match to production code paths. factory-boy is still added to `requirements.txt` per the spec for future use.
- **Mock at `get_adapter`.** `run_scrape` resolves adapters via `backend.services.scrape_runner.get_adapter`. Patching that one name returns a fake adapter and exercises the real DB + storage orchestration without launching Playwright.

---

## File Structure

| File | Responsibility | Create/Modify |
|------|----------------|---------------|
| `requirements.txt` | add pytest, pytest-asyncio, pytest-cov, factory-boy | Modify |
| `pyproject.toml` | `[tool.pytest.ini_options]` config (asyncio auto mode, testpaths, pythonpath) | Create |
| `backend/tests/__init__.py` | make `backend.tests` a package | Create |
| `backend/tests/conftest.py` | DB lifecycle + all shared fixtures (`db_session`, `client`, `auth_headers`, `test_org`, `test_user`, `test_project`, `test_brand`, `test_prompt`, `seed_reference`) | Create |
| `backend/tests/test_auth.py` | signup/login/protected-route tests | Create |
| `backend/tests/test_projects.py` | project CRUD + tenancy | Create |
| `backend/tests/test_brands.py` | brand CRUD + tenancy | Create |
| `backend/tests/test_prompts.py` | prompt CRUD + tags + tenancy | Create |
| `backend/tests/test_tracking_configs.py` | tracking-config create/bulk/toggle/duplicate | Create |
| `backend/tests/test_scrape.py` | manual run (adapter mocked) + history + detail | Create |
| `backend/tests/test_storage.py` | LocalStorageService round-trip | Create |
| `backend/tests/test_account_pool.py` | checkout/quota/cooldown/release/failure | Create |

All commits go on the **`feature/test-infrastructure`** branch (already created off `develop`). Every commit message ends with the `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` trailer.

---

### Task 1: Test dependencies and pytest configuration

**Files:**
- Modify: `requirements.txt`
- Create: `pyproject.toml`

- [ ] **Step 1: Add test deps to `requirements.txt`**

Append to the end of `requirements.txt`:

```
# --- Testing (Section 4) ---
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
factory-boy==3.3.1
```

(`httpx==0.28.1` is already present — do not duplicate it.)

- [ ] **Step 2: Create `pyproject.toml` at repo root**

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["backend/tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
pythonpath = ["."]
addopts = "-ra"
```

`pythonpath = ["."]` lets the tests `import main` and `from backend... import ...` with the repo root as rootdir. `asyncio_mode = "auto"` auto-marks async tests/fixtures so we don't decorate each one.

- [ ] **Step 3: Rebuild the api image so the new deps are installed**

Run: `docker compose build api && docker compose up -d api`
Expected: build succeeds, `ai-visibility-api-1` is `Up`.

- [ ] **Step 4: Verify pytest is available in the container**

Run: `docker compose exec api pytest --version`
Expected: prints `pytest 8.3.4`.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt pyproject.toml
git commit -m "chore: add pytest test dependencies and configuration

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Test harness — conftest fixtures + smoke tests

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_smoke.py`

- [ ] **Step 1: Create `backend/tests/__init__.py`** (empty file)

```python
```

- [ ] **Step 2: Create `backend/tests/conftest.py`**

```python
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
```

- [ ] **Step 3: Create `backend/tests/test_smoke.py`** (proves the harness works end-to-end)

```python
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
```

- [ ] **Step 4: Run the smoke tests**

Run: `docker compose exec api pytest backend/tests/test_smoke.py -v`
Expected: 3 passed. If `test_db_session_is_isolated` fails, the savepoint isolation is wrong — fix conftest before continuing. If a "different event loop" error appears, confirm all async fixtures are function-scoped (no `scope="session"` on async fixtures).

- [ ] **Step 5: Commit**

```bash
git add backend/tests/__init__.py backend/tests/conftest.py backend/tests/test_smoke.py
git commit -m "test: add pytest conftest with Postgres test DB harness and smoke tests

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Auth tests

**Files:**
- Create: `backend/tests/test_auth.py`

Behavior reference: signup auto-verifies when `APP_ENV=development` (set in the container); duplicate email → 409; bad credentials → 401; missing/invalid bearer → 401.

- [ ] **Step 1: Write `backend/tests/test_auth.py`**

```python
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
```

- [ ] **Step 2: Run**

Run: `docker compose exec api pytest backend/tests/test_auth.py -v`
Expected: 6 passed. If signup returns 500, check that the container has `APP_ENV=development` and SMTP env vars set (signup imports the email service at module load).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_auth.py
git commit -m "test: add auth signup/login/guard tests

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Project tests (with tenancy)

**Files:**
- Create: `backend/tests/test_projects.py`

Routes: `POST/GET /api/projects`, `GET/PUT/DELETE /api/projects/{id}`. Cross-org access returns 404 (via `verify_project_access`).

- [ ] **Step 1: Write `backend/tests/test_projects.py`**

```python
"""Project CRUD and multi-tenancy isolation."""


async def test_create_project(client, auth_headers):
    resp = await client.post(
        "/api/projects",
        headers=auth_headers,
        json={"name": "New Project", "website_url": "https://acme.test"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "New Project"
    assert body["id"]


async def test_list_projects_returns_only_own_org(client, auth_headers, test_project):
    resp = await client.get("/api/projects", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    ids = [p["id"] for p in resp.json()]
    assert str(test_project.id) in ids


async def test_get_project_from_other_org_returns_404(
    client, other_org_headers, test_project
):
    # test_project belongs to test_org; other_org_headers is a different org.
    resp = await client.get(
        f"/api/projects/{test_project.id}", headers=other_org_headers
    )
    assert resp.status_code == 404


async def test_update_project(client, auth_headers, test_project):
    resp = await client.put(
        f"/api/projects/{test_project.id}",
        headers=auth_headers,
        json={"name": "Renamed"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "Renamed"


async def test_delete_project(client, auth_headers, test_project):
    resp = await client.delete(
        f"/api/projects/{test_project.id}", headers=auth_headers
    )
    assert resp.status_code in (200, 204)
    # Soft-deleted: it no longer appears in the list.
    listing = await client.get("/api/projects", headers=auth_headers)
    assert str(test_project.id) not in [p["id"] for p in listing.json()]
```

- [ ] **Step 2: Run**

Run: `docker compose exec api pytest backend/tests/test_projects.py -v`
Expected: 5 passed. If create/update returns a non-200 success code, adjust the assertion to the route's actual status (inspect `backend/routes/project.py`); if a real tenancy leak appears (other-org GET returns 200), that's a code bug to fix, not a test bug.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_projects.py
git commit -m "test: add project CRUD and tenancy tests

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Brand tests

**Files:**
- Create: `backend/tests/test_brands.py`

Routes: `POST/GET /api/projects/{project_id}/brands`, `PUT/DELETE .../brands/{brand_id}`. Schema: `name` (required), `aliases` (list, default []), `is_primary` (bool, default False).

- [ ] **Step 1: Write `backend/tests/test_brands.py`**

```python
"""Brand CRUD and cross-tenant isolation."""


async def test_create_primary_brand(client, auth_headers, test_project):
    resp = await client.post(
        f"/api/projects/{test_project.id}/brands",
        headers=auth_headers,
        json={"name": "Acme", "is_primary": True, "aliases": ["acme inc"]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["is_primary"] is True
    assert body["aliases"] == ["acme inc"]


async def test_create_competitor_brand(client, auth_headers, test_project):
    resp = await client.post(
        f"/api/projects/{test_project.id}/brands",
        headers=auth_headers,
        json={"name": "Globex", "is_primary": False},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_primary"] is False


async def test_list_brands_for_project(client, auth_headers, test_project, test_brand):
    resp = await client.get(
        f"/api/projects/{test_project.id}/brands", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert str(test_brand.id) in [b["id"] for b in resp.json()]


async def test_brand_from_other_org_project_returns_404(
    client, other_org_headers, test_project
):
    resp = await client.get(
        f"/api/projects/{test_project.id}/brands", headers=other_org_headers
    )
    assert resp.status_code == 404
```

- [ ] **Step 2: Run**

Run: `docker compose exec api pytest backend/tests/test_brands.py -v`
Expected: 4 passed.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_brands.py
git commit -m "test: add brand CRUD and tenancy tests

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Prompt tests

**Files:**
- Create: `backend/tests/test_prompts.py`

Routes: `POST/GET /api/projects/{project_id}/prompts`, `PUT/DELETE .../prompts/{id}`, tag add/remove. Schema: `text` (required), `topic_id` (optional), `tag_ids` (list, default []). Response includes `tags` and `topic`.

- [ ] **Step 1: Write `backend/tests/test_prompts.py`**

```python
"""Prompt CRUD, tag attach, filtering, tenancy."""


async def test_create_prompt(client, auth_headers, test_project):
    resp = await client.post(
        f"/api/projects/{test_project.id}/prompts",
        headers=auth_headers,
        json={"text": "best project management tool"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["text"] == "best project management tool"
    assert body["tags"] == []


async def test_create_prompt_with_tags(
    client, auth_headers, db_session, test_project
):
    # Seed a tag in the same project, then create a prompt referencing it.
    from backend.database.migrations.tag import Tag as TagTable
    import uuid as _uuid
    tag = TagTable(id=_uuid.uuid4(), project_id=test_project.id, name="crm")
    db_session.add(tag)
    await db_session.commit()

    resp = await client.post(
        f"/api/projects/{test_project.id}/prompts",
        headers=auth_headers,
        json={"text": "tagged prompt", "tag_ids": [str(tag.id)]},
    )
    assert resp.status_code == 200, resp.text
    tags = resp.json()["tags"]
    assert [t["name"] for t in tags] == ["crm"]


async def test_list_prompts(client, auth_headers, test_project, test_prompt):
    resp = await client.get(
        f"/api/projects/{test_project.id}/prompts", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert str(test_prompt.id) in [p["id"] for p in resp.json()]


async def test_prompt_from_other_org_returns_404(
    client, other_org_headers, test_project
):
    resp = await client.get(
        f"/api/projects/{test_project.id}/prompts", headers=other_org_headers
    )
    assert resp.status_code == 404
```

> Note: the spec lists `test_list_prompts_with_filters`. The list route (`backend/routes/prompt.py`) currently takes no filter query params, so this is implemented as `test_list_prompts`. If filter params exist on the route, extend this test to pass them.

- [ ] **Step 2: Run**

Run: `docker compose exec api pytest backend/tests/test_prompts.py -v`
Expected: 4 passed.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_prompts.py
git commit -m "test: add prompt CRUD, tag, and tenancy tests

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Tracking-config tests

**Files:**
- Create: `backend/tests/test_tracking_configs.py`

Routes: `POST /api/projects/{project_id}/tracking-configs`, `.../bulk`, `GET`, `PATCH .../{id}/toggle`. Create requires `prompt_id`, `platform_id`, `country_id`. Duplicate (prompt+platform+country) → `BadRequest`. Bulk skips duplicates.

- [ ] **Step 1: Write `backend/tests/test_tracking_configs.py`**

```python
"""Tracking-config create / bulk / duplicate / toggle."""


def _payload(prompt, platform, country):
    return {
        "prompt_id": str(prompt.id),
        "platform_id": str(platform.id),
        "country_id": str(country.id),
    }


async def test_create_tracking_config(
    client, auth_headers, test_project, test_prompt, seed_reference
):
    resp = await client.post(
        f"/api/projects/{test_project.id}/tracking-configs",
        headers=auth_headers,
        json=_payload(test_prompt, seed_reference["platform"], seed_reference["country"]),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["prompt_id"] == str(test_prompt.id)
    assert body["is_active"] is True


async def test_duplicate_tracking_config_rejected(
    client, auth_headers, test_project, test_prompt, seed_reference
):
    payload = _payload(test_prompt, seed_reference["platform"], seed_reference["country"])
    first = await client.post(
        f"/api/projects/{test_project.id}/tracking-configs",
        headers=auth_headers, json=payload,
    )
    assert first.status_code == 200, first.text
    dup = await client.post(
        f"/api/projects/{test_project.id}/tracking-configs",
        headers=auth_headers, json=payload,
    )
    assert dup.status_code == 400


async def test_bulk_create_configs(
    client, auth_headers, db_session, test_project, test_prompt, seed_reference
):
    # A second prompt so the bulk payload has two distinct scopes.
    from backend.database.models.prompt import Prompt
    prompt2 = await Prompt.create(
        db_session, project_id=test_project.id, text="second prompt"
    )
    platform, country = seed_reference["platform"], seed_reference["country"]
    resp = await client.post(
        f"/api/projects/{test_project.id}/tracking-configs/bulk",
        headers=auth_headers,
        json={"configs": [
            _payload(test_prompt, platform, country),
            _payload(prompt2, platform, country),
        ]},
    )
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 2


async def test_toggle_config_active(
    client, auth_headers, db_session, test_project, test_prompt, seed_reference
):
    from backend.database.models.tracking_config import TrackingConfig
    cfg = await TrackingConfig.create(
        db_session, project_id=test_project.id, prompt_id=test_prompt.id,
        platform_id=seed_reference["platform"].id,
        country_id=seed_reference["country"].id,
    )
    assert cfg.is_active is True
    resp = await client.patch(
        f"/api/projects/{test_project.id}/tracking-configs/{cfg.id}/toggle",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_active"] is False
```

- [ ] **Step 2: Run**

Run: `docker compose exec api pytest backend/tests/test_tracking_configs.py -v`
Expected: 4 passed. If the duplicate case returns 500 instead of 400, check how `backend/routes/tracking_config.py` maps `BadRequest` — that's a route-level mapping bug to fix.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_tracking_configs.py
git commit -m "test: add tracking-config create/bulk/toggle tests

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Scrape tests (adapter mocked)

**Files:**
- Create: `backend/tests/test_scrape.py`

`run_now` resolves the adapter through `backend.services.scrape_runner.get_adapter`. We patch that to a fake adapter returning a `RawAnswer`, point `SCRAPE_STORAGE_DIR` at `tmp_path`, and assert the orchestration (DB run row + stored capture). No accounts are seeded, so `pool.checkout()` raises `NoAccountAvailable` and the run proceeds account-less — exactly the production path.

- [ ] **Step 1: Write `backend/tests/test_scrape.py`**

```python
"""Manual scrape run, history, and detail — adapter mocked, storage in tmp."""

import pytest

from backend.workers.scrapers.base_adapter import RawAnswer


class _FakeAdapter:
    async def run_prompt(self, prompt_text, account=None, proxy=None):
        return RawAnswer(
            answer_text="Acme is a top choice.",
            sources=["https://review.test/acme"],
            metadata={"model": "fake-1"},
        )


@pytest.fixture
def mock_adapter(monkeypatch, tmp_path):
    # Route the runner's adapter lookup to the fake, and storage to tmp.
    monkeypatch.setattr(
        "backend.services.scrape_runner.get_adapter",
        lambda platform_name: _FakeAdapter(),
    )
    monkeypatch.setenv("SCRAPE_STORAGE_DIR", str(tmp_path))
    return tmp_path


async def test_manual_run_creates_scrape_run_record(
    client, auth_headers, test_project, test_prompt, seed_reference, mock_adapter
):
    resp = await client.post(
        f"/api/projects/{test_project.id}/prompts/{test_prompt.id}/run",
        headers=auth_headers,
        json={"platform_id": str(seed_reference["platform"].id)},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "SUCCESS"
    assert body["id"]


async def test_run_history_returns_runs(
    client, auth_headers, test_project, test_prompt, seed_reference, mock_adapter
):
    # Trigger one run, then read the history.
    await client.post(
        f"/api/projects/{test_project.id}/prompts/{test_prompt.id}/run",
        headers=auth_headers,
        json={"platform_id": str(seed_reference["platform"].id)},
    )
    resp = await client.get(
        f"/api/projects/{test_project.id}/runs", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) >= 1


async def test_run_detail_returns_stored_data(
    client, auth_headers, test_project, test_prompt, seed_reference, mock_adapter
):
    run = await client.post(
        f"/api/projects/{test_project.id}/prompts/{test_prompt.id}/run",
        headers=auth_headers,
        json={"platform_id": str(seed_reference["platform"].id)},
    )
    run_id = run.json()["id"]
    resp = await client.get(
        f"/api/projects/{test_project.id}/runs/{run_id}", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["raw"]["answer_text"] == "Acme is a top choice."
```

> Isolation note: the run row is created and committed before `pool.checkout()` runs. Under `join_transaction_mode="create_savepoint"` that commit is a SAVEPOINT release, so the later `NoAccountAvailable` rollback inside `checkout()` does not erase the run — matching production. All of it is still undone by the per-test outer rollback.

- [ ] **Step 2: Run**

Run: `docker compose exec api pytest backend/tests/test_scrape.py -v`
Expected: 3 passed. If status comes back `FAILED`, print `body["error"]` — most likely the adapter patch target is wrong (must be `backend.services.scrape_runner.get_adapter`, where it is *used*, not the registry module).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_scrape.py
git commit -m "test: add scrape run/history/detail tests with mocked adapter

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Storage tests

**Files:**
- Create: `backend/tests/test_storage.py`

`LocalStorageService(storage_dir=...)` writes `{dir}/{project_id}/{YYYY-MM-DD}/{run_id}.json`.

- [ ] **Step 1: Write `backend/tests/test_storage.py`**

```python
"""LocalStorageService round-trip, directory creation, path format."""

import uuid
from datetime import datetime, timezone

from backend.services.storage import LocalStorageService


async def test_local_storage_save_and_retrieve(tmp_path):
    storage = LocalStorageService(storage_dir=str(tmp_path))
    project_id, run_id = uuid.uuid4(), uuid.uuid4()
    data = {"answer_text": "hello", "sources": ["https://a.test"]}
    path = await storage.save_raw(project_id, run_id, data)
    assert await storage.get_raw(path) == data


async def test_storage_creates_directories(tmp_path):
    storage = LocalStorageService(storage_dir=str(tmp_path))
    project_id, run_id = uuid.uuid4(), uuid.uuid4()
    path = await storage.save_raw(project_id, run_id, {"k": "v"})
    from pathlib import Path
    assert Path(path).exists()
    assert Path(path).parent.is_dir()


async def test_storage_path_format(tmp_path):
    storage = LocalStorageService(storage_dir=str(tmp_path))
    project_id, run_id = uuid.uuid4(), uuid.uuid4()
    path = await storage.save_raw(project_id, run_id, {"k": "v"})
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert str(project_id) in path
    assert today in path
    assert path.endswith(f"{run_id}.json")
```

- [ ] **Step 2: Run**

Run: `docker compose exec api pytest backend/tests/test_storage.py -v`
Expected: 3 passed.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_storage.py
git commit -m "test: add local storage service tests

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: Account-pool tests

**Files:**
- Create: `backend/tests/test_account_pool.py`

`AccountPool(db)` methods: `checkout`, `release` (cooldown), `report_failure` (DISABLE after 3, or `ban=True` → BANNED). Accounts created via `ScrapeAccount.create(db, platform_id, email, cookies, daily_quota_limit)`.

> Spec wording note: the spec says "bans after threshold". The code DISABLES (status `DISABLED`) after `FAILURE_DISABLE_THRESHOLD = 3` consecutive failures, and only BANS when `report_failure(ban=True)`. Tests assert the actual behavior.

- [ ] **Step 1: Write `backend/tests/test_account_pool.py`**

```python
"""Account pool checkout / quota / cooldown / release / failure handling."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from backend.workers.pool.account_pool import AccountPool, NoAccountAvailable
from backend.utils.enums import ScrapeAccountStatus
from backend.database.models.scrape_account import ScrapeAccount


@pytest.fixture
async def platform_id(seed_reference):
    return seed_reference["platform"].id


async def test_checkout_returns_least_recently_used(db_session, platform_id):
    older = await ScrapeAccount.create(db_session, platform_id, "a@test.com")
    newer = await ScrapeAccount.create(db_session, platform_id, "b@test.com")
    # Make `older` the least-recently-used.
    from sqlalchemy import update
    from backend.database.migrations.scrape_account import ScrapeAccount as T
    now = datetime.now(timezone.utc)
    await db_session.execute(
        update(T).where(T.id == older.id).values(last_used_at=now - timedelta(hours=2))
    )
    await db_session.execute(
        update(T).where(T.id == newer.id).values(last_used_at=now)
    )
    await db_session.commit()

    pool = AccountPool(db_session)
    chosen = await pool.checkout(platform_id)
    assert chosen.id == older.id


async def test_checkout_respects_quota(db_session, platform_id):
    acct = await ScrapeAccount.create(
        db_session, platform_id, "q@test.com", daily_quota_limit=1
    )
    # Exhaust the quota.
    from sqlalchemy import update
    from backend.database.migrations.scrape_account import ScrapeAccount as T
    await db_session.execute(
        update(T).where(T.id == acct.id).values(daily_quota_used=1)
    )
    await db_session.commit()

    pool = AccountPool(db_session)
    with pytest.raises(NoAccountAvailable):
        await pool.checkout(platform_id)


async def test_checkout_respects_cooldown(db_session, platform_id):
    acct = await ScrapeAccount.create(db_session, platform_id, "c@test.com")
    from sqlalchemy import update
    from backend.database.migrations.scrape_account import ScrapeAccount as T
    future = datetime.now(timezone.utc) + timedelta(minutes=30)
    await db_session.execute(
        update(T).where(T.id == acct.id).values(
            status=ScrapeAccountStatus.COOLDOWN, cooldown_until=future
        )
    )
    await db_session.commit()

    pool = AccountPool(db_session)
    with pytest.raises(NoAccountAvailable):
        await pool.checkout(platform_id)


async def test_release_sets_cooldown(db_session, platform_id):
    acct = await ScrapeAccount.create(db_session, platform_id, "r@test.com")
    pool = AccountPool(db_session)
    released = await pool.release(acct.id)
    assert released.status == ScrapeAccountStatus.COOLDOWN
    assert released.cooldown_until is not None


async def test_report_failure_disables_after_threshold(db_session, platform_id):
    acct = await ScrapeAccount.create(db_session, platform_id, "f@test.com")
    pool = AccountPool(db_session)
    for _ in range(3):
        result = await pool.report_failure(acct.id)
    assert result.status == ScrapeAccountStatus.DISABLED


async def test_report_failure_ban_sets_banned(db_session, platform_id):
    acct = await ScrapeAccount.create(db_session, platform_id, "b2@test.com")
    pool = AccountPool(db_session)
    result = await pool.report_failure(acct.id, ban=True)
    assert result.status == ScrapeAccountStatus.BANNED
```

- [ ] **Step 2: Run**

Run: `docker compose exec api pytest backend/tests/test_account_pool.py -v`
Expected: 6 passed. `checkout` uses `SELECT ... FOR UPDATE SKIP LOCKED`, which works fine inside the test transaction.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_account_pool.py
git commit -m "test: add account pool checkout/quota/cooldown/failure tests

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 11: Full suite + coverage

**Files:** none (verification only)

- [ ] **Step 1: Run the whole suite**

Run: `docker compose exec api pytest backend/tests/ -v`
Expected: all tests pass (smoke 3 + auth 6 + projects 5 + brands 4 + prompts 4 + tracking 4 + scrape 3 + storage 3 + account pool 6 = **38 tests**).

- [ ] **Step 2: Run with coverage**

Run: `docker compose exec api pytest backend/tests/ --cov=backend --cov-report=term-missing`
Expected: a coverage table prints; interactors/services/models exercised above show meaningful coverage. No threshold is enforced yet.

- [ ] **Step 3: Final commit (if anything changed during fixes)**

```bash
git add -A
git commit -m "test: verify full backend test suite passes

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**Spec coverage (Section 4):**
- 4a deps (pytest/pytest-asyncio/pytest-cov/factory-boy; httpx already present) → Task 1 ✓
- 4b conftest fixtures (`db_session`, `client`, `auth_headers`, `test_project`, `test_brand`, `test_prompt`, seed reference data) → Task 2 ✓ (separate Postgres test DB, per the spec's recommended option; `TEST_DATABASE_NAME` env var supported)
- 4b pytest config (asyncio auto mode, testpaths, python_files/functions) → Task 1 `pyproject.toml` ✓
- 4c test files test_auth/test_projects/test_brands/test_prompts/test_tracking_configs/test_scrape/test_storage/test_account_pool → Tasks 3–10 ✓
- 4d run commands (all / coverage / single file) → Tasks 3–11 ✓
- Mock the adapter, don't launch Playwright → Task 8 ✓

**Deviations (documented):**
- `test_list_prompts_with_filters` → `test_list_prompts` (route has no filter params today).
- `test_report_failure_bans_after_threshold` → `test_report_failure_disables_after_threshold` + `test_report_failure_ban_sets_banned` (code disables after 3, bans only on `ban=True`).
- Data built via async query classes instead of factory-boy (async incompatibility); factory-boy still installed per spec.

**Placeholder scan:** none — every test file and the conftest are complete and runnable.

**Type/name consistency:** fixture names (`db_session`, `client`, `auth_headers`, `other_org_headers`, `test_org`, `test_user`, `test_project`, `test_brand`, `test_prompt`, `seed_reference`) are defined in conftest (Task 2) and referenced consistently in Tasks 3–10. Query-class signatures (`Organization.create`, `User.create`, `Project.create`, `Brand.create`, `Prompt.create`, `TrackingConfig.create`, `ScrapeAccount.create`) match the live code read during planning.

**First-run risk notes for the executor:** success status codes for create/update routes are asserted as `200` (FastAPI default). If any route declares `status_code=201`, adjust that single assertion. Genuine failures (tenancy leaks, wrong error mapping) are code bugs to fix, not test edits — per the spec.
