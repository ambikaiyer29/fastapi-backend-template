from fastapi import APIRouter
from app.utils.decorators import log_request
from app.api.v1.dependencies import get_auth_rls_session, get_current_user
from app.api.v1.security import AuthenticatedUser
from sqlalchemy.orm import Session
from fastapi import Depends

router = APIRouter()

@router.get("/health")
@log_request
async def health_check():
    """Checks the health of the application."""
    return {"status": "ok"}


@router.get("/dodo-success")
@log_request
async def health_check():
    """Checks the health of the application."""
    return {"status": "success"}

@router.get("/dodo-failed")
@log_request
async def health_check():
    """Checks the health of the application."""
    return {"status": "failed"}

@router.get("/public")
@log_request
async def public_endpoint():
    """This is a public endpoint that does not require authentication."""
    return {"message": "Hello, this is a public endpoint!"}

# Note: The protected endpoint was for testing. We can remove or keep it.
# For now, let's keep it here but tag it appropriately.
@router.get("/protected", tags=["Testing"])
@log_request
async def protected_endpoint(
    # This endpoint now needs to import its dependencies directly
    db: Session = Depends(get_auth_rls_session),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    This is a protected endpoint for testing authentication and RLS.
    """
    return {
        "message": "Hello from a protected route!",
        "user_id": current_user.id,
        "tenant_id": current_user.tenant_id,
        "is_superadmin": current_user.is_superadmin
    }