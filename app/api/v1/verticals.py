from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from uuid import UUID

from app.database import get_db
from app.models.lookup_models import Vertical 
from app.schemas.lookup_base import LookupCreate, LookupUpdate, Lookup as VerticalSchema

# --- PLACEHOLDER FOR DEPENDENCY ---
def get_current_user_id() -> UUID:
    return UUID('00000000-0000-0000-0000-000000000001')

router = APIRouter(
    prefix="/verticals",
    tags=["Verticals"],
)

# --- 1. CREATE A VERTICAL ---
@router.post("/", response_model=VerticalSchema, status_code=status.HTTP_201_CREATED)
async def create_vertical(
    item_in: LookupCreate, 
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Creates a new vertical."""
    existing_item = db.query(Vertical).filter(Vertical.name == item_in.name, Vertical.is_deleted == False).first()
    if existing_item:
        raise HTTPException(status_code=400, detail=f"Vertical '{item_in.name}' already exists")

    try:
        db_item = Vertical(name=item_in.name, created_by=current_user_id)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create vertical: {str(e)}")

# --- 2. GET ALL VERTICALS ---
@router.get("/", response_model=List[VerticalSchema])
async def get_all_verticals(db: Session = Depends(get_db)):
    """Returns all active verticals."""
    items = db.query(Vertical).filter(Vertical.is_deleted == False).all()
    return items

# --- 3. GET A SINGLE VERTICAL BY ID ---
@router.get("/{item_id}", response_model=VerticalSchema)
async def get_vertical_by_id(item_id: UUID, db: Session = Depends(get_db)):
    """Returns a specific vertical by ID."""
    item = db.query(Vertical).filter(Vertical.id == item_id, Vertical.is_deleted == False).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Vertical with id {item_id} not found")
    return item

# --- 4. UPDATE A VERTICAL ---
@router.put("/{item_id}", response_model=VerticalSchema)
async def update_vertical(
    item_id: UUID,
    item_update: LookupUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Updates a vertical's name."""
    db_item = db.query(Vertical).filter(Vertical.id == item_id, Vertical.is_deleted == False).first()
    if not db_item:
        raise HTTPException(status_code=404, detail=f"Vertical with id {item_id} not found")
    
    if item_update.name and item_update.name != db_item.name:
        existing_item = db.query(Vertical).filter(
            Vertical.name == item_update.name,
            Vertical.id != item_id,
            Vertical.is_deleted == False
        ).first()
        if existing_item:
            raise HTTPException(status_code=400, detail=f"Vertical '{item_update.name}' already exists")
        db_item.name = item_update.name
    
    try:
        db_item.updated_by = current_user_id
        db_item.updated_at = func.now()
        db.commit()
        db.refresh(db_item)
        return db_item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update vertical: {str(e)}")

# --- 5. DELETE A VERTICAL (Soft Delete) ---
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vertical(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Soft-deletes a vertical."""
    db_item = db.query(Vertical).filter(Vertical.id == item_id, Vertical.is_deleted == False).first()
    if not db_item:
        raise HTTPException(status_code=404, detail=f"Vertical with id {item_id} not found or already deleted")
    
    try:
        db_item.is_deleted = True
        db_item.deleted_at = func.now()
        db_item.deleted_by = current_user_id
        db.add(db_item)
        db.commit()
        return
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to soft delete vertical: {str(e)}")