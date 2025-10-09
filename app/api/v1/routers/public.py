# app/api/v1/routers/public.py
import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db # Use the plain, non-RLS session
from app.schemas.plan_schemas import PlanRead, PriceInfo
from app.crud import plan_crud
from app.services.dodo_service import dodo_service

router = APIRouter()


@router.get("/plans", response_model=List[PlanRead])
async def get_public_pricing_plans(db: Session = Depends(get_db)):  # <-- Make the endpoint async
    """
    Public endpoint to fetch all active plans and enrich them with live
    pricing and details from the configured payment provider.
    """
    # 1. Fetch all active plans and their entitlements from our DB
    db_plans = plan_crud.get_all_plans(db)

    # 2. Create a list of tasks to fetch details for each plan concurrently
    tasks = [dodo_service.get_product_details(plan.external_product_id) for plan in db_plans]

    # 3. Run all tasks in parallel and wait for them to complete
    dodo_products_data = await asyncio.gather(*tasks)

    # 4. Combine our DB data with the live Dodo data
    enriched_plans = []
    for db_plan, dodo_product in zip(db_plans, dodo_products_data):
        price_info = None
        if dodo_product and dodo_product.get('price'):
            dodo_price = dodo_product['price']
            interval = None
            # Check if it's a recurring price to get the interval
            if dodo_price.get('type') == 'recurring_price':
                interval = dodo_price.get('payment_frequency_interval')

            price_info = PriceInfo(
                amount=dodo_price.get('price', 0),
                currency=dodo_price.get('currency', 'USD'),
                interval=interval
            )

        enriched_plans.append(
            PlanRead(
                id=db_plan.id,
                created_at=db_plan.created_at,
                updated_at=db_plan.updated_at,
                name=db_plan.name,
                entitlements=db_plan.entitlements,
                description=dodo_product.get('description') if dodo_product else None,
                image_url=dodo_product.get('image') if dodo_product else None,
                price=price_info
            )
        )

    return enriched_plans