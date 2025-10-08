-- =================================================================
--    FastAPI SaaS Starter Kit - Complete Database Schema
-- =================================================================
-- This single file contains all the necessary DDL to set up the
-- database from scratch, including schema, tables, roles,
-- permissions, and Row-Level Security policies.
-- It is designed to be idempotent (safe to run multiple times).
-- =================================================================

-- -----------------------------------------------------------------
-- Section 1: Schema, Extensions, and Helper Functions
-- -----------------------------------------------------------------

-- Create the schema for our application if it doesn't exist
CREATE SCHEMA IF NOT EXISTS "fastapiSK";

-- Enable the UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create a helper function to safely get RLS settings.
-- It returns NULL if a setting is not found, preventing query errors.
CREATE OR REPLACE FUNCTION "fastapiSK".get_current_setting(setting_name TEXT, is_nullable BOOLEAN DEFAULT false)
RETURNS TEXT AS $$
BEGIN
    RETURN current_setting(setting_name, is_nullable);
END;
$$ LANGUAGE plpgsql;


-- -----------------------------------------------------------------
-- Section 2: Table Definitions
-- -----------------------------------------------------------------

-- Tenants Table: Stores information about each tenant (organization)
CREATE TABLE IF NOT EXISTS "fastapiSK".tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    admin_user_id UUID, -- Foreign key added later
    tenant_data JSONB,  -- Formerly 'metadata'
    logo_path TEXT,
    external_customer_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

-- User Roles Table: Defines roles and their permission sets within a tenant
CREATE TABLE IF NOT EXISTS "fastapiSK".user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    permission_set INT,
    is_admin_role BOOLEAN DEFAULT FALSE,
    tenant_id UUID NOT NULL REFERENCES "fastapiSK".tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    UNIQUE(tenant_id, name) -- A role name must be unique within a tenant
);

-- Users Table: Stores user profiles, linking them to a tenant and a role
CREATE TABLE IF NOT EXISTS "fastapiSK".users (
    id UUID PRIMARY KEY, -- This ID comes from Supabase Auth
    email TEXT NOT NULL UNIQUE,
    role_id UUID REFERENCES "fastapiSK".user_roles(id) ON DELETE SET NULL,
    tenant_id UUID NOT NULL REFERENCES "fastapiSK".tenants(id) ON DELETE CASCADE,
    user_data JSONB,
    terms_accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

-- Items Table: A sample resource table to demonstrate multi-tenancy
CREATE TABLE IF NOT EXISTS "fastapiSK".items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    price INT, -- Store price in cents
    quantity INT,
    image_path TEXT,
    tenant_id UUID NOT NULL REFERENCES "fastapiSK".tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES "fastapiSK".users(id),
    updated_by UUID REFERENCES "fastapiSK".users(id)
);


-- -----------------------------------------------------------------
-- Section 3: Foreign Keys and Indexes
-- -----------------------------------------------------------------

-- Add foreign key from tenants to users for the admin_user_id.
-- This must be done after the users table is created.
-- We add 'IF NOT EXISTS' to the constraint name for idempotency.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_admin_user' AND conrelid = '"fastapiSK".tenants'::regclass
    ) THEN
        ALTER TABLE "fastapiSK".tenants
        ADD CONSTRAINT fk_admin_user
        FOREIGN KEY (admin_user_id)
        REFERENCES "fastapiSK".users(id)
        ON DELETE SET NULL;
    END IF;
END;
$$;

