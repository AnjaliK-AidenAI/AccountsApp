from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class AuditSchema(BaseModel):
    """Mixin for read schemas to include audit fields."""
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    created_by: UUID
    updated_by: Optional[UUID] = None
    deleted_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)