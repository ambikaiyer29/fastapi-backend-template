import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from your .env file
load_dotenv()

# Get your Supabase URL and anon key from environment variables
# Note: For this script, you need the ANON KEY, not the JWT secret.
# Find it in your Supabase Dashboard: Project Settings > API > Project API keys
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_KEY") # Add this to your .env file!

def get_jwt(email, pwd):
    """
    Signs in a Supabase user and returns their JWT access token.
    """
    if not all([SUPABASE_URL, SUPABASE_ANON_KEY]):
        print("Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set in your .env file.")
        return

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print("Authenticating...")
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": pwd
        })

        # The access token is in the session object
        access_token = response.session.access_token
        print("\n" + "="*50)
        print("✅ Successfully authenticated!")
        print(f"JWT for email {email}")
        print("Your JWT Access Token is:\n")
        print(access_token)
        print("="*50 + "\n")

    except Exception as e:
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    get_jwt("editor@yourdomain.com", "a-secure-password-for-testing")
