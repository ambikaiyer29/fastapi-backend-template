# In app/api/v1/dependencies.py
from fastapi import Header, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.orm import Session, joinedload
from passlib.context import CryptContext
from uuid import UUID
from datetime import datetime

from sqlalchemy.sql.functions import func

from app.crud import usage_crud
from app.db.session import SessionLocal
from app.db.models import ApiKey, User, UserRole, Tenant, Plan
from app.core.config import get_settings, Settings
from app.api.v1.security import AuthenticatedUser, get_token_data, reusable_oauth2, api_key_header_scheme
from app.core.permissions import AppPermissions
from sqlalchemy import text

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# THE NEW MASTER DEPENDENCY
def get_auth_rls_session(
        request: Request,
        settings: Settings = Depends(get_settings),
        jwt_credentials: HTTPAuthorizationCredentials | None = Depends(reusable_oauth2),
        api_key: str | None = Depends(api_key_header_scheme)
) -> Session:
    """
    The single, unified dependency to authenticate a user and provide a
    correctly-scoped RLS database session.
    """
    db = SessionLocal()
    user: AuthenticatedUser = None

    try:
        if jwt_credentials:
            # The JWT logic is self-contained and already works correctly because
            # it uses the 'user_can_select_self_policy' after setting the user_id.
            token_data = get_token_data(token=jwt_credentials, settings=settings)
            user_id, email = token_data.get("user_id"), token_data.get("email")
            if not user_id: raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid JWT.")

            # Set user_id for RLS bootstrap on the 'users' table
            db.execute(text("SET app.current_user_id = :user_id"), {"user_id": user_id})

            is_super = user_id == settings.SUPERADMIN_USER_ID

            # This lookup now works because of 'user_can_select_self_policy'
            user_in_db = db.query(User).filter(User.id == user_id).first()

            if not is_super and not user_in_db:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "User profile not found.")

            user = AuthenticatedUser(
                id=UUID(user_id), email=email, is_superadmin=is_super,
                tenant_id=user_in_db.tenant_id if user_in_db else None
            )

        elif api_key:
            # --- THIS IS THE FIX ---
            # All un-scoped lookups for API key auth must happen inside a single
            # privileged block.
            try:
                # 1. Elevate privilege for the entire auth sequence
                db.execute(text("SET app.is_superadmin = 'true'"))

                # 2. Find the API key
                parts = api_key.split('_')
                if len(parts) != 3 or parts[0] != 'sk' or parts[1] != 'live':
                    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key format.")

                secret_part = parts[2]
                prefix_part = secret_part[:8]
                key_prefix_to_find = f"sk_live_{prefix_part}"

                db_api_key = db.query(ApiKey).filter(ApiKey.key_prefix == key_prefix_to_find).first()

                if not db_api_key or not pwd_context.verify(api_key, db_api_key.hashed_key):
                    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key.")

                # 3. Find the user associated with the key (still in the privileged block)
                db_user = db.query(User).filter(User.id == db_api_key.user_id).first()
                if not db_user:
                    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User for API key not found.")

                # 4. Construct the AuthenticatedUser object
                user = AuthenticatedUser(id=db_user.id, email=db_user.email, tenant_id=db_user.tenant_id,
                                         is_superadmin=False)

                # 5. Update last_used_at timestamp
                db_api_key.last_used_at = datetime.utcnow()
                db.add(db_api_key)

            finally:
                # 6. CRITICAL: Reset the privilege after ALL lookups are complete.
                db.execute(text("RESET app.is_superadmin"))
            # --- END OF FIX ---

        else:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

        # Now that the user is identified, set the FINAL RLS context for the request.
        db.user = user
        # Re-set the superadmin flag to its true value for this user
        db.execute(text("SET app.is_superadmin = :value"), {"value": 'true' if user.is_superadmin else 'false'})
        db.execute(text("SET app.current_user_id = :user_id"), {"user_id": str(user.id)})
        if user.tenant_id:
            db.execute(text("SET app.current_tenant_id = :tenant_id"), {"tenant_id": str(user.tenant_id)})

        yield db
        db.commit()

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def require_terms_accepted(
    db: Session = Depends(get_auth_rls_session)
):
    """
    Checks if the user has accepted the terms. Raises 403 if not.
    This is a sub-dependency and is not meant to be used directly in endpoints.
    """
    user: AuthenticatedUser = db.user
    if user.is_superadmin:
        return

    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user or db_user.terms_accepted_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "TERMS_NOT_ACCEPTED", "message": "Terms of Service not accepted."}
        )


# SIMPLER DEPENDENCIES THAT READ FROM THE MASTER ONE
def get_current_user(db: Session = Depends(get_auth_rls_session),
                     _terms_check=Depends(require_terms_accepted)
                     ) -> AuthenticatedUser:
    """Retrieves the authenticated user from the session object."""
    return db.user


