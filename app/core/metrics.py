from prometheus_fastapi_instrumentator import Instrumentator

def instrument_app(app):
    """
    Instruments the FastAPI application with Prometheus metrics.
    """
    Instrumentator().instrument(app).expose(app)