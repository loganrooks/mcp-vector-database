import logging
from contextlib import asynccontextmanager
import fastapi
from fastapi import FastAPI, status

# Import config and core services needed for lifespan
from .. import config
from ..data_access import db_layer
from ..utils import http_client

# Import routers
from .routers import ingest, search, documents, collections, acquisition

logger = logging.getLogger(__name__)

# --- FastAPI Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize resources
    logger.info("FastAPI application startup...")
    await db_layer.get_db_pool() # Initialize DB pool
    http_client.get_async_client() # Initialize HTTP client
    # Initialize schema if needed
    try:
        async with db_layer.get_db_connection() as conn:
            await db_layer.initialize_schema(conn)
    except Exception as e:
        logger.error(f"Failed to initialize database schema during startup: {e}")
    yield
    # Shutdown: Cleanup resources
    logger.info("FastAPI application shutdown...")
    await db_layer.close_db_pool()
    await http_client.close_async_client()

# --- FastAPI App Initialization ---
app = FastAPI(
    title="PhiloGraph Backend API",
    description="API for interacting with the PhiloGraph knowledge base.",
    version="0.1.0 (Tier 0)",
    lifespan=lifespan
)

# --- Basic Health Check ---
@app.get("/", status_code=status.HTTP_200_OK, tags=["Health"])
async def read_root():
    """Basic health check endpoint."""
    return {"message": "PhiloGraph API is running"}

# --- Include Routers ---
app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(documents.router)
app.include_router(collections.router)
app.include_router(acquisition.router)


# --- Main Execution (for local testing) ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server for local development...")
    # Ensure config is loaded before uvicorn starts if it relies on env vars set here
    # (config.py already loads dotenv, so should be fine)
    uvicorn.run(
        "src.philograph.api.main:app", # Path to the app instance
        host=config.BACKEND_HOST,
        port=config.BACKEND_PORT,
        reload=True, # Enable auto-reload for development
        log_level=config.LOG_LEVEL.lower()
    )