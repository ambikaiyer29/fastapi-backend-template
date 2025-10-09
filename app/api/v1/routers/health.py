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

