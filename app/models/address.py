import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base # Assuming 'Base' is imported

class Address(Base):
    __tablename__ = "addresses"
    
    # PK is also the FK to Account (one-to-one mapping)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), primary_key=True) 

    # Address Fields (from Keka ref)
    addressLine1 = Column(String, nullable=False)
    addressLine2 = Column(String)
    countryCode = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String)
    zip = Column(String)
    
    # Relationship
    account = relationship("Account", back_populates="billing_address")

    # Audit Columns
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True))
    deleted_by = Column(UUID(as_uuid=True))