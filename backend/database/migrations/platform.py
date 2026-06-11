import uuid

from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy import (
 BOOLEAN,
 TEXT,
 TIMESTAMP,
 Column,
 text,
)

from backend.database.db import Base
from backend.utils.enums import AdapterType

class Platform(Base):
    """Reference/seed data: one row per AI answer platform."""

    __tablename__ = "platforms"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(TEXT, unique=True, nullable=False)  # e.g. "chatgpt", "perplexity"
    display_name = Column(TEXT, nullable=False)
    # SCRAPER today; API when a platform is swapped to an official API adapter.
    adapter_type = Column(
        ENUM(AdapterType, name="adapter_type"),
        nullable=False,
        server_default=AdapterType.SCRAPER.value,
    )
    is_active = Column(BOOLEAN, nullable=False, default=True, server_default=text("true"))
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
    )
