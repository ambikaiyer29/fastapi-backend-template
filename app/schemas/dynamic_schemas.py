from pydantic import BaseModel, Field, validator
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any, Literal

# Allowed field types for custom fields
FieldType = Literal['text', 'number', 'date', 'boolean', 'select']


class CustomFieldBase(BaseModel):
    name: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1, pattern=r'^[a-z_]+$')  # snake_case only
    field_type: FieldType
    is_required: bool = False
    options: Dict[str, Any] | None = None

    @validator('options')
    def validate_options(cls, v, values):
        if values.get('field_type') == 'select' and v is None:
            raise ValueError("The 'options' field is required for 'select' field type.")
        if values.get('field_type') != 'select' and v is not None:
            raise ValueError("The 'options' field is only allowed for 'select' field type.")
        return v


class CustomFieldCreate(CustomFieldBase):
    pass


class CustomFieldRead(CustomFieldBase):
    id: UUID
    object_id: UUID

    class Config:
        from_attributes = True


# --- Schemas for Custom Objects (Metadata) ---

class CustomObjectBase(BaseModel):
    name: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1, pattern=r'^[a-z_]+$')  # snake_case only


class CustomObjectCreate(CustomObjectBase):
    pass


class CustomObjectRead(CustomObjectBase):
    id: UUID
    fields: List[CustomFieldRead] = []

    class Config:
        from_attributes = True


class RecordBase(BaseModel):
    data: Dict[str, Any]


class RecordCreate(RecordBase):
    pass


class RecordUpdate(RecordBase):
    pass


class RecordRead(RecordBase):
    id: UUID
    object_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by_id: UUID

    class Config:
        from_attributes = True