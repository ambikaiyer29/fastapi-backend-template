-- Create the schema for our application
CREATE SCHEMA IF NOT EXISTS "fastapiSK";

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Tenants Table
-- Stores information about each tenant (organization/customer)
CREATE TABLE "fastapiSK".tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    admin_user_id UUID, -- Can be updated after initial creation
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

-- 2. User Roles Table
-- Defines roles and their permission sets within a tenant
CREATE TABLE "fastapiSK".user_roles (
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

-- 3. Users Table
-- Stores user information, linking them to a tenant and a role
CREATE TABLE "fastapiSK".users (
    id UUID PRIMARY KEY, -- This ID comes from Supabase Auth
    email TEXT NOT NULL UNIQUE,
    role_id UUID REFERENCES "fastapiSK".user_roles(id) ON DELETE SET NULL,
    tenant_id UUID NOT NULL REFERENCES "fastapiSK".tenants(id) ON DELETE CASCADE,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

-- 4. Items Table
-- A sample resource table to demonstrate multi-tenancy
CREATE TABLE "fastapiSK".items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    price INT, -- Store price in cents
    quantity INT,
    tenant_id UUID NOT NULL REFERENCES "fastapiSK".tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES "fastapiSK".users(id),
    updated_by UUID REFERENCES "fastapiSK".users(id)
);


-- 1. Rename the 'metadata' column in the 'tenants' table.
ALTER TABLE "fastapiSK".tenants RENAME COLUMN metadata TO tenant_data;

-- 2. Rename the 'metadata' column in the 'users' table.
ALTER TABLE "fastapiSK".users RENAME COLUMN metadata TO user_data;


-- Add foreign key constraint from tenants to users for the admin_user_id
-- This must be done after the users table is created
ALTER TABLE "fastapiSK".tenants
ADD CONSTRAINT fk_admin_user
FOREIGN KEY (admin_user_id)
REFERENCES "fastapiSK".users(id)
ON DELETE SET NULL;

-- Optional: Create indexes for frequently queried columns
CREATE INDEX idx_items_tenant_id ON "fastapiSK".items(tenant_id);
CREATE INDEX idx_users_tenant_id ON "fastapiSK".users(tenant_id);
CREATE INDEX idx_user_roles_tenant_id ON "fastapiSK".user_roles(tenant_id);



-- RLS POLICIES SCRIPT
-- Run this script AFTER creating the tables.

-- First, ensure all tables have RLS enabled.
-- This is a critical step; without it, policies are not enforced.
ALTER TABLE "fastapiSK".tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".users ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fastapiSK".items ENABLE ROW LEVEL SECURITY;

-- Create a helper function to safely get config settings.
-- It returns NULL if the setting is not found, preventing errors.
CREATE OR REPLACE FUNCTION "fastapiSK".get_current_setting(setting_name TEXT, is_nullable BOOLEAN DEFAULT false)
RETURNS TEXT AS $$
BEGIN
    RETURN current_setting(setting_name, is_nullable);
END;
$$ LANGUAGE plpgsql;





-- =================================================================
-- FINAL, PRODUCTION-GRADE RLS SCRIPT (Version 3)
-- This script adds a policy to allow users to select their own record,
-- which solves the initial lookup deadlock.
-- =================================================================

-- Drop all existing policies on the tables to ensure a clean slate.
DROP POLICY IF EXISTS "superadmin_bypass_policy" ON "fastapiSK".tenants;
DROP POLICY IF EXISTS "tenant_select_policy" ON "fastapiSK".tenants;
DROP POLICY IF EXISTS "tenant_update_policy" ON "fastapiSK".tenants;

DROP POLICY IF EXISTS "superadmin_bypass_policy" ON "fastapiSK".users;
DROP POLICY IF EXISTS "tenant_isolation_policy" ON "fastapiSK".users;
DROP POLICY IF EXISTS "user_can_select_self_policy" ON "fastapiSK".users; -- Drop the new one too

DROP POLICY IF EXISTS "superadmin_bypass_policy" ON "fastapiSK".user_roles;
DROP POLICY IF EXISTS "tenant_isolation_policy" ON "fastapiSK".user_roles;

DROP POLICY IF EXISTS "superadmin_bypass_policy" ON "fastapiSK".items;
DROP POLICY IF EXISTS "tenant_isolation_policy" ON "fastapiSK".items;

-- Policies for USERS table (The most important change is here)
---------------------------------------------------------------
-- 1. Superadmin can do anything.
CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".users FOR ALL
    USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean)
    WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);

-- 2. (THE FIX) A user can SELECT their own record. This is essential for the initial lookup.
CREATE POLICY "user_can_select_self_policy" ON "fastapiSK".users FOR SELECT
    USING (id = ("fastapiSK".get_current_setting('app.current_user_id', true))::uuid);

-- 3. Tenant members can access any user WITHIN their tenant.
CREATE POLICY "tenant_isolation_policy" ON "fastapiSK".users FOR ALL
    USING (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid)
    WITH CHECK (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);


-- Policies for TENANTS, USER_ROLES, ITEMS (These are standard and correct)
---------------------------------------------------------------
-- TENANTS
CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".tenants FOR ALL USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean) WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);
CREATE POLICY "tenant_select_policy" ON "fastapiSK".tenants FOR SELECT USING (id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);
CREATE POLICY "tenant_update_policy" ON "fastapiSK".tenants FOR UPDATE USING (id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid) WITH CHECK (id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);

-- USER_ROLES
CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".user_roles FOR ALL USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean) WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);
CREATE POLICY "tenant_isolation_policy" ON "fastapiSK".user_roles FOR ALL USING (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid) WITH CHECK (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);

-- ITEMS
CREATE POLICY "superadmin_bypass_policy" ON "fastapiSK".items FOR ALL USING (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean) WITH CHECK (("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean);
CREATE POLICY "tenant_isolation_policy" ON "fastapiSK".items FOR ALL USING (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid) WITH CHECK (tenant_id = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid);