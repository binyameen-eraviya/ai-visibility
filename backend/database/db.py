import os
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()


def _require(name: str) -> str:
    """Fetch a required env var, failing fast with a clear message if unset."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Required environment variable '{name}' is not set. "
            f"See backend/.env.example and copy it to backend/.env."
        )
    return value


# Inside Docker the DB host is the "db" compose service; locally it falls back
# to localhost (ENVIRONMENT must be "production" for the in-container case).
SERVER = "db" if os.getenv("ENVIRONMENT") == "production" else "localhost"

DATABASE_URL = (
    f"postgresql+asyncpg://{_require('POSTGRES_USER')}:"
    f"{_require('POSTGRES_PASSWORD')}@{SERVER}:5432/{_require('POSTGRES_DB')}"
)

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# Dependency
async def get_db():
    async with async_session() as session:
        yield session