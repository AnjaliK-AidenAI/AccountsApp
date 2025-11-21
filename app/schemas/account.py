from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from pydantic.fields import Field

# Import nested schemas
from app.schemas.audit import AuditSchema
from app.schemas.address import AddressCreate, Address
from app.schemas.contact import ContactCreate, Contact
from app.schemas.project import Project


class AccountBase(BaseModel):
    """Common fields for Account - Mandatory fields only."""
    name: str = Field(..., description="The official name of the Client/Account.")
    code: str = Field(..., description="A unique code for the client.")
    
    # Optional Business Fields
    probability: Optional[int] = None
    account_partner: Optional[str] = None
    delivery_partner: Optional[str] = None

    # Foreign Key IDs - Optional (nullable=True in model)
    department_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    vertical_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    status_id: Optional[UUID] = None


# --- Schemas for Data Input ---

class AccountCreate(AccountBase):
    """Schema for creating a NEW Account (handles nested creation)."""

    # Nested Address (One-to-One, required for creation)
    billing_address: AddressCreate

    # Nested Contacts (One-to-Many)
    contacts: Optional[List[ContactCreate]] = None


class AccountUpdate(BaseModel):
    """Schema for updating an Account (partial updates allowed)."""
    name: Optional[str] = None
    code: Optional[str] = None
    probability: Optional[int] = None
    account_partner: Optional[str] = None
    delivery_partner: Optional[str] = None
    department_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    vertical_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    status_id: Optional[UUID] = None


# --- Schema for Data Output (Reading) ---

class Account(AccountBase, AuditSchema):
    """Schema for reading an Account (includes nested relations)."""

    id: UUID

    # Relationship fields
    billing_address: Optional[Address] = None
    contacts: List[Contact] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)

    # Enable ORM mode (Pydantic v2)
    model_config = ConfigDict(from_attributes=True)
