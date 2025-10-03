# app/api/v1/routers/subscriptions.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import Dict

from app.api.v1.dependencies import get_auth_rls_session, get_tenant_admin, get_current_user
from app.api.v1.security import AuthenticatedUser
from app.db.models import Tenant, Plan, User  # Import models for queries
from app.schemas.plan_schemas import SubscriptionDetailsRead
from app.crud import usage_crud  # Import usage CRUD
from app.services.dodo_service import dodo_service  # Import our new service
from app.schemas.plan_schemas import SubscriptionDetailsRead, CheckoutSessionCreate # <-- Add CheckoutSessionCreate
from app.crud import plan_crud # <-- Import plan_crud
from app.db.models import CheckoutSession # <-- Import CheckoutSession model


router = APIRouter()


@router.get("/me", response_model=SubscriptionDetailsRead)
async def get_my_subscription_details(
        db: Session = Depends(get_auth_rls_session),
        admin_user=Depends(get_tenant_admin)
):
    """
    Fetch the current subscription and usage details for the user's tenant.
    Restricted to Tenant Admins.
    """
    # Fetch the tenant and their plan with entitlements in one query
    tenant = db.query(Tenant).options(
        joinedload(Tenant.plan).joinedload(Plan.entitlements)
    ).filter(Tenant.id == db.user.tenant_id).first()

    if not tenant or not tenant.plan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active subscription plan found for this tenant.")

    # Fetch live data from Dodo Payments
    # Note: We need a way to store the 'external_subscription_id'.
    # For now, let's assume it's stored on the tenant object.
    # We will need to add this column to the 'tenants' table.
    dodo_data = await dodo_service.get_subscription_details(tenant.external_subscription_id)

    # Calculate current usage for all metered features in the plan
    current_usage: Dict[str, int] = {}
    for entitlement in tenant.plan.entitlements:
        if entitlement.entitlement_type == 'METER':
            usage = usage_crud.get_current_usage(
                db=db,
                tenant_id=tenant.id,
                feature_slug=entitlement.feature_slug
            )
            current_usage[entitlement.feature_slug] = usage

    return SubscriptionDetailsRead(
        plan=tenant.plan,
        subscription_status=tenant.subscription_status,
        current_period_ends_at=tenant.current_period_ends_at,
        payment_provider_data=dodo_data,
        usage=current_usage
    )



@router.post("/checkout-session", status_code=status.HTTP_200_OK)
async def create_checkout_session(
    payload: CheckoutSessionCreate,
    db: Session = Depends(get_auth_rls_session),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Creates a payment checkout session for the user to purchase a plan.
    """
    # 1. Get the plan details from our DB
    plan = plan_crud.get_plan_by_id(db, plan_id=payload.plan_id)
    if not plan or not plan.external_product_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found or not configured for payments.")

    # 2. Call the Dodo service to create the session
    dodo_session = await dodo_service.create_checkout_session(
        plan_id=plan.external_product_id,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
        user=current_user,
        customer_email=current_user.email,
        tenant_id=str(current_user.tenant_id)
    )

    # 3. Track the checkout attempt in our database
    session_id = dodo_session.get("session_id")
    checkout_url = dodo_session.get("checkout_url")
    if not session_id or not checkout_url:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Payment provider did not return a valid session.")

    # Check if a session already exists to prevent duplicates
    db_session = db.query(CheckoutSession).filter(CheckoutSession.id == session_id).first()
    if not db_session:
        db_session = CheckoutSession(
            id=session_id,
            tenant_id=current_user.tenant_id,
            plan_id=payload.plan_id,
            status="PENDING"
        )
        db.add(db_session)
        db.commit()

    return {"checkout_url": checkout_url}