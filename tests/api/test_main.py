import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import status

# Assuming the FastAPI app instance is named 'app' in main.py
# Adjust the import path as necessary based on project structure
# With `pythonpath = src` in pytest.ini, import relative to src
from philograph.api.main import app

# Note: Other imports like psycopg, uuid, time, patch, ANY, specific models
# were removed as they were only needed by the moved tests.
# Fixtures specific to moved tests should also be moved or placed in conftest.py.

# Removed duplicate test_client fixture. Relies on conftest.py fixture now.

@pytest.mark.asyncio
async def test_read_root(test_client: AsyncClient):
    """
    Test the root endpoint ('/') to ensure it returns a 200 OK status
    and a basic running message.
    """
    response = await test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "PhiloGraph API is running"}

# All other test functions previously in this file have been moved to:
# - tests/api/test_ingest_router.py
# - tests/api/test_search_router.py
# - tests/api/test_documents_router.py
# - tests/api/test_collections_router.py
# - tests/api/test_acquisition_router.py