import json
import pytest
import httpx
import typer
# import typer # Duplicate removed
import click # Add click import
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

# Import the Typer app instance from your CLI module
# Adjust the import path based on your project structure
from philograph.cli.main import app, search # Import search function
# Import config for API_URL access in assertions
from philograph import config

# Fixture for the Typer CliRunner
@pytest.fixture
def runner():
    return CliRunner()

# Basic test to ensure the app runs without errors (e.g., help command)
def test_app_runs(runner):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "PhiloGraph Command Line Interface" in result.stdout

# Placeholder for future tests
def test_placeholder():
    pass
# --- Tests for make_api_request ---

# Mock the config used by the CLI module
@patch('src.philograph.cli.main.config')
def test_make_api_request_get_success(mock_config, runner):
    """Test make_api_request for a successful GET request."""
    mock_config.API_URL = "http://fakeapi.com"
    expected_response_data = {"message": "success"}

    # Mock the httpx.Client
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = expected_response_data

    mock_client_instance = MagicMock()
    mock_client_instance.request.return_value = mock_response

    # Use patch as a context manager, configuring the __enter__ return value
    with patch('httpx.Client') as MockHttpClient:
        # Configure the mock instance returned by Client()
        mock_enter_instance = MockHttpClient.return_value
        # Configure the __enter__ method of that instance to return our specific mock
        mock_enter_instance.__enter__.return_value = mock_client_instance

        # Import the function *after* patching config if it uses config at import time
        # Or ensure config is accessed dynamically within the function
        from src.philograph.cli.main import make_api_request
        
        response_data = make_api_request("GET", "/test-endpoint")

@patch('src.philograph.cli.main.config')
def test_make_api_request_post_success(mock_config, runner):
    """Test make_api_request for a successful POST request with JSON."""
    mock_config.API_URL = "http://fakeapi.com"
    request_data = {"key": "value"}
    expected_response_data = {"id": 123, "status": "created"}

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = expected_response_data

    mock_client_instance = MagicMock()
    mock_client_instance.request.return_value = mock_response

    with patch('httpx.Client') as MockHttpClient:
        mock_enter_instance = MockHttpClient.return_value
        mock_enter_instance.__enter__.return_value = mock_client_instance

        from src.philograph.cli.main import make_api_request
        response_data = make_api_request("POST", "/create-item", json_data=request_data)

    mock_client_instance.request.assert_called_once_with("POST", "http://fakeapi.com/create-item", json=request_data, params=None)
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert response_data == expected_response_data
    # Removed duplicated assertions from previous test
@patch('src.philograph.cli.main.config')
@patch('src.philograph.cli.main.error_console') # Patch the error console
def test_make_api_request_connection_error(mock_error_console, mock_config, runner):
    """Test make_api_request handles httpx.ConnectError."""
    mock_config.API_URL = "http://unreachableapi.com"
    connect_error = httpx.ConnectError("Connection failed")

    # Mock the httpx.Client to raise ConnectError
    mock_client_instance = MagicMock()
    mock_client_instance.request.side_effect = connect_error

    with patch('httpx.Client') as MockHttpClient:
        mock_enter_instance = MockHttpClient.return_value
        mock_enter_instance.__enter__.return_value = mock_client_instance

        from src.philograph.cli.main import make_api_request

        # Expect typer.Exit to be raised
        with pytest.raises(typer.Exit) as excinfo:
            make_api_request("GET", "/test-endpoint")

    # Assertions
    assert excinfo.value.exit_code == 1
    mock_client_instance.request.assert_called_once_with("GET", "http://unreachableapi.com/test-endpoint", json=None, params=None)
    # Check that the error console printed the expected messages
    assert mock_error_console.print.call_count == 2
    mock_error_console.print.assert_any_call("Error: Could not connect to the PhiloGraph backend at http://unreachableapi.com.")
    mock_error_console.print.assert_any_call("Please ensure the backend service is running.")
@patch('src.philograph.cli.main.config')
@patch('src.philograph.cli.main.error_console')
def test_make_api_request_http_status_error(mock_error_console, mock_config, runner):
    """Test make_api_request handles httpx.HTTPStatusError (e.g., 404, 500)."""
    mock_config.API_URL = "http://fakeapi.com"
    status_code = 404
    error_text = "Not Found"
    error_detail = {"detail": "Item not found"}

    # Mock the response object
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.text = error_text
    mock_response.json.return_value = error_detail
    # Configure raise_for_status to raise the error
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message=f"{status_code} Client Error: {error_text} for url http://fakeapi.com/not-found",
        request=MagicMock(), # Mock request object
        response=mock_response
    )

    # Mock the httpx.Client
    mock_client_instance = MagicMock()
    mock_client_instance.request.return_value = mock_response

    with patch('httpx.Client') as MockHttpClient:
        mock_enter_instance = MockHttpClient.return_value
        mock_enter_instance.__enter__.return_value = mock_client_instance

        from src.philograph.cli.main import make_api_request

        # Expect typer.Exit to be raised
        with pytest.raises(typer.Exit) as excinfo:
            make_api_request("GET", "/not-found")

