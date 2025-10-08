# app/db/models.py

import uuid
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Integer,
    Boolean,
    func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

SCHEMA_NAME = "fastapiSK"
Base = declarative_base()


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    admin_user_id = Column(UUID(as_uuid=True))
    tenant_data = Column(JSONB)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    logo_path = Column(String, nullable=True)

    plan_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.plans.id"), nullable=True)
    subscription_status = Column(String, default="inactive")
    current_period_ends_at = Column(DateTime, nullable=True)
    external_subscription_id = Column(String, nullable=True)
    external_customer_id = Column(String, nullable=True)

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    roles = relationship("UserRole", back_populates="tenant", cascade="all, delete-orphan")
    plan = relationship("Plan", back_populates="tenants")

class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    permission_set = Column(Integer)
    is_admin_role = Column(Boolean, default=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.tenants.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))

    tenant = relationship("Tenant", back_populates="roles")

    # --- THIS IS THE FIX ---
    # We explicitly tell SQLAlchemy how to join UserRole to User.
    # We use strings ('User.role_id', 'UserRole.id') because the User class is defined later in the file.
    users = relationship(
        "User",
        primaryjoin="foreign(User.role_id) == UserRole.id",
        back_populates="role"
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String, nullable=False, unique=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.user_roles.id"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.tenants.id"))
    user_data = Column(JSONB)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    terms_accepted_at = Column(DateTime(timezone=True), nullable=True)

    # This side of the relationship doesn't need the fix because back_populates will infer the correct join
    role = relationship("UserRole", back_populates="users")
    tenant = relationship("Tenant", back_populates="users")


class Item(Base):
    __tablename__ = "items"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    price = Column(Integer)
    quantity = Column(Integer)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.tenants.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.users.id"))
    image_path = Column(String, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.users.id"), nullable=True)
    action = Column(String, nullable=False)
    details = Column(JSONB)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class ApiKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.users.id"), nullable=False)
    key_prefix = Column(String, nullable=False, unique=True)
    hashed_key = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)


class CustomObject(Base):
    __tablename__ = "custom_objects"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False)

    created_by_id = Column("created_by", UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by_id = Column("updated_by", UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.users.id"))

    # Relationships
    fields = relationship("CustomField", back_populates="custom_object", cascade="all, delete-orphan")
    records = relationship("Record", back_populates="custom_object", cascade="all, delete-orphan")


class CustomField(Base):
    __tablename__ = "custom_fields"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    object_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.custom_objects.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False)
    field_type = Column(String, nullable=False)  # e.g., 'text', 'number', 'date', 'boolean', 'select'
    is_required = Column(Boolean, default=False, nullable=False)
    options = Column(JSONB)  # For 'select' type, e.g., {"options": ["A", "B"]}

    created_by_id = Column("created_by", UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    custom_object = relationship("CustomObject", back_populates="fields")


class Record(Base):
    __tablename__ = "records"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    object_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.custom_objects.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.tenants.id"), nullable=False)
    data = Column(JSONB, nullable=False)

    created_by_id = Column("created_by", UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by_id = Column("updated_by", UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.users.id"))

    # Relationships
    custom_object = relationship("CustomObject", back_populates="records")


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    external_product_id = Column(String, nullable=True)  # For Dodo/Stripe
    external_price_id = Column(String, nullable=True)  # For Dodo/Stripe
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    entitlements = relationship("PlanEntitlement", back_populates="plan", cascade="all, delete-orphan")
    tenants = relationship("Tenant", back_populates="plan")


class PlanEntitlement(Base):
    __tablename__ = "plan_entitlements"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.plans.id"), nullable=False)
    feature_slug = Column(String, nullable=False)  # e.g., "max_users"
    entitlement_type = Column(String, nullable=False)  # 'FLAG', 'LIMIT', or 'METER'
    value = Column(Integer, nullable=False)

    # Relationships
    plan = relationship("Plan", back_populates="entitlements")


class UsageRecord(Base):
    __tablename__ = "usage_records"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.tenants.id"), nullable=False)
    feature_slug = Column(String, nullable=False)
    usage_amount = Column(Integer, nullable=False)
    recorded_at = Column(DateTime, default=func.now(), nullable=False)



class CheckoutSession(Base):
    __tablename__ = "checkout_sessions"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(String, primary_key=True) # Dodo session ID
    tenant_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.tenants.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.plans.id"), nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    created_at = Column(DateTime, default=func.now(), nullable=False)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(String, primary_key=True) # The webhook-id from the header
    event_type = Column(String, nullable=False)
    received_at = Column(DateTime, default=func.now(), nullable=False)
    processed_successfully = Column(Boolean, default=False)
    payload = Column(JSONB)


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.tenants.id"), nullable=False)

    name = Column(String, nullable=False)
    email = Column(String, nullable=True)

    customer_data = Column(JSONB)

    # The attribute name and the column name should match. We remove the incorrect mapping.
    created_by_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA_NAME}.users.id"))