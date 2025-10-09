from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Dict, Any

# ===============================
# User Schemas
# ===============================
class UserRead(BaseModel):
    """Schema for safely returning user data."""
    id: UUID
    email: EmailStr

    class Config:
        from_attributes = True  # Enables the model to be created from an ORM object


# ===============================
# Tenant Schemas
# ===============================
class TenantCreate(BaseModel):
    """Schema for the data required to create a new tenant."""
    name: str = Field(..., min_length=1, description="Name of the new tenant")
    slug: str = Field(..., min_length=3, description="Unique slug for the tenant's URL")

    # Details for the tenant's first admin user
    admin_email: EmailStr = Field(..., description="Email for the tenant's primary admin")
    admin_password: str = Field(..., min_length=8, description="Password for the tenant's primary admin")
    terms_accepted: bool = Field(..., description="User must explicitly accept the terms and conditions.")


class TenantUpdate(BaseModel):
    """Schema for updating tenant details."""
    name: str | None = Field(None, min_length=1, description="New name of the tenant")
    slug: str | None = Field(None, min_length=3, description="New unique slug for the tenant's URL")
    tenant_data: Dict[str, Any] | None = Field(None, description="JSONB metadata for the tenant")
    logo_path: str | None = Field(None, description="Path to the tenant's logo in storage.")

class TenantRead(BaseModel):
    """Schema for safely returning tenant data."""
    id: UUID
    name: str
    slug: str
    admin_user_id: UUID | None
    tenant_data: Dict[str, Any] | None = Field(None) # Ensure metadata is read correctly
    created_at: datetime
    updated_at: datetime
    logo_path: str | None = Field(None, description="Path to the tenant's logo in storage.")
    logo_url: str | None = None  # This will not be populated from the DB directly.

    class Config:
        from_attributes = True
        allow_population_by_field_name = True # Allow setting by alias (metadata_)


class TenantOnboard(BaseModel):
    """Schema for a new user to onboard and create their first tenant."""
    name: str = Field(..., min_length=1, description="The display name of the new tenant.")
    slug: str = Field(..., min_length=3, description="The unique URL slug for the tenant.")
    terms_accepted: bool = Field(..., description="User must explicitly accept the terms and conditions.")
