import logging
import json
import psycopg
from typing import Any, Dict, List, Optional

import httpx # For potential errors from http_client

from .. import config
from ..data_access import db_layer
from ..utils import http_client

logger = logging.getLogger(__name__)

# --- Data Structures ---

class SearchResult:
    """Placeholder for search result data structure."""
    # Define attributes based on format_search_results later
    pass

# --- Service Class ---

class SearchService:
    """Handles search operations including embedding generation and DB interaction."""

    def __init__(self, db_layer: Any): # Use Any for now
        self.db_layer = db_layer
        # TODO: Potentially initialize http client session here if needed frequently

    # --- Main Search Method ---
    async def perform_search(
        self,
        query_text: str,
        top_k: int = config.SEARCH_TOP_K,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic search with optional filtering.

        Args:
            query_text: The user's search query.
            top_k: The maximum number of results to return.
            filters: Optional dictionary of metadata filters.

        Returns:
            A list of formatted search result dictionaries.

        Raises:
            ValueError: If query_text is empty or embedding dimension mismatch occurs.
            RuntimeError: If embedding generation or database search fails.
        """
        # TDD: Test search with valid query returns formatted results
        # TDD: Test search with valid query and filters returns filtered results
        # TDD: Test search with empty query text raises error
        # TDD: Test handling of embedding generation failure
        # TDD: Test handling of database search failure
        # TDD: Test result formatting includes necessary fields

        if not query_text:
            raise ValueError("Query text cannot be empty")

        logger.info(f"Performing search for query: '{query_text[:100]}...' with filters: {filters}, top_k: {top_k}")

        # 1. Get Query Embedding
        try:
            # Assuming get_query_embedding remains a standalone helper for now
            query_embedding = await get_query_embedding(query_text)
            logger.debug("Successfully generated query embedding.")
        except httpx.RequestError as req_err:
            # More specific handling for connection errors to embedding service
            logger.error(f"Embedding generation failed (Request Error): {req_err}", exc_info=True)
            raise RuntimeError("Embedding generation failed (Request Error)") from req_err
        except httpx.HTTPStatusError as status_err:
             # More specific handling for API errors from embedding service
            logger.error(f"Embedding generation failed (HTTP {status_err.response.status_code}): {status_err.response.text}", exc_info=True)
            raise RuntimeError(f"Embedding generation failed (HTTP {status_err.response.status_code})") from status_err
        except (ValueError, RuntimeError) as e:
            # Re-raise specific errors like ValueError or RuntimeErrors from get_query_embedding itself
            raise e
        except Exception as e:
            # Catch any other truly unexpected errors during embedding
            logger.exception("Unexpected error during query embedding generation", exc_info=e)
            raise RuntimeError("Search failed due to truly unexpected embedding error") from e

        # 2. Perform Database Search
        try:
            # Use self.db_layer now
            async with self.db_layer.get_db_connection() as conn:
                # TDD: Test db_layer.vector_search_chunks call with correct parameters
                db_results: List[db_layer.SearchResult] = await self.db_layer.vector_search_chunks(
                    conn, query_embedding, top_k, filters
                )
                logger.info(f"Retrieved {len(db_results)} results from database.")
        except psycopg.Error as db_e:
            logger.error(f"Database search failed: {db_e}", exc_info=True)
            raise RuntimeError(f"Database search failed: {db_e}") from db_e
        except AttributeError as attr_err:
             # Catch potential AttributeError if db_layer doesn't have get_db_connection (during early TDD)
             logger.error(f"DB layer interaction error: {attr_err}", exc_info=True)
             raise RuntimeError("Search failed due to DB layer configuration error") from attr_err
        except Exception as e:
            logger.exception("Unexpected error during database search", exc_info=e)
            raise RuntimeError("Search failed due to unexpected database error") from e

        # 3. Format Results
        # Assuming format_search_results remains a standalone helper for now
        formatted_results = format_search_results(db_results)

        return formatted_results
# --- Helper: Query Embedding Generation ---

async def get_query_embedding(text: str) -> List[float]:
    """Generates an embedding for the given query text via LiteLLM Proxy."""
    # TDD: Test successful embedding generation for a query string
    # TDD: Test handling of HTTP errors from LiteLLM proxy during query embedding
    # TDD: Test handling of errors in LiteLLM response body for query embedding
    if not text:
        raise ValueError("Query text cannot be empty")

    logger.debug(f"Requesting query embedding from LiteLLM: {config.LITELLM_PROXY_URL}")
    headers = {}
    if config.LITELLM_API_KEY:
        headers["Authorization"] = f"Bearer {config.LITELLM_API_KEY}"

    payload = {"model": config.EMBEDDING_MODEL_NAME, "input": [text]} # Send query as a list with one item

    try:
        response = await http_client.make_async_request(
            "POST",
            f"{config.LITELLM_PROXY_URL}/embeddings",
            json_data=payload,
            headers=headers,
            timeout=30.0 # Reasonable timeout for a single query embedding
        )
        response.raise_for_status() # Check for HTTP errors
        # Log raw response before attempting to parse JSON
        logger.debug(f"LiteLLM raw response status: {response.status_code}")
        logger.debug(f"LiteLLM raw response text: {response.text}")

        try:
            response_data = response.json()
            logger.debug(f"LiteLLM JSON response data: {response_data}") # Log parsed JSON
        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to decode JSON response from LiteLLM: {json_err}", exc_info=True)
            raise RuntimeError("Embedding generation failed (JSON Decode Error)") from json_err

        if 'data' not in response_data or not isinstance(response_data['data'], list) or len(response_data['data']) != 1 or 'embedding' not in response_data['data'][0]:
            logger.error(f"Unexpected response format from LiteLLM embedding endpoint: {response_data}")
            raise ValueError("Invalid response format received from embedding service")

        embedding = response_data['data'][0]['embedding']

        # Truncate embedding if it's longer than the target dimension (Workaround for MRL issue)
        if len(embedding) > config.TARGET_EMBEDDING_DIMENSION:
            logger.warning(f"Received embedding with dimension {len(embedding)}, truncating to {config.TARGET_EMBEDDING_DIMENSION}.")
            embedding = embedding[:config.TARGET_EMBEDDING_DIMENSION]

        # Validate embedding dimension
        if len(embedding) != config.TARGET_EMBEDDING_DIMENSION:
            logger.error(f"Query embedding dimension mismatch after potential truncation. Expected {config.TARGET_EMBEDDING_DIMENSION}, got {len(embedding)}.")
            # Keep the original error message reflecting the received dimension before truncation for clarity
            raise ValueError(f"Received query embedding with incorrect dimension ({response_data['data'][0]['embedding']})") # Report original length

        return embedding

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching query embedding: {e.response.status_code} - {e.response.text}", exc_info=True)
        raise RuntimeError(f"Embedding generation failed (HTTP {e.response.status_code})") from e
    except httpx.RequestError as e:
        logger.error(f"Request error fetching query embedding: {e}", exc_info=True)
        raise RuntimeError("Embedding generation failed (Request Error)") from e
    except (ValueError, KeyError) as e: # JSONDecodeError is handled within the try block now
         logger.error(f"Error processing query embedding response: {e}. Response: {response.text if 'response' in locals() else 'N/A'}", exc_info=True)
         raise RuntimeError("Embedding generation failed (Processing Error)") from e
    except Exception as e:
        logger.exception("Unexpected error fetching query embedding", exc_info=e)
        raise RuntimeError("Embedding generation failed (Unexpected Error)") from e


# --- Helper: Result Formatting ---

def format_search_results(db_results: List[db_layer.SearchResult]) -> List[Dict[str, Any]]:
    """Formats database search results into the desired API response structure."""
    # TDD: Test formatting maps all relevant fields correctly
    # TDD: Test formatting handles missing optional fields (e.g., author, year) gracefully
    # TDD: Test formatting of empty db_results list
    results_list = []
    for row in db_results:
        # Convert Pydantic model back to dict for JSON response if needed,
        # or define API response models separately. Assuming dict for now.
        formatted = {
            "chunk_id": row.chunk_id,
            "text": row.text_content,
            "distance": row.distance,
            "source_document": {
                "doc_id": row.doc_id,
                "title": row.doc_title,
                "author": row.doc_author,
                "year": row.doc_year,
                "source_path": row.doc_source_path # Correct attribute name
            },
            "location": {
                "section_id": row.section_id,
                "section_title": row.section_title,
                "chunk_sequence_in_section": row.chunk_sequence # Correct attribute name
            }
        }
        results_list.append(formatted)
    return results_list

# --- Main Search Function ---

async def perform_search(
    query_text: str,
    top_k: int = config.SEARCH_TOP_K,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Performs semantic search with optional filtering.

    Args:
        query_text: The user's search query.
        top_k: The maximum number of results to return.
        filters: Optional dictionary of metadata filters.

    Returns:
        A list of formatted search result dictionaries.

    Raises:
        ValueError: If query_text is empty or embedding dimension mismatch occurs.
        RuntimeError: If embedding generation or database search fails.
    """
    # TDD: Test search with valid query returns formatted results
    # TDD: Test search with valid query and filters returns filtered results
    # TDD: Test search with empty query text raises error
    # TDD: Test handling of embedding generation failure
    # TDD: Test handling of database search failure
    # TDD: Test result formatting includes necessary fields

    if not query_text:
        raise ValueError("Query text cannot be empty")

    logger.info(f"Performing search for query: '{query_text[:100]}...' with filters: {filters}, top_k: {top_k}")

    # 1. Get Query Embedding
    try:
        query_embedding = await get_query_embedding(query_text)
        logger.debug("Successfully generated query embedding.")
    except (ValueError, RuntimeError) as e:
        # Re-raise specific errors from embedding generation
        raise e
    except Exception as e:
        # Catch any other unexpected errors during embedding
        logger.exception("Unexpected error during query embedding generation", exc_info=e)
        raise RuntimeError("Search failed due to unexpected embedding error") from e

    # 2. Perform Database Search
    try:
        async with db_layer.get_db_connection() as conn:
            # TDD: Test db_layer.vector_search_chunks call with correct parameters
            db_results: List[db_layer.SearchResult] = await db_layer.vector_search_chunks(
                conn, query_embedding, top_k, filters
            )
            logger.info(f"Retrieved {len(db_results)} results from database.")
    except psycopg.Error as db_e:
        logger.error(f"Database search failed: {db_e}", exc_info=True)
        raise RuntimeError(f"Database search failed: {db_e}") from db_e
    except Exception as e:
        logger.exception("Unexpected error during database search", exc_info=e)
        raise RuntimeError("Search failed due to unexpected database error") from e

    # 3. Format Results
    formatted_results = format_search_results(db_results)

    return formatted_results

# Example Usage (called from API layer)
# async def main_search():
#     query = "What is the nature of Geist?"
#     filters = {"author": "Hegel"}
#     try:
#         results = await perform_search(query, filters=filters, top_k=5)
#         print(json.dumps(results, indent=2))
#     except Exception as e:
#         print(f"Search failed: {e}")
#     finally:
#         await db_layer.close_db_pool()
#         await http_client.close_async_client()

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main_search())