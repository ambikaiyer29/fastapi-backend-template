# app/api/v1/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client, PostgrestAPIResponse

from app.core.config import get_settings, Settings

router = APIRouter()


class UserSignup(BaseModel):
    email: EmailStr
    password: str


class ForgotPassword(BaseModel):
    email: EmailStr


def get_supabase_client(settings: Settings = Depends(get_settings)) -> Client:
    """Dependency to get a supabase client using the anon key."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def user_signup(
        payload: UserSignup,
        background_tasks: BackgroundTasks,
        supabase: Client = Depends(get_supabase_client)
):
    """
    Handles new user registration.
    Creates a user in Supabase Auth but does not create a tenant or profile yet.
    Supabase will automatically send a confirmation email.
    """
    try:
        # Supabase sign_up handles sending the confirmation email.
        response: PostgrestAPIResponse = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
        })

        # We need to handle the case where the user might already exist but is unconfirmed.
        # Supabase might return a user object in this case without raising an error.
        if response.user and response.user.aud != 'authenticated':
            # This indicates the user exists but is unconfirmed.
            # You might want to resend the confirmation email here if needed.
            # For now, we'll treat it as a successful signup prompt.
            return {"message": "Signup successful. Please check your email to confirm your account."}

        if not response.user:
            # This can happen if auto-confirmation is on, which is not our case.
            # Or if there's an unexpected issue.
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not sign up user.")

    except Exception as e:
        # This will catch specific API errors, e.g., "User already registered"
        error_message = str(e)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=error_message)

    return {"message": "Signup successful. Please check your email to confirm your account."}


@router.post("/forgot-password")
def forgot_password(
        payload: ForgotPassword,
        supabase: Client = Depends(get_supabase_client)
):
    """
    Triggers the password reset flow for a user.
    """
    try:
        supabase.auth.reset_password_email(payload.email)
    except Exception as e:
        # Don't reveal if an email exists or not for security.
        # Log the actual error for debugging.
        print(f"Forgot password error: {e}")

    # Always return a generic success message.
    return {"message": "If an account with this email exists, a password reset link has been sent."}