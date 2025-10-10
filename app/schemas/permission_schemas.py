# app/schemas/permission_schemas.py
from pydantic import BaseModel
from typing import List

class PermissionRead(BaseModel):
    """Schema for displaying a single permission."""
    name: str
    description: str

class PermissionGroupRead(BaseModel):
    """Schema for displaying a group of related permissions."""
    group_name: str
    permissions: List[PermissionRead]