import logging
from typing import Any, Dict, Optional

import httpx

from .. import config

logger = logging.getLogger(__name__)

# --- Async HTTP Client ---

# Create a global async client instance for connection pooling and keep-alive
# Configure timeouts
timeout_config = httpx.Timeout(10.0, read=60.0, connect=5.0) # 10s default, 60s read, 5s connect
limits_config = httpx.Limits(max_keepalive_connections=20, max_connections=100) # Default limits

_async_client: Optional[httpx.AsyncClient] = None

def get_async_client() -> httpx.AsyncClient:
    """Returns a shared instance of the async HTTP client."""
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(timeout=timeout_config, limits=limits_config, http2=True, follow_redirects=True)
    return _async_client

async def close_async_client():
    """Closes the shared async HTTP client instance."""
    global _async_client
    if _async_client:
        await _async_client.aclose()
        _async_client = None
        logger.info("Async HTTP client closed.")


async def make_async_request(
    method: str,
    url: str,
    json_data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    files: Optional[Dict[str, Any]] = None, # For file uploads (e.g., to GROBID)
    timeout: Optional[float] = None # Allow overriding default timeout
) -> httpx.Response:
    """
    Makes an asynchronous HTTP request using a shared client instance.

    Args:
        method: HTTP method (GET, POST, etc.).
        url: The URL to request.
        json_data: JSON payload for POST/PUT requests.
        params: URL query parameters.
        headers: Request headers.
        files: Files dictionary for multipart/form-data uploads.
        timeout: Optional specific timeout for this request.

    Returns:
        The httpx.Response object.

    Raises:
        httpx.RequestError: For connection errors, timeouts, etc.
        httpx.HTTPStatusError: For 4xx/5xx responses (if raise_for_status is called).
    """
    client = get_async_client()
    request_timeout = timeout if timeout is not None else timeout_config.read # Use read timeout as default override

    logger.debug(f"Making async request: {method} {url}")
    try:
        response = await client.request(
            method=method.upper(),
            url=url,
            json=json_data,
            params=params,
            headers=headers,
            files=files,
            timeout=request_timeout
        )
        # Let the caller decide whether to raise for status
        # response.raise_for_status()
        return response
    except httpx.TimeoutException as e:
        logger.error(f"Timeout error requesting {method} {url}: {e}")
        raise httpx.RequestError(f"Timeout requesting {url}") from e
    except httpx.RequestError as e:
        logger.error(f"Request error for {method} {url}: {e}")
        raise # Re-raise other request errors (connection, etc.)

# Example usage (will be used in other modules):
# async def fetch_embedding(text: str):
#     headers = {}
#     if config.LITELLM_API_KEY:
#         headers["Authorization"] = f"Bearer {config.LITELLM_API_KEY}"
#     payload = {"model": config.EMBEDDING_MODEL_NAME, "input": [text]}
#     try:
#         response = await make_async_request(
#             "POST",
#             f"{config.LITELLM_PROXY_URL}/embeddings",
#             json_data=payload,
#             headers=headers
#         )
#         response.raise_for_status() # Check for HTTP errors
#         data = response.json()
#         # Process data...
#         return data
#     except httpx.HTTPStatusError as e:
#         logger.error(f"HTTP error fetching embedding: {e.response.status_code} - {e.response.text}")
#         # Handle specific errors
#     except httpx.RequestError as e:
#         logger.error(f"Request error fetching embedding: {e}")
#         # Handle connection/timeout errors
#     except Exception as e:
#         logger.exception("Unexpected error fetching embedding", exc_info=e)
#         # Handle unexpected errors