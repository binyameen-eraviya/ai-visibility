import uuid

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy import ( 
 TEXT, 
 TIMESTAMP, 
 JSON, 
 Column, 
 ForeignKey,
 text,
)

from backend.database.db import Base
from backend.utils.enums import UserRole

class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(TEXT, nullable=False)
    email = Column(TEXT, unique=True, nullable=False)
    password = Column(TEXT, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    signup_token = Column(TEXT, nullable=False)
    verified_at = Column(TIMESTAMP(timezone=True), nullable=True)
    attrs = Column(MutableDict.as_mutable(JSON), default=dict)
    role = Column(
        ENUM(UserRole, name="user_role"),
        nullable=False,
        server_default=UserRole.USER.value,
    )
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
    organization = relationship("Organization", back_populates="users")