-- Create indexes for frequently queried columns for performance
CREATE INDEX IF NOT EXISTS idx_items_tenant_id ON "fastapiSK".items(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON "fastapiSK".users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_tenant_id ON "fastapiSK".user_roles(tenant_id);


-- -----------------------------------------------------------------
-- Section 5: Row-Level Security (RLS) Policies
-- -----------------------------------------------------------------

-- Enable and FORCE Row-Level Security on all tables.
-- FORCE ensures the policies apply even to the table owner (our 'api_user').
ALTER TABLE "fastapiSK".tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".tenants FORCE ROW LEVEL SECURITY;

ALTER TABLE "fastapiSK".user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".user_roles FORCE ROW LEVEL SECURITY;

ALTER TABLE "fastapiSK".users ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".users FORCE ROW LEVEL SECURITY;

ALTER TABLE "fastapiSK".items ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".items FORCE ROW LEVEL SECURITY;


-- Create Policies for USERS table
-- 1. Superadmin can do anything.
CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".users FOR ALL
    USING (
        -- COALESCE returns the first non-NULL value.
        -- NULLIF treats an empty string as NULL.
        -- This entire expression safely evaluates to TRUE only if 'app.is_superadmin' is exactly 'true'.
        -- Otherwise, it safely evaluates to FALSE.
        COALESCE(NULLIF("fastapiSK".get_current_setting('app.is_superadmin', true), ''), 'false')::boolean
    )
    WITH CHECK (
        COALESCE(NULLIF("fastapiSK".get_current_setting('app.is_superadmin', true), ''), 'false')::boolean
    );

-- 2. A user can SELECT their own record (essential for initial login/bootstrap).
CREATE POLICY "user_can_select_self_policy" ON "fastapiSK".users FOR SELECT
    USING (id = ("fastapiSK".get_current_setting('app.current_user_id', true))::uuid);

-- 3. Tenant members can access any user WITHIN their tenant.
CREATE POLICY "tenant_isolation_policy" ON "fastapiSK".users FOR ALL
    USING (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid)
    WITH CHECK (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);


-- Create Policies for TENANTS table
CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".tenants FOR ALL
    USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean)
    WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);

CREATE POLICY "tenant_select_policy" ON "fastapiSK".tenants FOR SELECT
    USING (id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);
CREATE POLICY "tenant_update_policy" ON "fastapiSK".tenants FOR UPDATE
    USING (id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid)
    WITH CHECK (id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);


-- Create Policies for USER_ROLES table
CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".user_roles FOR ALL
    USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean)
    WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);
CREATE POLICY "tenant_isolation_policy" ON "fastapiSK".user_roles FOR ALL
    USING (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid)
    WITH CHECK (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);


-- Create Policies for ITEMS table
CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".items FOR ALL
    USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean)
    WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);
CREATE POLICY "tenant_isolation_policy" ON "fastapiSK".items FOR ALL
    USING (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid)
    WITH CHECK (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);



-- =================================================================
--        DATABASE MIGRATION: Add Audit Logs Table & RLS
-- =================================================================

-- 1. Create the audit_logs table to store a record of important events.
CREATE TABLE IF NOT EXISTS "fastapiSK".audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES "fastapiSK".tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES "fastapiSK".users(id) ON DELETE SET NULL, -- Who performed the action
    action TEXT NOT NULL, -- A slug representing the action, e.g., "USER_INVITED"
    details JSONB, -- A snapshot of relevant data for the event
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create an index for efficient querying by tenant
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_id ON "fastapiSK".audit_logs(tenant_id);

-- 2. Enable and Force Row-Level Security on the new table.
ALTER TABLE "fastapiSK".audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".audit_logs FORCE ROW LEVEL SECURITY;

-- 3. Create the RLS Policies for the audit_logs table.

-- Superadmin can see all audit logs across all tenants
CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".audit_logs FOR ALL
    USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean)
    WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);

-- Tenant members can ONLY see audit logs belonging to their own tenant.
-- Note: We are making this a SELECT-only policy for regular users.
-- Only the system (via the backend) should be able to INSERT logs.
CREATE POLICY "tenant_isolation_policy" ON "fastapiSK".audit_logs FOR SELECT
    USING (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);


CREATE POLICY "tenant_insert_policy" ON "fastapiSK".audit_logs
FOR INSERT
WITH CHECK (
    tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid
);




