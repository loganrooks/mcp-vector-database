# tests/conftest.py
import pytest
import asyncio
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport # Import ASGITransport

# Import the FastAPI app instance
# Assuming it's defined in src/philograph/api/main.py
from src.philograph.api.main import app

@pytest_asyncio.fixture(scope="session") # Use session scope for efficiency
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an asynchronous test client for making requests to the FastAPI app.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
# Removed custom event_loop fixture to avoid conflict with pytest-asyncio.
# Removed custom test_client fixture. Tests will use FastAPI's TestClient directly.

# Optional: Add other shared fixtures here if needed