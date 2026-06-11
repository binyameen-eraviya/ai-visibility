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
from backend.database.migrations.project import Project  # noqa: F401  (mapper registration)

class Topic(Base):
    __tablename__ = "topics"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(TEXT, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # many-to-one relationship
    project = relationship("Project")
