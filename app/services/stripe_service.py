# app/services/stripe_service.py
import stripe
from fastapi import HTTPException, status, Request

from app.core.config import get_settings


class StripeService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.STRIPE_API_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        stripe.api_key = self.api_key

    def get_subscription_details(self, external_subscription_id: str) -> dict | None:
        """
        Fetches live subscription details from the Stripe API.
        Returns None if the subscription is not found.
        """
        if not external_subscription_id:
            return None

        try:
            # The Stripe library uses synchronous calls
            subscription = stripe.Subscription.retrieve(external_subscription_id)
            return subscription.to_dict_recursive()  # Convert the Stripe object to a dictionary
        except stripe.error.InvalidRequestError as e:
            if "No such subscription" in str(e):
                return None
            print(f"Stripe API error fetching subscription {external_subscription_id}: {e}")
            return None
        except Exception as e:
            print(f"Stripe generic error fetching subscription {external_subscription_id}: {e}")
            return None

    def create_checkout_session(self, price_id: str, success_url: str, cancel_url: str, customer_email: str | None,
                                client_reference_id: str) -> dict:
        """
        Creates a Stripe Checkout Session. The client_reference_id is our internal tenant_id.
        """
        try:
            checkout_session = stripe.checkout.Session.create(
                mode='subscription',
                customer_email=customer_email,
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    },
                ],
                success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url,
                client_reference_id=client_reference_id,
                # Enable Stripe to create a customer and save their payment method
                payment_method_collection='always'
            )
            return {
                "session_id": checkout_session.id,
                "checkout_url": checkout_session.url
            }
        except Exception as e:
            print(f"Stripe API error creating checkout session: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not create a checkout session with Stripe."
            )

    def create_customer_portal_session(self, customer_id: str, return_url: str) -> dict:
        """
        Creates a Stripe Customer Portal session for a tenant to manage their subscription.
        """
        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return {"portal_url": portal_session.url}
        except Exception as e:
            print(f"Stripe API error creating customer portal session: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not create a customer portal session with Stripe."
            )

    async def verify_webhook_signature(self, request: Request) -> stripe.Event:
        """
        Verifies the incoming Stripe webhook signature using the recommended
        construct_event method and returns the event object.
        Raises HTTPException if verification fails.
        """
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')

        if not sig_header:
            print("ERROR: Stripe webhook failed. Missing Stripe-Signature header.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe-Signature header."
            )

        try:
            # The construct_event method handles parsing, validation, and signature
            # verification all in one. It will raise the correct exceptions on failure.
            event = stripe.Webhook.construct_event(
                payload=payload, sig_header=sig_header, secret=self.webhook_secret
            )
            return event

        # Catch the specific exceptions from the new Stripe SDK version
        except ValueError as e:
            # Invalid payload
            print(f"ERROR: Stripe webhook error - Invalid payload: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid payload: {e}")
        except stripe.SignatureVerificationError as e:
            # Invalid signature
            print(f"ERROR: Stripe webhook signature verification failed: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid signature: {e}")


# Create a single, reusable instance of the service
stripe_service = StripeService()