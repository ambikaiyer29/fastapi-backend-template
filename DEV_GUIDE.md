
# FastAPI Multi-Tenant SaaS Starter Kit

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?style=for-the-badge&logo=postgresql)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?style=for-the-badge&logo=sqlalchemy)
![Supabase](https://img.shields.io/badge/Supabase-Auth-3ecf8e?style=for-the-badge&logo=supabase)

A production-grade starter kit for building secure, multi-tenant SaaS applications using FastAPI, PostgreSQL with Row-Level Security, and Supabase for authentication.

This project provides a robust foundation with a clear, modular structure, allowing you to focus on your application's core business logic instead of reinventing the wheel for security, user management, and multi-tenancy.

---

## ✨ Core Features

*   **Multi-Tenancy with RLS:** Securely isolates data between tenants at the database level using PostgreSQL's Row-Level Security (RLS). This is the gold standard for SaaS data security.
*   **Supabase Auth Integration:** Leverages Supabase for authentication, handling user sign-ups, invites, and JWT management. The code is decoupled, allowing for easy replacement with another auth provider.
*   **Role-Based Access Control (RBAC):** A flexible, bitmask-based permission system allows for granular control over what users can do within their tenant.
*   **Superadmin & Tenant Admin Roles:**
    *   **Superadmin (SaaS Owner):** Can onboard new tenants, manage their lifecycle, and has full system visibility.
    *   **Tenant Admin:** Can invite/manage users and create/assign custom roles within their own tenant.
*   **Production-Ready Foundation:** Includes structured logging, Prometheus metrics instrumentation, connection pooling, and a modular API structure.
*   **Asynchronous from the Start:** Built on FastAPI for high performance.
*   **Dependency Injection:** Heavily uses FastAPI's dependency injection for clean, testable, and reusable code (e.g., getting the current user, database sessions with RLS context).

## 🚀 Getting Started

Follow these instructions to get the project running on your local machine for development and testing.

### Prerequisites

*   **Python 3.11+**
*   **PostgreSQL 15+** (Can be a local instance or a free one from [Supabase](https://supabase.com/))
*   **A Supabase Project:** For authentication. You only need the Auth service.
*   **Postman (Optional but Recommended):** For testing the API endpoints. An end-to-end collection is provided.

### 1. Fork & Clone the Repository

First, fork this repository to your own GitHub account, then clone it to your local machine.

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Set Up the Environment

#### A. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
# On Windows, use: .venv\Scripts\activate
```

#### B. Install Dependencies

```bash
pip install -r requirements.txt
```

#### C. Configure Environment Variables

Create a `.env` file in the root of the project by copying the example file:

```bash
cp .env.example .env
```

Now, open the `.env` file and fill in the required values.

*   **Supabase Credentials:**
    *   Go to your Supabase project dashboard.
    *   `SUPABASE_URL`: Found in **Project Settings > API > Project URL**.
    *   `SUPABASE_JWT_SECRET`: Found in **Project Settings > API > JWT Settings**.
    *   `SUPABASE_SERVICE_ROLE_KEY`: Found in **Project Settings > API > Project API keys**.

*   **Database Credentials:**
    *   This starter kit uses a dedicated, non-privileged role (`api_user`) for the application, which is a security best practice.
    *   `DATABASE_URL`: The connection string for your PostgreSQL database.
        *   **Format:** `postgresql+psycopg2://<user>:<password>@<host>:<port>/<dbname>`
        *   **Important:** The user in this string should be the `api_user`, not the `postgres` superuser. See the database setup section below.

*   **Superadmin Configuration:**
    *   `SUPERADMIN_USER_ID`: The UUID of the user who will be the SaaS owner. You will create this user manually in Supabase Auth and paste their UID here.

### 3. Set Up the Database

#### A. Run the Initial SQL Scripts

The security of this application depends on specific database roles and policies. You must run these scripts in order using a PostgreSQL superuser account (like the default `postgres` user in Supabase's SQL Editor).

You should create a `/sql` directory in your project and place these scripts there.

1.  **`01_create_schema_and_tables.sql`:** Creates the `fastapiSK` schema and all required tables (`tenants`, `users`, `user_roles`, `items`).
2.  **`02_create_api_user_role.sql`:** Creates the dedicated `api_user` role with a secure password and grants it the necessary table permissions. **Remember to update the `DATABASE_URL` in your `.env` file with this user and password.**
3.  **`03_enable_rls_and_create_policies.sql`:** Enables Row-Level Security on all tables and creates the policies that enforce tenant isolation and superadmin access.

#### B. Create the Superadmin User

1.  Go to your Supabase dashboard **Authentication** section.
2.  Manually create a user (e.g., `superadmin@yourapp.com`) with a strong password.
3.  Copy the `UID` of this new user.
4.  Paste this `UID` into the `SUPERADMIN_USER_ID` variable in your `.env` file.

### 4. Run the Application

You can run the application using Uvicorn. The `--reload` flag is great for development.

```bash
uvicorn app.main:app --reload
```

The API will now be available at `http://12_7.0.0.1:8000`. You can access the interactive documentation at `http://127.0.0.1:8000/docs`.

## 🧪 Testing with Postman

An end-to-end Postman collection is provided to test the entire user and permissions flow.

1.  **Import:** Import the `SaaS_Starter_Kit.postman_collection.json` file into Postman.
2.  **Configure:**
    *   Click on the collection and go to the **Variables** tab.
    *   Ensure `baseUrl` is set to `http://127.0.0.1:8000`.
    *   Generate a JWT for your **superadmin** user using the `get_token.py` script and paste it into the `CURRENT VALUE` for the `superadmin_jwt` variable.
3.  **Run in Sequence:** The folders are numbered `00` to `03`. Run the requests in order. The collection includes test scripts that automatically capture IDs and tokens and save them as variables for subsequent requests.
4.  **Manual Steps:** You will be prompted to manually generate JWTs for the **Tenant Admin** and the invited **Editor** user as you progress through the collection. The `confirm_user.py` script can be used to set a password for invited users.

## 🛠️ Extending the Starter Kit (Your Application Logic)

This starter kit is designed to be a foundation. Here’s how to replace the example `items` resource with your own business logic (e.g., `projects`, `invoices`, `documents`).

Let's say you are building a project management tool and want to add a `projects` resource.

1.  **Database: Add a `projects` Table**
    *   Add a `CREATE TABLE` statement to your SQL schema file for a `projects` table.
    *   **Crucially, it must include a `tenant_id UUID NOT NULL` column** with a foreign key to `fastapiSK.tenants`.
    *   Add the RLS policies and `FORCE ROW LEVEL SECURITY` for this new table, copying the pattern from the `items` table.

2.  **ORM Model: Create `Project` in `app/db/models.py`**
    *   Create a new SQLAlchemy class `Project(Base)` that maps to your `projects` table.
    *   Add the `projects = relationship(...)` to your `Tenant` model to link them, including `cascade="all, delete-orphan"`.

3.  **Schemas: Create `app/schemas/project_schemas.py`**
    *   Create `ProjectCreate`, `ProjectUpdate`, and `ProjectRead` Pydantic schemas to define the API data contract for your new resource.

4.  **CRUD Logic: Create `app/crud/project_crud.py`**
    *   Create functions like `create_project`, `get_project_by_id`, etc. These will be very simple, as RLS handles the security. Copy the structure from `item_crud.py`.

5.  **API Endpoints: Create `app/api/v1/routers/projects.py`**
    *   Create a new `APIRouter`.
    *   Build the CRUD endpoints (`POST /`, `GET /`, `GET /{project_id}`, etc.).
    *   Protect these endpoints using the `require_permission` dependency. You will first need to define new permissions (e.g., `PROJECTS_READ`, `PROJECTS_CREATE`) in `app/core/permissions.py`.

6.  **API Hub: Register the Router in `app/api/v1/api.py`**
    *   Import your new router and include it in the `api_router`.

    ```python
    # In app/api/v1/api.py
    from app.api.v1.routers import ..., projects # Import
    
    # ...
    api_router.include_router(projects.router, prefix="/projects", tags=["Projects"]) # Register
    ```

By following this pattern, you can add any number of multi-tenant resources to the application while ensuring that the core security and data isolation are automatically applied.

## 💡 Project Structure

```
/app
|-- /api/v1             # API v1 logic
|   |-- /routers        # Endpoint files (tenants.py, users.py, items.py)
|   |-- api.py          # Hub that combines all routers
|   |-- dependencies.py # Core dependencies (get_current_user, permission checks)
|-- /core               # Core logic (config, logging, permissions)
|-- /crud               # Database interaction logic (CRUD functions)
|-- /db                 # Database setup (models, session)
|-- /schemas            # Pydantic data models (schemas)
|-- /utils              # Utility functions (e.g., decorators)
|-- main.py             # FastAPI app entrypoint
/sql                    # Directory for SQL setup scripts
.env.example            # Environment variable template
requirements.txt        # Project dependencies
get_token.py            # Utility script to get JWTs for testing
confirm_user.py         # Utility script to confirm invited users
...
```

---

Happy building!

