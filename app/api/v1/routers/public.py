# app/api/v1/routers/public.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db # Use the plain, non-RLS session
from app.schemas.plan_schemas import PlanRead
from app.crud import plan_crud

router = APIRouter()

@router.get("/plans", response_model=List[PlanRead])
def get_public_pricing_plans(db: Session = Depends(get_db)):
    """
    Public endpoint to fetch all active, customer-facing plans.
    Used for the website's pricing page.
    """
    # Note: RLS on the `plans` table allows public read access, so this is safe.
    return plan_crud.get_all_plans(db)