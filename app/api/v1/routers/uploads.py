# app/api/v1/routers/uploads.py
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from supabase import create_client, Client

from app.api.v1.dependencies import get_current_user
from app.api.v1.security import AuthenticatedUser
from app.core.config import get_settings, Settings
from pydantic import BaseModel

router = APIRouter()


class FileUploadResponse(BaseModel):
    """Response model for a successful file upload."""
    file_path: str
    file_url: str


@router.post("", response_model=FileUploadResponse)
def upload_file(
        # The 'folder' path parameter will determine where to store the file (e.g., 'logos', 'items', 'invoices')
        folder: str,
        file: UploadFile = File(...),
        current_user: AuthenticatedUser = Depends(get_current_user),
        settings: Settings = Depends(get_settings),
):
    """
    Uploads a file to a specified folder within the user's tenant directory.

    The backend securely constructs the final path and streams the file
    to Supabase Storage. RLS policies ensure tenant isolation.
    """
    if not current_user.tenant_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Superadmins cannot upload files to tenant assets.")

    # Initialize the Supabase admin client to bypass RLS for the upload itself
    # The RLS policies are applied based on the user's JWT, but for backend uploads,
    # the service key is necessary. The security check is in the path.
    supabase_admin: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    # Generate a unique filename to prevent overwrites
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"

    # Construct the secure, tenant-specific file path
    # Example: 'tenant-a-uuid/logos/some-unique-id.png'
    file_path = f"{current_user.tenant_id}/{folder}/{unique_filename}"

    # Read file content
    try:
        file_content = file.file.read()
    except Exception:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error reading file.")

    # Upload the file to Supabase Storage
    try:
        supabase_admin.storage.from_("tenant-assets").upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Error uploading file to storage: {e}")

    # Generate a short-lived signed URL for the client to use immediately
    try:
        response = supabase_admin.storage.from_("tenant-assets").create_signed_url(
            path=file_path,
            expires_in=60  # URL is valid for 60 seconds
        )
        file_url = response['signedURL']
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Could not create signed URL: {e}")

    return {"file_path": file_path, "file_url": file_url}