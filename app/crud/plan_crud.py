# app/crud/plan_crud.py
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.models import Plan, PlanEntitlement
from app.schemas.plan_schemas import PlanCreate, PlanUpdate, PlanEntitlementCreate

# --- CRUD for Plans ---

def create_plan(db: Session, plan_in: PlanCreate) -> Plan:
    db_plan = Plan(**plan_in.dict())
    db.add(db_plan)
    db.flush()
    return db_plan

def get_plan_by_id(db: Session, plan_id: UUID) -> Plan | None:
    return db.query(Plan).filter(Plan.id == plan_id).first()

def get_all_plans(db: Session) -> list[Plan]:
    return db.query(Plan).all()

def update_plan(db: Session, db_plan: Plan, plan_in: PlanUpdate) -> Plan:
    update_data = plan_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_plan, key, value)
    db.add(db_plan)
    db.flush()
    return db_plan

# --- CRUD for Plan Entitlements ---

def add_entitlement_to_plan(db: Session, entitlement_in: PlanEntitlementCreate, plan_id: UUID) -> PlanEntitlement:
    db_entitlement = PlanEntitlement(**entitlement_in.dict(), plan_id=plan_id)
    db.add(db_entitlement)
    db.flush()
    return db_entitlement

def get_entitlement_by_id(db: Session, entitlement_id: UUID) -> PlanEntitlement | None:
    return db.query(PlanEntitlement).filter(PlanEntitlement.id == entitlement_id).first()

def remove_entitlement_from_plan(db: Session, db_entitlement: PlanEntitlement):
    db.delete(db_entitlement)
    db.flush()