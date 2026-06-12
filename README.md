# AI Visibility Tracking Platform (AIScope)

Track how brands appear across AI answer engines (ChatGPT, Perplexity, Gemini, Google AI Overviews, Copilot). FastAPI + React + PostgreSQL + Alembic, extended with Celery + Redis workers and Playwright scraping.

**Architecture:** A thin FastAPI API handles CRUD, reports, and triggering scrape runs; raw answers are captured by platform adapters (behind a `BasePlatformAdapter` interface), parsed for mentions/sentiment/sources, and rolled up into daily metrics. Storage, LLM provider, and scrapers all sit behind swappable interfaces. Phase 1 is tracking + analytics. Full design: [`AI-Visibility-Platform-Architecture-Phase1.md`](AI-Visibility-Platform-Architecture-Phase1.md).

---

## Prerequisites

- **Docker** + **Docker Compose** (the whole stack runs in containers)
- **Git**
- **Node.js 20+** — only if you want to run the frontend outside Docker
- **Windows:** the helper scripts in [`scripts/`](scripts/) are PowerShell (`.ps1`). On macOS/Linux run the underlying `docker compose` commands directly (each script is a thin wrapper).

---

## Quick start

```bash
# 1. Copy the single env template (then edit secrets in .env)
cp .env.example .env

# 2. Build + start the stack and seed reference data
#    Windows (PowerShell):
./scripts/dev-up.ps1
#    macOS/Linux (or no scripts):
docker compose up -d --build
docker compose run --rm api python -m backend.database.seed
```

Then open:

- **API docs (Swagger):** http://localhost:8001/docs
- **API docs (ReDoc):** http://localhost:8001/redoc
- **Frontend:** http://localhost:3001

Migrations are applied automatically on api boot by the entrypoint; seeding (super admin, platforms, countries) is idempotent and safe to re-run.

---

## Services (docker compose)

| Service | Purpose | Default `up`? |
|---------|---------|---------------|
| `db` | Postgres 16 | yes |
| `redis` | Celery broker / result backend | yes |
| `api` | FastAPI (CRUD, reports, trigger runs) — host port **8001** | yes |
| `frontend` | React + Vite — host port **3001** | yes |
| `worker` | Celery worker (scrape/parse/aggregate queues) | only with `--profile worker` |
| `beat` | Celery Beat scheduler (daily runs, M4+) | only with `--profile worker` |

`worker` and `beat` are behind the **`worker` profile** so the common dev loop (`docker compose up`) stays fast. Milestone 2 runs scrapes synchronously inside the api process, so they aren't needed for most work. Start them with `docker compose --profile worker up -d` (or `./scripts/dev-up.ps1 -Worker`).

---

## Helper scripts (`scripts/`)

| Script | What it does |
|--------|--------------|
| `dev-up.ps1` | Build + start the core stack and seed data. `-Worker` also starts worker/beat. |
| `dev-down.ps1` | Stop the stack (named volumes preserved). |
| `dev-logs.ps1 [services...]` | Follow logs (defaults to `api`). |
| `test.ps1 [pytest args...]` | Run the backend test suite in the api container with coverage. |
| `reset-db.ps1` | **Destructive:** wipe the DB volume, recreate + seed. Asks for confirmation (`-Force` to skip). |

---

## Running tests

The backend suite (pytest + pytest-asyncio) runs inside the api container against a separate `aiscope_test` Postgres database:

```bash
# Windows
./scripts/test.ps1

# Any platform
docker compose exec api pytest backend/tests/ -v
docker compose exec api pytest backend/tests/ --cov=backend --cov-report=term-missing
docker compose exec api pytest backend/tests/test_auth.py -v   # a single file
```

Tests mock external services (Playwright, SMTP) — they never hit real endpoints.

---

## Branching workflow

- Feature branches off **`develop`** (e.g. `feature/<name>`).
- Open a PR into `develop`; `develop` merges to `main` for releases.
- Conventional commit messages: `type: short description` (`feat`, `fix`, `refactor`, `test`, `docs`, `chore`).
- Never commit `.env` files or secrets. Never force-push.

---

## Environment variables

One `.env` at the repo root configures everything. The real `.env` is gitignored; `.env.example` is the committed template. Docker Compose injects it into every service via `env_file: .env`. Running the backend outside Docker, `load_dotenv()` picks up the same root file (change the `db`/`redis` hosts in the URLs to `localhost`).

