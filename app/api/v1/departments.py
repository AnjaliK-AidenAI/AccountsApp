from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from uuid import UUID

from app.database import get_db
from app.models.lookup_models import Department
from app.schemas.lookup_base import LookupCreate, LookupUpdate, Lookup as DepartmentSchema


# --- TEMPORARY PLACEHOLDER (Replace with real auth later) ---
def get_current_user_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000001")


router = APIRouter(
    prefix="/departments",
    tags=["Departments"],
)


# ---------------------------
# 1. CREATE DEPARTMENT
# ---------------------------
@router.post("/", response_model=DepartmentSchema, status_code=status.HTTP_201_CREATED)
async def create_department(
    payload: LookupCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Create a new department."""

    existing = (
        db.query(Department)
        .filter(Department.name == payload.name, Department.is_deleted == False)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail=f"Department '{payload.name}' already exists"
        )

    try:
        department = Department(
            name=payload.name,
            created_by=current_user_id,
        )
        db.add(department)
        db.commit()
        db.refresh(department)
        return department

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create department: {str(e)}"
        )


# ---------------------------
# 2. GET ALL DEPARTMENTS
# ---------------------------
@router.get("/", response_model=List[DepartmentSchema])
async def get_all_departments(db: Session = Depends(get_db)):
    """Get all active (not deleted) departments."""
    return db.query(Department).filter(Department.is_deleted == False).all()


# ---------------------------
# 3. GET DEPARTMENT BY ID
# ---------------------------
@router.get("/{department_id}", response_model=DepartmentSchema)
async def get_department_by_id(
    department_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve a single department."""
    department = (
        db.query(Department)
        .filter(Department.id == department_id, Department.is_deleted == False)
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=404,
            detail=f"Department with id '{department_id}' not found",
        )

    return department


# ---------------------------
# 4. UPDATE DEPARTMENT
# ---------------------------
@router.put("/{department_id}", response_model=DepartmentSchema)
async def update_department(
    department_id: UUID,
    payload: LookupUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Update department name."""

    department = (
        db.query(Department)
        .filter(Department.id == department_id, Department.is_deleted == False)
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=404,
            detail=f"Department with id '{department_id}' not found",
        )

    # Name change only if name provided & not same
    if payload.name and payload.name != department.name:
        exists = (
            db.query(Department)
            .filter(
                Department.name == payload.name,
                Department.id != department_id,
                Department.is_deleted == False,
            )
            .first()
        )
        if exists:
            raise HTTPException(
                status_code=400,
                detail=f"Department '{payload.name}' already exists",
            )

        department.name = payload.name

    try:
        department.updated_by = current_user_id
        department.updated_at = func.now()
        db.commit()
        db.refresh(department)
        return department

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update department: {str(e)}",
        )


# ---------------------------
# 5. SOFT DELETE DEPARTMENT
# ---------------------------
@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Soft delete (mark as deleted) a department."""

    department = (
        db.query(Department)
        .filter(Department.id == department_id, Department.is_deleted == False)
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=404,
            detail=f"Department with id '{department_id}' not found or already deleted",
        )

    try:
        department.is_deleted = True
        department.deleted_by = current_user_id
        department.deleted_at = func.now()

        db.commit()
        return

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete department: {str(e)}",
        )