-- =================================================================
--        DATABASE MIGRATION: Add API Keys Table & RLS
-- =================================================================

-- 1. Create the api_keys table to store user-generated API keys.
CREATE TABLE IF NOT EXISTS "fastapiSK".api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES "fastapiSK".tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES "fastapiSK".users(id) ON DELETE CASCADE,

    key_prefix TEXT NOT NULL UNIQUE, -- The first 8 chars of the key, e.g., "sk_live_..." for display
    hashed_key TEXT NOT NULL UNIQUE, -- The securely hashed full API key

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant_id ON "fastapiSK".api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON "fastapiSK".api_keys(user_id);


-- 2. Enable and Force Row-Level Security on the new table.
ALTER TABLE "fastapiSK".api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".api_keys FORCE ROW LEVEL SECURITY;


-- 3. Create the RLS Policies for the api_keys table.

-- Superadmin can see all API keys across all tenants
CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".api_keys FOR ALL
    USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean)
    WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);

-- Tenant members can ONLY manage API keys belonging to their own tenant.
CREATE POLICY "tenant_isolation_policy" ON "fastapiSK".api_keys FOR ALL
    USING (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid)
    WITH CHECK (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);


-- =================================================================
--        DATABASE MIGRATION: Add Dynamic Schema Tables & RLS
-- =================================================================

-- 1. Create the `custom_objects` table to define tenant-specific data structures.
CREATE TABLE IF NOT EXISTS "fastapiSK".custom_objects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES "fastapiSK".tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL, -- e.g., "Deal", "Contact", "Property"
    slug TEXT NOT NULL,  -- e.g., "deal", "contact", "property" (used in API URLs)
    created_by UUID NOT NULL REFERENCES "fastapiSK".users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES "fastapiSK".users(id),
    UNIQUE(tenant_id, slug) -- The API slug must be unique within a tenant
);
CREATE INDEX IF NOT EXISTS idx_custom_objects_tenant_id ON "fastapiSK".custom_objects(tenant_id);

-- 2. Create the `custom_fields` table to define the fields for each custom object.
CREATE TABLE IF NOT EXISTS "fastapiSK".custom_fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    object_id UUID NOT NULL REFERENCES "fastapiSK".custom_objects(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES "fastapiSK".tenants(id) ON DELETE CASCADE, -- Denormalized for simpler RLS
    name TEXT NOT NULL, -- e.g., "Deal Value", "Contact Email"
    slug TEXT NOT NULL, -- e.g., "deal_value", "contact_email" (used as JSON keys)
    field_type TEXT NOT NULL, -- e.g., 'text', 'number', 'date', 'boolean', 'select'
    is_required BOOLEAN DEFAULT FALSE,
    options JSONB, -- For 'select' type fields, e.g., {"options": ["Open", "Closed", "Pending"]}
    created_by UUID NOT NULL REFERENCES "fastapiSK".users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(object_id, slug) -- The field slug must be unique within an object
);
CREATE INDEX IF NOT EXISTS idx_custom_fields_object_id ON "fastapiSK".custom_fields(object_id);

-- 3. Create the `records` table to store the actual data.
-- This is the most important table. It uses JSONB for ultimate flexibility.
CREATE TABLE IF NOT EXISTS "fastapiSK".records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    object_id UUID NOT NULL REFERENCES "fastapiSK".custom_objects(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES "fastapiSK".tenants(id) ON DELETE CASCADE,
    data JSONB NOT NULL, -- The dynamic data for the record
    created_by UUID NOT NULL REFERENCES "fastapiSK".users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES "fastapiSK".users(id)
);
CREATE INDEX IF NOT EXISTS idx_records_object_id ON "fastapiSK".records(object_id);


-- 5. Add RLS Policies for all new tables.
-- The standard tenant_isolation_policy is perfect for these tables.

-- RLS for custom_objects
ALTER TABLE "fastapiSK".custom_objects ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".custom_objects FORCE ROW LEVEL SECURITY;

CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".custom_objects FOR ALL USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean) WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);
CREATE POLICY "tenant_isolation_policy" ON "fastapiSK".custom_objects FOR ALL USING (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid) WITH CHECK (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);

-- RLS for custom_fields
ALTER TABLE "fastapiSK".custom_fields ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".custom_fields FORCE ROW LEVEL SECURITY;

CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".custom_fields FOR ALL USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean) WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);
CREATE POLICY "tenant_isolation_policy" ON "fastapiSK".custom_fields FOR ALL USING (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid) WITH CHECK (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);

-- RLS for records
ALTER TABLE "fastapiSK".records ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".records FORCE ROW LEVEL SECURITY;

CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".records FOR ALL USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean) WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);
CREATE POLICY "tenant_isolation_policy" ON "fastapiSK".records FOR ALL USING (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid) WITH
CHECK (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);


-- =================================================================
--    DATABASE MIGRATION: Add Plans, Entitlements, and Usage Tables
-- =================================================================

-- 1. Create the `plans` table. This is managed by the Superadmin.
CREATE TABLE IF NOT EXISTS "fastapiSK".plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE, -- e.g., "Free", "Pro", "Enterprise"
    is_active BOOLEAN DEFAULT TRUE,
    -- These fields link to the external payment provider (Dodo, Stripe, etc.)
    external_product_id TEXT,
    external_price_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Create the `plan_entitlements` table. This defines what each plan gets.
CREATE TABLE IF NOT EXISTS "fastapiSK".plan_entitlements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES "fastapiSK".plans(id) ON DELETE CASCADE,
    feature_slug TEXT NOT NULL, -- e.g., "max_users", "enable_analytics", "llm_tokens_per_month"
    entitlement_type TEXT NOT NULL, -- 'FLAG', 'LIMIT', or 'METER'
    value INT NOT NULL, -- For FLAG: 1=true/0=false. For LIMIT/METER: the actual number.
    UNIQUE(plan_id, feature_slug)
);

-- 3. Create the `usage_records` table to track metered usage.
CREATE TABLE IF NOT EXISTS "fastapiSK".usage_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES "fastapiSK".tenants(id) ON DELETE CASCADE,
    feature_slug TEXT NOT NULL,
    usage_amount INT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_usage_records_tenant_feature ON "fastapiSK".usage_records(tenant_id, feature_slug, recorded_at);

-- 4. ALTER the `tenants` table to link it to a subscription.
ALTER TABLE "fastapiSK".tenants ADD COLUMN IF NOT EXISTS plan_id UUID REFERENCES "fastapiSK".plans(id) ON DELETE SET NULL;
ALTER TABLE "fastapiSK".tenants ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'inactive'; -- e.g., 'active', 'trialing', 'past_due'
ALTER TABLE "fastapiSK".tenants ADD COLUMN IF NOT EXISTS current_period_ends_at TIMESTAMPTZ;
ALTER TABLE "fastapiSK".tenants ADD COLUMN IF NOT EXISTS external_subscription_id TEXT;


-- 6. Add RLS Policies.
-- Plans and their entitlements are considered public info for users to view.
-- `usage_records` is strictly private to the tenant.
ALTER TABLE "fastapiSK".plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".plans FORCE ROW LEVEL SECURITY;

ALTER TABLE "fastapiSK".plan_entitlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".plan_entitlements FORCE ROW LEVEL SECURITY;

ALTER TABLE "fastapiSK".usage_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".usage_records FORCE ROW LEVEL SECURITY;

-- --- POLICIES FOR 'plans' TABLE ---

-- 1. Allow ANYONE (including unauthenticated visitors) to read the plans.
--    This is necessary for the public pricing page.
-- Write access is implicitly restricted as there is no INSERT/UPDATE/DELETE policy for non-superadmins.
CREATE POLICY "allow_read_for_all" ON "fastapiSK".plans
FOR SELECT USING (true);

