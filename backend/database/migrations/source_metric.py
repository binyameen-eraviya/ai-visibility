import uuid

from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy import (
 DATE,
 FLOAT,
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
from backend.utils.enums import SourceType, UrlType
from backend.database.migrations.project import Project  # noqa: F401  (mapper registration)

class SourceMetric(Base):
    """Pre-aggregated daily citation counts per domain."""

    __tablename__ = "source_metrics"
    __table_args__ = (
        UniqueConstraint("project_id", "domain", "date", name="uq_source_metrics_project_domain_date"),
        Index("ix_source_metrics_project_date", "project_id", "date"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    domain = Column(TEXT, nullable=False)
    source_type = Column(
        ENUM(SourceType, name="source_type"),
        nullable=False,
        server_default=SourceType.OTHER.value,
    )
    # Dominant page type cited for this domain (most common across the day).
    url_type = Column(
        ENUM(UrlType, name="url_type"),
        nullable=False,
        server_default=UrlType.OTHER.value,
    )
    date = Column(DATE, nullable=False)
    citation_count = Column(INTEGER, nullable=False, default=0)
    # This domain's citations / all citations that day (0..1).
    retrieved_pct = Column(FLOAT, nullable=False, default=0.0, server_default=text("0"))
    # Avg times this domain is cited per chat in which it appears (>= 1.0).
    citation_rate = Column(FLOAT, nullable=False, default=0.0, server_default=text("0"))
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
    )
