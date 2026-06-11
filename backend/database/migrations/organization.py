import uuid

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ( 
 TEXT, 
 TIMESTAMP, 
 JSON, 
 Column, 
 text,
)

from backend.database.db import Base

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(TEXT, nullable=False)
    attrs = Column(MutableDict.as_mutable(JSON), default=dict)
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
    
    # one-to-many relationship
    users = relationship("User", back_populates="organization", cascade="all, delete")
