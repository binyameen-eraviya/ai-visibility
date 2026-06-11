import uuid

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
 TEXT,
 TIMESTAMP,
 Column,
 ForeignKey,
 text,
)

from backend.database.db import Base
from backend.database.migrations.organization import Organization  # noqa: F401  (mapper registration)

class Project(Base):
    __tablename__ = "projects"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(TEXT, nullable=False)
    website_url = Column(TEXT, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    deleted_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    # many-to-one relationship
    organization = relationship("Organization")
