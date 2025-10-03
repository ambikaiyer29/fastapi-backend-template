# app/api/v1/routers/custom_objects.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app.api.v1.dependencies import get_auth_rls_session, require_permission, get_current_user
from app.api.v1.security import AuthenticatedUser
from app.schemas.dynamic_schemas import CustomObjectCreate, CustomObjectRead, CustomFieldCreate, CustomFieldRead
from app.crud import dynamic_crud
from app.core.permissions import AppPermissions

router = APIRouter()


@router.post("", response_model=CustomObjectRead, status_code=status.HTTP_201_CREATED)
def create_custom_object(
        payload: CustomObjectCreate,
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(get_current_user),
        _permission_check=Depends(require_permission(AppPermissions.CUSTOM_OBJECTS_CREATE))
):
    """Create a new Custom Object definition for the tenant."""
    try:
        return dynamic_crud.create_custom_object(
            db=db,
            obj_in=payload,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "A custom object with this slug already exists.")


@router.get("", response_model=List[CustomObjectRead])
def get_all_custom_objects(
        db: Session = Depends(get_auth_rls_session),
        _permission_check=Depends(require_permission(AppPermissions.CUSTOM_OBJECTS_READ))
):
    """List all Custom Objects defined for the tenant."""
    return dynamic_crud.get_all_custom_objects(db)


@router.post("/{object_slug}/fields", response_model=CustomFieldRead, status_code=status.HTTP_201_CREATED)
def create_custom_field(
        object_slug: str,
        payload: CustomFieldCreate,
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(get_current_user),
        _permission_check=Depends(require_permission(AppPermissions.CUSTOM_OBJECTS_CREATE))
):
    """Create a new Custom Field definition for a Custom Object."""
    custom_object = dynamic_crud.get_custom_object_by_slug(db, slug=object_slug)
    if not custom_object:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Custom object not found.")

    try:
        return dynamic_crud.create_custom_field(
            db=db,
            field_in=payload,
            object_id=custom_object.id,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "A field with this slug already exists for this object.")


@router.get("/{object_slug}", response_model=CustomObjectRead)
def get_custom_object_details(
        object_slug: str,
        db: Session = Depends(get_auth_rls_session),
        _permission_check=Depends(require_permission(AppPermissions.CUSTOM_OBJECTS_READ))
):
    """Get details and all field definitions for a specific Custom Object."""
    custom_object = dynamic_crud.get_custom_object_by_slug(db, slug=object_slug)
    if not custom_object:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Custom object not found.")
    return custom_object