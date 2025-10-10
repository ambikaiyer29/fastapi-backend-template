# app/core/permissions.py
from enum import Flag, auto


# Define your application's permissions using a Flag enum.
# Each member gets a unique power-of-2 value, allowing combinations (bitmasking).
class AppPermissions(Flag):
    NONE = 0

    # Tenant Management (Superadmin only - for now, handled by get_superadmin)
    # TENANT_CREATE = auto() # Already handled by superadmin check
    # TENANT_DELETE = auto()
    # TENANT_READ = auto()
    # TENANT_UPDATE = auto()

    # User Management within a Tenant
    USERS_READ = auto()  # Can view users in their tenant
    USERS_INVITE = auto()  # Can invite new users
    USERS_UPDATE_ROLE = auto()  # Can change roles of other users
    USERS_DELETE = auto()  # Can delete users

    # Role Management within a Tenant
    ROLES_READ = auto()  # Can view roles in their tenant
    ROLES_CREATE = auto()  # Can create new roles
    ROLES_UPDATE = auto()  # Can update existing roles (e.g., permission_set)
    ROLES_DELETE = auto()  # Can delete roles

    # Item Management (Example application resource)
    ITEMS_READ = auto()  # Can view items
    ITEMS_CREATE = auto()  # Can create new items
    ITEMS_UPDATE = auto()  # Can update existing items
    ITEMS_DELETE = auto()  # Can delete items

    # --- ADD NEW PERMISSIONS ---
    # Metadata Management (typically for tenant admins)
    CUSTOM_OBJECTS_CREATE = auto()
    CUSTOM_OBJECTS_READ = auto()
    CUSTOM_OBJECTS_UPDATE = auto()
    CUSTOM_OBJECTS_DELETE = auto()

    # Data/Record Management (for regular tenant users)
    RECORDS_CREATE = auto()
    RECORDS_READ = auto()
    RECORDS_UPDATE = auto()
    RECORDS_DELETE = auto()

    # --- ADD NEW PERMISSIONS ---
    CUSTOMERS_CREATE = auto()
    CUSTOMERS_READ = auto()
    CUSTOMERS_UPDATE = auto()
    CUSTOMERS_DELETE = auto()
    # Convenience roles (combinations of permissions)
    TENANT_ADMIN_PERMISSIONS = (
            USERS_READ | USERS_INVITE | USERS_UPDATE_ROLE | USERS_DELETE |
            ROLES_READ | ROLES_CREATE | ROLES_UPDATE | ROLES_DELETE |
            ITEMS_READ | ITEMS_CREATE | ITEMS_UPDATE | ITEMS_DELETE |
            CUSTOM_OBJECTS_CREATE | CUSTOM_OBJECTS_READ | CUSTOM_OBJECTS_UPDATE | CUSTOM_OBJECTS_DELETE |
            RECORDS_CREATE | RECORDS_READ | RECORDS_UPDATE | RECORDS_DELETE |
            CUSTOMERS_CREATE | CUSTOMERS_READ | CUSTOMERS_UPDATE | CUSTOMERS_DELETE
    )

_permission_descriptions = {
        AppPermissions.USERS_READ: "Can view users and their roles within the tenant.",
        AppPermissions.USERS_INVITE: "Can invite new users to the tenant.",
        AppPermissions.USERS_UPDATE_ROLE: "Can change the roles of other users.",
        AppPermissions.USERS_DELETE: "Can remove users from the tenant.",
        AppPermissions.ROLES_READ: "Can view roles and their permissions.",
        AppPermissions.ROLES_CREATE: "Can create new custom roles.",
        AppPermissions.ROLES_UPDATE: "Can update the permissions of existing roles.",
        AppPermissions.ROLES_DELETE: "Can delete custom roles.",
        AppPermissions.ITEMS_READ: "Can view items.",
        AppPermissions.ITEMS_CREATE: "Can create new items.",
        AppPermissions.ITEMS_UPDATE: "Can update existing items.",
        AppPermissions.ITEMS_DELETE: "Can delete items.",
        AppPermissions.CUSTOM_OBJECTS_CREATE: "Can create new custom object definitions.",
        AppPermissions.CUSTOM_OBJECTS_READ: "Can view custom object definitions.",
        AppPermissions.CUSTOM_OBJECTS_UPDATE: "Can update custom object definitions.",
        AppPermissions.CUSTOM_OBJECTS_DELETE: "Can delete custom object definitions.",
        AppPermissions.RECORDS_CREATE: "Can create new records for custom objects.",
        AppPermissions.RECORDS_READ: "Can view records of custom objects.",
        AppPermissions.RECORDS_UPDATE: "Can update records of custom objects.",
        AppPermissions.RECORDS_DELETE: "Can delete records of custom objects.",
        AppPermissions.CUSTOMERS_CREATE: "Can create new customer profiles.",
        AppPermissions.CUSTOMERS_READ: "Can view customer profiles.",
        AppPermissions.CUSTOMERS_UPDATE: "Can update customer profiles.",
        AppPermissions.CUSTOMERS_DELETE: "Can delete customer profiles.",
        AppPermissions.TENANT_ADMIN_PERMISSIONS: "Full Admin permission",
    }

    # This function will be our single source of truth for getting a description.
def get_permission_description(permission: AppPermissions) -> str:
    """Returns the description for a given AppPermissions member."""
    return _permission_descriptions.get(permission, "No description available.")


# print(f"DEBUG: The final TENANT_ADMIN_PERMISSIONS integer value is: {AppPermissions.TENANT_ADMIN_PERMISSIONS.value}")
