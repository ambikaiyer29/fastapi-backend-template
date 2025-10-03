# app/api/v1/routers/records.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.v1.dependencies import get_auth_rls_session, require_permission, get_current_user
from app.api.v1.security import AuthenticatedUser
from app.schemas.dynamic_schemas import RecordCreate, RecordRead, RecordUpdate
from app.crud import dynamic_crud
from app.core.permissions import AppPermissions

router = APIRouter()


@router.post("/{object_slug}", response_model=RecordRead, status_code=status.HTTP_201_CREATED)
def create_new_record(
        object_slug: str,
        payload: RecordCreate,
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(get_current_user),
        _permission_check=Depends(require_permission(AppPermissions.RECORDS_CREATE))
):
    """Create a new record for a specified Custom Object."""
    custom_object = dynamic_crud.get_custom_object_by_slug(db, slug=object_slug)
    if not custom_object:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Custom object definition not found.")

    try:
        return dynamic_crud.create_record(
            db=db,
            record_in=payload,
            custom_object=custom_object,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.get("/{object_slug}", response_model=List[RecordRead])
def get_all_records(
        object_slug: str,
        db: Session = Depends(get_auth_rls_session),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        _permission_check=Depends(require_permission(AppPermissions.RECORDS_READ))
):
    """List all records for a specified Custom Object."""
    custom_object = dynamic_crud.get_custom_object_by_slug(db, slug=object_slug)
    if not custom_object:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Custom object definition not found.")

    return dynamic_crud.get_records_by_object(db, object_id=custom_object.id, skip=skip, limit=limit)


@router.get("/{object_slug}/{record_id}", response_model=RecordRead)
def get_record_details(
        object_slug: str,  # Included for URL consistency, though not strictly needed for lookup
        record_id: UUID,
        db: Session = Depends(get_auth_rls_session),
        _permission_check=Depends(require_permission(AppPermissions.RECORDS_READ))
):
    """Get a single record by its ID."""
    record = dynamic_crud.get_record_by_id(db, record_id=record_id)
    if not record or record.custom_object.slug != object_slug:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Record not found.")
    return record


@router.put("/{object_slug}/{record_id}", response_model=RecordRead)
def update_existing_record(
        object_slug: str,
        record_id: UUID,
        payload: RecordUpdate,
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(get_current_user),
        _permission_check=Depends(require_permission(AppPermissions.RECORDS_UPDATE))
):
    """Update a record."""
    record = dynamic_crud.get_record_by_id(db, record_id=record_id)
    if not record or record.custom_object.slug != object_slug:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Record not found.")

    try:
        return dynamic_crud.update_record(
            db=db,
            db_record=record,
            record_in=payload,
            custom_object=record.custom_object,
            user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.delete("/{object_slug}/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_record(
        object_slug: str,
        record_id: UUID,
        db: Session = Depends(get_auth_rls_session),
        _permission_check=Depends(require_permission(AppPermissions.RECORDS_DELETE))
):
    """Delete a record."""
    record = dynamic_crud.get_record_by_id(db, record_id=record_id)
    if not record or record.custom_object.slug != object_slug:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Record not found.")

    dynamic_crud.delete_record(db, db_record=record)