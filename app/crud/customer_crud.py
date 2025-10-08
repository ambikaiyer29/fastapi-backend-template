# app/crud/customer_crud.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from app.db.models import Customer
from app.schemas.customer_schemas import CustomerCreate, CustomerUpdate


def create_customer(db: Session, customer_in: CustomerCreate, tenant_id: UUID, user_id: UUID) -> Customer:
    """Creates a new customer record for a tenant."""
    try:
        db_customer = Customer(
            **customer_in.dict(),
            tenant_id=tenant_id,
            created_by_id=user_id
        )
        db.add(db_customer)
        db.flush()
        return db_customer
    except IntegrityError:
        db.rollback()
        # Raise a more specific error that the API layer can catch
        raise ValueError("A customer with this email already exists in this tenant.")


def get_customer_by_id(db: Session, customer_id: UUID) -> Customer | None:
    """
    Fetches a single customer by their ID.
    RLS is applied automatically, so it will only return a customer
    if they belong to the current user's tenant.
    """
    return db.query(Customer).filter(Customer.id == customer_id).first()


def get_customers_by_tenant(db: Session, skip: int = 0, limit: int = 100) -> list[Customer]:
    """
    Fetches a paginated list of all customers for the current user's tenant.
    """
    return db.query(Customer).order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()


def update_customer(db: Session, db_customer: Customer, customer_in: CustomerUpdate, user_id: UUID) -> Customer:
    """Updates an existing customer's details."""
    update_data = customer_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_customer, key, value)

    db_customer.updated_by_id = user_id
    db.add(db_customer)
    db.flush()
    return db_customer


def delete_customer(db: Session, db_customer: Customer):
    """Deletes a customer."""
    db.delete(db_customer)
    db.flush()