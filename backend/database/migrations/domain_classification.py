import uuid

from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy import (
 TEXT,
 TIMESTAMP,
 Column,
 text,
)

from backend.database.db import Base
from backend.utils.enums import SourceType, UrlType, DomainClassifier


class DomainClassification(Base):
    """Cache of domain -> type classifications.

    Once a domain is classified (by the known list, a brand match, or the LLM)
    the result is cached here so we never pay an LLM call for it again. Keyed by
    bare domain (e.g. "reddit.com"), so it's shared across all projects.
    """

    __tablename__ = "domain_classifications"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    domain = Column(TEXT, nullable=False, unique=True)
    domain_type = Column(
        ENUM(SourceType, name="source_type"),
        nullable=False,
        server_default=SourceType.OTHER.value,
    )
    url_type = Column(ENUM(UrlType, name="url_type"), nullable=True)
    classified_by = Column(
        ENUM(DomainClassifier, name="domain_classifier"),
        nullable=False,
        server_default=DomainClassifier.LLM.value,
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
    )
