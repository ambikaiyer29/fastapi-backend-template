# app/schemas/api_key_schemas.py
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class ApiKeyRead(BaseModel):
    """Schema for displaying an API key (prefix only)."""
    id: UUID
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None

    class Config:
        from_attributes = True


class ApiKeyCreateResponse(BaseModel):
    """
    Schema for the response when a new API key is created.
    The full key is shown only once.
    """
    message: str = "API key created successfully. Please save this key securely. You will not be able to see it again."
    api_key_details: ApiKeyRead
    full_api_key: str = Field(..., description="The full, unhashed API key. This is shown only once.")