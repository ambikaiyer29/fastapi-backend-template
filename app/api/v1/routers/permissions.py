# app/api/v1/routers/permissions.py
from fastapi import APIRouter, Depends
from typing import List

from app.api.v1.dependencies import get_current_user  # Any authenticated user can see the list
from app.schemas.permission_schemas import PermissionGroupRead, PermissionRead
from app.core.permissions import AppPermissions, get_permission_description

router = APIRouter()

@router.get("", response_model=List[PermissionGroupRead])
def get_all_available_permissions(
        _user=Depends(get_current_user)
):
    """
    Returns a structured list of all available permissions in the system.
    """
    grouped_permissions = {}

    for member in AppPermissions:
        print(f"Member : {member}")
        if member.name == 'NONE' or member.value == 0:
            continue

        group_name = member.name.split('_')[0].title()
        if group_name not in grouped_permissions:
            grouped_permissions[group_name] = []

        # Use our new helper function to get the description
        description = get_permission_description(member)

        grouped_permissions[group_name].append(
            PermissionRead(name=member.name, description=description)
        )

    response = [
        PermissionGroupRead(group_name=group, permissions=perms)
        for group, perms in grouped_permissions.items()
    ]

    return response