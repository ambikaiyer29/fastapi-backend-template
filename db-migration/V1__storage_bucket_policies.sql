-- =================================================================
--        Final RLS Policies for Supabase Storage (`tenant-assets` bucket)
-- =================================================================
-- Run this script in the Supabase SQL Editor.
-- DO NOT run "ALTER TABLE storage.objects..." manually.
-- Creating the first policy via the UI or running this script will
-- implicitly enable RLS on the storage objects table.

-- 1. Create a helper function to extract the tenant_id from a file path.
--    This function is idempotent and safe to run multiple times.
CREATE OR REPLACE FUNCTION "fastapiSK".get_tenant_id_from_path(path_text TEXT)
RETURNS UUID AS $$
DECLARE
    tenant_id_str TEXT;
BEGIN
    tenant_id_str := split_part(path_text, '/', 1);
    -- Handle potential errors if the path is not in the expected format
    BEGIN
        RETURN tenant_id_str::UUID;
    EXCEPTION WHEN invalid_text_representation THEN
        RETURN NULL;
    END;
END;
$$ LANGUAGE plpgsql;


-- POLICY: Allow users to view files within their own tenant's folder.
CREATE POLICY "tenant_select_policy"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'tenant-assets' AND
    (
        -- Superadmin can see everything
        ("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean OR
        -- Tenant users can see files if the path starts with their tenant_id
        "fastapiSK".get_tenant_id_from_path(name) = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid
    )
);

-- POLICY: Allow users to upload files into their own tenant's folder.
CREATE POLICY "tenant_insert_policy"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'tenant-assets' AND
    (
        -- Superadmin can insert anywhere (for administrative tasks)
        ("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean OR
        -- Tenant users can ONLY insert files if the path starts with their tenant_id
        "fastapiSK".get_tenant_id_from_path(name) = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid
    )
);

-- POLICY: Allow users to update/move files within their own tenant's folder.
CREATE POLICY "tenant_update_policy"
ON storage.objects FOR UPDATE
USING (
    bucket_id = 'tenant-assets' AND
    (
        -- Superadmin can update anything
        ("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean OR
        -- Tenant users can ONLY update files if the path starts with their tenant_id
        "fastapiSK".get_tenant_id_from_path(name) = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid
    )
);

-- POLICY: Allow users to delete files from their own tenant's folder.
CREATE POLICY "tenant_delete_policy"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'tenant-assets' AND
    (
        -- Superadmin can delete anything
        ("fastapiSK".get_current_setting('app.is_superadmin', true))::boolean OR
        -- Tenant users can ONLY delete files if the path starts with their tenant_id
        "fastapiSK".get_tenant_id_from_path(name) = ("fastapiSK".get_current_setting('app.current_tenant_id', true))::uuid
    )
);