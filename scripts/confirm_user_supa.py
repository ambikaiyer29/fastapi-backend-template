# confirm_user.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from your .env file
load_dotenv()

# Use the SERVICE ROLE KEY for admin actions
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# --- CONFIGURE THESE TWO VARIABLES ---
USER_EMAIL_TO_CONFIRM = "editor@yourdomain.com"  # The email of the user you invited
NEW_PASSWORD = "a-secure-password-for-testing"  # The password you want to set


def confirm_and_update_user():
    """
    Finds an invited user by email, confirms them, and sets their password.
    """
    if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY]):
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in your .env file.")
        return

    try:
        print(f"Connecting to Supabase at {SUPABASE_URL}...")
        supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        # 1. Get the user by their email
        print(f"Searching for user: {USER_EMAIL_TO_CONFIRM}")
        response = supabase_admin.auth.admin.list_users()

        target_user = None
        for user in response:
            if user.email == USER_EMAIL_TO_CONFIRM:
                target_user = user
                break

        if not target_user:
            print(f"❌ Error: User with email '{USER_EMAIL_TO_CONFIRM}' not found.")
            return

        print(f"✅ Found user with ID: {target_user.id}")

        # 2. Update the user's attributes
        print(f"Updating user... Setting password and confirming email.")
        update_response = supabase_admin.auth.admin.update_user_by_id(
            target_user.id,
            {"password": NEW_PASSWORD, "email_confirm": True}
        )

        updated_user = update_response.user
        print("\n" + "=" * 50)
        if updated_user and updated_user.email_confirmed_at:
            print("✅ Successfully confirmed user and set password!")
        else:
            print("⚠️  Something went wrong. The user might not be fully updated.")
            print("Response:", update_response)
        print("=" * 50 + "\n")

    except Exception as e:
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    confirm_and_update_user()