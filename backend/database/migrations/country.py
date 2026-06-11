import uuid

from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
 BOOLEAN,
 TEXT,
 TIMESTAMP,
 Column,
 text,
)

from backend.database.db import Base

class Country(Base):
    """Reference/seed data: countries available for tracking."""

    __tablename__ = "countries"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    code = Column(TEXT, unique=True, nullable=False)  # ISO 2-letter, e.g. "US"
    name = Column(TEXT, nullable=False)
    is_active = Column(BOOLEAN, nullable=False, default=True, server_default=text("true"))
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
    )