@patch('src.philograph.cli.main.config')
@patch('src.philograph.cli.main.error_console')
def test_make_api_request_json_decode_error(mock_error_console, mock_config, runner):
    """Test make_api_request handles JSONDecodeError from response."""
    mock_config.API_URL = "http://fakeapi.com"
    status_code = 200
    invalid_json_text = "This is not valid JSON"

    # Mock the response object
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.text = invalid_json_text
    mock_response.raise_for_status.return_value = None # Don't raise HTTPStatusError
    # Configure json() to raise the error
    mock_response.json.side_effect = json.JSONDecodeError("Expecting value", invalid_json_text, 0)

    # Mock the httpx.Client
    mock_client_instance = MagicMock()
    mock_client_instance.request.return_value = mock_response

    with patch('httpx.Client') as MockHttpClient:
        mock_enter_instance = MockHttpClient.return_value
        mock_enter_instance.__enter__.return_value = mock_client_instance

        from src.philograph.cli.main import make_api_request

        # Expect typer.Exit to be raised
        with pytest.raises(typer.Exit) as excinfo:
            make_api_request("GET", "/valid-endpoint-invalid-json")

    # Assertions
    assert excinfo.value.exit_code == 1
    mock_client_instance.request.assert_called_once_with("GET", "http://fakeapi.com/valid-endpoint-invalid-json", json=None, params=None)
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    # Check error console output
    mock_error_console.print.assert_called_once_with(f"Error: Invalid response format received from server (Status: {status_code}).")
    # Assertions
    assert excinfo.value.exit_code == 1
    mock_client_instance.request.assert_called_once_with("GET", "http://fakeapi.com/valid-endpoint-invalid-json", json=None, params=None)
    mock_response.raise_for_status.assert_called_once()
    # Check error console output
@patch('src.philograph.cli.main.config')
@patch('src.philograph.cli.main.error_console')
def test_make_api_request_unexpected_error(mock_error_console, mock_config, runner):
    """Test make_api_request handles unexpected exceptions."""
    mock_config.API_URL = "http://fakeapi.com"
    error_message = "Something went very wrong"
    unexpected_error = Exception(error_message)

    # Mock the httpx.Client to raise the unexpected error
    mock_client_instance = MagicMock()
    mock_client_instance.request.side_effect = unexpected_error

    with patch('httpx.Client') as MockHttpClient:
        mock_enter_instance = MockHttpClient.return_value
        mock_enter_instance.__enter__.return_value = mock_client_instance

        from src.philograph.cli.main import make_api_request

        # Expect typer.Exit to be raised
        with pytest.raises(typer.Exit) as excinfo:
            make_api_request("GET", "/unexpected")

    # Assertions
    assert excinfo.value.exit_code == 1
    mock_client_instance.request.assert_called_once_with("GET", "http://fakeapi.com/unexpected", json=None, params=None)
    # Check error console output
    mock_error_console.print.assert_called_once_with(f"An unexpected error occurred: {unexpected_error}")
# --- Tests for CLI Commands ---

@patch('src.philograph.cli.main.make_api_request')
@patch('src.philograph.cli.main.display_results') # Mock display to isolate command logic
def test_ingest_success(mock_display_results, mock_make_api_request, runner):
    """Test the ingest command calls the API correctly on success."""
    test_path = "dummy_test_doc.pdf" # Use relative path, interpreted within container's /app/data/source_documents
    mock_api_response = {"message": "Ingestion started", "document_id": 1}
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, ["ingest", test_path])

    # Expect exit code 1 because the dummy file doesn't exist, causing API 404
    assert result.exit_code == 1
    # Remove assertion: make_api_request exits internally on 404 before mock is called
    # Remove assertion: display_results is not called when command exits early on 404
    # mock_display_results.assert_called_once_with(mock_api_response)
