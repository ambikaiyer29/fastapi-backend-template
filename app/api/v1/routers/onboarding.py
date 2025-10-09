# app/api/v1/routers/onboarding.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user, get_auth_rls_session
from app.api.v1.security import AuthenticatedUser
from app.crud import tenant_crud # We will add a new function here
from app.schemas.tenant_schemas import TenantRead, TenantOnboard

router = APIRouter()

# This is for the self-service onboarding flow. after the /auth/signup

@router.post("/tenant", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
def onboard_new_tenant(
    payload: TenantOnboard,
    db: Session = Depends(get_auth_rls_session),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Onboarding for a newly signed-up user to create their first tenant.
    This endpoint should only be called once per user.
    """
    # --- ADD THIS VALIDATION CHECK ---
    if not payload.terms_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the Terms and Conditions to proceed."
        )
    # --- END OF ADDITION ---

    # Critical Check: Ensure this user is not already part of a tenant.
    if current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user is already associated with a tenant."
        )

    # Use a new CRUD function to create the tenant and link the user
    try:
        new_tenant = tenant_crud.create_tenant_for_new_user(
            db=db,
            tenant_data=payload,
            user=current_user
        )
        return new_tenant
    except Exception as e:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))