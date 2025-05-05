from src.philograph import config # Add config import
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import psycopg

from src.philograph.search.service import SearchService, SearchResult, format_search_results # Import helper
from src.philograph.data_access import db_layer as db_layer_module # Import the module itself

# Define test data
TEST_QUERY = "What is Geist?"
TEST_EMBEDDING = [0.1] * 768 # Use correct dimension from config (assuming 768)
MOCK_DB_RESULT_ROW = db_layer_module.SearchResult(
    chunk_id=1, text_content="Chunk text", sequence=1, section_id=1,
    section_title="Section 1", doc_id=1, doc_title="Doc Title",
    doc_author="Author Name", doc_year=2024, source_path="/path/doc.pdf",
    distance=0.5
)
MOCK_DB_RESULTS = [MOCK_DB_RESULT_ROW]
EXPECTED_FORMATTED_RESULT = format_search_results(MOCK_DB_RESULTS) # Use the actual formatter
TEST_FILTERS = {"author": "Test Author", "year": 2023}

@pytest.fixture
def mock_db_layer():
    """Fixture for a mocked db_layer module/object."""
    mock = MagicMock()
    # Mock the async context manager part
    mock_conn = AsyncMock()
    mock.get_db_connection.return_value.__aenter__.return_value = mock_conn
    # Mock the function called within the context
    mock.vector_search_chunks = AsyncMock(return_value=MOCK_DB_RESULTS)
    return mock

@pytest.fixture
def mock_http_client():
    """Fixture for a mocked httpx.AsyncClient."""
    mock = AsyncMock(spec=httpx.AsyncClient)
    # TODO: Configure mock return values for POST to LiteLLM proxy
    return mock

@pytest.fixture
@patch('src.philograph.utils.http_client.get_async_client')
def search_service(mock_get_async_client, mock_db_layer, mock_http_client):
    """Fixture for SearchService with mocked dependencies."""
    mock_get_async_client.return_value.__aenter__.return_value = mock_http_client
    return SearchService(db_layer=mock_db_layer)