| Variable | Required | Purpose |
|----------|----------|---------|
| `DATABASE_URL` | yes | Async SQLAlchemy URL (host `db` inside Docker, `localhost` outside) |
| `SYNC_DATABASE_URL` | no | Sync URL for Alembic/tests (derived from `DATABASE_URL` if unset) |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | yes | Initialize the Postgres container; also the fallback URL parts outside Docker |
| `JWT_SECRET_KEY` / `JWT_ALGORITHM` | yes | JWT signing — set a strong random secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | yes | Access-token lifetime in minutes (`1440` = 1 day) |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | yes | Redis URLs (used by worker/beat) |
| `LLM_API_KEYS` / `LLM_API_KEY` / `LLM_MODEL` / `GEMINI_API_MODEL` / `GEMINI_SCRAPER_API_KEY` | from M3 | Gemini/LLM config — free keys at https://aistudio.google.com/apikey (comma-separate `LLM_API_KEYS` for rotation) |
| `SCRAPE_STORAGE_DIR` | yes | Raw-capture storage root (Docker volume) |
| `APP_ENV` | yes | `development` auto-verifies new signups (no email). Never `development` in a real deployment |
| `DEBUG` / `LOG_LEVEL` | no | Diagnostics / log verbosity |
| `CORS_ORIGINS` | yes | Comma-separated allowed origins (read by `main.py`) |
| `SMTP_SERVER` / `SMTP_PORT` / `SMTP_EMAIL` / `SMTP_APP_PASSWORD` | yes* | SMTP config. Placeholders let the app boot; real values only needed to actually send email |
| `FE_URL` | yes | Frontend URL used in email links |
| `SUPER_ADMIN_EMAIL` / `SUPER_ADMIN_PASSWORD` | yes | Seeded super-admin credentials |
| `PORT_BACKEND` / `PORT_FRONTEND` | yes | Host ports compose maps to api:8000 / frontend:80 |
| `VITE_API_URL` | yes | Baked into the frontend image at build time (compose passes it as a build arg) |
| `TEST_DATABASE_NAME` | no | Override the test DB name (default `{POSTGRES_DB}_test`) |

\* The api raises "SMTP credentials not configured" at startup if `SMTP_EMAIL`/`SMTP_APP_PASSWORD` are empty — keep the placeholders even if you don't send email.

---

## Smoke test the API

```bash
# Signup (field is user_name, not name). With APP_ENV=development the user is
# auto-verified and can log in immediately.
curl -X POST http://localhost:8001/api/signup \
  -H "Content-Type: application/json" \
  -d '{"user_name": "Test User", "email": "test@example.com", "password": "TestPass123!", "organization_name": "Test Org"}'

# Login -> { "user": {...}, "access_token": "..." }
curl -X POST http://localhost:8001/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "TestPass123!"}'
```

If `APP_ENV` is not `development`, new users verify via the emailed link, or a `SUPER_ADMIN` verifies them: `POST /api/admin/users/{user_id}/verify` with a bearer token.

When the worker profile is running, verify Celery is wired up:

```bash
docker compose --profile worker exec api python -c "from backend.workers.tasks import ping; print(ping.delay().get(timeout=10))"
# -> pong
```

---

## Troubleshooting

- **Port already in use (8001 / 3001 / 5432):** change `PORT_BACKEND`/`PORT_FRONTEND` in `.env`, or stop the conflicting process. Postgres/Redis are not published to the host.
- **Line endings (Windows):** `.gitattributes` enforces LF so `entrypoint.sh`/`nginx.conf` work in Linux containers. If a shell script fails with `\r` errors, ensure your editor isn't re-adding CRLF and re-checkout.
- **Playwright Chromium download** is baked into the api/worker images at build time; a slow first `--build` is expected.
- **`api` keeps restarting / "SMTP credentials not configured":** fill the `SMTP_*` placeholders in the root `.env` (any non-empty values let it boot).
- **`worker`/`beat` didn't start:** they're behind the `worker` profile — use `docker compose --profile worker up -d` or `./scripts/dev-up.ps1 -Worker`.
- **Clean slate:** `./scripts/reset-db.ps1` (or `docker compose down -v && docker compose up -d`) wipes volumes and re-seeds.

---

## Layout additions over the boilerplate

```
backend/workers/
  celery_app.py        # Celery app, queues, beat schedule
  tasks.py             # diagnostic ping task
  scrapers/            # BasePlatformAdapter + per-platform adapters (M2, M5)
  parsers/             # mention/sentiment/source extraction (M3)
  aggregator/          # daily_metrics roll-up (M6)
  pool/                # account + proxy pool managers (M2, M4)
backend/tests/         # pytest suite (conftest harness + integration tests)
scripts/               # PowerShell dev helpers
```

Raw scrape captures go to the `scrape_storage` Docker volume at `/app/storage/scrapes/{project_id}/{date}/{run_id}.json` (behind a storage service interface, swappable to S3 later).
