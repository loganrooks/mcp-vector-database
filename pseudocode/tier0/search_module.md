# PhiloGraph Tier 0 - Pseudocode: Search Module

## Overview

This module handles the logic for performing searches based on user queries. It generates query embeddings using the LiteLLM Proxy, interacts with the Database Interaction Layer to perform vector searches combined with metadata filtering, and formats the results for the Backend API.

**Dependencies:**

*   Database Interaction Layer (`db_layer.py`)
*   LiteLLM Proxy (running locally, accessible via `{{LITELLM_PROXY_URL}}`)
*   Configuration:
    *   `{{LITELLM_PROXY_URL}}`: URL for the LiteLLM Proxy.
    *   `{{EMBEDDING_MODEL_NAME}}`: Internal model name configured in LiteLLM (e.g., "philo-embed").
    *   `{{SEARCH_TOP_K}}`: Default number of results to return.

```pseudocode
IMPORT db_layer
IMPORT http_client // For calling LiteLLM
IMPORT logging

// --- Configuration ---
CONSTANT LITELLM_URL = get_config("{{LITELLM_PROXY_URL}}")
CONSTANT EMBED_MODEL = get_config("{{EMBEDDING_MODEL_NAME}}")
CONSTANT DEFAULT_TOP_K = get_config("{{SEARCH_TOP_K}}", default=10)

// --- Main Search Function ---
FUNCTION perform_search(query_text, top_k = DEFAULT_TOP_K, filters = NULL):
    // TDD: Test search with valid query returns formatted results
    // TDD: Test search with valid query and filters returns filtered results
    // TDD: Test search with empty query text raises error
    // TDD: Test handling of embedding generation failure
    // TDD: Test handling of database search failure
    // TDD: Test result formatting includes necessary fields (text, doc title, author, distance, etc.)

    IF NOT query_text:
        RAISE ValueError("Query text cannot be empty")

    logging.info(f"Performing search for query: '{query_text}' with filters: {filters}")

    // 1. Get Query Embedding
    TRY:
        query_embedding = get_query_embedding(query_text, LITELLM_URL, EMBED_MODEL)
        // TDD: Test that query_embedding has the correct dimension {{TARGET_EMBEDDING_DIMENSION}}
        logging.debug("Successfully generated query embedding.")
    CATCH Exception as e:
        logging.error(f"Failed to generate query embedding: {e}")
        // Re-raise or return specific error structure for API
        RAISE RuntimeError(f"Embedding generation failed: {e}")

    // 2. Perform Database Search
    db_conn = db_layer.get_db_connection()
    TRY:
        // TDD: Test db_layer.vector_search_chunks call with correct parameters
        db_results = db_layer.vector_search_chunks(db_conn, query_embedding, top_k, filters)
        logging.info(f"Retrieved {len(db_results)} results from database.")
    CATCH Exception as e:
        logging.error(f"Database search failed: {e}")
        RAISE RuntimeError(f"Database search failed: {e}")
    FINALLY:
        db_layer.close_db_connection(db_conn)

    // 3. Format Results
    // TDD: Test formatting of empty db_results list
    // TDD: Test formatting includes all expected fields from db_results objects
    formatted_results = format_search_results(db_results)

    RETURN formatted_results

END FUNCTION

// --- Helper: Query Embedding Generation ---
FUNCTION get_query_embedding(text, litellm_url, model_name):
    // TDD: Test successful embedding generation for a query string
    // TDD: Test handling of HTTP errors from LiteLLM proxy during query embedding
    // TDD: Test handling of errors in LiteLLM response body for query embedding

    logging.debug(f"Requesting query embedding from LiteLLM: {litellm_url}")
    response = http_client.post(
        f"{litellm_url}/embeddings",
        json={"model": model_name, "input": [text]}, // Send query as a list with one item
        headers={"Authorization": "Bearer {{LITELLM_API_KEY}}"} // Or however auth is handled
    )
    response.raise_for_status() // Check for HTTP errors
    response_data = response.json()

    IF 'data' not in response_data OR len(response_data['data']) != 1 OR 'embedding' not in response_data['data'][0]:
        logging.error(f"Unexpected response format from LiteLLM: {response_data}")
        RAISE ValueError("Invalid response format received from embedding service")

    embedding = response_data['data'][0]['embedding']
    // Optional: Validate embedding dimension here if not done in db_layer
    // ASSERT len(embedding) == db_layer.TARGET_DIMENSION

    RETURN embedding
END FUNCTION

// --- Helper: Result Formatting ---
FUNCTION format_search_results(db_results):
    // db_results: List of objects/dicts returned by db_layer.vector_search_chunks
    // Each object contains fields like: chunk_id, text_content, sequence, section_id, section_title,
    // doc_id, doc_title, doc_author, doc_year, source_path, distance

    // TDD: Test formatting maps all relevant fields correctly
    // TDD: Test formatting handles missing optional fields (e.g., author, year) gracefully

    results_list = []
    FOR row in db_results:
        formatted = {
            "chunk_id": row.chunk_id,
            "text": row.text_content,
            "distance": row.distance, // Or other similarity score
            "source_document": {
                "doc_id": row.doc_id,
                "title": row.doc_title,
                "author": row.doc_author,
                "year": row.doc_year,
                "source_path": row.source_path
            },
            "location": {
                "section_id": row.section_id,
                "section_title": row.section_title,
                "chunk_sequence_in_section": row.sequence
            }
            // Add other relevant metadata as needed
        }
        results_list.append(formatted)

    RETURN results_list
END FUNCTION