@pytest.mark.asyncio
class TestSearchService:
    # Test successful search flow
    @patch('src.philograph.search.service.get_query_embedding', new_callable=AsyncMock)
    async def test_search_success(self, mock_get_embedding, search_service, mock_db_layer, mock_http_client):
        """Test the happy path for search: get embedding, search DB, format results."""
        mock_get_embedding.return_value = TEST_EMBEDDING

        # Call the service method
        results = await search_service.perform_search(TEST_QUERY)

        # Assertions
        mock_get_embedding.assert_awaited_once_with(TEST_QUERY)
        mock_db_layer.vector_search_chunks.assert_awaited_once_with(
            mock_db_layer.get_db_connection.return_value.__aenter__.return_value, # Check connection object passed
            TEST_EMBEDDING,
            config.SEARCH_TOP_K, # Check default top_k
            None # Check default filters
        )
        assert results == EXPECTED_FORMATTED_RESULT

    # Test handling of filters
    @patch('src.philograph.search.service.get_query_embedding', new_callable=AsyncMock)
    async def test_search_with_filters(self, mock_get_embedding, search_service, mock_db_layer, mock_http_client):
        """Test that filters are correctly passed to the db_layer."""
        mock_get_embedding.return_value = TEST_EMBEDDING
        # Assume DB returns the same mock results even with filters for this test
        mock_db_layer.vector_search_chunks.return_value = MOCK_DB_RESULTS

        # Call the service method with filters
        results = await search_service.perform_search(TEST_QUERY, filters=TEST_FILTERS, top_k=5) # Use specific top_k

        # Assertions
        mock_get_embedding.assert_awaited_once_with(TEST_QUERY)
        mock_db_layer.vector_search_chunks.assert_awaited_once_with(
            mock_db_layer.get_db_connection.return_value.__aenter__.return_value,
            TEST_EMBEDDING,
            5, # Check specific top_k passed
            TEST_FILTERS # Check filters passed
        )
        assert results == EXPECTED_FORMATTED_RESULT # Check formatting still works

    # Test LiteLLM proxy connection error
    @patch('src.philograph.search.service.get_query_embedding', new_callable=AsyncMock)
    async def test_search_litellm_connection_error(self, mock_get_embedding, search_service, mock_db_layer, mock_http_client):
        """Test that a connection error during embedding generation raises RuntimeError."""
        mock_get_embedding.side_effect = httpx.RequestError("Connection failed", request=MagicMock())

        # Expect the specific message for RequestError after refactoring
        with pytest.raises(RuntimeError, match="Embedding generation failed \(Request Error\)"):
            await search_service.perform_search(TEST_QUERY)

        mock_get_embedding.assert_awaited_once_with(TEST_QUERY)
        mock_db_layer.vector_search_chunks.assert_not_awaited() # DB should not be called

    # Test LiteLLM proxy API error (e.g., 500)
    @patch('src.philograph.search.service.get_query_embedding', new_callable=AsyncMock)
    async def test_search_litellm_api_error(self, mock_get_embedding, search_service, mock_db_layer, mock_http_client):
        """Test that an HTTP status error during embedding generation raises RuntimeError."""
        # Simulate a 500 error response
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get_embedding.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )

        # Expect the specific message for HTTPStatusError after refactoring
        with pytest.raises(RuntimeError, match="Embedding generation failed \(HTTP 500\)"):
             await search_service.perform_search(TEST_QUERY)

        mock_get_embedding.assert_awaited_once_with(TEST_QUERY)
        mock_db_layer.vector_search_chunks.assert_not_awaited() # DB should not be called

    # Test DB layer connection error
    @patch('src.philograph.search.service.get_query_embedding', new_callable=AsyncMock)
    async def test_search_db_connection_error(self, mock_get_embedding, search_service, mock_db_layer, mock_http_client):
        """Test that a DB connection error during search raises RuntimeError."""
        mock_get_embedding.return_value = TEST_EMBEDDING
        # Simulate DB connection error
        mock_db_layer.get_db_connection.return_value.__aenter__.side_effect = psycopg.OperationalError("DB connection failed")

        with pytest.raises(RuntimeError, match="Database search failed: DB connection failed"):
            await search_service.perform_search(TEST_QUERY)

        mock_get_embedding.assert_awaited_once_with(TEST_QUERY)
        # vector_search_chunks should not be called if connection fails
        mock_db_layer.vector_search_chunks.assert_not_awaited()

    # Test DB layer query error
    @patch('src.philograph.search.service.get_query_embedding', new_callable=AsyncMock)
    async def test_search_db_query_error(self, mock_get_embedding, search_service, mock_db_layer, mock_http_client):
        """Test that a DB query error during search raises RuntimeError."""
        mock_get_embedding.return_value = TEST_EMBEDDING
        # Simulate DB query error
        db_error = psycopg.ProgrammingError("Syntax error in query")
        mock_db_layer.vector_search_chunks.side_effect = db_error

        with pytest.raises(RuntimeError, match=f"Database search failed: {db_error}"):
            await search_service.perform_search(TEST_QUERY)

        mock_get_embedding.assert_awaited_once_with(TEST_QUERY)
        # Ensure vector_search_chunks was called (or awaited) before raising the error
        mock_db_layer.vector_search_chunks.assert_awaited_once()

    # Test handling empty search results
    @patch('src.philograph.search.service.get_query_embedding', new_callable=AsyncMock)
    async def test_search_empty_results(self, mock_get_embedding, search_service, mock_db_layer, mock_http_client):
        """Test that an empty result list from the DB returns an empty list."""
        mock_get_embedding.return_value = TEST_EMBEDDING
        # Simulate empty DB results
        mock_db_layer.vector_search_chunks.return_value = []

        results = await search_service.perform_search(TEST_QUERY)

        mock_get_embedding.assert_awaited_once_with(TEST_QUERY)
        mock_db_layer.vector_search_chunks.assert_awaited_once()
        assert results == []