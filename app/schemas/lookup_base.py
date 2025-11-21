from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
# Assuming app/schemas/audit.py exists and defines AuditSchema
from app.schemas.audit import AuditSchema 

# --- Base Schemas for Input ---

class LookupBase(BaseModel):
    """Common structure for all lookup entities (Department, Unit, etc.)."""
    name: str = Field(..., description="The unique name of the lookup entity.")

class LookupCreate(LookupBase):
    """Schema for creating a new lookup entity."""
    pass

class LookupUpdate(LookupBase):
    """Schema for updating a lookup entity (name is optional for partial updates)."""
    name: Optional[str] = None

# --- Final Read Schema Template ---

class Lookup(LookupBase, AuditSchema):
    """Base schema for reading a lookup entity (includes ID and Audit fields)."""
    id: UUID