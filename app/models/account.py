import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base # Assuming 'Base' is imported

class Account(Base):
    __tablename__ = "accounts"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Business Fields
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False) 
    probability = Column(Integer) # e.g., 0-100
    account_partner = Column(String) #later we will get from people's app
    delivery_partner = Column(String) #later we will get from people's app
    
    # Foreign Keys (Categorization) - Set to nullable=True as requested(for optionality)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=True)
    vertical_id = Column(UUID(as_uuid=True), ForeignKey("verticals.id"), nullable=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
    status_id = Column(UUID(as_uuid=True), ForeignKey("statuses.id"), nullable=True)

    # Relationships 
    projects = relationship("Project", back_populates="account", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="account", cascade="all, delete-orphan")
    billing_address = relationship("Address", uselist=False, back_populates="account", cascade="all, delete-orphan")

    # Audit Columns
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True))
    deleted_by = Column(UUID(as_uuid=True))