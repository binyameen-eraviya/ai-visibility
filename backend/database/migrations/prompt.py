import uuid

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy import (
 TEXT,
 TIMESTAMP,
 Column,
 ForeignKey,
 Table,
)
from sqlalchemy import text as sa_text  # aliased: "text" is a column name on this table

from backend.database.db import Base
from backend.utils.enums import PromptStatus
from backend.database.migrations.project import Project  # noqa: F401  (mapper registration)
from backend.database.migrations.topic import Topic  # noqa: F401  (mapper registration)
from backend.database.migrations.tag import Tag  # noqa: F401  (mapper registration)

# Association table: prompts <-> tags (composite PK).
prompt_tags = Table(
    "prompt_tags",
    Base.metadata,
    Column(
        "prompt_id",
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa_text("gen_random_uuid()"),
    )
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    text = Column(TEXT, nullable=False)  # the actual prompt string
    topic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="SET NULL"),
        nullable=True,
    )
    status = Column(
        ENUM(PromptStatus, name="prompt_status"),
        nullable=False,
        server_default=PromptStatus.ACTIVE.value,
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=sa_text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        server_default=sa_text("CURRENT_TIMESTAMP"),
    )
    deleted_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    # many-to-one relationships
    project = relationship("Project")
    topic = relationship("Topic")
    # many-to-many relationship
    tags = relationship("Tag", secondary=prompt_tags)
