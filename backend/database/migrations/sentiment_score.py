import uuid

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
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

class SentimentScore(Base):
    __tablename__ = "sentiment_scores"
    __table_args__ = (
        UniqueConstraint("answer_id", "brand_id", name="uq_sentiment_scores_answer_brand"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.id"), nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    score = Column(INTEGER, nullable=False)  # 0..100
    reasoning = Column(TEXT, nullable=True)  # LLM rationale for the score
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # many-to-one relationships
    answer = relationship("Answer")
    brand = relationship("Brand")
