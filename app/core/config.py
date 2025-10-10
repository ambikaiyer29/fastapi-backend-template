from typing import Literal, List

from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_JWT_SECRET: str
    SUPABASE_KEY: str
    DATABASE_URL: str
    SUPERADMIN_USER_ID: str
    SUPABASE_SERVICE_ROLE_KEY: str

    DODO_API_KEY: str | None = None
    DODO_WEBHOOK_SECRET: str | None = None
    DODO_BASE_URL: str = "https://test.dodopayments.com"

    STRIPE_API_KEY: str | None = None
    STRIPE_PUBLISHABLE_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    PAYMENT_GATEWAY: Literal["stripe", "dodo"] = "dodo"

    CORS_ORIGINS_STR: str = "http://localhost:3000"

    FRONTEND_ACCEPT_INVITE_URL: str

    @property
    def CORS_ORIGINS(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(',')]


    def model_post_init(self, __context) -> None:
        if self.PAYMENT_GATEWAY == "stripe" and not all([self.STRIPE_API_KEY, self.STRIPE_PUBLISHABLE_KEY, self.STRIPE_WEBHOOK_SECRET]):
            raise ValueError("Stripe API keys are required when PAYMENT_GATEWAY is 'stripe'")
        elif self.PAYMENT_GATEWAY == "dodo" and not all([self.DODO_API_KEY, self.DODO_WEBHOOK_SECRET]):
            raise ValueError("Dodo API keys are required when PAYMENT_GATEWAY is 'dodo'")


    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()