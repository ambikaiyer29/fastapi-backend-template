CREATE ROLE api_user
WITH LOGIN
PASSWORD 'YourStrongAndUniquePasswordHere'
NOSUPERUSER
NOCREATEDB
NOCREATEROLE
INHERIT
NOREPLICATION
CONNECTION LIMIT -1
NOBYPASSRLS;


-- 1. Grant usage on the schema. This allows the user to "see" the schema and its objects.
GRANT USAGE ON SCHEMA "fastapiSK" TO api_user;

-- 2. Grant USAGE on all sequences in the schema, which might be used for future tables with serial keys.
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA "fastapiSK" TO api_user;

-- 3. Grant the specific permissions our API needs on the tables.
-- It needs to be able to do everything (SELECT, INSERT, UPDATE, DELETE).
-- RLS policies will handle the row-level restrictions from here.
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "fastapiSK".tenants TO api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "fastapiSK".user_roles TO api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "fastapiSK".users TO api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "fastapiSK".items TO api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "fastapiSK".audit_logs TO api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "fastapiSK".api_keys TO api_user;

-- 4. Grant Permissions to 'api_user'.
-- (Remember to add this to your master schema.sql)
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "fastapiSK".custom_objects TO api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "fastapiSK".custom_fields TO api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "fastapiSK".records TO api_user;

-- 5. Grant Permissions to 'api_user'.
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "fastapiSK".plans TO api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "fastapiSK".plan_entitlements TO api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "fastapiSK".usage_records TO api_user;

-- 2. Grant Permissions to 'api_user'.
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "fastapiSK".checkout_sessions TO api_user;
GRANT SELECT, INSERT, UPDATE ON TABLE "fastapiSK".webhook_events TO api_user;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "fastapiSK".customers TO api_user;

-- Grant necessary privileges to the new role
GRANT USAGE ON SCHEMA "fastapiSK" TO api_user;

-- Grant permissions on ALL TABLES that exist in the schema
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA "fastapiSK" TO api_user;

-- Grant permissions on ALL SEQUENCES for future use with serial keys
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA "fastapiSK" TO api_user;