from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from uuid import UUID

from app.database import get_db
from app.models.lookup_models import Location
from app.schemas.lookup_base import LookupCreate, LookupUpdate, Lookup as LocationSchema


# --- TEMPORARY AUTH PLACEHOLDER ---
def get_current_user_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000001")


router = APIRouter(
    prefix="/locations",
    tags=["Locations"],
)


# --------------------------------------------------
# 1. CREATE A LOCATION
# --------------------------------------------------
@router.post("/", response_model=LocationSchema, status_code=status.HTTP_201_CREATED)
async def create_location(
    item_in: LookupCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Creates a new location."""

    existing_item = (
        db.query(Location)
        .filter(Location.name == item_in.name, Location.is_deleted == False)
        .first()
    )
    if existing_item:
        raise HTTPException(
            status_code=400,
            detail=f"Location '{item_in.name}' already exists",
        )

    try:
        db_item = Location(
            name=item_in.name,
            created_by=current_user_id,
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create location: {str(e)}",
        )


# --------------------------------------------------
# 2. GET ALL LOCATIONS
# --------------------------------------------------
@router.get("/", response_model=List[LocationSchema])
async def get_all_locations(db: Session = Depends(get_db)):
    """Returns all active (not deleted) locations."""
    return db.query(Location).filter(Location.is_deleted == False).all()


# --------------------------------------------------
# 3. GET LOCATION BY ID
# --------------------------------------------------
@router.get("/{item_id}", response_model=LocationSchema)
async def get_location_by_id(
    item_id: UUID,
    db: Session = Depends(get_db),
):
    """Return a single specific location by ID."""

    db_item = (
        db.query(Location)
        .filter(Location.id == item_id, Location.is_deleted == False)
        .first()
    )

    if not db_item:
        raise HTTPException(
            status_code=404,
            detail=f"Location with id '{item_id}' not found",
        )

    return db_item


# --------------------------------------------------
# 4. UPDATE LOCATION
# --------------------------------------------------
@router.put("/{item_id}", response_model=LocationSchema)
async def update_location(
    item_id: UUID,
    item_update: LookupUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Updates a location's name."""

    db_item = (
        db.query(Location)
        .filter(Location.id == item_id, Location.is_deleted == False)
        .first()
    )

    if not db_item:
        raise HTTPException(
            status_code=404,
            detail=f"Location with id '{item_id}' not found",
        )

    # Check duplicate name
    if item_update.name and item_update.name != db_item.name:
        existing_item = (
            db.query(Location)
            .filter(
                Location.name == item_update.name,
                Location.id != item_id,
                Location.is_deleted == False,
            )
            .first()
        )
        if existing_item:
            raise HTTPException(
                status_code=400,
                detail=f"Location '{item_update.name}' already exists",
            )

        db_item.name = item_update.name

    try:
        db_item.updated_by = current_user_id
        db_item.updated_at = func.now()
        db.commit()
        db.refresh(db_item)
        return db_item

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update location: {str(e)}",
        )


# --------------------------------------------------
# 5. SOFT DELETE LOCATION
# --------------------------------------------------
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Soft-deletes a location."""

    db_item = (
        db.query(Location)
        .filter(Location.id == item_id, Location.is_deleted == False)
        .first()
    )

    if not db_item:
        raise HTTPException(
            status_code=404,
            detail=f"Location with id '{item_id}' not found or already deleted",
        )

    try:
        db_item.is_deleted = True
        db_item.deleted_by = current_user_id
        db_item.deleted_at = func.now()

        db.commit()
        return

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete location: {str(e)}",
        )
