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

# --- Tests for 'status' command ---

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
def test_status_success_pending(mock_display_results, mock_make_api_request, runner):
    """Test the status command successfully retrieves and displays a pending status."""
    test_id = str(uuid.uuid4())
    mock_api_response = {
        "acquisition_id": test_id,
        "status": "pending",
        "details": "Waiting for download...",
        "progress": 0.0,
        "file_path": None,
        "error_message": None
    }
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, ["status", test_id])

    assert result.exit_code == 0
    mock_make_api_request.assert_called_once_with("GET", f"/acquire/status/{test_id}")
    mock_display_results.assert_called_once_with(mock_api_response)

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
def test_status_success_failed(mock_display_results, mock_make_api_request, runner):
    """Test the status command successfully retrieves and displays a failed status."""
    test_id = str(uuid.uuid4())
    mock_api_response = {
        "acquisition_id": test_id,
        "status": "failed",
        "details": "Download failed.",
        "progress": 0.0,
        "file_path": None,
        "error_message": "Network error"
    }
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, ["status", test_id])

    assert result.exit_code == 0
    mock_make_api_request.assert_called_once_with("GET", f"/acquire/status/{test_id}")
    mock_display_results.assert_called_once_with(mock_api_response)

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
def test_status_success(mock_display_results, mock_make_api_request, runner):
    """Test the status command successfully retrieves and displays a status."""
    test_id = str(uuid.uuid4())
    mock_api_response = {"acquisition_id": test_id, "status": "pending", "details": "Processing..."}
    mock_make_api_request.return_value = mock_api_response

    result = runner.invoke(app, ["status", test_id])

    assert result.exit_code == 0
    mock_make_api_request.assert_called_once_with("GET", f"/acquire/status/{test_id}")
    mock_display_results.assert_called_once_with(mock_api_response)

@patch('philograph.cli.main.make_api_request')
@patch('philograph.cli.main.display_results')
@patch('philograph.cli.main.error_console')
def test_status_api_error(mock_error_console, mock_display_results, mock_make_api_request, runner):
    """Test the status command handles generic API errors."""
    test_id = str(uuid.uuid4())

    # Simulate make_api_request raising typer.Exit due to a 500 or other error
    mock_make_api_request.side_effect = typer.Exit(code=1)

    result = runner.invoke(app, ["status", test_id])

    assert result.exit_code == 1
    mock_make_api_request.assert_called_once_with("GET", f"/acquire/status/{test_id}")
    mock_display_results.assert_not_called()
    # Error printing handled within make_api_request

# Removed redundant test: test_status_not_found
# Removed redundant test: test_status_invalid_id