# app/api/v1/routers/tenants.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.utils.decorators import log_request
from app.api.v1.dependencies import get_auth_rls_session, get_superadmin
from app.schemas.tenant_schemas import TenantCreate, TenantRead
from app.crud import tenant_crud
from app.core.config import get_settings, Settings
from app.api.v1.dependencies import get_tenant_admin # Import the tenant admin dependency
from app.schemas.tenant_schemas import TenantUpdate # Import TenantUpdate
from app.db.models import User
from supabase import create_client, Client # Import Supabase client

# Create a new router for tenants
router = APIRouter()


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
@log_request
def create_tenant(
        payload: TenantCreate,
        db: Session = Depends(get_auth_rls_session),
        settings: Settings = Depends(get_settings),
        # This dependency ensures only the superadmin can call this endpoint
        superadmin=Depends(get_superadmin)
):
    """
    Onboard a new tenant.

    This is a privileged operation, restricted to superadmins.
    It creates a new tenant, a default admin role, and the primary admin user
    in both Supabase Auth and the local database.
    """
    try:
        if not payload.terms_accepted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must accept the Terms and Conditions to proceed."
            )

        new_tenant = tenant_crud.create_tenant_with_admin_user(
            db=db,
            tenant_data=payload,
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY
        )
        return new_tenant
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A tenant with slug '{payload.slug}' already exists."
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# You can add more tenant-related endpoints here later, like:
# @router.get("/{tenant_id}", response_model=TenantRead)
# def read_tenant(...):
#     # Logic to get a specific tenant
#     pass


@router.get("/me", response_model=TenantRead)
def read_current_tenant(
        db: Session = Depends(get_auth_rls_session),
        admin_user: User = Depends(get_tenant_admin),
        settings: Settings = Depends(get_settings),
):
    """
    Fetch details for the currently authenticated user's tenant.
    This is restricted to tenant admins.
    """
    # The get_tenant_admin dependency ensures the user is an admin.
    # The RLS session will ensure we can only fetch the user's own tenant.
    tenant = tenant_crud.get_tenant_by_id(db, tenant_id=admin_user.tenant_id)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found.")

    # Convert to Pydantic model
    tenant_read = TenantRead.model_validate(tenant, from_attributes=True)

    # Generate a signed URL for the logo if a path exists
    if tenant.logo_path:
        supabase_admin: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        try:
            res = supabase_admin.storage.from_("tenant-assets").create_signed_url(tenant.logo_path, 300)  # 5-minute URL
            tenant_read.logo_url = res['signedURL']
        except Exception:
            tenant_read.logo_url = None  # Fail gracefully

    return tenant_read


@router.put("/me", response_model=TenantRead)
def update_current_tenant(
        payload: TenantUpdate,
        db: Session = Depends(get_auth_rls_session),
        admin_user: User = Depends(get_tenant_admin),
):
    """
    Update details for the currently authenticated user's tenant.
    This is restricted to tenant admins.
    """
    # The admin_user object already contains the tenant_id, so we can fetch the tenant directly.
    db_tenant = tenant_crud.get_tenant_by_id(db, tenant_id=admin_user.tenant_id)
    if not db_tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found.")

    # Prevent a tenant admin from changing their slug, which is a superadmin-only action.
    if payload.slug is not None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tenant slug can only be changed by a superadmin.")

    return tenant_crud.update_tenant(
        db=db,
        db_tenant=db_tenant,
        tenant_update=payload,
        updater_id=admin_user.id
    )