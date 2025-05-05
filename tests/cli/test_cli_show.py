import pytest
from unittest.mock import patch, MagicMock
import typer
from typer.testing import CliRunner
import uuid # Added for UUID usage

# Import the Typer app instance from your CLI module
# Adjust the import path based on your project structure
from philograph.cli.main import app

# Fixture for the Typer CliRunner
@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)

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

@patch('philograph.cli.main.make_api_request') # Don't expect API call
@patch('philograph.cli.main.display_results') # Don't expect display
@patch('philograph.cli.main.error_console')
def test_show_document_invalid_id_format(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the show command handles a non-integer document ID."""
    test_id = "not-an-integer"
    item_type = "document"

    result = runner.invoke(app, ["show", item_type, test_id])

    assert result.exit_code != 0 # Expect non-zero exit code for error
    mock_error_console.print.assert_called_once_with(
        f"Error: Invalid Document ID '{test_id}'. Must be an integer."
    )
    mock_make_api_request.assert_not_called()
    mock_display_results.assert_not_called()

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
    invalid_item_type = "bibliography" # Example invalid type

    result = runner.invoke(app, ["show", invalid_item_type, test_id])

    assert result.exit_code != 0 # Expect non-zero exit code for error
    mock_error_console.print.assert_called_once_with(
        f"Error: Invalid item type '{invalid_item_type}'. Must be 'document' or 'chunk'."
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