# app/api/v1/security.py
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from uuid import UUID

from app.core.config import get_settings, Settings

reusable_oauth2 = HTTPBearer(scheme_name="Authorization", auto_error=False)
api_key_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthenticatedUser(BaseModel):
    """Pydantic model for the authenticated user's data. This is used internally."""
    id: UUID
    tenant_id: UUID | None = None
    email: EmailStr | None = None  # <-- ADD EMAIL
    is_superadmin: bool = False

def get_token_data(
    token: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
    settings: Settings = Depends(get_settings)
) -> dict:
    """
    Validates the JWT token and returns the payload containing the user_id.
    This is a low-level dependency focused only on token validation.
    """
    try:
        payload = jwt.decode(
            token.credentials,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User identifier (sub) not found in token.",
            )
        # Return the essential data from the token
        return {"user_id": user_id, "email" :  email}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials, token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )