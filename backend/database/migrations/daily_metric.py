import uuid

from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
 DATE,
 FLOAT,
 INTEGER,
 TIMESTAMP,
 Column,
 ForeignKey,
 Index,
 UniqueConstraint,
 text,
)

from backend.database.db import Base
from backend.database.migrations.project import Project  # noqa: F401  (mapper registration)
from backend.database.migrations.brand import Brand  # noqa: F401  (mapper registration)
from backend.database.migrations.platform import Platform  # noqa: F401  (mapper registration)
from backend.database.migrations.country import Country  # noqa: F401  (mapper registration)

class DailyMetric(Base):
    """Pre-aggregated daily metrics. The dashboard reads ONLY this table."""

    __tablename__ = "daily_metrics"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "brand_id", "platform_id", "country_id", "date",
            name="uq_daily_metrics_scope_date",
        ),
        Index("ix_daily_metrics_project_date", "project_id", "date"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    platform_id = Column(UUID(as_uuid=True), ForeignKey("platforms.id"), nullable=False)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=False)
    date = Column(DATE, nullable=False)
    visibility_pct = Column(FLOAT, nullable=False, default=0.0)
    avg_position = Column(FLOAT, nullable=True)
    avg_sentiment = Column(FLOAT, nullable=True)
    share_of_voice = Column(FLOAT, nullable=False, default=0.0)
    total_runs = Column(INTEGER, nullable=False, default=0)
    mention_count = Column(INTEGER, nullable=False, default=0)
    # Share of the day's chats (for this scope) where the AI used a web search.
    web_search_pct = Column(FLOAT, nullable=False, default=0.0, server_default=text("0"))
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
    )
