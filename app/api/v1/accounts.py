from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import func
from uuid import UUID

from app.database import get_db

# ACCOUNT MODELS
from app.models.account import Account
from app.models.address import Address
from app.models.contact import Contact
from app.models.project import Project

# LOOKUP MODELS (IMPORTANT)
from app.models.lookup_models import (
    Department,
    Unit,
    Vertical,
    Location,
    Status
)

# SCHEMAS
from app.schemas.account import AccountCreate, AccountUpdate, Account as AccountSchema


# TEMPORARY USER (replace when auth is added)
def get_current_user_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000001")


router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"],
)


# -----------------------------------------------------------
# CREATE ACCOUNT
# -----------------------------------------------------------
@router.post("/", response_model=AccountSchema, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_in: AccountCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):

    # Prevent duplicate code
    if db.query(Account).filter(Account.code == account_in.code, Account.is_deleted == False).first():
        raise HTTPException(status_code=400, detail=f"Account code '{account_in.code}' already exists")

    # Validate FK function
    def validate_fk(model, value: UUID, field_name: str):
        if value is None:
            return
        exists = db.query(model).filter(model.id == value, model.is_deleted == False).first()
        if not exists:
            raise HTTPException(
                status_code=404,
                detail=f"{field_name} with id '{value}' does not exist"
            )

    # Validate all lookups
    validate_fk(Department, account_in.department_id, "Department")
    validate_fk(Unit, account_in.unit_id, "Unit")
    validate_fk(Vertical, account_in.vertical_id, "Vertical")
    validate_fk(Location, account_in.location_id, "Location")
    validate_fk(Status, account_in.status_id, "Status")

    try:
        # Create account first
        fields = account_in.model_dump(exclude={'billing_address', 'contacts'}, exclude_none=True)
        db_account = Account(**fields, created_by=current_user_id)
        db.add(db_account)
        db.flush()

        # Create address (one-to-one)
        address_data = account_in.billing_address.model_dump(exclude_none=True)
        db_address = Address(**address_data, account_id=db_account.id, created_by=current_user_id)
        db.add(db_address)

        # Create contacts (optional)
        if account_in.contacts:
            for c in account_in.contacts:
                data = c.model_dump(exclude_none=True)
                db.add(Contact(**data, account_id=db_account.id, created_by=current_user_id))

        db.commit()

        created = db.query(Account).options(
            selectinload(Account.billing_address),
            selectinload(Account.contacts),
            selectinload(Account.projects)
        ).filter(Account.id == db_account.id).first()

        return created

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create account: {str(e)}")


