from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from uuid import UUID

from app.database import get_db
from app.models.lookup_models import Status
from app.schemas.lookup_base import LookupCreate, LookupUpdate, Lookup as StatusSchema


# --- TEMPORARY AUTH PLACEHOLDER ---
def get_current_user_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000001")


router = APIRouter(
    prefix="/statuses",
    tags=["Statuses"],
)


# ---------------------------
# 1. CREATE STATUS
# ---------------------------
@router.post("/", response_model=StatusSchema, status_code=status.HTTP_201_CREATED)
async def create_status(
    payload: LookupCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Create a new status."""

    existing = (
        db.query(Status)
            .filter(Status.name == payload.name, Status.is_deleted == False)
            .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Status '{payload.name}' already exists",
        )

    try:
        status_item = Status(
            name=payload.name,
            created_by=current_user_id,
        )
        db.add(status_item)
        db.commit()
        db.refresh(status_item)
        return status_item

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create status: {str(e)}",
        )


# ---------------------------
# 2. GET ALL STATUSES
# ---------------------------
@router.get("/", response_model=List[StatusSchema])
async def get_all_statuses(db: Session = Depends(get_db)):
    """Return all active statuses."""
    return db.query(Status).filter(Status.is_deleted == False).all()


# ---------------------------
# 3. GET STATUS BY ID
# ---------------------------
@router.get("/{status_id}", response_model=StatusSchema)
async def get_status_by_id(
    status_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve a specific status."""

    status_item = (
        db.query(Status)
            .filter(Status.id == status_id, Status.is_deleted == False)
            .first()
    )

    if not status_item:
        raise HTTPException(
            status_code=404,
            detail=f"Status with id '{status_id}' not found",
        )

    return status_item


# ---------------------------
# 4. UPDATE STATUS
# ---------------------------
@router.put("/{status_id}", response_model=StatusSchema)
async def update_status(
    status_id: UUID,
    payload: LookupUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Update the name of a status."""

    status_item = (
        db.query(Status)
            .filter(Status.id == status_id, Status.is_deleted == False)
            .first()
    )
    if not status_item:
        raise HTTPException(
            status_code=404,
            detail=f"Status with id '{status_id}' not found",
        )

    # Name change validation
    if payload.name and payload.name != status_item.name:
        existing = (
            db.query(Status)
                .filter(
                    Status.name == payload.name,
                    Status.id != status_id,
                    Status.is_deleted == False,
                )
                .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Status '{payload.name}' already exists",
            )

        status_item.name = payload.name

    try:
        status_item.updated_by = current_user_id
        status_item.updated_at = func.now()

        db.commit()
        db.refresh(status_item)
        return status_item

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update status: {str(e)}",
        )


# ---------------------------
# 5. SOFT DELETE STATUS
# ---------------------------
@router.delete("/{status_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_status(
    status_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Soft delete a status."""

    status_item = (
        db.query(Status)
            .filter(Status.id == status_id, Status.is_deleted == False)
            .first()
    )

    if not status_item:
        raise HTTPException(
            status_code=404,
            detail=f"Status with id '{status_id}' not found or already deleted",
        )

    try:
        status_item.is_deleted = True
        status_item.deleted_by = current_user_id
        status_item.deleted_at = func.now()

        db.commit()
        return

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete status: {str(e)}",
        )
