import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base # Assuming 'Base' is imported

class Project(Base):
    __tablename__ = "projects"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Business Fields
    project_name = Column(String, nullable=True)
    project_code = Column(String, nullable=True)
    status = Column(String, nullable=True) 
    start_date = Column(DateTime(timezone=True), nullable=True) 
    end_date = Column(DateTime(timezone=True), nullable=True) 
    revenue_budget = Column(Float, nullable=True)
    billing_type = Column(String, nullable=True)
    probability = Column(Float, nullable=True)
    project_manager = Column(String, nullable=True) 

    # Foreign Key - Set to nullable=True as requested for initial optionality
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False) 
    account = relationship("Account", back_populates="projects")

    # Audit Columns
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True))
    deleted_by = Column(UUID(as_uuid=True))