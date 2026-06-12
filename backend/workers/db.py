"""Database access for Celery tasks.

Tasks run outside FastAPI's request/dependency lifecycle, so they can't use the
`get_db` dependency -- they open their own sessions here.

Why a dedicated engine: each task wraps its async work in `asyncio.run()`, which
spins up a fresh event loop per task. SQLAlchemy's default pooled connections are
bound to the loop that created them, so reusing the API's pooled engine across
task loops raises "Future attached to a different loop". A NullPool engine opens
and closes a connection per checkout, so nothing is shared across loops.
"""

import asyncio
from contextlib import asynccontextmanager

from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from backend.database.db import DATABASE_URL

# NullPool: no cross-event-loop connection reuse (see module docstring).
task_engine = create_async_engine(DATABASE_URL, echo=False, poolclass=NullPool)
task_session = sessionmaker(task_engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_task_db():
    """Yield a task-scoped AsyncSession; commit on success, rollback on error.

    Service/query code commits internally, so the trailing commit here is usually
    a no-op -- it just guarantees nothing is left dangling.
    """
    async with task_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def run_async(coro):
    """Run an async coroutine to completion from a synchronous Celery task."""
    return asyncio.run(coro)
