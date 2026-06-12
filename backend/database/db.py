import os
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Loads the root .env when running outside Docker. Inside containers,
# docker-compose injects the same variables via `env_file: .env`, so this
# is a no-op there (no .env file is copied into images).
load_dotenv()


def _require(name: str) -> str:
    """Fetch a required env var, failing fast with a clear message if unset."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Required environment variable '{name}' is not set. "
            f"Copy .env.example to .env at the repo root and fill it in."
        )
    return value


# Single source of truth: DATABASE_URL from the root .env (host "db" inside
# Docker). Falls back to a localhost URL built from POSTGRES_* when running
# directly on the host without DATABASE_URL set.
DATABASE_URL = os.getenv("DATABASE_URL") or (
    f"postgresql+asyncpg://{_require('POSTGRES_USER')}:"
    f"{_require('POSTGRES_PASSWORD')}@localhost:5432/{_require('POSTGRES_DB')}"
)

# Synchronous URL (Alembic migrations, test harness). Derived from
# DATABASE_URL when not provided explicitly.
SYNC_DATABASE_URL = os.getenv("SYNC_DATABASE_URL") or DATABASE_URL.replace("+asyncpg", "")

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# Dependency
async def get_db():
    async with async_session() as session:
        yield session
