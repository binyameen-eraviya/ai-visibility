import uuid

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy import (
 INTEGER,
 JSON,
 TEXT,
 TIMESTAMP,
 Column,
 ForeignKey,
 text,
)

from backend.database.db import Base
from backend.utils.enums import ScrapeAccountStatus
from backend.database.migrations.platform import Platform  # noqa: F401  (mapper registration)

class ScrapeAccount(Base):
    """A reusable login for one platform, managed by the account pool.

    v1 is intentionally small -- enough to prove checkout/cooldown/quota flow.
    """

    __tablename__ = "scrape_accounts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    platform_id = Column(UUID(as_uuid=True), ForeignKey("platforms.id"), nullable=False)
    email = Column(TEXT, nullable=False)
    # Session cookies so the adapter can skip the login flow on each run.
    cookies = Column(MutableDict.as_mutable(JSON), default=dict)
    daily_quota_used = Column(INTEGER, nullable=False, default=0, server_default=text("0"))
    daily_quota_limit = Column(INTEGER, nullable=False, default=10, server_default=text("10"))
    cooldown_until = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(
        ENUM(ScrapeAccountStatus, name="scrape_account_status"),
        nullable=False,
        server_default=ScrapeAccountStatus.ACTIVE.value,
    )
    # Free-form bag for counters like consecutive failures.
    attrs = Column(MutableDict.as_mutable(JSON), default=dict)
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True)
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

    # many-to-one relationship
    platform = relationship("Platform")
