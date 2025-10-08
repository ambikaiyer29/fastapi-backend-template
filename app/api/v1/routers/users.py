# app/api/v1/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.v1.dependencies import get_auth_rls_session, get_current_user, require_permission, check_entitlement
from app.api.v1.security import AuthenticatedUser
from app.core.permissions import AppPermissions
from app.schemas.user_schemas import UserRead
from app.crud import user_crud
from app.api.v1.dependencies import get_tenant_admin
from app.schemas.user_schemas import UserInvite, UserUpdate
from app.core.config import get_settings, Settings
from app.db.models import User
from supabase import create_client, Client
from uuid import UUID

router = APIRouter()


@router.get("/me", response_model=UserRead)
def read_current_user(
        current_user: AuthenticatedUser = Depends(get_current_user),
        db: Session = Depends(get_auth_rls_session)
):
    """
    Fetch the profile of the currently authenticated user.
    """
    # The get_current_user dependency already gives us the user's ID.
    # We fetch it again from the DB to get all related data, like the role.
    user = user_crud.get_user_by_id(db, user_id=current_user.id)
    if not user:
        # This should theoretically not happen if the JWT is valid and user exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current user not found.")
    return user


@router.get("", response_model=List[UserRead])
def read_users_in_tenant(
        db: Session = Depends(get_auth_rls_session)
):
    """
    Fetch all users within the current user's tenant.

    - A regular tenant user will only see users from their own tenant.
    - The superadmin will see all users across all tenants.
    This is enforced by the RLS policies and the get_auth_rls_session dependency.
    """
    users = user_crud.get_users_by_tenant(db)
    return users


@router.post("/invite", response_model=UserRead)
def invite_new_user(
        payload: UserInvite,
        db: Session = Depends(get_auth_rls_session),
        settings: Settings = Depends(get_settings),
        current_user: AuthenticatedUser = Depends(get_current_user),
        # 2. Perform the permission check as a separate, "silent" dependency.
        #    Use an underscore to indicate we don't need its return value.
        _permission_check=Depends(require_permission(AppPermissions.USERS_INVITE)),
        # --- THIS IS THE NEW ENTITLEMENT CHECK ---
        # This dependency will run and check if the tenant is allowed to add another user.
        # It will raise a 402 Payment Required error if the limit is reached.
        _entitlement_check=check_entitlement("max_users")
        # --- END OF ADDITION ---
):
    """Invite a new user to the tenant."""
    supabase_admin: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    try:
        new_user = user_crud.invite_user(
            db=db,
            invite_data=payload,
            tenant_id=current_user.tenant_id,
            inviter_id=current_user.id,
            supabase_admin=supabase_admin
        )
        return new_user
    except ValueError as e:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.put("/{user_id}", response_model=UserRead)
def update_user_profile(  # Renamed to avoid confusion with internal UserUpdate schema
        user_id: UUID,
        payload: UserUpdate,
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(require_permission(AppPermissions.USERS_UPDATE_ROLE))
        # Permission check
):
    """Update a user's role."""
    # Prevent users from changing their own role via this endpoint (to prevent self-lockout)
    if user_id == current_user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot update your own role via this endpoint.")

    try:
        updated_user = user_crud.update_user_role(
            db=db,
            user_id=user_id,
            role_id=payload.role_id,
            updater_id=current_user.id
        )
        return updated_user
    except ValueError as e:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_from_tenant(
        user_id: UUID,
        db: Session = Depends(get_auth_rls_session),
        settings: Settings = Depends(get_settings),
        current_user: AuthenticatedUser = Depends(get_current_user),
        _permission_check = Depends(require_permission(AppPermissions.USERS_DELETE))  # Permission check
):
    """Delete a user from the tenant."""
    if user_id == current_user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Admins cannot delete themselves.")

    supabase_admin: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    try:
        user_crud.delete_user(db=db, user_id=user_id, supabase_admin=supabase_admin)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))