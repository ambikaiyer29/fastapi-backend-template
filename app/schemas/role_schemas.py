# app/schemas/role_schemas.py
from pydantic import BaseModel, Field, validator, computed_field
from uuid import UUID
from typing import List, Set

from app.core.permissions import AppPermissions # Import our permissions

class RoleCreate(BaseModel):
    """Schema for creating a new role."""
    name: str = Field(..., min_length=1, description="Name of the new role (e.g., 'Editor', 'Viewer')")
    # Allow creation with a list of permission names
    permissions: Set[str] = Field(default_factory=set, description="List of permission names for this role.")

    @validator('permissions', pre=True, each_item=True)
    def validate_permission_names(cls, v):
        if v not in AppPermissions.__members__:
            raise ValueError(f"'{v}' is not a valid permission name.")
        return v

    def to_permission_set_int(self) -> int:
        """Converts a list of permission names to an integer bitmask."""
        permission_mask = 0
        for p_name in self.permissions:
            permission_mask |= AppPermissions[p_name].value
        return permission_mask

class RoleUpdate(RoleCreate):
    """Schema for updating an existing role."""
    # We can reuse RoleCreate's structure, but add fields that might be optional on update
    name: str | None = Field(None, min_length=1, description="New name for the role")
    permissions: Set[str] | None = Field(None, description="New list of permission names for this role.")

class RoleRead(BaseModel):
    """Schema for reading role data."""
    id: UUID
    name: str
    is_admin_role: bool
    permission_set: int # We still want to see the raw integer

    # --- THIS IS THE FIX ---
    # Use @computed_field to derive the 'permissions' list.
    # This tells Pydantic to call this function to generate the value for this field.
    @computed_field
    @property
    def permissions(self) -> List[str]:
        """Decodes the permission_set integer back into a list of names."""
        decoded_permissions = []
        # 'self' here is the Pydantic model instance.
        # We can access other fields like 'self.permission_set'.
        permission_mask = self.permission_set or 0
        for p_name, p_flag in AppPermissions.__members__.items():
            if p_name != "NONE" and (permission_mask & p_flag.value) == p_flag.value:
                decoded_permissions.append(p_name)
        return decoded_permissions
    # --- END OF FIX ---

    class Config:
        # Pydantic v2 uses 'from_attributes' instead of 'orm_mode'
        from_attributes = True
