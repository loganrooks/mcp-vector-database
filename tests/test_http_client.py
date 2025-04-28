import pytest
import httpx
import importlib
from unittest.mock import patch

# Assuming utils is importable from tests context
from src.philograph.utils import http_client

# --- Fixtures ---

@pytest.fixture(autouse=True)
async def manage_client_state():
    """Ensure client is reset before each test and closed after."""
    # Reset client before test
    if http_client._async_client is not None:
        await http_client.close_async_client()
        http_client._async_client = None # Ensure it's None

    # Reload the module to reset global state potentially affected by other tests
    importlib.reload(http_client)

    yield # Run the test

    # Close client after test
    await http_client.close_async_client()

# --- Tests for get_async_client ---

def test_get_async_client_creates_instance():
    """Test that get_async_client creates an instance if none exists."""
    assert http_client._async_client is None
    client = http_client.get_async_client()
    assert isinstance(client, httpx.AsyncClient)
    assert http_client._async_client is client

def test_get_async_client_returns_same_instance():
    """Test that get_async_client returns the same singleton instance."""
    client1 = http_client.get_async_client()
    client2 = http_client.get_async_client()
    assert client1 is client2
    assert http_client._async_client is client1

# --- Tests for close_async_client ---

@pytest.mark.asyncio
async def test_close_async_client_closes_and_resets():
    """Test that close_async_client closes the client and resets the global var."""
    client = http_client.get_async_client() # Create instance
    assert http_client._async_client is not None
    await http_client.close_async_client()
    assert http_client._async_client is None
    assert client.is_closed is True

@pytest.mark.asyncio
async def test_close_async_client_no_instance_does_nothing():
    """Test that close_async_client does nothing if no client exists."""
    assert http_client._async_client is None
    await http_client.close_async_client() # Should not raise error
    assert http_client._async_client is None

# TODO: Add tests for make_async_request using pytest-httpx
# --- Tests for make_async_request ---

@pytest.mark.asyncio
async def test_make_async_request_get_success(httpx_mock):
    """Test successful GET request using make_async_request."""
    test_url = "http://test-server.com/data"
    expected_response_data = {"message": "success"}
    httpx_mock.add_response(url=test_url, method="GET", json=expected_response_data, status_code=200)

    response = await http_client.make_async_request("GET", test_url)

    assert response.status_code == 200
    assert response.json() == expected_response_data

@pytest.mark.asyncio
async def test_make_async_request_post_success(httpx_mock):
    """Test successful POST request with JSON data."""
    test_url = "http://test-server.com/create"
    request_data = {"name": "test_item"}
    expected_response_data = {"id": 123, "name": "test_item"}
    httpx_mock.add_response(url=test_url, method="POST", json=expected_response_data, status_code=201)

    response = await http_client.make_async_request("POST", test_url, json_data=request_data)

    assert response.status_code == 201
    assert response.json() == expected_response_data
    # Check if the request payload matches (optional but good practice)
    request = httpx_mock.get_request()
    # Compare parsed JSON instead of raw bytes to avoid whitespace issues
    import json
    assert json.loads(request.read()) == request_data

@pytest.mark.asyncio
async def test_make_async_request_with_params(httpx_mock):
    """Test request with query parameters."""
    test_url = "http://test-server.com/search"
    params = {"query": "test", "limit": "10"}
    httpx_mock.add_response(url=f"{test_url}?query=test&limit=10", method="GET", json=[], status_code=200)

    response = await http_client.make_async_request("GET", test_url, params=params)

    assert response.status_code == 200
    request = httpx_mock.get_request()
    assert str(request.url) == f"{test_url}?query=test&limit=10"

@pytest.mark.asyncio
async def test_make_async_request_with_headers(httpx_mock):
    """Test request with custom headers."""
    test_url = "http://test-server.com/secure"
    headers = {"Authorization": "Bearer testtoken"}
    httpx_mock.add_response(url=test_url, method="GET", json={"status": "ok"}, status_code=200)

    response = await http_client.make_async_request("GET", test_url, headers=headers)

    assert response.status_code == 200
    request = httpx_mock.get_request()
    assert request.headers["authorization"] == "Bearer testtoken"

@pytest.mark.asyncio
async def test_make_async_request_http_error_no_raise(httpx_mock):
    """Test that 4xx/5xx errors are returned, not raised by default."""
    test_url = "http://test-server.com/notfound"
    httpx_mock.add_response(url=test_url, method="GET", status_code=404, json={"detail": "Not Found"})

    response = await http_client.make_async_request("GET", test_url)

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}

@pytest.mark.asyncio
async def test_make_async_request_timeout_error(httpx_mock):
    """Test that TimeoutException raises RequestError."""
    test_url = "http://test-server.com/timeout"
    httpx_mock.add_exception(httpx.TimeoutException("Request timed out", request=None))

    with pytest.raises(httpx.RequestError) as excinfo:
        await http_client.make_async_request("GET", test_url)
    assert "Timeout requesting http://test-server.com/timeout" in str(excinfo.value)

@pytest.mark.asyncio
async def test_make_async_request_connect_error(httpx_mock):
    """Test that ConnectError raises RequestError."""
    test_url = "http://test-server.com/connect-error"
    httpx_mock.add_exception(httpx.ConnectError("Connection failed", request=None))

    with pytest.raises(httpx.ConnectError): # It re-raises the specific RequestError subclass
        await http_client.make_async_request("GET", test_url)

@pytest.mark.asyncio
async def test_make_async_request_override_timeout(httpx_mock):
    """Test overriding the default timeout."""
    test_url = "http://test-server.com/slow"
    httpx_mock.add_response(url=test_url, method="GET", json={"status": "ok"}, status_code=200)

    # This test mainly checks if the timeout parameter is passed correctly.
    # We can't easily verify the *actual* timeout duration with httpx_mock alone,
    # but we check it's passed to the underlying client.request.
    with patch.object(http_client._async_client, 'request', wraps=http_client._async_client.request) as mock_request:
         await http_client.make_async_request("GET", test_url, timeout=5.0)
         mock_request.assert_called_once()
         # Check the timeout value passed in the call arguments
         call_args, call_kwargs = mock_request.call_args
         assert call_kwargs.get('timeout') == 5.0