# app/schemas/audit_log_schemas.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Dict, Any

class AuditLogRead(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID | None
    action: str
    details: Dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True