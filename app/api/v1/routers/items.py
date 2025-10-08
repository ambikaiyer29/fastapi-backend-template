# app/api/v1/routers/items.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from supabase import create_client, Client
from app.core.config import get_settings, Settings

from app.api.v1.dependencies import get_auth_rls_session, require_permission  # Updated import
from app.api.v1.security import AuthenticatedUser
from app.schemas.item_schemas import ItemCreate, ItemRead, ItemUpdate
from app.crud import item_crud
from app.core.permissions import AppPermissions  # Import AppPermissions

router = APIRouter()


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_new_item(
        payload: ItemCreate,
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(require_permission(AppPermissions.ITEMS_CREATE))  # Permission check
):
    """
    Create a new item within the user's tenant.
    Any authenticated user in a tenant can create an item.
    """
    if not current_user.tenant_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Superadmins cannot create items for tenants.")

    return item_crud.create_item(
        db=db,
        item=payload,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )


@router.get("", response_model=List[ItemRead])
def get_all_items(
        db: Session = Depends(get_auth_rls_session),
        settings: Settings = Depends(get_settings),
        _permission_check=require_permission(AppPermissions.ITEMS_READ)
):
    """List all items for the user's tenant, with signed URLs for images."""
    db_items = item_crud.get_items(db=db)

    # Initialize supabase client to generate signed URLs
    supabase_admin: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    # Augment the response items with signed URLs
    response_items = []
    for item in db_items:
        item_read = ItemRead.model_validate(item, from_attributes=True)
        if item.image_path:
            try:
                # Generate a URL valid for 5 minutes
                res = supabase_admin.storage.from_("tenant-assets").create_signed_url(item.image_path, 300)
                item_read.image_url = res['signedURL']
            except Exception:
                item_read.image_url = None  # Handle error gracefully
        response_items.append(item_read)

    return response_items

@router.get("/{item_id}", response_model=ItemRead)
def get_item(
        item_id: UUID,
        db: Session = Depends(get_auth_rls_session),
        settings: Settings = Depends(get_settings),
        current_user: AuthenticatedUser = Depends(require_permission(AppPermissions.ITEMS_READ))  # Permission check
):
    """Get a specific item by its ID."""
    db_item = item_crud.get_item_by_id(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")

    if db_item.image_path:
        try:
            # Initialize supabase client to generate signed URLs
            supabase_admin: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
            # Generate a URL valid for 5 minutes
            res = supabase_admin.storage.from_("tenant-assets").create_signed_url(db_item.image_path, 300)
            db_item.image_url = res['signedURL']
        except Exception:
            db_item.image_url = None  # Handle error gracefully
    return db_item


@router.put("/{item_id}", response_model=ItemRead)
def update_existing_item(
        item_id: UUID,
        payload: ItemUpdate,
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(require_permission(AppPermissions.ITEMS_UPDATE))  # Permission check
):
    """Update an item's properties."""
    db_item = item_crud.get_item_by_id(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")

    return item_crud.update_item(
        db=db,
        db_item=db_item,
        item_update=payload,
        user_id=current_user.id
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_item(
        item_id: UUID,
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(require_permission(AppPermissions.ITEMS_DELETE))  # Permission check
):
    """Delete an item."""
    db_item = item_crud.get_item_by_id(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")

    item_crud.delete_item(db=db, db_item=db_item)