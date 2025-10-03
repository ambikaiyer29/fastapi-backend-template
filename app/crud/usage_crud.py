# app/crud/usage_crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from uuid import UUID
from datetime import datetime

from app.db.models import UsageRecord, Tenant


def record_usage(db: Session, *, tenant_id: UUID, feature_slug: str, usage_amount: int):
    """Records a new usage entry for a metered feature."""
    usage = UsageRecord(
        tenant_id=tenant_id,
        feature_slug=feature_slug,
        usage_amount=usage_amount
    )
    db.add(usage)
    # The calling function will handle the commit.


def get_current_usage(db: Session, *, tenant_id: UUID, feature_slug: str) -> int:
    """
    Calculates the total usage for a metered feature within the current billing period.
    """
    # First, get the tenant's current billing period end date
    tenant = db.query(Tenant.current_period_ends_at).filter(Tenant.id == tenant_id).first()
    if not tenant or not tenant.current_period_ends_at:
        return 0  # No active period, so usage is 0

    # Calculate the start of the billing period (assuming monthly)
    # A more robust solution would store the start date as well.
    period_start = tenant.current_period_ends_at - timedelta(days=30)  # Approximation

    # Sum the usage records within this period
    total_usage = db.query(func.sum(UsageRecord.usage_amount)).filter(
        and_(
            UsageRecord.tenant_id == tenant_id,
            UsageRecord.feature_slug == feature_slug,
            UsageRecord.recorded_at >= period_start,
            UsageRecord.recorded_at <= tenant.current_period_ends_at
        )
    ).scalar()

    return total_usage or 0  # Return 0 if total_usage is None