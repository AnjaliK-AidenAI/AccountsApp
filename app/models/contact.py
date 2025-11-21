import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base # Assuming 'Base' is imported

class Contact(Base):
    __tablename__ = "contacts"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Contact Fields (from Keka ref)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True) # Removed unique constraint, as multiple contacts for the same client might use the same email or people might have a unique contact list across multiple accounts.
    phone = Column(String)

    # Foreign Key
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False) # A contact must belong to an account
    account = relationship("Account", back_populates="contacts")

    # Audit Columns
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True))
    deleted_by = Column(UUID(as_uuid=True))