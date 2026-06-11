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
from backend.utils.enums import SourceType
from backend.database.migrations.answer import Answer  # noqa: F401  (mapper registration)

class Source(Base):
    """A URL cited by the AI in one answer."""

    __tablename__ = "sources"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.id"), nullable=False)
    url = Column(TEXT, nullable=False)
    domain = Column(TEXT, nullable=False)
    source_type = Column(
        ENUM(SourceType, name="source_type"),
        nullable=False,
        server_default=SourceType.OTHER.value,
    )
    position = Column(INTEGER, nullable=True)  # order in the answer
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # many-to-one relationship
    answer = relationship("Answer")
