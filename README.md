# AI Visibility Tracking Platform

Track how brands appear across AI answer engines (ChatGPT, Perplexity, Gemini, Google AI Overviews, Copilot). Built on the org FastAPI boilerplate: FastAPI + React + PostgreSQL + Alembic, extended with Celery + Redis workers and Playwright scraping.

## Services (docker compose)

- `db` - Postgres 16
- `redis` - Celery broker/result backend
- `api` - FastAPI (thin: CRUD, reports, enqueue jobs)
- `worker` - Celery worker (queues: scrape, parse, aggregate; Playwright installed)
- `beat` - Celery Beat scheduler (daily runs, from Milestone 4)
- `frontend` - React + Vite

## Setup

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Add tables in `backend/database/migrations/`, query classes in `backend/database/models/`, business logic in `backend/interactors/`, routes in `backend/routes/`, workers in `backend/workers/`.

```bash
docker compose run --rm api alembic revision --autogenerate -m "describe_change"
docker compose up --build
```

The initial migration (`backend/alembic/versions/8f2c41d9a0b1_initial_schema.py`) creates all 18 tables and is applied automatically on boot by the entrypoint. Seed the reference data (super admin, platforms, countries) once after first boot:

```bash
docker compose run --rm api python -m backend.database.seed
```

API: http://localhost:8001
Frontend: http://localhost:3001

## Verify the worker is wired up

```bash
docker compose exec api python -c "from backend.workers.tasks import ping; print(ping.delay().get(timeout=10))"
# -> pong
```

## Layout additions over the boilerplate

```
backend/workers/
  celery_app.py        # Celery app, queues, beat schedule
  tasks.py             # diagnostic ping task
  scrapers/            # BasePlatformAdapter + per-platform adapters (M2, M5)
  parsers/             # mention/sentiment/source extraction (M3)
  aggregator/          # daily_metrics roll-up (M6)
  pool/                # account + proxy pool managers (M2, M4)
```

Raw scrape captures go to the `scrape_storage` Docker volume at `/app/storage/scrapes/{project_id}/{date}/{run_id}.json` (behind a storage service interface, swappable to S3 later).