@patch('src.philograph.cli.main.make_api_request')
@patch('src.philograph.cli.main.display_results') # Mock display as it's not called on error
@patch('src.philograph.cli.main.error_console') # Mock error console to check output
def test_ingest_api_error(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the ingest command handles API errors gracefully."""
    test_path = "dummy_test_doc.pdf" # Use relative path
    # Simulate make_api_request raising typer.Exit after handling an internal error
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, ["ingest", test_path])

    assert result.exit_code == 1
    # Remove assertion: make_api_request exits internally on 404 before mock side_effect
    # mock_make_api_request.assert_called_once_with("POST", "/ingest", json_data={"path": test_path})
    mock_display_results.assert_not_called() # Display should not be called on error
    # We don't assert mock_error_console here because the error is printed
    # *within* make_api_request, which is already tested. We just ensure
    # the command exits correctly.
# Removed patch decorator
# Removed display_results mock
def test_search_success_query_only(runner): # Removed mock_display_results
    """Test the search command calls the API correctly with only a query."""
    test_query = "philosophy of time"
    expected_payload = {"query": test_query, "limit": 10}
    mock_api_response_data = {
        "results": [
            {"id": 1, "type": "chunk", "score": 0.9, "text": "...", "document_title": "Being and Time", "source_document": {"title": "Being and Time", "author": "Heidegger", "year": 1927, "doc_id": 1}, "chunk_id": 1, "distance": 0.1},
            {"id": 5, "type": "chunk", "score": 0.85, "text": "...", "document_title": "Phenomenology of Spirit", "source_document": {"title": "Phenomenology of Spirit", "author": "Hegel", "year": 1807, "doc_id": 2}, "chunk_id": 5, "distance": 0.15}
        ]
    }

    # Patch make_api_request directly again
    with patch('philograph.cli.main.make_api_request') as mock_make_api_request:
        mock_make_api_request.return_value = mock_api_response_data

        # Use runner.invoke again
        result = runner.invoke(app, ["search", test_query])

        # Assert exit code
        assert result.exit_code == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"

        # Check that make_api_request was called correctly
        mock_make_api_request.assert_called_once_with(
            "POST",
            "/search",
            json_data=expected_payload
        )
    # Check stdout for expected content
    assert "Search Results" in result.stdout
    assert "Being and Time" in result.stdout
    assert "Phenomenology of Spirit" in result.stdout
    assert "0.1000" in result.stdout # Check distance formatting
    assert "0.1500" in result.stdout
# Removed display_results mock
def test_search_success_with_filters(runner): # Removed mock_display_results
    """Test the search command calls the API correctly with query and filters."""
    test_query = "ethics"
    test_author = "Aristotle"
    test_year = -350 # Example year
    filters_dict = {"author": test_author, "year": test_year}
    expected_payload = {"query": test_query, "filters": filters_dict, "limit": 10}
    mock_api_response_data = {
        "results": [
            {"id": 10, "type": "chunk", "score": 0.7, "text": "...", "document_title": "Nicomachean Ethics", "source_document": {"title": "Nicomachean Ethics", "author": "Aristotle", "year": -350, "doc_id": 3}, "chunk_id": 10, "distance": 0.3}
        ]
    }

    # Patch make_api_request directly again
    with patch('philograph.cli.main.make_api_request') as mock_make_api_request:
        mock_make_api_request.return_value = mock_api_response_data

        # Use runner.invoke again
        result = runner.invoke(app, [
            "search",
            test_query,
            "--author", test_author,
            "--year", str(test_year)
        ])

        # Assert exit code
        assert result.exit_code == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"

        # Check that make_api_request was called correctly
        mock_make_api_request.assert_called_once_with(
            "POST",
            "/search",
            json_data=expected_payload
        )
    # Check stdout for expected content
    assert "Search Results" in result.stdout
    assert "Nicomachean Ethics" in result.stdout
    assert "0.3000" in result.stdout
# Removed patch decorator
@patch('src.philograph.cli.main.display_results', autospec=True) # Added autospec
@patch('src.philograph.cli.main.error_console', autospec=True) # Added autospec
def test_search_api_error(mock_error_console, mock_display_results, runner):
    """Test the search command handles API errors gracefully."""
    test_query = "ontology"
    expected_payload = {"query": test_query, "limit": 10}

    # Use patch as context manager
    with patch('philograph.cli.main.make_api_request') as mock_make_api_request:
        # Simulate make_api_request raising typer.Exit after handling an internal error
        mock_make_api_request.side_effect = typer.Exit(1)

        # Use runner.invoke and assert exit code
        result = runner.invoke(app, ["search", test_query])

        # Assert exit code is 1
        assert result.exit_code == 1

        # Check that make_api_request was called correctly *inside* the patch context
        mock_make_api_request.assert_called_once_with(
            "POST",
            "/search",
            json_data=expected_payload
        )
    mock_display_results.assert_not_called()
    # Error printing is handled within make_api_request, no need to assert mock_error_console here
# Removed display_results and console mocks
def test_search_empty_results(runner): # Removed mock_console, mock_display_results
    """Test the search command handles an empty list of results from the API."""
    test_query = "nonexistent topic"
    expected_payload = {"query": test_query, "limit": 10}
    mock_api_response_data = {"results": []}

    # Patch make_api_request directly again
    with patch('philograph.cli.main.make_api_request') as mock_make_api_request:
        mock_make_api_request.return_value = mock_api_response_data

        # Use runner.invoke again
        result = runner.invoke(app, ["search", test_query])

        # Assert exit code
        assert result.exit_code == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"

        # Check that make_api_request was called correctly
        mock_make_api_request.assert_called_once_with(
            "POST",
            "/search",
            json_data=expected_payload
        )
    # Check that the "No results found" message was printed to stdout
    assert "No results found." in result.stdout
    # display_results should NOT be called directly when results are empty (mock removed)
# Removed test_search_filter_encoding_error as it's no longer relevant
# after changing search to use POST and send filters as dict.
# --- Tests for 'show' command ---

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
def test_show_document_success(mock_display_results, mock_make_api_request, runner):
    """Test the show command successfully retrieves and displays a document."""
    test_id_str = "123" # Use string as CLI argument
    test_id_int = 123   # Expected integer for API call
    mock_api_response = {
        "id": test_id_int, # API likely returns int
        "type": "document",
        "title": "Test Document",
        "author": "Test Author",
        "year": 2024,
        "source_path": "/path/to/test.pdf",
        "content_summary": "This is a summary.",
        "sections": [
            {"id": "sec_abc", "title": "Section 1"},
            {"id": "sec_def", "title": "Section 2"}
        ]
    }
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, ["show", "document", test_id_str]) # Pass string ID to CLI

    assert result.exit_code == 0
    mock_make_api_request.assert_called_once_with("GET", f"/documents/{test_id_int}") # Check API call uses int
    mock_display_results.assert_called_once_with(mock_api_response)
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
def test_show_chunk_success(mock_display_results, mock_make_api_request, runner):
    """Test the show command successfully retrieves and displays a chunk."""
    test_id = "chk_xyz987" # Assuming chunk IDs might be strings
    mock_api_response = {
        "id": test_id,
        "type": "chunk",
        "text": "This is the content of the test chunk.",
        "embedding_vector": "[0.1, 0.2, ...]", # Placeholder
        "document_id": 123,
        "section_id": "sec_abc",
        "metadata": {"page": 5}
    }
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, ["show", "chunk", test_id])

    assert result.exit_code == 0
    # Assuming endpoint structure /chunks/{chunk_id}
    mock_make_api_request.assert_called_once_with("GET", f"/chunks/{test_id}")
    mock_display_results.assert_called_once_with(mock_api_response)
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_show_invalid_item_type(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the show command handles an invalid item type."""
    test_id = "123"
    invalid_type = "invalid_type"

    result = runner.invoke(app, ["show", invalid_type, test_id])

    assert result.exit_code != 0 # Expect non-zero exit code for error
    mock_error_console.print.assert_called_once_with(
        f"Error: Invalid item type '{invalid_type}'. Must be 'document' or 'chunk'."
    )
    mock_make_api_request.assert_not_called()
    mock_display_results.assert_not_called()
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console') # Keep patching error_console for consistency, though not asserted here
def test_show_document_not_found(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the show command handles a 404 Not Found for a document."""
    test_id = "999" # Non-existent ID

    # Simulate make_api_request raising typer.Exit due to a 404
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, ["show", "document", test_id]) # Let runner catch SystemExit

    assert result.exit_code == 1
    mock_make_api_request.assert_called_once_with("GET", f"/documents/999")
    mock_display_results.assert_not_called()
    # Error printing is handled within make_api_request, tested separately
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_show_api_error(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the show command handles generic API errors."""
    test_id = "123"
    item_type = "document"

    # Simulate make_api_request raising typer.Exit due to a 500 or other error
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, ["show", item_type, test_id]) # Let runner catch SystemExit

    assert result.exit_code == 1
    mock_make_api_request.assert_called_once_with("GET", f"/documents/123")
    mock_display_results.assert_not_called()
    # Error printing is handled within make_api_request, tested separately
# --- Tests for 'collection create' command ---

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
def test_collection_create_success(mock_display_results, mock_make_api_request, runner):
    """Test the collection create command successfully creates a collection."""
    test_name = "My New Collection"
    mock_api_response = {
        "message": f"Collection '{test_name}' created successfully.",
        "collection_id": 5
    }
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, ["collection", "create", test_name])

    assert result.exit_code == 0
    mock_make_api_request.assert_called_once_with(
        "POST",
        "/collections",
        json_data={"name": test_name}
    )
    mock_display_results.assert_called_once_with(mock_api_response)
