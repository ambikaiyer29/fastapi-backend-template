INSERT INTO "fastapiSK".tenants (name, slug)
VALUES ('My Test Tenant', 'test-tenant')
RETURNING id;



INSERT INTO "fastapiSK".user_roles (name, tenant_id, is_admin_role)
VALUES ('Admin', '2b2480af-0495-4f28-aded-ab28bdb64282', true)
RETURNING id;


INSERT INTO "fastapiSK".users (id, email, tenant_id, role_id)
VALUES (
    '3999078f-70dc-4d15-9c83-bbbad388d172',
    'youremail+25@gmail.com',
    '2b2480af-0495-4f28-aded-ab28bdb64282',
    'fcddac8e-8034-4364-9b69-e0635437fdd8'
);