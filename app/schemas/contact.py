from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.schemas.audit import AuditSchema


class ContactBase(BaseModel):
    """Common fields for Contact."""
    name: str
    email: str
    phone: Optional[str] = None


class ContactCreate(ContactBase):
    """Schema for creating a new Contact (nested or direct)."""
    account_id: UUID
    pass


class ContactUpdate(BaseModel):
    """Schema for updating an existing Contact."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    account_id: Optional[UUID] = None   # Allow moving contact to another account
                                         # (make sure your router handles this)


class ContactOut(ContactBase, AuditSchema):
    """Schema for reading a Contact record (output)."""
    id: UUID
    account_id: UUID

    class Config:
        from_attributes = True  # Needed for Pydantic v2 ORM mode


# Alias for backward compatibility if needed
Contact = ContactOut
