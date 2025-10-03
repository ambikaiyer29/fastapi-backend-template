# app/api/v1/routers/webhooks.py
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel

from app.db.session import get_db
from app.services.dodo_service import dodo_service
from app.db.models import Tenant, User, Plan, WebhookEvent  # <-- Import WebhookEvent

router = APIRouter()


# Helper Pydantic model for parsing the webhook headers
class DodoWebhookHeaders(BaseModel):
    webhook_id: str
    webhook_signature: str
    webhook_timestamp: str


@router.post("/dodo", status_code=status.HTTP_202_ACCEPTED)  # Use 202 for "Accepted for processing"
async def handle_dodo_webhook(
        request: Request,
        db: Session = Depends(get_db)  # Use a plain session for this handler
):
    """
    Handles incoming webhooks from Dodo Payments with idempotency and
    out-of-order handling.
    """
    # 1. Extract Headers and Verify Signature
    try:
        headers = DodoWebhookHeaders(
            webhook_id=request.headers.get("webhook-id"),
            webhook_signature=request.headers.get("webhook-signature"),
            webhook_timestamp=request.headers.get("webhook-timestamp"),
        )
        payload = await dodo_service.verify_webhook_signature(request)
    except Exception as e:
        print(f"ERROR: Webhook signature verification failed or headers missing: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid headers or signature.")

    # 2. Idempotency Check: Has this event already been processed?
    event_id = headers.webhook_id
    if db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first():
        print(f"INFO: Received duplicate webhook event (id: {event_id}). Acknowledging and skipping.")
        return {"status": "duplicate", "message": "Event already processed."}

    # Store the event immediately to prevent race conditions.
    # We commit this in a separate transaction.
    new_event = WebhookEvent(id=event_id, event_type=payload.get("type"), payload=payload)
    db.add(new_event)
    db.commit()

    # 3. Process the Event
    try:
        # Re-fetch the event to ensure we are working with a committed record
        event_to_process = db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
        process_event(db, event_to_process)

        # Mark as successfully processed and commit.
        event_to_process.processed_successfully = True
        db.commit()

        return {"status": "processed"}
    except HTTPException as e:
        db.rollback()
        # If our logic intentionally raises an HTTP error (e.g., 404),
        # we still want to return 200 to Dodo so it doesn't retry.
        print(f"ERROR: Could not process webhook {event_id}. Reason: {e.detail}")
        return {"status": "error", "detail": e.detail}
    except Exception as e:
        db.rollback()
        print(f"CRITICAL: An unexpected error occurred processing webhook {event_id}. Error: {e}")
        # An unexpected error means we should let Dodo retry.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


def process_event(db: Session, event: WebhookEvent):
    """
    The core business logic for handling a webhook event.
    This is separated for clarity and testability.
    """
    event_type = event.event_type
    payload = event.payload
    data = payload.get("data", {})

    print(f"INFO: Processing webhook event: {event_type} (id: {event.id})")

    # The payload timestamp is what we use for out-of-order checks.
    event_timestamp = datetime.fromisoformat(payload.get("timestamp").replace("Z", "+00:00"))

    # Extract key identifiers from the payload
    subscription_data = data
    external_subscription_id = subscription_data.get("subscription_id")
    customer_data = subscription_data.get("customer", {})
    customer_email = customer_data.get("email")

    if not external_subscription_id or not customer_email:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Webhook missing key identifiers.")

    # Fetch our internal tenant
    user = db.query(User).filter(User.email == customer_email).first()
    if not user or not user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Tenant for email {customer_email} not found.")

    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Tenant record {user.tenant_id} not found.")

    # --- Out-of-Order Handling ---
    # Before changing the status, check if a newer event has already updated the period end date.
    if tenant.current_period_ends_at and event_timestamp < tenant.current_period_ends_at.replace(tzinfo=timezone.utc):
        print(
            f"INFO: Skipping stale webhook event (id: {event.id}). Event timestamp {event_timestamp} is older than last update {tenant.current_period_ends_at}.")
        return  # Acknowledge and skip processing this old event.

    # --- State Machine Logic ---
    if event_type == "subscription.active" or event_type == "subscription.renewed":
        # ... (logic to find plan, update tenant status to 'active', etc.)
        external_product_id = subscription_data.get("product_id")
        plan = db.query(Plan).filter(Plan.external_product_id == external_product_id).first()
        if not plan: raise HTTPException(status.HTTP_404_NOT_FOUND,
                                         f"Plan with external_id {external_product_id} not found.")

        tenant.plan_id = plan.id
        tenant.subscription_status = 'active'
        tenant.external_subscription_id = external_subscription_id
        # Update the period end date from the payload
        period_ends_at_str = subscription_data.get("period_ends_at")
        if period_ends_at_str:
            tenant.current_period_ends_at = datetime.fromisoformat(period_ends_at_str.replace("Z", "+00:00"))

    elif event_type == "subscription.on_hold" or event_type == "subscription.failed":
        tenant.subscription_status = 'past_due'

    elif event_type == "subscription.cancelled" or event_type == "subscription.expired":
        tenant.subscription_status = 'inactive'

    else:
        print(f"INFO: Unhandled event type: {event_type}")

    return