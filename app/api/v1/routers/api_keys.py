# app/api/v1/routers/api_keys.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.v1.dependencies import get_auth_rls_session, get_current_user
from app.api.v1.security import AuthenticatedUser
from app.schemas.api_key_schemas import ApiKeyRead, ApiKeyCreateResponse
from app.crud import api_key_crud

router = APIRouter()


@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_new_api_key(
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Generate a new API key for the authenticated user.
    The full key is returned only once in this response.
    """
    if not current_user.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Superadmins cannot create API keys.")

    db_api_key, full_key = api_key_crud.create_api_key(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id
    )
    return {
        "api_key_details": db_api_key,
        "full_api_key": full_key
    }


@router.get("", response_model=List[ApiKeyRead])
def get_user_api_keys(
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(get_current_user)
):
    """List all API keys for the authenticated user."""
    return api_key_crud.get_api_keys_by_user(db=db, user_id=current_user.id)


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_api_key(
        api_key_id: UUID,
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Revoke/delete an API key."""
    db_api_key = api_key_crud.get_api_key_by_id(db=db, api_key_id=api_key_id)

    # RLS ensures they can only get their own keys.
    # We add an extra check for safety.
    if not db_api_key or db_api_key.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "API key not found.")

    api_key_crud.delete_api_key(db=db, db_api_key=db_api_key)