from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router, public_api_router
from app.core.config import get_settings
from app.core.metrics import instrument_app
from app.core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings() # <-- Create an instance of the settings
app = FastAPI(title="SaaS Starter Kit")

# --- ADD THE CORS MIDDLEWARE CONFIGURATION ---

# Define the origins that are allowed to connect to your API.
# This is a critical security setting.
# In a production environment, you should lock this down to your specific frontend domain.
# For local development, you might allow "http://localhost:3000" if your frontend runs there.
# The wildcard "*" is permissive and can be useful for development, but is NOT recommended for production.

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True, # Allows cookies to be included in requests
    allow_methods=["*"],    # Allows all methods (GET, POST, PUT, etc.)
    allow_headers=["*"],    # Allows all headers
)
# --- END OF CORS CONFIGURATION ---


# Instrument the app with Prometheus metrics
instrument_app(app)

# Include the API router
app.include_router(public_api_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")

# Example of using the logging decorator
from app.utils.decorators import log_request

@app.get("/")
@log_request
async def read_root():
    return {"message": "Welcome to the SaaS Starter Kit"}