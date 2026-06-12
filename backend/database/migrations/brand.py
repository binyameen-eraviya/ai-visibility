import uuid

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
 BOOLEAN,
 TEXT,
 TIMESTAMP,
 JSON,
 Column,
 ForeignKey,
 text,
)

from backend.database.db import Base
from backend.database.migrations.project import Project  # noqa: F401  (mapper registration)

class Brand(Base):
    __tablename__ = "brands"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(TEXT, nullable=False)
    # Alternate names / misspellings used by the parser for mention detection.
    aliases = Column(MutableList.as_mutable(JSON), default=list)
    # True = the client's own brand; False = competitor.
    is_primary = Column(BOOLEAN, nullable=False, default=False, server_default=text("false"))
    # Onboarding v2: the brand's own site, for favicon + competitor domain match.
    website_url = Column(TEXT, nullable=True)
    favicon_url = Column(TEXT, nullable=True)
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
    project = relationship("Project")
