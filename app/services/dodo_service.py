# app/services/dodo_service.py
import httpx
import json
from fastapi import HTTPException, status, Request
from standardwebhooks import Webhook

from app.api.v1.security import AuthenticatedUser
from app.core.config import get_settings


class DodoPaymentsService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.DODO_API_KEY
        self.webhook_secret = settings.DODO_WEBHOOK_SECRET
        # Use the test URL from the docs for development
        self.base_url = settings.DODO_BASE_URL
        # The standardwebhooks library instance
        self.webhook_verifier = Webhook(self.webhook_secret)

    async def get_product_details(self, product_id: str) -> dict | None:
        """
        Fetches detailed information for a single product from the Dodo Payments API.
        Returns None if the product is not found.
        """
        if not product_id:
            return None

        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = await client.get(
                    f"{self.base_url}/products/{product_id}",
                    headers=headers
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Dodo Payments API error fetching product {product_id}: {e.response.text}")
            # In a public pricing page, we might not want to crash the whole page if one product fails.
            # Returning None allows us to handle this gracefully.
            return None

    async def create_checkout_session(self, plan_id: str, success_url: str,
                                      cancel_url: str,
                                      user: AuthenticatedUser,
                                      customer_email: str,
                                      tenant_id: str) -> dict:
        """
        Creates a Checkout Session with Dodo Payments and returns the response.
        """
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                # Construct a valid customer object. For a new checkout, we'll
                # create a new customer with their email and a name.
                # We can derive a temporary name from the email if we don't store one.
                customer_name = user.email.split('@')[0]
                payload = {
                    "product_cart": [
                        {
                            "product_id": plan_id,  # This is the external_product_id from our `plans` table
                            "quantity": 1
                        }
                    ],
                    "customer": {
                        "email": user.email,
                        "name" : customer_name
                    },
                    "return_url": success_url,  # Note: Dodo docs seem to use return_url for both success/cancel
                    # We can pass our internal IDs as metadata to link the transaction on webhook receipt
                    "metadata": {
                        "internal_tenant_id": tenant_id,
                        "internal_user_id": str(user.id)
                    }
                }
                response = await client.post(
                    f"{self.base_url}/checkouts",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Dodo Payments API error creating checkout session: {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not create a checkout session with the payment provider."
            )

    async def verify_webhook_signature(self, request: Request) -> dict:
        """
        Verifies the incoming webhook signature and returns the parsed payload.
        Raises HTTPException if verification fails.
        """
        try:
            payload_bytes = await request.body()
            headers = request.headers

            # The standardwebhooks library expects lowercase headers
            webhook_headers = {
                "webhook-id": headers.get("webhook-id", ""),
                "webhook-signature": headers.get("webhook-signature", ""),
                "webhook-timestamp": headers.get("webhook-timestamp", ""),
            }

            # The verify function automatically handles signature checking
            # and will raise an exception on failure.
            payload = self.webhook_verifier.verify(payload_bytes, webhook_headers)
            return payload

        except Exception as e:
            print(f"Webhook verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook signature verification failed."
            )


# Create a single, reusable instance of the service
dodo_service = DodoPaymentsService()