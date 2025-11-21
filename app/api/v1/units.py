from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from uuid import UUID

from app.database import get_db
from app.models.lookup_models import Unit 
from app.schemas.lookup_base import LookupCreate, LookupUpdate, Lookup as UnitSchema

# --- PLACEHOLDER FOR DEPENDENCY ---
def get_current_user_id() -> UUID:
    return UUID('00000000-0000-0000-0000-000000000001')

router = APIRouter(
    prefix="/units",
    tags=["Units"],
)

# --- 1. CREATE A UNIT ---
@router.post("/", response_model=UnitSchema, status_code=status.HTTP_201_CREATED)
async def create_unit(
    item_in: LookupCreate, 
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Creates a new unit."""
    existing_item = db.query(Unit).filter(Unit.name == item_in.name, Unit.is_deleted == False).first()
    if existing_item:
        raise HTTPException(status_code=400, detail=f"Unit '{item_in.name}' already exists")

    try:
        db_item = Unit(name=item_in.name, created_by=current_user_id)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create unit: {str(e)}")

# --- 2. GET ALL UNITS ---
@router.get("/", response_model=List[UnitSchema])
async def get_all_units(db: Session = Depends(get_db)):
    """Returns all active units."""
    items = db.query(Unit).filter(Unit.is_deleted == False).all()
    return items

# --- 3. GET A SINGLE UNIT BY ID ---
@router.get("/{item_id}", response_model=UnitSchema)
async def get_unit_by_id(item_id: UUID, db: Session = Depends(get_db)):
    """Returns a specific unit by ID."""
    item = db.query(Unit).filter(Unit.id == item_id, Unit.is_deleted == False).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Unit with id {item_id} not found")
    return item

# --- 4. UPDATE A UNIT ---
@router.put("/{item_id}", response_model=UnitSchema)
async def update_unit(
    item_id: UUID,
    item_update: LookupUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Updates a unit's name."""
    db_item = db.query(Unit).filter(Unit.id == item_id, Unit.is_deleted == False).first()
    if not db_item:
        raise HTTPException(status_code=404, detail=f"Unit with id {item_id} not found")
    
    if item_update.name and item_update.name != db_item.name:
        existing_item = db.query(Unit).filter(
            Unit.name == item_update.name,
            Unit.id != item_id,
            Unit.is_deleted == False
        ).first()
        if existing_item:
            raise HTTPException(status_code=400, detail=f"Unit '{item_update.name}' already exists")
        db_item.name = item_update.name
    
    try:
        db_item.updated_by = current_user_id
        db_item.updated_at = func.now()
        db.commit()
        db.refresh(db_item)
        return db_item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update unit: {str(e)}")

# --- 5. DELETE A UNIT (Soft Delete) ---
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unit(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Soft-deletes a unit."""
    db_item = db.query(Unit).filter(Unit.id == item_id, Unit.is_deleted == False).first()
    if not db_item:
        raise HTTPException(status_code=404, detail=f"Unit with id {item_id} not found or already deleted")
    
    try:
        db_item.is_deleted = True
        db_item.deleted_at = func.now()
        db_item.deleted_by = current_user_id
        db.add(db_item)
        db.commit()
        return
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to soft delete unit: {str(e)}")