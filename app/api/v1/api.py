from fastapi import APIRouter
from app.api.v1.routers import tenants, health, users, roles, items, superadmin, uploads, auth, onboarding, audit_logs, \
    api_keys, custom_objects, records, plans, public, subscriptions, webhooks, customers

# This is the main router for the v1 API
api_router = APIRouter()

# Include the tenants router
# All routes from tenants.py will now be prefixed with '/tenants'
# and tagged as 'Tenants' in the OpenAPI docs
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(items.router, prefix="/items", tags=["Items"])

# Its endpoints will have /superadmin prefix and will use the get_superadmin dependency.
api_router.include_router(superadmin.router, prefix="/superadmin", tags=["Superadmin"])

api_router.include_router(uploads.router, prefix="/uploads", tags=["File Uploads"])

# Protected onboarding route
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])

api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])

api_router.include_router(api_keys.router, prefix="/api-keys", tags=["API Keys"])

api_router.include_router(custom_objects.router, prefix="/custom-objects", tags=["Dynamic Objects (Metadata)"])
api_router.include_router(records.router, prefix="/records", tags=["Dynamic Records (Data)"])

api_router.include_router(plans.router, prefix="/plans", tags=["Plans (Superadmin)"])
# The public router for pricing pages, etc.
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])

# The protected router for tenants to manage their subscription
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions (Tenant Admin)"])


public_api_router = APIRouter()
public_api_router.include_router(public.router, prefix="/public", tags=["Public"])
public_api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
public_api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

