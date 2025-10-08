# app/api/v1/routers/audit_logs.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.api.v1.dependencies import get_auth_rls_session, get_tenant_admin
from app.schemas.audit_log_schemas import AuditLogRead
from app.crud import audit_log_crud
from app.db.models import User

router = APIRouter()

@router.get("", response_model=List[AuditLogRead])
def get_tenant_audit_logs(
    db: Session = Depends(get_auth_rls_session),
    # This endpoint is restricted to tenant admins
    admin_user: User = Depends(get_tenant_admin),
    skip: int = Query(0, ge=0, description="Skip the first N audit logs"),
    limit: int = Query(100, ge=1, le=1000, description="Return N audit logs, max 1000")
):
    """
    Retrieve a paginated list of audit logs for the current tenant.
    Restricted to users with an admin role.
    """
    return audit_log_crud.get_audit_logs_by_tenant(db=db, skip=skip, limit=limit)