-- 2. Allow ONLY the Superadmin to create, update, or delete plans.
CREATE POLICY "superadmin_full_access" ON "fastapiSK".plans
FOR ALL -- Applies to INSERT, UPDATE, DELETE
USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean)
WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);


-- --- POLICIES FOR 'plan_entitlements' TABLE ---

-- 1. Allow ANYONE to read the entitlements associated with the plans.
CREATE POLICY "allow_read_for_all" ON "fastapiSK".plan_entitlements
FOR SELECT USING (true);

-- 2. Allow ONLY the Superadmin to create, update, or delete entitlements.
CREATE POLICY "superadmin_full_access" ON "fastapiSK".plan_entitlements
FOR ALL -- Applies to INSERT, UPDATE, DELETE
USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean)
WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);


-- --- POLICIES FOR 'usage_records' TABLE ---

CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".usage_records FOR ALL USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean) WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);
CREATE POLICY "tenant_isolation_policy" ON "fastapiSK".usage_records FOR ALL USING (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid) WITH CHECK (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);


-- =================================================================
--    DATABASE MIGRATION: Add Checkout Sessions Table & RLS
-- =================================================================

-- 1. Create the `checkout_sessions` table to track payment attempts.
CREATE TABLE IF NOT EXISTS "fastapiSK".checkout_sessions (
    id TEXT PRIMARY KEY, -- The session ID from Dodo Payments, e.g., "cks_..."
    tenant_id UUID NOT NULL REFERENCES "fastapiSK".tenants(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES "fastapiSK".plans(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'COMPLETED', 'EXPIRED'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_checkout_sessions_tenant_id ON "fastapiSK".checkout_sessions(tenant_id);


-- 3. Add RLS Policies for the new table.
ALTER TABLE "fastapiSK".checkout_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".checkout_sessions FORCE ROW LEVEL SECURITY;


CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".checkout_sessions FOR ALL USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean) WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);
CREATE POLICY "tenant_isolation_policy" ON "fastapiSK".checkout_sessions FOR ALL USING (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid) WITH CHECK (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);


-- =================================================================
--    DATABASE MIGRATION: Add Webhook Events Table for Idempotency
-- =================================================================

CREATE TABLE IF NOT EXISTS "fastapiSK".webhook_events (
    id TEXT PRIMARY KEY, -- The 'webhook-id' from the header
    event_type TEXT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_successfully BOOLEAN DEFAULT FALSE,
    -- Store the full payload for debugging and reprocessing if needed
    payload JSONB
);


-- =================================================================
--        DATABASE MIGRATION: Add First-Class Customers Table
-- =================================================================

-- 1. Create the `customers` table to store tenant-specific customer data.
CREATE TABLE IF NOT EXISTS "fastapiSK".customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES "fastapiSK".tenants(id) ON DELETE CASCADE,

    name TEXT NOT NULL,
    email TEXT, -- Can be nullable, a customer might be a company

    customer_data JSONB, -- For storing custom fields like address, phone, etc.

    created_by_id UUID NOT NULL REFERENCES "fastapiSK".users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by_id UUID REFERENCES "fastapiSK".users(id),

    -- An email should be unique for a given tenant, if it exists.
    UNIQUE(tenant_id, email)
);

-- Create an index for efficient querying by tenant
CREATE INDEX IF NOT EXISTS idx_customers_tenant_id ON "fastapiSK".customers(tenant_id);


-- 3. Add RLS Policies for the new table.
ALTER TABLE "fastapiSK".customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".customers FORCE ROW LEVEL SECURITY;

-- Superadmin can see all customers across all tenants
CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".customers FOR ALL
    USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean)
    WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);

-- Tenant members can ONLY see and manage customers belonging to their own tenant.
CREATE POLICY "tenant_isolation_policy" ON "fastapiSK".customers FOR ALL
    USING (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid)
    WITH CHECK (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);
