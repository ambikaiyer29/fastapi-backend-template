from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Dict, Any

class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, description="The name of the customer (person or company).")
    email: EmailStr | None = Field(None, description="The customer's primary email address.")
    customer_data: Dict[str, Any] | None = Field(None, description="Flexible JSON field for custom attributes.")

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    email: EmailStr | None = None
    customer_data: Dict[str, Any] | None = None

class CustomerRead(CustomerBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by_id: UUID

    class Config:
        from_attributes = True