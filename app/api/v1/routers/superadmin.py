# app/api/v1/routers/superadmin.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.v1.dependencies import get_auth_rls_session, get_superadmin
from app.api.v1.security import AuthenticatedUser
from app.schemas.plan_schemas import TenantPlanAssignment
from app.schemas.tenant_schemas import TenantRead, TenantUpdate  # Import TenantUpdate
from app.crud import tenant_crud, plan_crud
from app.core.config import get_settings, Settings
from supabase import create_client, Client  # Needed for supabase admin client

router = APIRouter()


# All endpoints in this router will be implicitly for superadmins because of the prefix
# and/or explicit dependency in the API hub.
# We'll still use get_superadmin on individual endpoints for clarity and safety.

@router.get("/tenants", response_model=List[TenantRead])
def get_all_tenants(
        db: Session = Depends(get_auth_rls_session),
        superadmin_user: AuthenticatedUser = Depends(get_superadmin)  # Explicit superadmin check
):
    """
    [SUPERADMIN ONLY] Retrieve a list of all tenants.
    RLS is bypassed for the superadmin user automatically.
    """
    return tenant_crud.get_all_tenants_superadmin(db)


@router.get("/tenants/{tenant_id}", response_model=TenantRead)
def get_tenant_details(
        tenant_id: UUID,
        db: Session = Depends(get_auth_rls_session),
        superadmin_user: AuthenticatedUser = Depends(get_superadmin)  # Explicit superadmin check
):
    """
    [SUPERADMIN ONLY] Retrieve details for a specific tenant.
    """
    tenant = tenant_crud.get_tenant_by_id_superadmin(db, tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found.")
    return tenant


@router.put("/tenants/{tenant_id}", response_model=TenantRead)
def update_tenant_details(
        tenant_id: UUID,
        payload: TenantUpdate,
        db: Session = Depends(get_auth_rls_session),
        settings: Settings = Depends(get_settings),
        superadmin_user: AuthenticatedUser = Depends(get_superadmin)  # Explicit superadmin check
):
    """
    [SUPERADMIN ONLY] Update details for a specific tenant.
    """
    db_tenant = tenant_crud.get_tenant_by_id_superadmin(db, tenant_id=tenant_id)
    if not db_tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found.")

    try:
        updated_tenant = tenant_crud.update_tenant_superadmin(
            db=db,
            db_tenant=db_tenant,
            tenant_update=payload,
            updater_id=superadmin_user.id
        )
        return updated_tenant
    except IntegrityError:  # E.g., duplicate slug
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "A tenant with this slug already exists.")


@router.delete("/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant_and_users(
        tenant_id: UUID,
        db: Session = Depends(get_auth_rls_session),
        settings: Settings = Depends(get_settings),
        superadmin_user: AuthenticatedUser = Depends(get_superadmin)  # Explicit superadmin check
):
    """
    [SUPERADMIN ONLY] Delete a tenant and all its associated users from Supabase Auth and database.
    """
    db_tenant = tenant_crud.get_tenant_by_id_superadmin(db, tenant_id=tenant_id)
    if not db_tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found.")

    supabase_admin: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    try:
        tenant_crud.delete_tenant_superadmin(
            db=db,
            db_tenant=db_tenant,
            supabase_admin=supabase_admin
        )
    except Exception as e:
        db.rollback()
        # Catch any unexpected errors during deletion, possibly from Supabase Auth
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Error deleting tenant: {e}")


# --- ADD THIS NEW ENDPOINT ---
@router.post("/tenants/{tenant_id}/assign-plan", response_model=TenantRead)
def assign_plan_to_tenant(
        tenant_id: UUID,
        payload: TenantPlanAssignment,
        db: Session = Depends(get_auth_rls_session),
        superadmin_user: AuthenticatedUser = Depends(get_superadmin)
):
    """
    [SUPERADMIN ONLY] Manually assign a subscription plan to a tenant.
    This simulates a successful payment/subscription event.
    """
    db_tenant = tenant_crud.get_tenant_by_id_superadmin(db, tenant_id=tenant_id)
    if not db_tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found.")

    # Also verify that the plan exists
    db_plan = plan_crud.get_plan_by_id(db, plan_id=payload.plan_id)
    if not db_plan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found.")

    return tenant_crud.assign_plan_to_tenant(
        db=db,
        db_tenant=db_tenant,
        plan_assign=payload,
        updater_id=superadmin_user.id
    )