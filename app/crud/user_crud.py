# app/crud/user_crud.py
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from supabase import Client
from sqlalchemy import func, and_

from app.crud.audit_log_crud import create_audit_log
from app.db.models import User, UserRole
from app.schemas.user_schemas import UserInvite

def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """
    Fetches a single user by their ID.

    Note: RLS policies are applied automatically at the database level.
    This function will return a user only if the requester has permission to see them.
    We use joinedload to efficiently fetch the related role in the same query.
    """
    return db.query(User).options(joinedload(User.role)).filter(User.id == user_id).first()


def get_users_by_tenant(db: Session) -> list[User]:
    """
    Fetches all users that the current session is allowed to see.

    The magic happens here: RLS policies automatically filter this query
    to only include users from the requester's own tenant. The superadmin
    will see all users across all tenants.
    """
    return db.query(User).options(joinedload(User.role)).all()


def invite_user(db: Session, invite_data: UserInvite, tenant_id: UUID, inviter_id: UUID,
                supabase_admin: Client) -> User:
    """Invites a user to a tenant and creates their profile."""
    # First, check if the role they are assigning belongs to their tenant
    role = db.query(UserRole).filter(UserRole.id == invite_data.role_id).first()
    if not role:
        raise ValueError("Role not found or you do not have permission to assign it.")

    try:
        # Use the admin invite method. This creates the auth user and sends a magic link.
        response = supabase_admin.auth.admin.invite_user_by_email(invite_data.email)
        invited_auth_user = response.user
        if not invited_auth_user:
            raise Exception("Failed to invite user in Supabase Auth.")
    except Exception as e:
        error_message = str(e)
        if "User already exists" in error_message:
            raise ValueError("User with this email already exists.")
        raise ValueError(f"Supabase Auth error: {error_message}")

    # Create the user profile in our local database
    new_user_profile = User(
        id=invited_auth_user.id,
        email=invite_data.email,
        tenant_id=tenant_id,
        role_id=invite_data.role_id,
        created_by=inviter_id
    )
    db.add(new_user_profile)
    db.flush()

    # --- ADD AUDIT LOG ---
    create_audit_log(
        db=db,
        tenant_id=tenant_id,
        user_id=inviter_id,
        action="USER_INVITED",
        details={
            "invited_user_id": new_user_profile.id,
            "invited_email": new_user_profile.email,
            "role_id": str(new_user_profile.role_id)
        }
    )
    # --- END ---
    return new_user_profile


def update_user_role(db: Session, user_id_to_update: UUID, new_role_id: UUID, updater_id: UUID) -> User:
    """
    Updates the role of a user within the same tenant.
    Includes a safeguard to prevent the removal of the last admin.
    """
    # 1. Fetch the user to be updated, including their current role information.
    # RLS ensures we can only fetch users from our own tenant.
    user_to_update = db.query(User).options(joinedload(User.role)).filter(User.id == user_id_to_update).first()
    if not user_to_update:
        raise ValueError("User to update not found.")

    # 2. Fetch the new role to be assigned.
    # RLS ensures we can only fetch roles from our own tenant.
    new_role = db.query(UserRole).filter(UserRole.id == new_role_id).first()
    if not new_role:
        raise ValueError("Role to assign not found.")

    # 3. --- THE "LAST ADMIN" SAFEGUARD LOGIC ---
    # Check if we are demoting an admin user.
    is_demoting_an_admin = user_to_update.role and user_to_update.role.is_admin_role and not new_role.is_admin_role

    if is_demoting_an_admin:
        # We are trying to remove an admin. We must check if they are the last one.
        # We need to query for the count of OTHER admins in the tenant.

        # This subquery finds all the admin roles within the tenant.
        admin_roles_subquery = db.query(UserRole.id).filter(
            UserRole.tenant_id == user_to_update.tenant_id,
            UserRole.is_admin_role == True
        ).subquery()

        # This query counts how many users are assigned to any of those admin roles.
        admin_count = db.query(func.count(User.id)).filter(
            User.tenant_id == user_to_update.tenant_id,
            User.role_id.in_(admin_roles_subquery)
        ).scalar()

        # If the count is 1 (or less, for safety), we block the demotion.
        if admin_count <= 1:
            raise ValueError("Cannot remove the last admin from the tenant. Please assign a new admin first.")

    # 4. If the safeguard passes, proceed with the update.
    # Store old role ID for the log
    old_role_id = user_to_update.role_id

    user_to_update.role_id = new_role_id
    user_to_update.updated_by = updater_id
    db.add(user_to_update)
    db.flush()
    # --- ADD AUDIT LOG ---
    create_audit_log(
        db=db,
        tenant_id=user_to_update.tenant_id,
        user_id=updater_id,
        action="USER_ROLE_UPDATED",
        details={
            "updated_user_id": user_to_update.id,
            "updated_user_email": user_to_update.email,
            "old_role_id": str(old_role_id),
            "new_role_id": str(new_role_id)
        }
    )
    # --- END ---

    # Eagerly load the new role to ensure the returned object is up-to-date
    db.refresh(user_to_update, attribute_names=['role'])
    return user_to_update


def delete_user(db: Session, user_id: UUID, supabase_admin: Client):
    """Deletes a user from the tenant and Supabase Auth."""
    user_to_delete = get_user_by_id(db, user_id=user_id)
    if not user_to_delete:
        raise ValueError("User not found.")

    try:
        supabase_admin.auth.admin.delete_user(str(user_to_delete.id))
    except Exception as e:
        # Log the error but proceed, as we want to remove them from our DB regardless
        print(f"Could not delete user from Supabase Auth, but proceeding with local deletion. Error: {e}")

    db.delete(user_to_delete)
    db.flush()