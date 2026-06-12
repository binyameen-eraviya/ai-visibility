import uuid

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
 BOOLEAN,
 TEXT,
 TIMESTAMP,
 Column,
 ForeignKey,
 text,
)

from backend.database.db import Base
from backend.database.migrations.scrape_run import ScrapeRun  # noqa: F401  (mapper registration)

class Answer(Base):
    """Parsed output: one answer per successful scrape run."""

    __tablename__ = "answers"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    scrape_run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("scrape_runs.id"),
        unique=True,
        nullable=False,
    )
    answer_text = Column(TEXT, nullable=False)
    # True if the AI performed a web search for this answer (cited URLs present).
    web_search_used = Column(BOOLEAN, nullable=True)
    parsed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # many-to-one (effectively one-to-one) relationship
    scrape_run = relationship("ScrapeRun")