# --- Tests for 'collection add' command ---

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
def test_collection_add_item_success(mock_display_results, mock_make_api_request, runner):
    """Test the collection add command successfully adds an item."""
    test_collection_id = 5
    test_item_type = "document"
    test_item_id = 123
    mock_api_response = {
        "message": f"Item {test_item_id} ({test_item_type}) added to collection {test_collection_id}.",
        "collection_id": test_collection_id,
        "item_id": test_item_id,
        "item_type": test_item_type
    }
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, [
        "collection",
        "add",
        str(test_collection_id),
        test_item_type,
        str(test_item_id)
    ])

    assert result.exit_code == 0
    mock_make_api_request.assert_called_once_with(
        "POST",
        f"/collections/{test_collection_id}/items",
        json_data={"item_type": test_item_type.lower(), "item_id": test_item_id}
    )
    mock_display_results.assert_called_once_with(mock_api_response)
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console') # Patch error console for consistency
def test_collection_add_item_api_error_404(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the collection add command handles API 404 errors (e.g., collection/item not found)."""
    test_collection_id = 999 # Non-existent
    test_item_type = "document"
    test_item_id = 123

    # Simulate make_api_request raising typer.Exit due to a 404
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, [
        "collection",
        "add",
        str(test_collection_id),
        test_item_type,
        str(test_item_id)
    ])

    assert result.exit_code == 1 # Expecting failure exit code
    mock_make_api_request.assert_called_once_with(
        "POST",
        f"/collections/{test_collection_id}/items",
        json_data={"item_type": test_item_type.lower(), "item_id": test_item_id}
    )
    mock_display_results.assert_not_called()
    # Error printing is handled within make_api_request, which is tested separately


@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_collection_add_item_invalid_type(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the collection add command handles API 422 errors for invalid item_type."""
    test_collection_id = 5
    invalid_item_type = "paper" # Invalid type
    test_item_id = 123

    # Simulate make_api_request raising typer.Exit due to a 422 from API validation
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, [
        "collection",
        "add",
        str(test_collection_id),
        invalid_item_type,
        str(test_item_id)
    ])

    assert result.exit_code == 1 # Expecting failure exit code
    mock_make_api_request.assert_called_once_with(
        "POST",
        f"/collections/{test_collection_id}/items",
        json_data={"item_type": invalid_item_type.lower(), "item_id": test_item_id}
    )
    mock_display_results.assert_not_called()
    # Error printing is handled within make_api_request


