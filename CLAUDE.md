# AIScope - Claude Code Instructions

## Git Workflow
- After completing any task, stage and commit changes with a conventional commit message
- Commit format: `type: short description`
- Types: `feat` (new feature), `fix` (bug fix), `refactor` (code restructure), `test` (adding tests), `docs` (documentation), `chore` (tooling, deps, config)
- Never commit `.env` files or any file containing secrets, API keys, or passwords
- Never push automatically, I will push manually after reviewing
- Never force-push
- Commit on the current branch only
- If no branch has been specified, ask which branch to use before making changes

## Code Conventions
- Backend: FastAPI + async SQLAlchemy, follow the existing interactor pattern (one file per action in `backend/interactors/`)
- Migrations go in `backend/database/migrations/`, models (query classes) in `backend/database/models/`
- Schemas in `backend/utils/schema/request.py` and `response.py`
- Routes in `backend/routes/`, registered in `main.py`
- Frontend: React + Vite, Tailwind CSS, TanStack Query for data fetching, Zustand for global state
- API client in `frontend/src/config/api.js`, hooks in `frontend/src/hooks/`
- All database queries must filter by `organization_id` for multi-tenancy
- All platform scrapers must implement `BasePlatformAdapter` interface
- Storage, LLM provider, and scraper implementations must be behind abstract interfaces for swappability

## Testing
- Write tests alongside features when asked
- Use pytest + pytest-asyncio for backend tests
- Mock external services (Playwright, LLM APIs) in tests, never hit real services
- Test files go in `backend/tests/`

## Environment
- Docker Compose stack: api (port 8001), frontend (port 3001), db (Postgres 16), redis, worker (Celery), beat
- Real `.env` files are gitignored, `.env.example` files are committed
- All secrets and config come from environment variables, never hardcoded

## Project Context
- This is an AI Search Visibility Tracking Platform (codename AIScope)
- Phase 1: tracking and analytics (current)
- Phase 2: solutions/execution layer (future)
- Architecture doc: see `AI-Visibility-Platform-Architecture-Phase1.md` in the project root
