import uuid

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
 BOOLEAN,
 INTEGER,
 TEXT,
 TIMESTAMP,
 Column,
 ForeignKey,
 UniqueConstraint,
 text,
)

from backend.database.db import Base
from backend.database.migrations.answer import Answer  # noqa: F401  (mapper registration)
from backend.database.migrations.brand import Brand  # noqa: F401  (mapper registration)

class Mention(Base):
    __tablename__ = "mentions"
    __table_args__ = (
        UniqueConstraint("answer_id", "brand_id", name="uq_mentions_answer_brand"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.id"), nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    mentioned = Column(BOOLEAN, nullable=False, default=False, server_default=text("false"))
    position = Column(INTEGER, nullable=True)  # rank of the brand within the answer
    context_snippet = Column(TEXT, nullable=True)  # sentence where the brand appeared
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # many-to-one relationships
    answer = relationship("Answer")
    brand = relationship("Brand")
