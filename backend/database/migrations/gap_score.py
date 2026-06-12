import uuid

from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
 DATE,
 INTEGER,
 TEXT,
 TIMESTAMP,
 Column,
 ForeignKey,
 Index,
 UniqueConstraint,
 text,
)

from backend.database.db import Base
from backend.database.migrations.project import Project  # noqa: F401  (mapper registration)


class GapScore(Base):
    """Per-domain content-gap score for a project on a day.

    A "gap" is a domain that gets the AI to cite competitors while leaving the
    client's own brand unmentioned -- i.e. content the client should be on but
    isn't. Higher gap_score = more chats where that happened = bigger gap.
    """

    __tablename__ = "gap_scores"
    __table_args__ = (
        UniqueConstraint("project_id", "domain", "date", name="uq_gap_scores_project_domain_date"),
        Index("ix_gap_scores_project_date", "project_id", "date"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    domain = Column(TEXT, nullable=False)
    date = Column(DATE, nullable=False)
    # Chats where a competitor was mentioned AND this domain was cited AND the
    # client's own brand was NOT mentioned.
    gap_score = Column(INTEGER, nullable=False, default=0)
    # Total competitor brand mentions across the chats that cited this domain.
    competitor_mentions = Column(INTEGER, nullable=False, default=0)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
    )