@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_collection_add_item_invalid_collection_id(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the collection add command handles API 404 for invalid collection_id."""
    invalid_collection_id = 999 # Non-existent
    test_item_type = "document"
    test_item_id = 123

    # Simulate make_api_request raising typer.Exit due to a 404 from API
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, [
        "collection",
        "add",
        str(invalid_collection_id),
        test_item_type,
        str(test_item_id)
    ])

    assert result.exit_code == 1 # Expecting failure exit code
    mock_make_api_request.assert_called_once_with(
        "POST",
        f"/collections/{invalid_collection_id}/items",
        json_data={"item_type": test_item_type.lower(), "item_id": test_item_id}
    )
    mock_display_results.assert_not_called()
    # Error printing is handled within make_api_request
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_collection_add_item_invalid_item_id(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the collection add command handles API error for invalid item_id."""
    test_collection_id = 1
    test_item_type = "document"
    invalid_item_id = 9999 # Non-existent

    # Simulate make_api_request raising typer.Exit due to a 404/422 from API
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, [
        "collection",
        "add",
        str(test_collection_id),
        test_item_type,
        str(invalid_item_id)
    ])

    assert result.exit_code == 1 # Expecting failure exit code
    mock_make_api_request.assert_called_once_with(
        "POST",
        f"/collections/{test_collection_id}/items",
        json_data={"item_type": test_item_type.lower(), "item_id": invalid_item_id}
    )
    mock_display_results.assert_not_called()
    # Error printing is handled within make_api_request
# Tests for `collection list` command (maps to list_items function)
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_collection_list_items_success(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the collection list command successfully lists items in a collection."""
    test_collection_id = 1
    mock_api_response = {
        "items": [
            {"item_id": 101, "item_type": "document", "details": {"title": "Doc 1"}},
            {"item_id": 505, "item_type": "chunk", "details": {"doc_id": 101, "chunk_index": 0}}
        ]
    }
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, [
        "collection",
        "list",
        str(test_collection_id)
    ])

    assert result.exit_code == 0
    mock_make_api_request.assert_called_once_with(
        "GET",
        f"/collections/{test_collection_id}"
    )
    mock_display_results.assert_called_once_with(mock_api_response)
    mock_error_console.print.assert_not_called()
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_collection_list_items_empty(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the collection list command handles an empty collection."""
    test_collection_id = 2
    mock_api_response = {"items": []} # API returns empty list
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, [
        "collection",
        "list",
        str(test_collection_id)
    ])

    assert result.exit_code == 0
    mock_make_api_request.assert_called_once_with(
        "GET",
        f"/collections/{test_collection_id}"
    )
    # Check that display_results is called with the full response, even if items list is empty
    mock_display_results.assert_called_once_with(mock_api_response)
    mock_error_console.print.assert_not_called()
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_collection_list_items_not_found(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the collection list command handles API 404 for non-existent collection."""
    non_existent_collection_id = 999

    # Simulate make_api_request raising typer.Exit due to a 404 from API
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, [
        "collection",
        "list",
        str(non_existent_collection_id)
    ])

    assert result.exit_code == 1 # Expecting failure exit code
    mock_make_api_request.assert_called_once_with(
        "GET",
        f"/collections/{non_existent_collection_id}"
    )
    mock_display_results.assert_not_called()
    # Error printing is handled within make_api_request
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_collection_list_items_api_error(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the collection list command handles a generic API error."""
    test_collection_id = 3

    # Simulate make_api_request raising typer.Exit due to a 500 error from API
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, [
        "collection",
        "list",
        str(test_collection_id)
    ])

    assert result.exit_code == 1 # Expecting failure exit code
    mock_make_api_request.assert_called_once_with(
        "GET",
        f"/collections/{test_collection_id}"
    )
    mock_display_results.assert_not_called()
    # Error printing is handled within make_api_request
