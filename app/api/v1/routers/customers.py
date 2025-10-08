# app/api/v1/routers/customers.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.v1.dependencies import get_auth_rls_session, require_permission, get_current_user
from app.api.v1.security import AuthenticatedUser
from app.schemas.customer_schemas import CustomerCreate, CustomerRead, CustomerUpdate
from app.crud import customer_crud
from app.core.permissions import AppPermissions

router = APIRouter()


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_new_customer(
        payload: CustomerCreate,
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(get_current_user),
        _permission_check=Depends(require_permission(AppPermissions.CUSTOMERS_CREATE))
):
    """Create a new customer for the user's tenant."""
    try:
        return customer_crud.create_customer(
            db=db,
            customer_in=payload,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))


@router.get("", response_model=List[CustomerRead])
def get_all_customers(
        db: Session = Depends(get_auth_rls_session),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        _permission_check=Depends(require_permission(AppPermissions.CUSTOMERS_READ))
):
    """List all customers for the user's tenant."""
    return customer_crud.get_customers_by_tenant(db=db, skip=skip, limit=limit)


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer_details(
        customer_id: UUID,
        db: Session = Depends(get_auth_rls_session),
        _permission_check=Depends(require_permission(AppPermissions.CUSTOMERS_READ))
):
    """Get a single customer by their ID."""
    db_customer = customer_crud.get_customer_by_id(db, customer_id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")
    return db_customer


@router.put("/{customer_id}", response_model=CustomerRead)
def update_existing_customer(
        customer_id: UUID,
        payload: CustomerUpdate,
        db: Session = Depends(get_auth_rls_session),
        current_user: AuthenticatedUser = Depends(get_current_user),
        _permission_check=Depends(require_permission(AppPermissions.CUSTOMERS_UPDATE))
):
    """Update a customer's details."""
    db_customer = customer_crud.get_customer_by_id(db, customer_id=customer_id)
    if db_customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Customer not found.")

    return customer_crud.update_customer(
        db=db,
        db_customer=db_customer,
        customer_in=payload,
        user_id=current_user.id
    )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_customer(
        customer_id: UUID,
        db: Session = Depends(get_auth_rls_session),
        _permission_check=Depends(require_permission(AppPermissions.CUSTOMERS_DELETE))
):
    """Delete a customer."""
    db_customer = customer_crud.get_customer_by_id(db, customer_id=customer_id)
    if db_customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Customer not found.")

    customer_crud.delete_customer(db=db, db_customer=db_customer)