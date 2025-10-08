# app/schemas/item_schemas.py
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the item")
    price: int = Field(..., gt=0, description="Price of the item in cents")
    quantity: int = Field(..., ge=0, description="Quantity of the item in stock")
    image_path: str | None = Field(None, description="Path to the item's image in storage.")

# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass

# Properties to receive on item update
class ItemUpdate(ItemBase):
    pass

# Properties to return to the client
class ItemRead(ItemBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    image_url: str | None = None  # We will dynamically add a signed URL here

    class Config:
        from_attributes = True