# Security Audit — Phase 1 (Section 7)

Date: 2026-06-11. Scope: backend FastAPI app, docker-compose, config. This is a
baseline review of the three Section 7 items; it is not a full pen-test.

## 7a — CORS

- Origins come from the `CORS_ALLOWED_ORIGINS` env var (root `.env` → injected
  into the api container; also read by `main.py`). **Never `"*"`.**
- `allow_credentials=True` with an explicit allow-list (not wildcard).
- **Hardened:** origins are now stripped of whitespace and empty entries are
  dropped, so a blank/trailing-comma value can't create a bogus `""` origin
  (`main.py`).
- **Verified:** request with `Origin: http://localhost:3001` → header
  `access-control-allow-origin: http://localhost:3001`; request with a
  non-listed origin → no `Access-Control-Allow-Origin` header (browser blocks).

**Verdict: PASS.**

## 7b — Secrets

Scanned the repo (excluding `node_modules`) for hardcoded credentials, API
keys, tokens, and private keys.

- DB credentials (`POSTGRES_*`), JWT (`JWT_SECRET_KEY`/`JWT_ALGORITHM`/
  `JWT_TOKEN_EXPIRE_DAYS`), Redis/Celery URLs, SMTP, LLM (`LLM_API_KEY`), and
  the seed super-admin (`SUPER_ADMIN_EMAIL`/`SUPER_ADMIN_PASSWORD`) are **all
  read from environment variables** (`backend/database/db.py`,
  `backend/utils/constants.py`, `backend/database/seed.py`).
- No private keys, AWS/Slack/OpenAI/GitHub token patterns, or hardcoded
  passwords found.
- `.env` files are gitignored (`.env`, `.env.*`, `**/.env*`), with
  `*.env.example` explicitly un-ignored. **No real `.env` is tracked** in git.
- The only literal "token" values are non-secret placeholders: the seeded
  super-admin's `signup_token="super-admin"` and test fixtures' `signup_token`.
  These are verification tokens, not credentials.

**Verdict: PASS.**

## 7c — SQL injection

The app uses the SQLAlchemy ORM (`select(...)`, model query classes) with bound
parameters throughout — including JSON attribute filters
(`UserTable.attrs["reset_token"].as_string() == reset_token`). No string-built
SQL in application code.

Raw `text(...)` usages reviewed:
- Model defaults / Alembic migrations: `sa.text('gen_random_uuid()')`,
  `sa.text('CURRENT_TIMESTAMP')`, etc. — **static literals**, no interpolation.
- `/health`: `text("SELECT 1")` — static.
- `backend/tests/conftest.py`: `text(f'CREATE DATABASE "{TEST_DB}"')` — the only
  f-string-built SQL. **Test-only**, the name is derived from env
  (`TEST_DATABASE_NAME`/`POSTGRES_DB`), not user input, and `CREATE DATABASE`
  cannot take a bind parameter. Not reachable from the running app.

No `.execute()` with `%`/`.format()`/f-string interpolation in app code.

**Verdict: PASS** (the one f-string SQL is test-only and not user-influenced).

## Summary

| Item | Verdict | Action taken |
|------|---------|--------------|
| 7a CORS | PASS | Hardened origin parsing (strip/filter) |
| 7b Secrets | PASS | None needed — all secrets env-driven, `.env` gitignored |
| 7c SQL injection | PASS | None needed — ORM bind params; only static/test raw SQL |
