# app/crud/role_crud.py
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.models import UserRole
from app.schemas.role_schemas import RoleCreate, RoleUpdate  # Import RoleUpdate
from app.core.permissions import AppPermissions  # Import AppPermissions


def create_role(db: Session, role_data: RoleCreate, tenant_id: UUID, creator_id: UUID) -> UserRole:
    """Creates a new role within a tenant."""
    # Convert permission names to integer bitmask
    permission_int = role_data.to_permission_set_int()

    new_role = UserRole(
        name=role_data.name,
        tenant_id=tenant_id,
        is_admin_role=False,  # Custom roles are not super-admin by definition
        permission_set=permission_int,
        created_by=creator_id
    )
    db.add(new_role)
    db.flush()
    return new_role


def get_roles_by_tenant(db: Session) -> list[UserRole]:
    """Lists all roles for the tenant visible in the current RLS-scoped session."""
    return db.query(UserRole).all()


def get_role_by_id(db: Session, role_id: UUID) -> UserRole | None:
    """Fetches a single role by its ID."""
    return db.query(UserRole).filter(UserRole.id == role_id).first()


def update_role(db: Session, db_role: UserRole, role_update: RoleUpdate, updater_id: UUID) -> UserRole:
    """Updates an existing role's details."""
    update_data = role_update.dict(exclude_unset=True)

    if "name" in update_data:
        db_role.name = update_data["name"]

    if "permissions" in update_data and update_data["permissions"] is not None:
        # Convert new permission names to integer bitmask
        permission_mask = 0
        for p_name in update_data["permissions"]:
            permission_mask |= AppPermissions[p_name].value
        db_role.permission_set = permission_mask

    db_role.updated_by = updater_id
    db.add(db_role)
    db.flush()
    return db_role


def delete_role(db: Session, db_role: UserRole):
    """Deletes a role."""
    db.delete(db_role)
    db.flush()