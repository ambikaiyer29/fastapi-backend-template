# app/crud/item_crud.py
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.models import Item
from app.schemas.item_schemas import ItemCreate, ItemUpdate


def create_item(db: Session, item: ItemCreate, tenant_id: UUID, user_id: UUID) -> Item:
    """
    Creates a new item record in the database for a specific tenant.

    The RLS policies in the database ensure that the user can only create items
    for their own tenant.
    """
    db_item = Item(
        **item.dict(),  # Unpack the Pydantic model into keyword arguments
        tenant_id=tenant_id,
        created_by=user_id
    )
    db.add(db_item)
    db.flush()
    return db_item


def get_item_by_id(db: Session, item_id: UUID) -> Item | None:
    """
    Fetches a single item by its ID.

    RLS policies automatically ensure this query will only find an item
    if it belongs to the current user's tenant.
    """
    return db.query(Item).filter(Item.id == item_id).first()


def get_items(db: Session) -> list[Item]:
    """
    Fetches all items for the current user's tenant.

    RLS policies automatically filter this query to only return items
    belonging to the tenant associated with the current session.
    """
    return db.query(Item).all()


def update_item(db: Session, db_item: Item, item_update: ItemUpdate, user_id: UUID) -> Item:
    """
    Updates an existing item's details.

    The item to update (db_item) is fetched by a function that already
    respects RLS, so we can be sure we are not updating another tenant's data.
    """
    update_data = item_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db_item.updated_by = user_id
    db.add(db_item)
    db.flush()
    return db_item


def delete_item(db: Session, db_item: Item):
    """
    Deletes an item from the database.

    Similar to update, the item to delete is pre-fetched by an RLS-aware function.
    """
    db.delete(db_item)
    db.flush()