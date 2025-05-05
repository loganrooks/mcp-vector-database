import pytest
from unittest.mock import patch, MagicMock
import json
import httpx
import typer
from typer.testing import CliRunner

# Import config for API_URL access in assertions
# Assuming config is accessible, adjust if needed
from philograph import config

# Import the function to be tested
# Adjust the import path based on your project structure
from src.philograph.cli.main import make_api_request

# Fixture for the Typer CliRunner (might not be needed for helper tests, but kept for consistency)
@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)

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

        response_data = make_api_request("GET", "/test-endpoint")

    # Assertions (moved outside with block for clarity)
    mock_client_instance.request.assert_called_once_with("GET", "http://fakeapi.com/test-endpoint", json=None, params=None)
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert response_data == expected_response_data

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

        response_data = make_api_request("POST", "/create-item", json_data=request_data)

    mock_client_instance.request.assert_called_once_with("POST", "http://fakeapi.com/create-item", json=request_data, params=None)
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert response_data == expected_response_data

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

        # Expect typer.Exit to be raised
        with pytest.raises(typer.Exit) as excinfo:
            make_api_request("GET", "/not-found")

    # Assertions
    assert excinfo.value.exit_code == 1
    mock_client_instance.request.assert_called_once_with("GET", "http://fakeapi.com/not-found", json=None, params=None)
    mock_response.raise_for_status.assert_called_once()
    # Check error console output (adjust based on actual implementation)
    mock_error_console.print.assert_called_once_with(f"Error from server ({status_code}): {error_detail.get('detail', error_text)}")

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

        # Expect typer.Exit to be raised
        with pytest.raises(typer.Exit) as excinfo:
            make_api_request("GET", "/unexpected")

    # Assertions
    assert excinfo.value.exit_code == 1
    mock_client_instance.request.assert_called_once_with("GET", "http://fakeapi.com/unexpected", json=None, params=None)
    # Check error console output
    mock_error_console.print.assert_called_once_with(f"An unexpected error occurred: {unexpected_error}")