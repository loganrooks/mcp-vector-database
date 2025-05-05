# tests/conftest.py
import pytest
import asyncio
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport # Import ASGITransport

# Import the FastAPI app instance
# Assuming it's defined in src/philograph/api/main.py
from src.philograph.api.main import app

# Removed custom event_loop fixture to avoid conflict with pytest-asyncio.
# Removed custom test_client fixture. Tests will use FastAPI's TestClient directly.

# Optional: Add other shared fixtures here if needed