def get_superadmin(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    """Checks if the user from the session is a superadmin."""
    if not user.is_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required.")
    return user


def require_permission(required_permission: AppPermissions):
    def permission_checker(
            # This now correctly depends on our new, terms-aware user provider.
            user: AuthenticatedUser = Depends(get_current_user),
            db: Session = Depends(get_auth_rls_session)
    ):
        if user.is_superadmin:
            return

        # We need to re-fetch the user here WITH the role loaded.
        # This query is safe because the user is already authenticated and terms-accepted.
        user_with_role = db.query(User).options(joinedload(User.role)).filter(User.id == user.id).first()
        if not user_with_role or not user_with_role.role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no assigned role.")

        current_permissions = user_with_role.role.permission_set or 0
        if not (current_permissions & required_permission.value) == required_permission.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"User lacks '{required_permission.name}' permission.")

    return permission_checker


def get_tenant_admin(
        # This dependency will run AFTER the main get_auth_rls_session has run,
        # because get_current_user depends on it.
        db: Session = Depends(get_auth_rls_session),
        user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """
    Dependency that checks if the authenticated user has an admin role
    within their tenant by checking their role's `is_admin_role` flag.

    Raises a 403 Forbidden error if the user is not a tenant admin.
    Returns the AuthenticatedUser object if they are.
    """
    # Superadmins are also considered tenant admins for the purpose of this check
    if user.is_superadmin:
        return user

    # We use the RLS-scoped session (db) to fetch the user's role details
    user_with_role = db.query(User).options(joinedload(User.role)).filter(User.id == user.id).first()

    if not user_with_role or not user_with_role.role or not user_with_role.role.is_admin_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have admin privileges for this tenant."
        )
    return user


def check_entitlement(feature_slug: str, consumed_amount: int = 1):
    """
    Dependency factory to check if a tenant is entitled to a feature.
    - For FLAGS, it checks if the feature is enabled.
    - For LIMITS, it checks if the current count is below the max.
    - For METERS, it checks if the current usage + consumed_amount is within the meter.

    Raises 402 Payment Required if the check fails.
    """

    def entitlement_checker(
            db: Session = Depends(get_auth_rls_session)
    ):
        user = db.user
        if user.is_superadmin:
            return  # Superadmin bypasses all entitlement checks

        # 1. Fetch the tenant, their plan, and all entitlements in one go.
        tenant = db.query(Tenant).options(
            joinedload(Tenant.plan).joinedload(Plan.entitlements)
        ).filter(Tenant.id == user.tenant_id).first()

        if not tenant or not tenant.plan or tenant.subscription_status != 'active':
            raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "No active subscription found.")

        # 2. Find the specific entitlement for the feature.
        entitlement = next((e for e in tenant.plan.entitlements if e.feature_slug == feature_slug), None)
        if not entitlement:
            raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED,
                                f"Your plan does not include the feature: {feature_slug}.")

        # 3. Perform the check based on the entitlement type.
        if entitlement.entitlement_type == 'FLAG':
            if entitlement.value != 1:
                raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "This feature is not enabled for your plan.")

        elif entitlement.entitlement_type == 'LIMIT':
            # Example for 'max_users'. This needs to be made generic.
            if feature_slug == 'max_users':
                current_count = db.query(func.count(User.id)).filter(User.tenant_id == user.tenant_id).scalar()
                if current_count >= entitlement.value:
                    raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED,
                                        f"You have reached the limit of {entitlement.value} users for your plan.")
            # ... you would add logic for other limits here ...

        elif entitlement.entitlement_type == 'METER':
            # This is where we use our new CRUD function.
            current_usage = usage_crud.get_current_usage(db, tenant_id=user.tenant_id, feature_slug=feature_slug)
            if (current_usage + consumed_amount) > entitlement.value:
                raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED,
                                    f"You have exceeded your usage quota for this feature.")

    return Depends(entitlement_checker)


def get_system_db_session():
    """
    Provides a database session with superadmin privileges.
    This is ONLY for trusted, internal, system-level processes like
    handling a verified webhook, where we need to operate across all tenants.
    """
    db = SessionLocal()
    try:
        # Elevate privileges for the duration of this session
        db.execute(text("SET app.is_superadmin = 'true'"))
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        # We don't need to reset, as the session is closed, but it's good practice
        db.execute(text("RESET ALL"))
        db.close()


def get_user_for_onboarding(
        settings: Settings = Depends(get_settings),
        jwt_credentials: HTTPAuthorizationCredentials | None = Depends(reusable_oauth2),
) -> tuple[AuthenticatedUser, Session]:
    """
    A special dependency for the one-time tenant onboarding endpoint.

    It validates the JWT, ensures the user is not already onboarded, and provides
    a PRIVILEGED database session to allow the creation of the initial tenant.
    """
    if not jwt_credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    token_data = get_token_data(token=jwt_credentials, settings=settings)
    user_id, email = token_data.get("user_id"), token_data.get("email")
    if not user_id or not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

    # Construct a user object from the token data.
    user = AuthenticatedUser(id=UUID(user_id), email=email, is_superadmin=False, tenant_id=None)

    # We use a temporary privileged session for the checks and the operation.
    db = SessionLocal()
    try:
        # 1. Elevate privileges for this session
        db.execute(text("SET app.is_superadmin = 'true'"))

        # 2. Check if user already has a profile. This query now works.
        existing_profile = db.query(User).filter(User.id == user.id).first()
        if existing_profile:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "User has already completed onboarding.")

        # 3. Provide the user and the privileged session to the endpoint
        yield user, db

        # 4. If the endpoint succeeds, commit the transaction
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        # 5. Always close the session
        db.close()