# -----------------------------------------------------------
# GET ALL ACCOUNTS
# -----------------------------------------------------------
@router.get("/", response_model=List[AccountSchema])
async def get_all_accounts(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    accounts = db.query(Account).options(
        selectinload(Account.billing_address),
        selectinload(Account.contacts),
        selectinload(Account.projects)
    ).filter(Account.is_deleted == False).offset(skip).limit(limit).all()

    return accounts


# -----------------------------------------------------------
# GET ACCOUNT BY ID
# -----------------------------------------------------------
@router.get("/{account_id}", response_model=AccountSchema)
async def get_account_by_id(account_id: UUID, db: Session = Depends(get_db)):

    account = db.query(Account).options(
        selectinload(Account.billing_address),
        selectinload(Account.contacts),
        selectinload(Account.projects)
    ).filter(Account.id == account_id, Account.is_deleted == False).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return account


# -----------------------------------------------------------
# UPDATE ACCOUNT
# -----------------------------------------------------------
@router.put("/{account_id}", response_model=AccountSchema)
async def update_account(
    account_id: UUID,
    account_update: AccountUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Update:
      - Account fields
      - Billing Address
      - Contacts (Add/Update/Delete)
    """

    # ----------------------------------------
    # 1. Fetch Account
    # ----------------------------------------
    db_account = db.query(Account).filter(
        Account.id == account_id,
        Account.is_deleted == False
    ).first()

    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")

    # ----------------------------------------
    # 2. Prevent duplicate account code
    # ----------------------------------------
    if account_update.code:
        exists = db.query(Account).filter(
            Account.code == account_update.code,
            Account.id != account_id,
            Account.is_deleted == False
        ).first()
        if exists:
            raise HTTPException(status_code=400, detail=f"Account code '{account_update.code}' already exists")

    # ----------------------------------------
    # 3. Validate FK IDs (if provided)
    # ----------------------------------------
    def validate_fk(model, value: UUID, field_name: str):
        if value is None:
            return
        exists = db.query(model).filter(model.id == value, model.is_deleted == False).first()
        if not exists:
            raise HTTPException(status_code=404, detail=f"{field_name} with id '{value}' does not exist")

    validate_fk(Department, account_update.department_id, "Department")
    validate_fk(Unit, account_update.unit_id, "Unit")
    validate_fk(Vertical, account_update.vertical_id, "Vertical")
    validate_fk(Location, account_update.location_id, "Location")
    validate_fk(Status, account_update.status_id, "Status")

    try:
        # ----------------------------------------
        # 4. Update Account fields
        # ----------------------------------------
        updated_data = account_update.model_dump(exclude_unset=True)
        updated_data.pop("billing_address",None)
        updated_data.pop("contacts",None) 

        for key,value in updated_data.items():
            if hasattr(db_account, key):
                setattr(db_account, key, value)

        db_account.updated_by = current_user_id
        db_account.updated_at = func.now()

        # # ----------------------------------------
        # # 5. Update Billing Address
        # # ----------------------------------------
        # if account_update.billing_address:

        #     addr_data = account_update.billing_address.model_dump(exclude_unset=True)

        #     db_address = db.query(Address).filter(
        #         Address.account_id == account_id,
        #         Address.is_deleted == False
        #     ).first()

        #     if db_address:
        #         # update existing
        #         for key, value in addr_data.items():
        #             setattr(db_address, key, value)
        #         db_address.updated_by = current_user_id
        #         db_address.updated_at = func.now()
        #     else:
        #         # create new if missing
        #         db_address = Address(
        #             account_id=account_id,
        #             **addr_data,
        #             created_by=current_user_id
        #         )
        #         db.add(db_address)

        # ----------------------------------------
        # # 6. Update Contacts (Full Replace Strategy)
        # # ----------------------------------------
        # if account_update.contacts is not None:

        #     # Soft-delete old contacts
        #     db.query(Contact).filter(Contact.account_id == account_id).update({
        #         Contact.is_deleted: True,
        #         Contact.updated_at : func.now(),
        #         Contact.updated_by : current_user_id,
        #         Contact.deleted_at : func.now(),
        #         Contact.deleted_by : current_user_id
        #     })

        #     # Add new contacts
        #     for c in account_update.contacts:
        #         data = c.model_dump(exclude_none=True)
        #         db.add(Contact(
        #             **data,
        #             account_id=account_id,
        #             created_by=current_user_id
        #         ))

        # ----------------------------------------
        # 7. Commit all changes
        # ----------------------------------------
        db.commit()

        # ----------------------------------------
        # 8. Return updated account with relationships
        # ----------------------------------------
        updated = db.query(Account).options(
            selectinload(Account.billing_address),
            selectinload(Account.contacts),
            selectinload(Account.projects)
        ).filter(Account.id == account_id).first()

        return updated

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update account: {str(e)}")

# -----------------------------------------------------------
# SOFT DELETE ACCOUNT
# -----------------------------------------------------------
@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):

    acct = db.query(Account).filter(
        Account.id == account_id,
        Account.is_deleted == False
    ).first()

    if not acct:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        acct.is_deleted = True
        acct.deleted_at = func.now()
        acct.deleted_by = current_user_id
        acct.updated_at = func.now()
        acct.updated_by = current_user_id

        # cascade delete
        db.query(Address).filter(Address.account_id == account_id).update({
            Address.is_deleted: True,
            Address.updated_at: func.now(),
            Address.updated_by: current_user_id,
            Address.deleted_at: func.now(),
            Address.deleted_by: current_user_id
        })

        db.query(Contact).filter(Contact.account_id == account_id).update({
            Contact.is_deleted: True,
            Contact.updated_at: func.now(),
            Contact.updated_by: current_user_id,
            Contact.deleted_at: func.now(),
            Contact.deleted_by: current_user_id
        })

        db.query(Project).filter(Project.account_id == account_id).update({
            Project.is_deleted: True,
            Project.updated_at: func.now(),
            Project.updated_by: current_user_id,
            Project.deleted_at: func.now(),
            Project.deleted_by: current_user_id
        })

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to soft delete account")
