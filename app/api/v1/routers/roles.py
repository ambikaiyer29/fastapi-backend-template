# app/api/v1/routers/roles.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from uuid import UUID

from app.api.v1.dependencies import get_auth_rls_session, require_permission  # Updated imports
from app.schemas.role_schemas import RoleCreate, RoleRead, RoleUpdate  # Import RoleUpdate
from app.crud import role_crud
from app.core.permissions import AppPermissions  # Import AppPermissions
from app.api.v1.security import AuthenticatedUser  # Needed for current_user.id

router = APIRouter()


@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
def create_new_role(
        payload: RoleCreate,
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(require_permission(AppPermissions.ROLES_CREATE))  # Permission check
):
    """Create a new custom role within the tenant."""
    try:
        new_role = role_crud.create_role(
            db=db,
            role_data=payload,
            tenant_id=current_user.tenant_id,
            creator_id=current_user.id
        )
        return new_role
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "A role with this name already exists in your tenant.")


@router.get("", response_model=List[RoleRead])
def get_all_roles(
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(require_permission(AppPermissions.ROLES_READ))  # Permission check
):
    """List all roles in the current user's tenant."""
    return role_crud.get_roles_by_tenant(db)


@router.get("/{role_id}", response_model=RoleRead)
def get_role_by_id(
        role_id: UUID,
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(require_permission(AppPermissions.ROLES_READ))
):
    """Get a specific role by ID."""
    role = role_crud.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found.")
    return role


@router.put("/{role_id}", response_model=RoleRead)
def update_existing_role(
        role_id: UUID,
        payload: RoleUpdate,
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(require_permission(AppPermissions.ROLES_UPDATE))
):
    """Update an existing role."""
    db_role = role_crud.get_role_by_id(db, role_id)
    if not db_role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found.")

    # Prevent updating admin role permissions via this endpoint, or if it's the default admin role
    # This is a sensible protection to avoid locking out the main tenant admin
    if db_role.is_admin_role:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role permissions cannot be updated via this endpoint.")

    return role_crud.update_role(
        db=db,
        db_role=db_role,
        role_update=payload,
        updater_id=current_user.id
    )


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_role(
        role_id: UUID,
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(require_permission(AppPermissions.ROLES_DELETE))
):
    """Delete a role."""
    db_role = role_crud.get_role_by_id(db, role_id)
    if not db_role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found.")

    # Prevent deleting admin role
    if db_role.is_admin_role:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role cannot be deleted.")

    # Check if any users are assigned to this role before deleting
    from app.db.models import User  # Import User model here to avoid circular dependency
    if db.query(User).filter(User.role_id == role_id).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot delete role while users are assigned to it.")

    role_crud.delete_role(db=db, db_item=db_role)