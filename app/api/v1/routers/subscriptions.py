# app/api/v1/routers/subscriptions.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import Dict

from app.api.v1.dependencies import get_auth_rls_session, get_tenant_admin, get_current_user
from app.api.v1.security import AuthenticatedUser
from app.core.config import Settings, get_settings
from app.db.models import Tenant, Plan, User  # Import models for queries
from app.schemas.plan_schemas import SubscriptionDetailsRead
from app.crud import usage_crud  # Import usage CRUD
from app.services.dodo_service import dodo_service  # Import our new service
from app.schemas.plan_schemas import SubscriptionDetailsRead, CheckoutSessionCreate # <-- Add CheckoutSessionCreate
from app.crud import plan_crud # <-- Import plan_crud
from app.db.models import CheckoutSession # <-- Import CheckoutSession model
from app.services.stripe_service import stripe_service


router = APIRouter()


@router.get("/me", response_model=SubscriptionDetailsRead)
async def get_my_subscription_details(
        db: Session = Depends(get_auth_rls_session),
        settings: Settings = Depends(get_settings),  # <-- Add settings dependency
        admin_user=Depends(get_tenant_admin)
):
    """
    Fetch the current subscription and usage details for the user's tenant.
    Restricted to Tenant Admins.
    """
    # 1. Fetch our internal tenant data, including the plan and its entitlements
    tenant = db.query(Tenant).options(
        joinedload(Tenant.plan).joinedload(Plan.entitlements)
    ).filter(Tenant.id == db.user.tenant_id).first()

    if not tenant or not tenant.plan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active subscription plan found for this tenant.")

    # 2. Fetch live data from the configured payment provider
    payment_provider_data = None
    if settings.PAYMENT_GATEWAY == "stripe":
        # Stripe's SDK is synchronous, so we don't need to await
        payment_provider_data = stripe_service.get_subscription_details(tenant.external_subscription_id)
    elif settings.PAYMENT_GATEWAY == "dodo":
        payment_provider_data = await dodo_service.get_subscription_details(tenant.external_subscription_id)

    # 3. Calculate current usage for all metered features
    current_usage: Dict[str, int] = {}
    for entitlement in tenant.plan.entitlements:
        if entitlement.entitlement_type == 'METER':
            usage = usage_crud.get_current_usage(
                db=db,
                tenant_id=tenant.id,
                feature_slug=entitlement.feature_slug
            )
            current_usage[entitlement.feature_slug] = usage

    # 4. Combine all data into the final response
    return SubscriptionDetailsRead(
        plan=tenant.plan,
        subscription_status=tenant.subscription_status,
        current_period_ends_at=tenant.current_period_ends_at,
        payment_provider_data=payment_provider_data,
        usage=current_usage
    )



@router.post("/checkout-session", status_code=status.HTTP_200_OK)
async def create_checkout_session(
    payload: CheckoutSessionCreate,
    db: Session = Depends(get_auth_rls_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    """
    Creates a payment checkout session for the user to purchase a plan.
    """
    # 1. Get the plan details from our DB
    plan = plan_crud.get_plan_by_id(db, plan_id=payload.plan_id)
    if not plan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found.")

    session_data = {}
    if settings.PAYMENT_GATEWAY == "stripe":
        if not plan.external_price_id:  # Stripe uses price IDs
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Plan is not configured for Stripe (missing price ID).")
        session_data = stripe_service.create_checkout_session(
            price_id=plan.external_price_id,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
            customer_email=current_user.email,
            client_reference_id=str(current_user.tenant_id)
        )
    elif settings.PAYMENT_GATEWAY == "dodo":
        # 2. Call the Dodo service to create the session
        if not plan.external_product_id: # Dodo uses product IDs
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Plan is not configured for Dodo (missing product ID).")

        session_data = await dodo_service.create_checkout_session(
            plan_id=plan.external_product_id,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
            user=current_user,
            customer_email=current_user.email,
            tenant_id=str(current_user.tenant_id)
        )
    else:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "No valid payment gateway configured.")

    # 3. Track the checkout attempt in our database
    session_id = session_data.get("session_id")
    checkout_url = session_data.get("checkout_url")
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


@router.post("/customer-portal-session", status_code=status.HTTP_200_OK)
async def create_customer_portal_session(
        return_url: str,  # Usually the URL of your billing page
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(get_current_user),
        settings: Settings = Depends(get_settings),
):
    """
    Creates a self-service customer portal session for the user to manage their subscription.
    """
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found.")

    portal_data = {}
    if settings.PAYMENT_GATEWAY == "stripe":
        if not tenant.external_customer_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tenant is not a paying customer with Stripe.")
        portal_data = stripe_service.create_customer_portal_session(
            customer_id=tenant.external_customer_id,
            return_url=return_url
        )
        return {"portal_url": portal_data.get("portal_url")}

    # Add logic for Dodo's customer portal if they have one
    elif settings.PAYMENT_GATEWAY == "dodo":
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Customer portal not implemented for Dodo Payments yet.")

    else:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "No valid payment gateway configured.")