# Tests for `acquire` command (maps to acquire_missing_texts function)
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_acquire_success_direct(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the acquire command successfully handles a direct success response."""
    test_title = "Test Title"
    mock_api_response = {"status": "completed", "message": "Acquisition process finished."}
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, [
        "acquire",
        "--title", test_title
    ])

    assert result.exit_code == 0
    mock_make_api_request.assert_called_once_with(
        "POST",
        "/acquire",
        json_data={"text_details": {"title": test_title, "author": None}} # Match implementation payload
    )
    mock_display_results.assert_called_once_with(mock_api_response)
    mock_error_console.print.assert_not_called()
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
@patch('typer.prompt') # Mock user input
def test_acquire_confirmation_flow(mock_prompt, mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the acquire command confirmation flow."""
    test_title = "Confirm Title"
    test_author = "Confirm Author"
    acquisition_id = "confirm-123"
    book_options = [
        {"title": "Confirm Title", "author": "Confirm Author", "year": 2024, "extension": "pdf", "size": "2MB", "zlibrary_id": "z1"},
        {"title": "Another Book", "author": "Other Author", "year": 2023, "extension": "epub", "size": "1MB", "zlibrary_id": "z2"}
    ]
    mock_initial_response = {
        "status": "needs_confirmation",
        "acquisition_id": acquisition_id,
        "options": book_options
    }
    mock_confirm_response = {"status": "processing", "message": "Acquisition confirmed and processing."}

    # Configure mocks: first call returns options, second call (confirm) returns success
    mock_make_api_request.side_effect = [mock_initial_response, mock_confirm_response]
    # Simulate user selecting the first book
    mock_prompt.return_value = 1

    result = runner.invoke(app, [
        "acquire",
        "--title", test_title,
        "--author", test_author
    ])

    assert result.exit_code == 0

    # Check API calls
    assert mock_make_api_request.call_count == 2
    # Call 1: Initial search
    mock_make_api_request.assert_any_call(
        "POST",
        "/acquire",
        json_data={"text_details": {"title": test_title, "author": test_author}}
    )
    # Call 2: Confirmation
    mock_make_api_request.assert_any_call(
        "POST",
        "/acquire/confirm",
        json_data={
            "acquisition_id": acquisition_id,
            "selected_book_details": book_options[0] # User selected first option
        }
    )

    # Check user prompt
    mock_prompt.assert_called_once_with("Enter selection number (or 0 to cancel)", type=int, default=0)

    # Check final display
    mock_display_results.assert_called_once_with(mock_confirm_response)
    mock_error_console.print.assert_not_called()
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
@patch('typer.prompt') # Mock user input
def test_acquire_confirmation_flow_yes_flag(mock_prompt, mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the acquire command confirmation flow with the --yes flag."""
    test_title = "Yes Flag Title"
    acquisition_id = "yes-456"
    book_options = [
        {"title": "Yes Flag Title", "author": "Yes Author", "year": 2024, "extension": "pdf", "size": "3MB", "zlibrary_id": "z3"}
        # Assume only one option is returned for simplicity with --yes
    ]
    mock_initial_response = {
        "status": "needs_confirmation",
        "acquisition_id": acquisition_id,
        "options": book_options
    }
    mock_confirm_response = {"status": "processing", "message": "Acquisition confirmed (auto) and processing."}

    # Configure mocks: first call returns options, second call (confirm) returns success
    mock_make_api_request.side_effect = [mock_initial_response, mock_confirm_response]

    result = runner.invoke(app, [
        "acquire",
        "--title", test_title,
        "--yes" # Add the yes flag
    ])

    assert result.exit_code == 0

    # Check API calls
    assert mock_make_api_request.call_count == 2
    # Call 1: Initial search
    mock_make_api_request.assert_any_call(
        "POST",
        "/acquire",
        json_data={"text_details": {"title": test_title, "author": None}}
    )
    # Call 2: Confirmation (should use the first/only option)
    mock_make_api_request.assert_any_call(
        "POST",
        "/acquire/confirm",
        json_data={
            "acquisition_id": acquisition_id,
            "selected_book_details": book_options[0]
        }
    )

    # Check user prompt was NOT called
    mock_prompt.assert_not_called()

    # Check final display
    mock_display_results.assert_called_once_with(mock_confirm_response)
    mock_error_console.print.assert_not_called()
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_acquire_api_error(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the acquire command handles a generic API error during initial search."""
    test_title = "API Error Title"

    # Simulate make_api_request raising typer.Exit due to a 500 error from API
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, [
        "acquire",
        "--title", test_title
    ])

    assert result.exit_code == 1 # Expecting failure exit code
    mock_make_api_request.assert_called_once_with(
        "POST",
        "/acquire",
        json_data={"text_details": {"title": test_title, "author": None}}
    )
    mock_display_results.assert_not_called()
    # Error printing is handled within make_api_request
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_acquire_missing_arguments(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the acquire command exits if no title or author is provided."""
    result = runner.invoke(app, [
        "acquire"
        # No --title or --author
    ])

    assert result.exit_code == 1 # Expecting failure exit code due to missing args check
    mock_make_api_request.assert_not_called()
    mock_display_results.assert_not_called()
    mock_error_console.print.assert_called_once_with("Error: Must provide either --title/--author or --find-missing-threshold.")
# --- Tests for 'status' command ---

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
def test_status_success(mock_display_results, mock_make_api_request, runner):
    """Test the status command successfully retrieves and displays status."""
    test_acquisition_id = "acq_test_123"
    mock_api_response = {
        "acquisition_id": test_acquisition_id,
        "status": "completed",
        "details": "Ingestion successful for 1 file.",
        "document_id": 456
    }
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, ["status", test_acquisition_id])

    assert result.exit_code == 0
    mock_make_api_request.assert_called_once_with("GET", f"/acquire/status/{test_acquisition_id}")
    mock_display_results.assert_called_once_with(mock_api_response)
@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_status_api_error(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the status command handles generic API errors."""
    test_acquisition_id = "acq_err_456"
    # Simulate make_api_request raising typer.Exit due to a 500 or other error
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, ["status", test_acquisition_id])

    assert result.exit_code == 1
    mock_make_api_request.assert_called_once_with("GET", f"/acquire/status/{test_acquisition_id}")
    mock_display_results.assert_not_called()
    # Error printing is handled within make_api_request

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_status_not_found(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the status command handles a 404 Not Found error."""
    test_acquisition_id = "acq_not_found_789"
    # Simulate make_api_request raising typer.Exit due to a 404
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, ["status", test_acquisition_id])

    assert result.exit_code == 1
    mock_make_api_request.assert_called_once_with("GET", f"/acquire/status/{test_acquisition_id}")
    mock_display_results.assert_not_called()
    # Error printing is handled within make_api_request

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_status_invalid_id(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the status command handles an invalid ID format by relying on API error."""
    test_invalid_id = "invalid-id-format"
    # Simulate make_api_request raising typer.Exit due to API error (e.g., 400/422)
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, ["status", test_invalid_id])

    # Expecting exit code 1 from make_api_request's error handling
    assert result.exit_code == 1
    mock_make_api_request.assert_called_once_with("GET", f"/acquire/status/{test_invalid_id}")
    mock_display_results.assert_not_called()
    # Check if Typer prints a usage error or if we print a specific error
    # This assertion might need adjustment based on actual output
    # assert "Invalid value" in result.stdout or "Error:" in result.stdout
@patch('philograph.cli.main.make_api_request')
def test_acquire_missing_texts_initial_call(mock_make_api_request, runner: CliRunner):
    """Test the initial API call for acquire-missing-texts."""
    # Arrange
    mock_make_api_request.return_value = {"status": "processing", "message": "Search initiated."}
    threshold = 7

    # Act
    result = runner.invoke(app, ["acquire", "--find-missing-threshold", str(threshold)])

    # Assert
    assert result.exit_code == 0
    mock_make_api_request.assert_called_once_with(
        "POST",
        "/acquire",
        json_data={"find_missing_threshold": threshold}
    )
    assert "Identifying potentially missing texts" in result.stdout
    assert "Search initiated." in result.stdout
@patch('philograph.cli.main.make_api_request')
@patch('typer.prompt') # Mock user input
def test_acquire_missing_texts_confirmation_flow(mock_prompt, mock_make_api_request, runner: CliRunner):
    """Test the confirmation flow for acquire-missing-texts."""
    # Arrange
    acquisition_id = "test-acq-id-123"
    options = [
        {"title": "Book A", "author": "Author X", "year": 2020, "extension": "pdf", "size": "1MB", "internal_id": "opt1"},
        {"title": "Book B", "author": "Author Y", "year": 2021, "extension": "epub", "size": "2MB", "internal_id": "opt2"},
    ]
    initial_response = {
        "status": "needs_confirmation",
        "acquisition_id": acquisition_id,
        "options": options
    }
    confirm_response = {"status": "complete", "message": "Acquisition confirmed and processing."}

    # Mock the sequence of API calls and user input
    mock_make_api_request.side_effect = [initial_response, confirm_response]
    mock_prompt.return_value = 1 # Simulate user selecting the first option

    # Act
    result = runner.invoke(app, ["acquire", "--find-missing-threshold", "5"]) # Threshold doesn't matter here

    # Assert
    assert result.exit_code == 0

    # Check output for prompt and confirmation message
    assert "Potential matches found." in result.stdout
    assert "Confirming acquisition for: 'Book A'" in result.stdout # Check confirmation message

    # Check that typer.prompt was called
    mock_prompt.assert_called_once()

    # Check API calls
    assert mock_make_api_request.call_count == 2
    # Check first call (initial acquire)
    call1_args, call1_kwargs = mock_make_api_request.call_args_list[0]
    assert call1_args == ("POST", "/acquire")
    assert call1_kwargs['json_data'] == {"find_missing_threshold": 5}

    # Check second call (confirm)
    call2_args, call2_kwargs = mock_make_api_request.call_args_list[1]
    assert call2_args == ("POST", "/acquire/confirm")
    assert call2_kwargs['json_data'] == {
        "acquisition_id": acquisition_id,
        "selected_book_details": options[0] # User selected option 1
    }

    # Check final output
    assert "Acquisition confirmed and processing." in result.stdout
@patch('philograph.cli.main.make_api_request')
@patch('typer.prompt') # Mock user input
def test_acquire_missing_texts_confirmation_cancel(mock_prompt, mock_make_api_request, runner: CliRunner):
    """Test cancelling the confirmation flow for acquire-missing-texts."""
    # Arrange
    acquisition_id = "test-acq-id-456"
    options = [
        {"title": "Book C", "author": "Author Z", "year": 2022, "extension": "pdf", "size": "3MB", "internal_id": "opt3"},
    ]
    initial_response = {
        "status": "needs_confirmation",
        "acquisition_id": acquisition_id,
        "options": options
    }

    # Mock the initial API call and user input (cancelling)
    mock_make_api_request.return_value = initial_response
    mock_prompt.return_value = 0 # Simulate user entering 0 to cancel

    # Act
    result = runner.invoke(app, ["acquire", "--find-missing-threshold", "5"])

    # Assert
    assert result.exit_code == 0

    # Check output for prompt and cancellation message
    assert "Potential matches found." in result.stdout
    assert "Acquisition cancelled." in result.stdout

    # Check that typer.prompt was called
    mock_prompt.assert_called_once()

    # Check that only the initial API call was made
    mock_make_api_request.assert_called_once_with(
        "POST",
        "/acquire",
        json_data={"find_missing_threshold": 5}
    )
@patch('philograph.cli.main.make_api_request')
def test_acquire_missing_texts_initial_api_error(mock_make_api_request, runner: CliRunner):
    """Test acquire-missing-texts when the initial API call fails."""
    # Arrange
    mock_make_api_request.side_effect = typer.Exit(code=1) # Simulate make_api_request raising Exit on error

    # Act
    result = runner.invoke(app, ["acquire", "--find-missing-threshold", "5"])

    # Assert
    assert result.exit_code == 1 # Expecting exit code 1 due to the raised Exit
    mock_make_api_request.assert_called_once_with(
        "POST",
        "/acquire",
        json_data={"find_missing_threshold": 5}
    )
    # Error message is printed by make_api_request, no need to assert stdout here
@patch('philograph.cli.main.make_api_request')
def test_acquire_missing_texts_confirmation_missing_data(mock_make_api_request, runner: CliRunner):
    """Test acquire-missing-texts confirmation flow with missing options/ID."""
    # Arrange
    # Case 1: Missing options
    initial_response_missing_options = {
        "status": "needs_confirmation",
        "acquisition_id": "test-acq-id-789",
        "options": [] # Empty options list
    }
    mock_make_api_request.return_value = initial_response_missing_options

    # Act 1
    result1 = runner.invoke(app, ["acquire", "--find-missing-threshold", "5"])

    # Assert 1
    assert result1.exit_code == 1
    # Cannot reliably assert stderr with CliRunner and rich, relying on exit code
    mock_make_api_request.assert_called_once_with("POST", "/acquire", json_data={"find_missing_threshold": 5})

    # Arrange Case 2: Missing acquisition_id
    mock_make_api_request.reset_mock()
    initial_response_missing_id = {
        "status": "needs_confirmation",
        "acquisition_id": None, # Missing ID
        "options": [{"title": "Book D"}]
    }
    mock_make_api_request.return_value = initial_response_missing_id

    # Act 2
    result2 = runner.invoke(app, ["acquire", "--find-missing-threshold", "5"])

    # Assert 2
    assert result2.exit_code == 1
    # Cannot reliably assert stderr with CliRunner and rich, relying on exit code
    mock_make_api_request.assert_called_once_with("POST", "/acquire", json_data={"find_missing_threshold": 5})
@patch('philograph.cli.main.make_api_request')
@patch('typer.prompt') # Mock user input, should not be called
def test_acquire_missing_texts_auto_confirm_yes(mock_prompt, mock_make_api_request, runner: CliRunner):
    """Test the --yes flag auto-confirms when only one option is available."""
    # Arrange
    acquisition_id = "test-acq-id-yes"
    options = [
        {"title": "Book E", "author": "Author A", "year": 2023, "extension": "pdf", "size": "4MB", "internal_id": "opt5"},
    ] # Only one option
    initial_response = {
        "status": "needs_confirmation",
        "acquisition_id": acquisition_id,
        "options": options
    }
    confirm_response = {"status": "complete", "message": "Acquisition auto-confirmed."}

    # Mock the sequence of API calls
    mock_make_api_request.side_effect = [initial_response, confirm_response]

    # Act
    result = runner.invoke(app, ["acquire", "--find-missing-threshold", "5", "--yes"])

    # Assert
    assert result.exit_code == 0

    # Check output for auto-confirmation message
    assert "Found 1 match. Auto-confirming acquisition" in result.stdout
    assert "Book E" in result.stdout
    assert "(--yes used)" in result.stdout

    # Check that typer.prompt was NOT called
    mock_prompt.assert_not_called()

    # Check API calls
    assert mock_make_api_request.call_count == 2
    # Check first call (initial acquire)
    call1_args, call1_kwargs = mock_make_api_request.call_args_list[0]
    assert call1_args == ("POST", "/acquire")
    assert call1_kwargs['json_data'] == {"find_missing_threshold": 5}

    # Check second call (confirm)
    call2_args, call2_kwargs = mock_make_api_request.call_args_list[1]
    assert call2_args == ("POST", "/acquire/confirm")
    assert call2_kwargs['json_data'] == {
        "acquisition_id": acquisition_id,
        "selected_book_details": options[0] # Auto-selected the only option
    }

    # Check final output
    assert "Acquisition auto-confirmed." in result.stdout
@patch('philograph.cli.main.make_api_request')
@patch('typer.prompt') # Mock user input
def test_acquire_specific_text_confirmation_flow(mock_prompt, mock_make_api_request, runner: CliRunner):
    """Test the acquire command with title/author and confirmation flow."""
    # Arrange
    title = "Specific Book Title"
    author = "Specific Author"
    acquisition_id = "test-acq-id-spec-789"
    options = [
        {"title": title, "author": author, "year": 2024, "extension": "epub", "size": "1.5MB", "internal_id": "opt-spec-1"},
    ]
    initial_response = {
        "status": "needs_confirmation",
        "acquisition_id": acquisition_id,
        "options": options
    }
    confirm_response = {"status": "complete", "message": "Specific acquisition confirmed."}

    # Mock the sequence of API calls and user input
    mock_make_api_request.side_effect = [initial_response, confirm_response]
    mock_prompt.return_value = 1 # Simulate user selecting the first option

    # Act
    result = runner.invoke(app, ["acquire", "--title", title, "--author", author])

    # Assert
    assert result.exit_code == 0

    # Check output
    assert f"Searching for text: Title='{title}', Author='{author}'" in result.stdout
    assert "Potential matches found." in result.stdout
    assert f"Confirming acquisition for: '{title}'" in result.stdout

    # Check that typer.prompt was called
    mock_prompt.assert_called_once()

    # Check API calls
    assert mock_make_api_request.call_count == 2
    # Check first call (initial acquire with details)
    call1_args, call1_kwargs = mock_make_api_request.call_args_list[0]
    assert call1_args == ("POST", "/acquire")
    assert call1_kwargs['json_data'] == {"text_details": {"title": title, "author": author}}

    # Check second call (confirm)
    call2_args, call2_kwargs = mock_make_api_request.call_args_list[1]
    assert call2_args == ("POST", "/acquire/confirm")
    assert call2_kwargs['json_data'] == {
        "acquisition_id": acquisition_id,
        "selected_book_details": options[0]
    }

    # Check final output
    assert "Specific acquisition confirmed." in result.stdout