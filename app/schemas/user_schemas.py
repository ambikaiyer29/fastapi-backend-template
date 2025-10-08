# app/schemas/user_schemas.py
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Dict, Any

class RoleRead(BaseModel):
    """Schema for reading role information."""
    id: UUID
    name: str

    class Config:
        from_attributes = True

class UserRead(BaseModel):
    """Schema for safely returning user data, including their role."""
    id: UUID
    email: EmailStr
    tenant_id: UUID
    role: RoleRead | None # The role can be optional if needed
    user_data: Dict[str, Any] | None = Field(None)

    class Config:
        from_attributes = True

class UserInvite(BaseModel):
    """Schema for inviting a new user."""
    email: EmailStr = Field(..., description="Email of the user to invite.")
    role_id: UUID = Field(..., description="The ID of the role to assign to the new user.")
    user_data: Dict[str, Any] | None = Field(None)

class UserUpdate(BaseModel):
    """Schema for updating a user's role."""
    role_id: UUID = Field(..., description="The new role ID to assign to the user.")
    user_data: Dict[str, Any] | None = Field(None)

class CompleteInvite(BaseModel):
    """Schema for an invited user to complete their account setup."""
    password: str = Field(..., min_length=8)
    terms_accepted: bool