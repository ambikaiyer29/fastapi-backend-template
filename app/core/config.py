from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_JWT_SECRET: str
    SUPABASE_KEY: str
    DATABASE_URL: str
    SUPERADMIN_USER_ID: str
    SUPABASE_SERVICE_ROLE_KEY: str
    DODO_API_KEY: str
    DODO_WEBHOOK_SECRET: str

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()