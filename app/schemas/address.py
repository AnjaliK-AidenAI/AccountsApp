from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.schemas.audit import AuditSchema

class AddressBase(BaseModel):
    """Common fields for Address."""
    addressLine1: str = Field(..., description="First line of the billing address.")
    addressLine2: Optional[str] = Field(None, description="Second line of the billing address.")
    countryCode: str = Field(..., description="ISO country code (e.g., 'US', 'IN').")
    city: str
    state: Optional[str] = None
    zip: Optional[str] = None

class AddressCreate(AddressBase):
    """Schema for creating a new Address (used as a nested object)."""
    pass

class Address(AddressBase, AuditSchema):
    """Schema for reading an Address record (output)."""
    account_id: UUID  # Address uses account_id as its PK/FK in the model