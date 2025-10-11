# In app/api/v1/routers/audit_logs.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

# --- THIS IS THE FIX ---
# Import the specific user model and dependencies needed
from app.api.v1.dependencies import get_auth_rls_session, get_tenant_admin
from app.api.v1.security import AuthenticatedUser # Use AuthenticatedUser for type hint
# --- END OF FIX ---
from app.schemas.audit_log_schemas import AuditLogRead
from app.crud import audit_log_crud


router = APIRouter()

@router.get("", response_model=List[AuditLogRead])
def get_tenant_audit_logs(
    # 1. Get the RLS-scoped session. This is our primary dependency.
    db: Session = Depends(get_auth_rls_session),
    # 2. As a separate check, ensure the user is an admin.
    #    We use an underscore because we don't need the return value in the endpoint body,
    #    as the check is all that matters.
    _admin_check: AuthenticatedUser = Depends(get_tenant_admin),
    skip: int = Query(0, ge=0, description="Skip the first N audit logs"),
    limit: int = Query(100, ge=1, le=1000, description="Return N audit logs, max 1000")
):
    """
    Retrieve a paginated list of audit logs for the current tenant.
    Restricted to users with an admin role.
    """
    # The 'db' session is now guaranteed to be the correctly authenticated and
    # RLS-scoped session, and we've verified the user is an admin.
    return audit_log_crud.get_audit_logs_by_tenant(db=db, skip=skip, limit=limit)