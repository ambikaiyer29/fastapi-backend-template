# app/api/v1/routers/plans.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from uuid import UUID

from app.api.v1.dependencies import get_auth_rls_session, get_superadmin
from app.api.v1.security import AuthenticatedUser
from app.schemas.plan_schemas import PlanCreate, PlanRead, PlanUpdate, PlanEntitlementCreate, PlanEntitlementRead
from app.crud import plan_crud

router = APIRouter()


# All endpoints in this router require superadmin privileges.

@router.post("", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
def create_new_plan(
        payload: PlanCreate,
        db: Session = Depends(get_auth_rls_session),
        _superadmin: AuthenticatedUser = Depends(get_superadmin)
):
    """
    [SUPERADMIN ONLY] Create a new subscription plan.
    """
    try:
        return plan_crud.create_plan(db=db, plan_in=payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "A plan with this name already exists.")


@router.get("", response_model=List[PlanRead])
def get_all_plans(
        db: Session = Depends(get_auth_rls_session),
        _superadmin: AuthenticatedUser = Depends(get_superadmin)
):
    """
    [SUPERADMIN ONLY] Retrieve a list of all plans.
    """
    return plan_crud.get_all_plans(db)


@router.put("/{plan_id}", response_model=PlanRead)
def update_existing_plan(
        plan_id: UUID,
        payload: PlanUpdate,
        db: Session = Depends(get_auth_rls_session),
        _superadmin: AuthenticatedUser = Depends(get_superadmin)
):
    """
    [SUPERADMIN ONLY] Update an existing plan's details.
    """
    db_plan = plan_crud.get_plan_by_id(db, plan_id=plan_id)
    if not db_plan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found.")

    return plan_crud.update_plan(db=db, db_plan=db_plan, plan_in=payload)


@router.post("/{plan_id}/entitlements", response_model=PlanEntitlementRead, status_code=status.HTTP_201_CREATED)
def add_entitlement_to_plan(
        plan_id: UUID,
        payload: PlanEntitlementCreate,
        db: Session = Depends(get_auth_rls_session),
        _superadmin: AuthenticatedUser = Depends(get_superadmin)
):
    """
    [SUPERADMIN ONLY] Add a new entitlement to a plan.
    """
    db_plan = plan_crud.get_plan_by_id(db, plan_id=plan_id)
    if not db_plan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found.")

    try:
        return plan_crud.add_entitlement_to_plan(db=db, entitlement_in=payload, plan_id=plan_id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "This feature slug already exists for this plan.")


@router.delete("/entitlements/{entitlement_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_entitlement_from_plan(
        entitlement_id: UUID,
        db: Session = Depends(get_auth_rls_session),
        _superadmin: AuthenticatedUser = Depends(get_superadmin)
):
    """
    [SUPERADMIN ONLY] Remove an entitlement from a plan.
    """
    db_entitlement = plan_crud.get_entitlement_by_id(db, entitlement_id=entitlement_id)
    if not db_entitlement:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entitlement not found.")

    plan_crud.remove_entitlement_from_plan(db, db_entitlement=db_entitlement)