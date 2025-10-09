from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Literal
from typing import Dict, Any

# Define the allowed entitlement types
EntitlementType = Literal['FLAG', 'LIMIT', 'METER']

# --- Schemas for Plan Entitlements ---

class PlanEntitlementBase(BaseModel):
    feature_slug: str = Field(..., description="A unique slug for the feature, e.g., 'max_users'.")
    entitlement_type: EntitlementType
    value: int = Field(..., description="For FLAG: 1=true/0=false. For LIMIT/METER: the numeric value.")

class PlanEntitlementCreate(PlanEntitlementBase):
    pass

class PlanEntitlementRead(PlanEntitlementBase):
    id: UUID
    plan_id: UUID

    class Config:
        from_attributes = True

# --- Schemas for Plans ---

class PlanBase(BaseModel):
    name: str = Field(..., description="The display name of the plan, e.g., 'Pro'.")
    is_active: bool = True
    external_product_id: str | None = None
    external_price_id: str | None = None

class PlanCreate(PlanBase):
    pass

class PlanUpdate(PlanBase):
    name: str | None = None # All fields are optional on update
    is_active: bool | None = None

class PriceInfo(BaseModel):
    """A simplified schema to represent price details from the payment provider."""
    amount: int
    currency: str
    interval: str | None = None # e.g., "Month", "Year" for subscriptions


class PlanRead(PlanBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    entitlements: List[PlanEntitlementRead] = []

    # Enriched from Dodo Payments
    description: str | None = None
    image_url: str | None = None
    price: PriceInfo | None = None

    class Config:
        from_attributes = True

# --- Schema for Tenant Plan Assignment ---

class TenantPlanAssignment(BaseModel):
    plan_id: UUID
    subscription_status: Literal['active', 'trialing', 'inactive', 'past_due'] = 'active'
    current_period_ends_at: datetime | None = None


class SubscriptionDetailsRead(BaseModel):
    """
    Schema for displaying a tenant's complete subscription details,
    combining local data with live data from the payment provider.
    """
    # From our database
    plan: PlanRead
    subscription_status: str
    current_period_ends_at: datetime | None

    # Live data from payment provider (Dodo)
    payment_provider_data: Dict[str, Any] | None

    # Calculated usage data
    usage: Dict[str, int] | None

class CheckoutSessionCreate(BaseModel):
    plan_id: UUID
    success_url: str
    cancel_url: str