from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.schemas.audit import AuditSchema

class ProjectBase(BaseModel):
    """Common fields for Project."""
    project_name: Optional[str] = None
    project_code: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    revenue_budget: Optional[float] = None
    billing_type: Optional[str] = None
    probability: Optional[float] = None
    project_manager: Optional[str] = None

class ProjectCreate(ProjectBase):
    """Schema for creating a new Project."""
    # account_id is set by the service layer
    account_id: UUID
    pass

class ProjectUpdate(ProjectBase):
    """Schema for updating an existing Project."""
    # All fields are optional when updating

class Project(ProjectBase, AuditSchema):
    """Schema for reading a Project record (output)."""
    id: UUID
    account_id: Optional[UUID] = None