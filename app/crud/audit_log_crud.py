# app/crud/audit_log_crud.py
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any

from app.db.models import AuditLog

def create_audit_log(
    db: Session,
    *,
    tenant_id: UUID,
    user_id: UUID,
    action: str,
    details: Dict[str, Any]
):
    """Creates a new audit log entry."""
    log_entry = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        details=details
    )
    db.add(log_entry)
    # The calling function is responsible for the db.commit() or db.flush()

def get_audit_logs_by_tenant(db: Session, *, skip: int = 0, limit: int = 100) -> list[AuditLog]:
    """Retrieves a paginated list of audit logs for the tenant in the current RLS scope."""
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()