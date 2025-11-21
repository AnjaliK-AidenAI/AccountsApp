from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from uuid import UUID

from app.database import get_db
from app.models.contact import Contact
from app.models.account import Account
from app.schemas.contact import ContactCreate, ContactUpdate, ContactOut


# --- TEMPORARY USER UNTIL AUTH IS ADDED ---
def get_current_user_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000001")


router = APIRouter(
    prefix="/contacts",
    tags=["Contacts"],
)


# ------------------------------------------------------
# 1. CREATE CONTACT
# ------------------------------------------------------
@router.post("/", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: ContactCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Create a new contact for an account."""

    # Validate account exists
    account = (
        db.query(Account)
        .filter(Account.id == payload.account_id, Account.is_deleted == False)
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=404,
            detail=f"Account {payload.account_id} does not exist",
        )

    try:
        new_contact = Contact(
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            account_id=payload.account_id,
            created_by=current_user_id,
        )

        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)
        return new_contact

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create contact: {str(e)}")


# ------------------------------------------------------
# 2. GET ALL CONTACTS (ACTIVE ONLY)
# ------------------------------------------------------
@router.get("/", response_model=List[ContactOut])
async def get_all_contacts(db: Session = Depends(get_db)):
    """Fetch all active (not deleted) contacts."""
    return db.query(Contact).filter(Contact.is_deleted == False).all()


# ------------------------------------------------------
# 3. GET CONTACT BY ID
# ------------------------------------------------------
@router.get("/{contact_id}", response_model=ContactOut)
async def get_contact_by_id(
    contact_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve a contact by its ID."""

    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.is_deleted == False)
        .first()
    )

    if not contact:
        raise HTTPException(
            status_code=404,
            detail=f"Contact with id {contact_id} not found",
        )

    return contact


# ------------------------------------------------------
# 4. UPDATE CONTACT
# ------------------------------------------------------
@router.put("/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: UUID,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Update a contact."""

    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.is_deleted == False)
        .first()
    )

    if not contact:
        raise HTTPException(
            status_code=404,
            detail=f"Contact with id {contact_id} not found",
        )

    # Update only provided fields
    if payload.name:
        contact.name = payload.name

    if payload.email:
        contact.email = payload.email

    if payload.phone:
        contact.phone = payload.phone

    # Optional: Allow moving contact between accounts
    if payload.account_id and payload.account_id != contact.account_id:
        # Check new account exists
        account = (
            db.query(Account)
            .filter(Account.id == payload.account_id, Account.is_deleted == False)
            .first()
        )
        if not account:
            raise HTTPException(
                status_code=404,
                detail=f"Target account {payload.account_id} does not exist",
            )
        contact.account_id = payload.account_id

    try:
        contact.updated_by = current_user_id
        contact.updated_at = func.now()

        db.commit()
        db.refresh(contact)
        return contact

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update contact: {str(e)}")


# ------------------------------------------------------
# 5. SOFT DELETE CONTACT
# ------------------------------------------------------
@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Soft delete a contact."""

    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.is_deleted == False)
        .first()
    )

    if not contact:
        raise HTTPException(
            status_code=404,
            detail=f"Contact with id {contact_id} not found or already deleted",
        )

    try:
        contact.is_deleted = True
        contact.deleted_at = func.now()
        contact.deleted_by = current_user_id

        db.commit()
        return

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete contact: {str(e)}")



# You cannot create a contact without an account.

# You can move a contact to a different account during update.

# You can delete a contact independently — it won’t delete the account.

# When an account is soft-deleted → all its contacts are also soft deleted.