from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import func
from uuid import UUID

from app.database import get_db
from app.models.project import Project
from app.models.account import Account
from app.schemas.project import ProjectCreate, ProjectUpdate, Project as ProjectSchema

# --- TEMP DEPENDENCY (replace with real auth later) ---
def get_current_user_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000001")


router = APIRouter(prefix="/projects", tags=["Projects"])


# ---------------------------
# 1. CREATE A PROJECT
# ---------------------------
@router.post("/", response_model=ProjectSchema, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Create a project. Requires a valid account_id (project must belong to an account).
    Validates project_code uniqueness if provided.
    Returns the created project with the related account loaded.
    """
    # Validate account existence (business rule: project must have an account)
    account = db.query(Account).filter(Account.id == project_in.account_id, Account.is_deleted == False).first()
    if not account:
        raise HTTPException(status_code=400, detail="account_id is invalid or the account is deleted")

    # Optional: validate unique project_code if provided
    if project_in.project_code:
        duplicate = db.query(Project).filter(
            Project.project_code == project_in.project_code,
            Project.is_deleted == False
        ).first()
        if duplicate:
            raise HTTPException(status_code=400, detail=f"Project code '{project_in.project_code}' already exists")

    try:
        project_fields = project_in.model_dump(exclude_none=True)
        db_project = Project(**project_fields, created_by=current_user_id)
        db.add(db_project)

        # Flush to populate DB defaults / get PK, though we will refresh after commit
        db.flush()
        db.commit()
        db.refresh(db_project)

        # Return the project with related account loaded (avoid N+1 on clients)
        project_with_account = db.query(Project).options(
            selectinload(Project.account)
        ).filter(Project.id == db_project.id).first()

        return project_with_account

    except Exception as e:
        db.rollback()
        print(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


# ---------------------------
# 2. GET ALL PROJECTS
# ---------------------------
@router.get("/", response_model=List[ProjectSchema])
async def get_all_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Retrieve a paginated list of active projects. Loads the related Account to avoid N+1.
    """
    projects = db.query(Project).options(
        selectinload(Project.account)
    ).filter(Project.is_deleted == False).offset(skip).limit(limit).all()
    return projects


# ---------------------------
# 3. GET A SINGLE PROJECT BY ID
# ---------------------------
@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project_by_id(project_id: UUID, db: Session = Depends(get_db)):
    """
    Retrieve a single project (with its account).
    """
    db_project = db.query(Project).options(
        selectinload(Project.account)
    ).filter(Project.id == project_id, Project.is_deleted == False).first()

    if not db_project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")

    return db_project


# ---------------------------
# 4. UPDATE A PROJECT
# ---------------------------
@router.put("/{project_id}", response_model=ProjectSchema)
async def update_project_details(
    project_id: UUID,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Update mutable fields of an existing project.
    Validates new account_id if provided and uniqueness of project_code if changed.
    Returns the updated project with the related account loaded.
    """
    db_project = db.query(Project).filter(Project.id == project_id, Project.is_deleted == False).first()
    if not db_project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")

    # If client attempts to change project_code, validate uniqueness
    update_data = project_update.model_dump(exclude_unset=True)

    if "project_code" in update_data and update_data["project_code"] != db_project.project_code:
        if update_data["project_code"]:
            dup = db.query(Project).filter(
                Project.project_code == update_data["project_code"],
                Project.id != project_id,
                Project.is_deleted == False
            ).first()
            if dup:
                raise HTTPException(status_code=400, detail=f"Project code '{update_data['project_code']}' already exists")

    # If account_id is present in update, validate it
    if "account_id" in update_data:
        new_account_id = update_data["account_id"]
        if new_account_id is None:
            raise HTTPException(status_code=400, detail="account_id cannot be null")
        acct = db.query(Account).filter(Account.id == new_account_id, Account.is_deleted == False).first()
        if not acct:
            raise HTTPException(status_code=400, detail="Provided account_id is invalid or deleted")

    try:
        # Apply updates
        for key, value in update_data.items():
            if hasattr(db_project, key):
                setattr(db_project, key, value)

        db_project.updated_by = current_user_id
        db_project.updated_at = func.now()

        db.commit()
        db.refresh(db_project)

        updated = db.query(Project).options(selectinload(Project.account)).filter(Project.id == project_id).first()
        return updated

    except Exception as e:
        db.rollback()
        print(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")


# ---------------------------
# 5. SOFT DELETE A PROJECT
# ---------------------------
@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Soft-delete a project (set is_deleted + deleted_at + deleted_by).
    Also updates updated_at and updated_by.
    """
    db_project = db.query(Project).filter(Project.id == project_id, Project.is_deleted == False).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found or already deleted")

    try:
        db_project.is_deleted = True
        db_project.updated_at = func.now()
        db_project.updated_by = current_user_id
        db_project.deleted_at = func.now()
        db_project.deleted_by = current_user_id

        db.add(db_project)
        db.commit()
        return

    except Exception as e:
        db.rollback()
        print(f"Error soft deleting project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to soft delete project: {str(e)}")
