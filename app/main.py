from fastapi import FastAPI
from app.api.v1.api import api_router, public_api_router
from app.core.metrics import instrument_app
from app.core.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(title="SaaS Starter Kit")

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