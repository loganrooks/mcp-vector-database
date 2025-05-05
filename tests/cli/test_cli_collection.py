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
    mock_make_api_request.assert_called_once_with("POST", "/collections", json_data={"name": test_name})
    mock_display_results.assert_called_once_with(mock_api_response)

# --- Tests for 'collection add' command ---

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
def test_collection_add_item_success(mock_display_results, mock_make_api_request, runner):
    """Test adding an item to a collection successfully."""
    collection_id = str(uuid.uuid4()) # Use UUID
    item_type = "document"
    item_id = str(uuid.uuid4()) # Use UUID
    mock_api_response = {"message": "Item added to collection."}
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, ["collection", "add", collection_id, item_type, item_id])

    assert result.exit_code == 0
    mock_make_api_request.assert_called_once_with(
        "POST",
        f"/collections/{collection_id}/items",
        json_data={"item_type": item_type, "item_id": item_id}
    )
    mock_display_results.assert_called_once_with(mock_api_response)

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
def test_collection_add_item_chunk_success(mock_display_results, mock_make_api_request, runner):
    """Test adding a chunk item to a collection successfully."""
    test_collection_id = "col_abc" # Use string as CLI argument
    test_item_id = "chk_xyz" # Use string as CLI argument
    item_type = "chunk"
    mock_api_response = {"message": f"Item {test_item_id} added to collection {test_collection_id}."}
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, [
        "collection",
        "add",
        test_collection_id,
        item_type,
        test_item_id
    ])

    assert result.exit_code == 0
    expected_endpoint = f"/collections/{test_collection_id}/items"
    expected_payload = {"item_type": item_type, "item_id": test_item_id}
    mock_make_api_request.assert_called_once_with("POST", expected_endpoint, json_data=expected_payload)
    mock_display_results.assert_called_once_with(mock_api_response)


@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_collection_add_item_api_error_404(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test adding an item handles 404 (collection or item not found)."""
    collection_id = str(uuid.uuid4())
    item_type = "document"
    item_id = str(uuid.uuid4())

    # Simulate make_api_request raising typer.Exit due to a 404
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, ["collection", "add", collection_id, item_type, item_id])

    assert result.exit_code == 1
    mock_make_api_request.assert_called_once_with(
        "POST",
        f"/collections/{collection_id}/items",
        json_data={"item_type": item_type, "item_id": item_id}
    )
    mock_display_results.assert_not_called()
    # Error printing handled within make_api_request

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_collection_add_item_invalid_type(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test adding an item handles invalid item type (API 422)."""
    collection_id = str(uuid.uuid4())
    item_type = "invalid_type"
    item_id = str(uuid.uuid4())

    # Simulate make_api_request raising typer.Exit due to a 422
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, ["collection", "add", collection_id, item_type, item_id])

    assert result.exit_code == 1
    mock_make_api_request.assert_called_once_with(
        "POST",
        f"/collections/{collection_id}/items",
        json_data={"item_type": item_type, "item_id": item_id}
    )
    mock_display_results.assert_not_called()
    # Error printing handled within make_api_request

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console') # Keep error_console patch
def test_collection_add_item_invalid_collection_id(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test adding an item handles invalid collection ID format (API 422)."""
    collection_id = "not-a-uuid" # Keep invalid ID
    item_type = "document"
    item_id = str(uuid.uuid4())

    # Simulate make_api_request raising typer.Exit due to an API error (e.g., 422)
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, ["collection", "add", collection_id, item_type, item_id])

    assert result.exit_code == 1 # Expect exit code 1 due to API error
    # No longer check stdout for Typer validation message
    mock_make_api_request.assert_called_once() # API should be called now
    mock_display_results.assert_not_called()
    # error_console might be called by make_api_request, so don't assert not_called

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_collection_add_item_invalid_item_id(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test adding an item handles invalid item ID format (API 422)."""
    collection_id = str(uuid.uuid4())
    item_type = "document"
    item_id = "not-a-uuid"

    # Simulate make_api_request raising typer.Exit due to a 422
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, ["collection", "add", collection_id, item_type, item_id])

    assert result.exit_code == 1
    mock_make_api_request.assert_called_once_with(
        "POST",
        f"/collections/{collection_id}/items",
        json_data={"item_type": item_type, "item_id": item_id}
    )
    mock_display_results.assert_not_called()
    # Error printing handled within make_api_request

# --- Tests for 'collection list' command ---

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console') # Patch error console for consistency
def test_collection_list_items_success(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test listing items in a collection successfully."""
    collection_id = str(uuid.uuid4())
    mock_api_response = {
        "collection_id": collection_id,
        "name": "Test Collection",
        "items": [
            {"item_id": str(uuid.uuid4()), "item_type": "document", "title": "Doc 1"},
            {"item_id": str(uuid.uuid4()), "item_type": "chunk", "text_preview": "Chunk text..."}
        ]
    }
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, ["collection", "list", collection_id])

    assert result.exit_code == 0
    mock_make_api_request.assert_called_once_with("GET", f"/collections/{collection_id}")
    mock_display_results.assert_called_once_with(mock_api_response)

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_collection_list_items_empty(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test listing items in an empty collection."""
    collection_id = str(uuid.uuid4())
    mock_api_response = {
        "collection_id": collection_id,
        "name": "Empty Collection",
        "items": []
    }
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, ["collection", "list", collection_id])

    assert result.exit_code == 0
    mock_make_api_request.assert_called_once_with("GET", f"/collections/{collection_id}")
    mock_display_results.assert_called_once_with(mock_api_response)

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_collection_list_items_not_found(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test listing items handles collection not found (API 404)."""
    collection_id = str(uuid.uuid4())

    # Simulate make_api_request raising typer.Exit due to a 404
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, ["collection", "list", collection_id])

    assert result.exit_code == 1
    mock_make_api_request.assert_called_once_with("GET", f"/collections/{collection_id}")
    mock_display_results.assert_not_called()
    # Error printing handled within make_api_request

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_collection_list_items_api_error(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test listing items handles generic API errors."""
    collection_id = str(uuid.uuid4())

    # Simulate make_api_request raising typer.Exit due to a 500 or other error
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, ["collection", "list", collection_id])

    assert result.exit_code == 1
    mock_make_api_request.assert_called_once_with("GET", f"/collections/{collection_id}")
    mock_display_results.assert_not_called()
    # Error printing handled within make_api_request