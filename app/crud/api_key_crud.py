# app/crud/api_key_crud.py
import secrets
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.models import ApiKey
from app.api.v1.dependencies import pwd_context  # Import the hashing context


def create_api_key(db: Session, *, user_id: UUID, tenant_id: UUID) -> (ApiKey, str):
    """
    Generates a new API key, hashes it, and stores it in the database.
    Returns the database object and the full, unhashed key.
    """
    # Generate a secure, URL-safe random key
    full_key = f"sk_live_{secrets.token_urlsafe(32)}"

    # Create the prefix for display and lookup
    prefix = full_key.split('_')[2][:8]
    key_prefix = f"sk_live_{prefix}"

    # Hash the full key securely
    hashed_key = pwd_context.hash(full_key)

    new_api_key = ApiKey(
        user_id=user_id,
        tenant_id=tenant_id,
        key_prefix=key_prefix,
        hashed_key=hashed_key
    )
    db.add(new_api_key)
    db.flush()

    return new_api_key, full_key


def get_api_keys_by_user(db: Session, *, user_id: UUID) -> list[ApiKey]:
    """Retrieves all API keys for a specific user."""
    return db.query(ApiKey).filter(ApiKey.user_id == user_id).all()


def get_api_key_by_id(db: Session, *, api_key_id: UUID) -> ApiKey | None:
    """Retrieves a single API key by its ID."""
    return db.query(ApiKey).filter(ApiKey.id == api_key_id).first()


def delete_api_key(db: Session, db_api_key: ApiKey):
    """Deletes an API key."""
    db.delete(db_api_key)
    db.flush()