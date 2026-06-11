import uuid

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy import (
 BOOLEAN,
 TIMESTAMP,
 Column,
 ForeignKey,
 UniqueConstraint,
 text,
)

from backend.database.db import Base
from backend.utils.enums import TrackingFrequency
from backend.database.migrations.project import Project  # noqa: F401  (mapper registration)
from backend.database.migrations.prompt import Prompt  # noqa: F401  (mapper registration)
from backend.database.migrations.platform import Platform  # noqa: F401  (mapper registration)
from backend.database.migrations.country import Country  # noqa: F401  (mapper registration)

class TrackingConfig(Base):
    """Run this prompt on this platform in this country on this schedule."""

    __tablename__ = "tracking_configs"
    __table_args__ = (
        UniqueConstraint("prompt_id", "platform_id", "country_id", name="uq_tracking_configs_prompt_platform_country"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id"), nullable=False)
    platform_id = Column(UUID(as_uuid=True), ForeignKey("platforms.id"), nullable=False)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=False)
    frequency = Column(
        ENUM(TrackingFrequency, name="tracking_frequency"),
        nullable=False,
        server_default=TrackingFrequency.DAILY.value,
    )
    is_active = Column(BOOLEAN, nullable=False, default=True, server_default=text("true"))
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # many-to-one relationships
    project = relationship("Project")
    prompt = relationship("Prompt")
    platform = relationship("Platform")
    country = relationship("Country")
