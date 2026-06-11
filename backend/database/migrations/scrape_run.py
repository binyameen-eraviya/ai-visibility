import uuid

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy import (
 INTEGER,
 TEXT,
 TIMESTAMP,
 Column,
 ForeignKey,
 text,
)

from backend.database.db import Base
from backend.utils.enums import ScrapeStatus
from backend.database.migrations.tracking_config import TrackingConfig  # noqa: F401  (mapper registration)

class ScrapeRun(Base):
    """One scrape attempt for one tracking config."""

    __tablename__ = "scrape_runs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    tracking_config_id = Column(UUID(as_uuid=True), ForeignKey("tracking_configs.id"), nullable=False)
    status = Column(
        ENUM(ScrapeStatus, name="scrape_status"),
        nullable=False,
        server_default=ScrapeStatus.PENDING.value,
    )
    raw_storage_path = Column(TEXT, nullable=True)  # path to stored JSON/HTML on disk
    screenshot_path = Column(TEXT, nullable=True)
    error = Column(TEXT, nullable=True)
    account_id = Column(UUID(as_uuid=True), nullable=True)  # account pool tracking (Milestone 4)
    duration_ms = Column(INTEGER, nullable=True)
    scraped_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # many-to-one relationship
    tracking_config = relationship("TrackingConfig")
