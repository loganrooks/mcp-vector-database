import pytest
from unittest.mock import patch, MagicMock
import typer
from typer.testing import CliRunner

# Import the Typer app instance from your CLI module
# Adjust the import path based on your project structure
from philograph.cli.main import app

# Fixture for the Typer CliRunner
@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)

# --- Tests for 'search' command ---

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

# Test search with --doc-id filter
def test_search_success_with_doc_id_filter(runner):
    """Test the search command calls the API correctly with query and doc_id filter."""
    test_query = "specific concept"
    test_doc_id = 3
    filters_dict = {"doc_id": test_doc_id}
    expected_payload = {"query": test_query, "filters": filters_dict, "limit": 10}
    mock_api_response_data = {
        "results": [
            {"id": 10, "type": "chunk", "score": 0.7, "text": "...", "document_title": "Relevant Doc", "source_document": {"title": "Relevant Doc", "author": "Author", "year": 2023, "doc_id": test_doc_id}, "chunk_id": 10, "distance": 0.3}
        ]
    }

    with patch('philograph.cli.main.make_api_request') as mock_make_api_request:
        mock_make_api_request.return_value = mock_api_response_data

        result = runner.invoke(app, [
            "search",
            test_query,
            "--doc-id", str(test_doc_id)
        ])

        assert result.exit_code == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        mock_make_api_request.assert_called_once_with(
            "POST",
            "/search",
            json_data=expected_payload
        )
    assert "Search Results" in result.stdout
    assert "Relevant Doc" in result.stdout
    assert "0.3000" in result.stdout

# Test search with --limit option
def test_search_success_with_limit(runner):
    """Test the search command calls the API correctly with a specific limit."""
    test_query = "another concept"
    test_limit = 5
    expected_payload = {"query": test_query, "limit": test_limit}
    # Mock response with fewer results than default, matching the limit
    mock_api_response_data = {
        "results": [
            {"id": 1, "type": "chunk", "score": 0.9, "text": "...", "source_document": {"title": "Doc A", "author": "Auth A", "year": 2020, "doc_id": 1}, "chunk_id": 1, "distance": 0.1},
            {"id": 2, "type": "chunk", "score": 0.8, "text": "...", "source_document": {"title": "Doc B", "author": "Auth B", "year": 2021, "doc_id": 2}, "chunk_id": 2, "distance": 0.2},
            {"id": 3, "type": "chunk", "score": 0.7, "text": "...", "source_document": {"title": "Doc C", "author": "Auth C", "year": 2022, "doc_id": 3}, "chunk_id": 3, "distance": 0.3},
            {"id": 4, "type": "chunk", "score": 0.6, "text": "...", "source_document": {"title": "Doc D", "author": "Auth D", "year": 2023, "doc_id": 4}, "chunk_id": 4, "distance": 0.4},
            {"id": 5, "type": "chunk", "score": 0.5, "text": "...", "source_document": {"title": "Doc E", "author": "Auth E", "year": 2024, "doc_id": 5}, "chunk_id": 5, "distance": 0.5},
        ]
    }

    with patch('philograph.cli.main.make_api_request') as mock_make_api_request:
        mock_make_api_request.return_value = mock_api_response_data

        result = runner.invoke(app, [
            "search",
            test_query,
            "--limit", str(test_limit)
        ])

        assert result.exit_code == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        mock_make_api_request.assert_called_once_with(
            "POST",
            "/search",
            json_data=expected_payload
        )
    assert "Search Results" in result.stdout
    # Check if roughly the correct number of results are displayed (Rich table formatting makes exact count hard)
    assert result.stdout.count("Doc ") == test_limit

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