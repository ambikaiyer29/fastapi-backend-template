# Features of the FastAPI SaaS Starter Kit

## Build Your Vision, Not Your Boilerplate

You're a developer with a great idea for a B2B SaaS application. You know your market, and you know the core features that will make your product unique. But between you and your first paying customer lies a mountain of foundational, repetitive, and security-critical work.

Authentication, multi-tenancy, billing, permissions, user management—this is the boilerplate that consumes weeks of development time and pushes your launch date further and further away.

This starter kit is designed to eliminate that mountain.

We've built the complete, production-grade foundation for a modern B2B SaaS application, so you can skip the boilerplate and start building your core business logic on day one. This isn't just a collection of scripts; it's a cohesive platform, architected for security, scalability, and developer freedom.

**This starter kit is for:**
*   **Solo Founders & Indie Hackers** who need to move fast and launch an MVP without sacrificing security or scalability.
*   **Startup Teams** who want a consistent, professional backend foundation so they can focus on feature velocity.
*   **Freelancers & Agencies** who need to rapidly deliver robust, multi-tenant applications for their clients.
*   **Backend Developers** who want a powerful, standalone backend that gives them the freedom to connect any frontend (React, Vue, mobile) or just expose a pure API.

---

## Core Platform & Security Features

This is the bedrock of your application, designed for security and peace of mind.

*   #### 🛡️ Ironclad Multi-Tenancy (RLS)
    Your application is multi-tenant from the ground up. We use PostgreSQL's powerful **Row-Level Security (RLS)** to create a bank-grade, unbreakable wall between your customers' data at the database layer. A bug in your application code can never lead to a cross-tenant data leak.

*   #### 🔑 Unified Authentication (JWT & API Keys)
    A single, secure system for everyone. Authenticate users from your web app with **JWTs** and enable programmatic integrations for your power users with self-service **API Keys**. All standard flows, including password resets and email verification, are built-in.

*   #### 🔒 Granular Permissions & Roles (RBAC)
    Go beyond simple "admin" and "user" roles. Our flexible, bitmask-based Role-Based Access Control (RBAC) system allows you to create unlimited custom roles (like "Editor," "Viewer," "Accountant") and define exactly what they can do, protecting every API endpoint with fine-grained permission checks.

*   #### 🔎 Built-in Audit Trails
    Provide the accountability and security your B2B customers expect. The system automatically records critical events like user invitations and role changes into a secure, tenant-isolated audit log that admins can view.

---

## B2B Application & Monetization Features

This is the engine that turns your idea into a business.

*   #### Pluggable Monetization Engine
    **Ready to charge from day one.** The starter kit includes a complete subscription management and entitlement system.
    *   **Pluggable Providers:** Comes with ready-to-use, decoupled service integrations for both **Stripe** and **Dodo Payments**. Choose your provider via a simple environment variable.
    *   **Subscription Management:** APIs for creating checkout sessions and customer portals, allowing users to purchase and manage their subscriptions.
    *   **Robust Webhook Handling:** A secure, idempotent, and order-safe webhook system to manage the entire subscription lifecycle (`active`, `past_due`, `canceled`).
    *   **Entitlement System:** Define what each plan gets. Protect your API endpoints based on a tenant's subscription plan with support for **Flags** (on/off features), **Limits** (e.g., max users), and **Meters** (e.g., tokens per month).

*   #### First-Class Customer Management
    Built for B2B. We provide a first-class `Customer` object, allowing your tenants to manage their own clients, separate from the internal users who log into the system. This is the foundation for building any CRM, project management, or client-focused tool.

*   #### Dynamic "Salesforce-like" Application Builder
    This is the killer feature that turns your starter kit into a platform. You are not limited to pre-defined tables.
    *   **Define Custom Objects:** Allow your tenants to create their own data structures (e.g., "Deals," "Properties," "Invoices") directly via the API.
    *   **Define Custom Fields:** Let them specify the schema for their objects with typed fields (`text`, `number`, `date`, `select`, etc.).
    *   **Automatic API Generation:** The starter kit automatically provides secure, tenant-isolated, and permission-protected CRUD API endpoints for any custom object a tenant creates.

*   #### Secure, Multi-Tenant File Storage
    Handle file uploads with ease. The integration with Supabase Storage uses RLS policies on the storage layer itself, ensuring tenants can only ever upload to and retrieve files from their own secure folder.

---

## Use Cases & Ideas You Can Build Today

Because this starter kit is an extensible, open-source foundation, you can adapt it to a huge range of B2B SaaS ideas. Here are just a few to get you started:

*   **Micro-CRM for a Niche Industry:**
    *   Use the `Customer` object for contacts.
    *   Use the Dynamic Builder to create a "Deals" or "Opportunities" object with custom stages.
    *   Use File Storage to attach contracts or proposals to each deal.
    *   Use the **Billing Engine** to offer different tiers (e.g., "Basic CRM" vs. "Pro CRM" with more features).

*   **Project Management Tool for Agencies:**
    *   The `Tenant` is the agency.
    *   The `Customer` object represents the agency's clients.
    *   Use the Dynamic Builder to create a "Projects" object and a "Tasks" object, linking tasks to projects.
    *   Create custom roles like "Project Manager" and "Team Member" with different permissions.
    *   Use the **Billing Engine** to charge agencies based on the number of users or projects (a `LIMIT` entitlement).

*   **Simple Invoicing Platform for Freelancers:**
    *   The `Tenant` is the freelancer.
    *   The `Customer` object represents their clients.
    *   Use the Dynamic Builder to create an "Invoices" object with fields like `amount`, `due_date`, and `status`.
    *   Use the **Billing Engine** to charge the freelancer a monthly subscription fee for using the platform.

*   **Vertical SaaS for a Specific Business:**
    *   (e.g., for a gym) The `Tenant` is the gym.
    *   The `Customer` object represents gym members.
    *   Use the Dynamic Builder to create a "Classes" object and a "Bookings" object.
    *   Use the **Billing Engine** to offer different membership tiers to the gym.

This is more than just code; it's a launchpad. Fork it, customize it, and build your vision. **Since the entire foundation is open and extensible, you are never locked in.** You have the freedom to take this in any direction you choose.