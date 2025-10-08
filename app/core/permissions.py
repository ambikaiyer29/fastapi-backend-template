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


    # You could define other common roles here, e.g.:
    # TENANT_EDITOR_PERMISSIONS = ITEMS_READ | ITEMS_CREATE | ITEMS_UPDATE
    # TENANT_VIEWER_PERMISSIONS = ITEMS_READ

    # Superadmin permissions should ideally bypass all checks.
    # Our current superadmin dependency handles this.

    # Note: `auto()` assigns powers of 2 (1, 2, 4, 8, 16, etc.)
    # Example: AppPermissions.USERS_READ.value would be 1
    # AppPermissions.USERS_INVITE.value would be 2
    # AppPermissions.USERS_READ | AppPermissions.USERS_INVITE would be 3

    # print(f"DEBUG: The new TENANT_ADMIN_PERMISSIONS integer value is: {TENANT_ADMIN_PERMISSIONS}")


# print(f"DEBUG: The final TENANT_ADMIN_PERMISSIONS integer value is: {AppPermissions.TENANT_ADMIN_PERMISSIONS.value}")
