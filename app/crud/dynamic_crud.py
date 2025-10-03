from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from datetime import date, datetime

from app.db.models import CustomObject, CustomField, Record
from app.schemas.dynamic_schemas import CustomObjectCreate, CustomFieldCreate, RecordCreate, RecordUpdate


# --- CRUD for Custom Objects (Metadata) ---

def create_custom_object(db: Session, obj_in: CustomObjectCreate, tenant_id: UUID, user_id: UUID) -> CustomObject:
    db_obj = CustomObject(**obj_in.dict(), tenant_id=tenant_id, created_by_id=user_id)
    db.add(db_obj)
    db.flush()
    return db_obj


def get_custom_object_by_slug(db: Session, slug: str) -> CustomObject | None:
    # RLS automatically scopes this to the current tenant
    return db.query(CustomObject).options(joinedload(CustomObject.fields)).filter(CustomObject.slug == slug).first()


def get_all_custom_objects(db: Session) -> list[CustomObject]:
    return db.query(CustomObject).all()


# --- CRUD for Custom Fields (Metadata) ---

def create_custom_field(db: Session, field_in: CustomFieldCreate, object_id: UUID, tenant_id: UUID,
                        user_id: UUID) -> CustomField:
    db_field = CustomField(**field_in.dict(), object_id=object_id, tenant_id=tenant_id, created_by_id=user_id)
    db.add(db_field)
    db.flush()
    return db_field


# --- CRUD for Records (Actual Data) ---

def validate_record_data(data: dict, fields: list[CustomField]):
    """
    Validates a record's data against its object's field definitions.
    This is the core validation engine.
    """
    validated_data = {}
    field_map = {field.slug: field for field in fields}

    # Check for required fields
    for field in fields:
        if field.is_required and field.slug not in data:
            raise ValueError(f"Required field '{field.name}' ({field.slug}) is missing.")

    # Validate provided data
    for slug, value in data.items():
        if slug not in field_map:
            raise ValueError(f"'{slug}' is not a valid field for this object.")

        field = field_map[slug]

        # Type validation and coercion
        try:
            if field.field_type == 'text':
                if not isinstance(value, str): raise TypeError()
                validated_data[slug] = value
            elif field.field_type == 'number':
                if not isinstance(value, (int, float)): raise TypeError()
                validated_data[slug] = value
            elif field.field_type == 'boolean':
                if not isinstance(value, bool): raise TypeError()
                validated_data[slug] = value
            elif field.field_type == 'date':
                # Expects ISO format string (e.g., "2023-12-31")
                validated_data[slug] = date.fromisoformat(value).isoformat()
            elif field.field_type == 'select':
                if value not in field.options.get('options', []):
                    raise ValueError(f"'{value}' is not a valid option for '{field.name}'.")
                validated_data[slug] = value
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid value for field '{field.name}': {e or 'Incorrect type.'}")

    return validated_data


def create_record(db: Session, record_in: RecordCreate, custom_object: CustomObject, tenant_id: UUID,
                  user_id: UUID) -> Record:
    # 1. Validate the incoming data against the object's field definitions
    validated_data = validate_record_data(record_in.data, custom_object.fields)

    # 2. Create the record with the validated data
    db_record = Record(
        object_id=custom_object.id,
        tenant_id=tenant_id,
        data=validated_data,
        created_by_id=user_id
    )
    db.add(db_record)
    db.flush()
    return db_record


def get_records_by_object(db: Session, object_id: UUID, skip: int = 0, limit: int = 100) -> list[Record]:
    return db.query(Record).filter(Record.object_id == object_id).order_by(Record.created_at.desc()).offset(skip).limit(
        limit).all()

def get_record_by_id(db: Session, record_id: UUID) -> Record | None:
    return db.query(Record).filter(Record.id == record_id).first()


def update_record(db: Session, db_record: Record, record_in: RecordUpdate, custom_object: CustomObject,
                  user_id: UUID) -> Record:
    # Validate the updated data. Note: this simple validator expects all fields.
    # A more advanced version might handle partial updates.
    validated_data = validate_record_data(record_in.data, custom_object.fields)

    db_record.data = validated_data
    db_record.updated_by_id = user_id
    db.add(db_record)
    db.flush()
    return db_record


def delete_record(db: Session, db_record: Record):
    db.delete(db_record)
    db.flush()