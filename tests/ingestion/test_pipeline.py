import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

# Assuming config values are needed and potentially mocked
from philograph import config
from philograph.ingestion import pipeline
from philograph.data_access import db_layer # For mocking types if needed

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


# --- Fixtures (if needed later) ---


# --- Tests for get_embeddings_in_batches ---

async def test_get_embeddings_in_batches_empty_input():
    """
    Test that get_embeddings_in_batches returns an empty list for empty input.
    """
    # Red Phase: Write a failing test (or trivially passing test for empty case)
    result = await pipeline.get_embeddings_in_batches([])
    assert result == []
@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_success(mock_make_request):
    """
    Test successful embedding generation for a single batch.
    """
    # Red Phase: Write the test for the success case
    chunks_data = [
        (1, "This is chunk 1.", 0),
        (1, "This is chunk 2.", 1),
    ]
    expected_dimension = config.TARGET_EMBEDDING_DIMENSION # Use configured dimension
    mock_embedding_1 = [0.1] * expected_dimension
    mock_embedding_2 = [0.2] * expected_dimension
    expected_embeddings = [mock_embedding_1, mock_embedding_2]

    # Mock the response from httpx client
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    # The json() method needs to be an async function returning the expected structure
    async def mock_json():
        return {
            "data": [
                {"embedding": mock_embedding_1},
                {"embedding": mock_embedding_2},
            ],
            "model": "mock_model",
            "usage": {"prompt_tokens": 10, "total_tokens": 10}
        }
    mock_response.json = mock_json
    mock_response.raise_for_status = MagicMock() # Does nothing on success

    mock_make_request.return_value = mock_response

    # Call the function
    result = await pipeline.get_embeddings_in_batches(chunks_data, batch_size=5) # Batch size > len(chunks)

    # Assertions
    assert result == expected_embeddings
    mock_make_request.assert_called_once()
    call_args, call_kwargs = mock_make_request.call_args
    assert call_args[0] == "POST"
    assert call_args[1] == f"{config.LITELLM_PROXY_URL}/embeddings"
    assert call_kwargs['json_data']['model'] == config.EMBEDDING_MODEL_NAME
    assert call_kwargs['json_data']['input'] == ["This is chunk 1.", "This is chunk 2."]
    assert call_kwargs['timeout'] == 120.0
    # Check for Authorization header if API key is configured (optional)
    if config.LITELLM_API_KEY:
        assert "Authorization" in call_kwargs['headers']
        assert call_kwargs['headers']["Authorization"] == f"Bearer {config.LITELLM_API_KEY}"
@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_http_status_error(mock_make_request):
    """
    Test handling of HTTPStatusError during embedding generation.
    """
    # Red Phase: Test HTTP error handling
    chunks_data = [(1, "Chunk text", 0)]

    # Mock the response to raise HTTPStatusError
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.request = MagicMock(spec=httpx.Request) # Needed for HTTPStatusError
    error = httpx.HTTPStatusError(
        "Server error", request=mock_response.request, response=mock_response
    )
    # Configure raise_for_status to raise the error
    mock_response.raise_for_status = MagicMock(side_effect=error)

    mock_make_request.return_value = mock_response

    # Expect a RuntimeError to be raised by the function
    with pytest.raises(RuntimeError, match=r"Embedding generation failed \(HTTP 500\)"):
        await pipeline.get_embeddings_in_batches(chunks_data, batch_size=1)

    mock_make_request.assert_called_once()

@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_request_error(mock_make_request):
    """
    Test handling of RequestError during embedding generation.
    """
    # Red Phase: Test RequestError handling
    chunks_data = [(1, "Chunk text", 0)]

    # Mock make_async_request to raise RequestError
    error = httpx.RequestError("Network error", request=MagicMock(spec=httpx.Request))
    mock_make_request.side_effect = error

    # Expect a RuntimeError to be raised by the function
    with pytest.raises(RuntimeError, match=r"Embedding generation failed \(Request Error\)"):
        await pipeline.get_embeddings_in_batches(chunks_data, batch_size=1)

    mock_make_request.assert_called_once()
# TODO: Add more tests for get_embeddings_in_batches (success, errors, batching)
@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_missing_data_field(mock_make_request):
    """
    Test handling of a successful response missing the 'data' field.
    """
    # Red Phase: Test response validation (missing 'data')
    chunks_data = [(1, "Chunk text", 0)]

    # Mock the response from httpx client - successful status, but bad body
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    async def mock_json():
        return {
            # Missing 'data' field
            "model": "mock_model",
            "usage": {"prompt_tokens": 5, "total_tokens": 5}
        }
    mock_response.json = mock_json
    mock_response.raise_for_status = MagicMock() # Does nothing on success

    mock_make_request.return_value = mock_response

    # Expect a RuntimeError due to processing error
    with pytest.raises(RuntimeError, match=r"Embedding generation failed \(Processing Error\)"):
        await pipeline.get_embeddings_in_batches(chunks_data, batch_size=1)

    mock_make_request.assert_called_once()

@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_mismatched_data_length(mock_make_request):
    """
    Test handling of a response with mismatched 'data' length.
    """
    # Red Phase: Test response validation (mismatched 'data' length)
    chunks_data = [
        (1, "This is chunk 1.", 0),
        (1, "This is chunk 2.", 1),
    ]
    expected_dimension = config.TARGET_EMBEDDING_DIMENSION
    mock_embedding_1 = [0.1] * expected_dimension
    # Only return one embedding when two were requested

    # Mock the response from httpx client
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    async def mock_json():
        return {
            "data": [
                {"embedding": mock_embedding_1},
                # Missing embedding for chunk 2
            ],
            "model": "mock_model",
            "usage": {"prompt_tokens": 10, "total_tokens": 5} # Usage might be inaccurate
        }
    mock_response.json = mock_json
    mock_response.raise_for_status = MagicMock()

    mock_make_request.return_value = mock_response

    # Expect a RuntimeError due to processing error (specifically ValueError initially)
    with pytest.raises(RuntimeError, match=r"Embedding generation failed \(Processing Error\)"):
        await pipeline.get_embeddings_in_batches(chunks_data, batch_size=5)

    mock_make_request.assert_called_once()
@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_multiple_batches(mock_make_request):
    """
    Test successful embedding generation requiring multiple batches.
    """
    batch_size = 2
    chunks_data = [
        (1, "Chunk 1 text.", 0),
        (1, "Chunk 2 text.", 1),
        (2, "Chunk 3 text.", 0),
        (2, "Chunk 4 text.", 1),
        (3, "Chunk 5 text.", 0),
    ]
    expected_dimension = config.TARGET_EMBEDDING_DIMENSION
    mock_embeddings = [
        [float(i+1)/10.0] * expected_dimension for i in range(len(chunks_data))
    ]
    expected_result = mock_embeddings

    # Mock responses for each batch
    async def mock_response_batch_1(*args, **kwargs):
        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.status_code = 200
        async def mock_json():
            return {
                "data": [
                    {"embedding": mock_embeddings[0]},
                    {"embedding": mock_embeddings[1]},
                ], "model": "mock", "usage": {}
            }
        mock_resp.json = mock_json
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    async def mock_response_batch_2(*args, **kwargs):
        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.status_code = 200
        async def mock_json():
            return {
                "data": [
                    {"embedding": mock_embeddings[2]},
                    {"embedding": mock_embeddings[3]},
                ], "model": "mock", "usage": {}
            }
        mock_resp.json = mock_json
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    async def mock_response_batch_3(*args, **kwargs):
        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.status_code = 200
        async def mock_json():
            return {
                "data": [
                    {"embedding": mock_embeddings[4]},
                ], "model": "mock", "usage": {}
            }
        mock_resp.json = mock_json
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    # Set the side effects for consecutive calls
    mock_make_request.side_effect = [
        await mock_response_batch_1(),
        await mock_response_batch_2(),
        await mock_response_batch_3(),
    ]

    # Call the function
    result = await pipeline.get_embeddings_in_batches(chunks_data, batch_size=batch_size)

    # Assertions
    assert result == expected_result
    assert mock_make_request.call_count == 3

    # Check calls (optional, but good for verification)
    call1_args, call1_kwargs = mock_make_request.call_args_list[0]
    assert call1_kwargs['json_data']['input'] == ["Chunk 1 text.", "Chunk 2 text."]
@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_invalid_dimension(mock_make_request):
    """
    Test handling of embeddings received with an incorrect dimension.
    """
    # Red Phase: Test dimension validation
    chunks_data = [(1, "Chunk text", 0)]
    correct_dimension = config.TARGET_EMBEDDING_DIMENSION
    invalid_dimension = correct_dimension - 1 # Or any incorrect dimension
    mock_invalid_embedding = [0.5] * invalid_dimension

    # Mock the response from httpx client
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    async def mock_json():
        return {
            "data": [
                {"embedding": mock_invalid_embedding},
            ],
            "model": "mock_model",
            "usage": {"prompt_tokens": 5, "total_tokens": 5}
        }
    mock_response.json = mock_json
    mock_response.raise_for_status = MagicMock()

    mock_make_request.return_value = mock_response

    # Expect a RuntimeError due to processing error (specifically ValueError initially)
    with pytest.raises(RuntimeError, match=r"Embedding generation failed \(Processing Error\)"):
        await pipeline.get_embeddings_in_batches(chunks_data, batch_size=1)

    mock_make_request.assert_called_once()
    # No need to check call_args_list[1] as only one call is expected
    # Removed leftover assertion from previous test
    # Removed another leftover assertion from previous test
    # Removed final leftover assertion from previous test
# --- Tests for extract_content_and_metadata ---

@patch("philograph.ingestion.pipeline.text_processing.call_grobid_extractor", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.file_utils.get_file_extension")
async def test_extract_content_and_metadata_pdf(mock_get_ext, mock_call_grobid):
    """
    Test that extract_content_and_metadata calls call_grobid_extractor for PDF files.
    """
    # Red Phase: Test PDF dispatch
    mock_path = Path("/fake/path/document.pdf")
    mock_get_ext.return_value = ".pdf"
    expected_result = {"metadata": {"title": "PDF Title"}, "text_by_section": {"Abstract": "Text"}}
    mock_call_grobid.return_value = expected_result

    result = await pipeline.extract_content_and_metadata(mock_path)

    assert result == expected_result
    mock_get_ext.assert_called_once_with(mock_path)
@patch("philograph.ingestion.pipeline.text_processing.extract_epub_content")
@patch("philograph.ingestion.pipeline.file_utils.get_file_extension")
async def test_extract_content_and_metadata_epub(mock_get_ext, mock_extract_epub):
    """
    Test that extract_content_and_metadata calls extract_epub_content for EPUB files.
    """
    # Red Phase: Test EPUB dispatch
    mock_path = Path("/fake/path/document.epub")
    mock_get_ext.return_value = ".epub"
    expected_result = {"metadata": {"title": "EPUB Title"}, "text_by_section": {"Chapter 1": "Text"}}
    # Note: extract_epub_content is synchronous, so mock its return value directly
    mock_extract_epub.return_value = expected_result

    result = await pipeline.extract_content_and_metadata(mock_path)

    assert result == expected_result
    mock_get_ext.assert_called_once_with(mock_path)
    mock_extract_epub.assert_called_once_with(mock_path)
    # Removed incorrect assertion for mock_call_grobid
@pytest.mark.parametrize("ext", [".txt", ".md"])
@patch("philograph.ingestion.pipeline.text_processing.extract_text_content")
@patch("philograph.ingestion.pipeline.file_utils.get_file_extension")
async def test_extract_content_and_metadata_text(mock_get_ext, mock_extract_text, ext):
    """
    Test that extract_content_and_metadata calls extract_text_content for TXT/MD files.
    """
    # Red Phase: Test TXT/MD dispatch
    mock_path = Path(f"/fake/path/document{ext}")
    mock_get_ext.return_value = ext
    expected_result = {"metadata": {}, "text_by_section": {"body": "Plain text content."}}
    # Note: extract_text_content is synchronous
    mock_extract_text.return_value = expected_result

    result = await pipeline.extract_content_and_metadata(mock_path)

    assert result == expected_result
    mock_get_ext.assert_called_once_with(mock_path)
    mock_extract_text.assert_called_once_with(mock_path)
@patch("philograph.ingestion.pipeline.file_utils.get_file_extension")
async def test_extract_content_and_metadata_unsupported(mock_get_ext):
    """
    Test that extract_content_and_metadata returns None for unsupported file types.
    """
    # Red Phase: Test unsupported dispatch
    mock_path = Path("/fake/path/document.zip")
    mock_get_ext.return_value = ".zip"

    result = await pipeline.extract_content_and_metadata(mock_path)

    assert result is None
    mock_get_ext.assert_called_once_with(mock_path)
# --- Tests for extract_content_and_metadata ---

# TODO: Add tests for extract_content_and_metadata (dispatch logic, mocking text_processing)

# --- Tests for process_document ---

# TODO: Add tests for process_document (single file, directory, errors, existing doc)
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

# Assuming config values are needed and potentially mocked
from philograph import config
from philograph.ingestion import pipeline
from philograph.data_access import db_layer # For mocking types if needed
from philograph.utils import text_processing # Ensure this is imported

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


# --- Fixtures (if needed later) ---


# --- Tests for get_embeddings_in_batches ---

async def test_get_embeddings_in_batches_empty_input():
    """
    Test that get_embeddings_in_batches returns an empty list for empty input.
    """
    # Red Phase: Write a failing test (or trivially passing test for empty case)
    result = await pipeline.get_embeddings_in_batches([])
    assert result == []
@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_success(mock_make_request):
    """
    Test successful embedding generation for a single batch.
    """
    # Red Phase: Write the test for the success case
    chunks_data = [
        (1, "This is chunk 1.", 0),
        (1, "This is chunk 2.", 1),
    ]
    expected_dimension = config.TARGET_EMBEDDING_DIMENSION # Use configured dimension
    mock_embedding_1 = [0.1] * expected_dimension
    mock_embedding_2 = [0.2] * expected_dimension
    expected_embeddings = [mock_embedding_1, mock_embedding_2]

    # Mock the response from httpx client
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    # The json() method needs to be an async function returning the expected structure
    async def mock_json():
        return {
            "data": [
                {"embedding": mock_embedding_1},
                {"embedding": mock_embedding_2},
            ],
            "model": "mock_model",
            "usage": {"prompt_tokens": 10, "total_tokens": 10}
        }
    mock_response.json = mock_json
    mock_response.raise_for_status = MagicMock() # Does nothing on success

    mock_make_request.return_value = mock_response

    # Call the function
    result = await pipeline.get_embeddings_in_batches(chunks_data, batch_size=5) # Batch size > len(chunks)

    # Assertions
    assert result == expected_embeddings
    mock_make_request.assert_called_once()
    call_args, call_kwargs = mock_make_request.call_args
    assert call_args[0] == "POST"
    assert call_args[1] == f"{config.LITELLM_PROXY_URL}/embeddings"
    assert call_kwargs['json_data']['model'] == config.EMBEDDING_MODEL_NAME
    assert call_kwargs['json_data']['input'] == ["This is chunk 1.", "This is chunk 2."]
    assert call_kwargs['timeout'] == 120.0
    # Check for Authorization header if API key is configured (optional)
    if config.LITELLM_API_KEY:
        assert "Authorization" in call_kwargs['headers']
        assert call_kwargs['headers']["Authorization"] == f"Bearer {config.LITELLM_API_KEY}"
@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_http_status_error(mock_make_request):
    """
    Test handling of HTTPStatusError during embedding generation.
    """
    # Red Phase: Test HTTP error handling
    chunks_data = [(1, "Chunk text", 0)]

    # Mock the response to raise HTTPStatusError
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.request = MagicMock(spec=httpx.Request) # Needed for HTTPStatusError
    error = httpx.HTTPStatusError(
        "Server error", request=mock_response.request, response=mock_response
    )
    # Configure raise_for_status to raise the error
    mock_response.raise_for_status = MagicMock(side_effect=error)

    mock_make_request.return_value = mock_response

    # Expect a RuntimeError to be raised by the function
    with pytest.raises(RuntimeError, match=r"Embedding generation failed \(HTTP 500\)"):
        await pipeline.get_embeddings_in_batches(chunks_data, batch_size=1)

    mock_make_request.assert_called_once()

@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_request_error(mock_make_request):
    """
    Test handling of RequestError during embedding generation.
    """
    # Red Phase: Test RequestError handling
    chunks_data = [(1, "Chunk text", 0)]

    # Mock make_async_request to raise RequestError
    error = httpx.RequestError("Network error", request=MagicMock(spec=httpx.Request))
    mock_make_request.side_effect = error

    # Expect a RuntimeError to be raised by the function
    with pytest.raises(RuntimeError, match=r"Embedding generation failed \(Request Error\)"):
        await pipeline.get_embeddings_in_batches(chunks_data, batch_size=1)

    mock_make_request.assert_called_once()
# TODO: Add more tests for get_embeddings_in_batches (success, errors, batching)
@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_missing_data_field(mock_make_request):
    """
    Test handling of a successful response missing the 'data' field.
    """
    # Red Phase: Test response validation (missing 'data')
    chunks_data = [(1, "Chunk text", 0)]

    # Mock the response from httpx client - successful status, but bad body
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    async def mock_json():
        return {
            # Missing 'data' field
            "model": "mock_model",
            "usage": {"prompt_tokens": 5, "total_tokens": 5}
        }
    mock_response.json = mock_json
    mock_response.raise_for_status = MagicMock() # Does nothing on success

    mock_make_request.return_value = mock_response

    # Expect a RuntimeError due to processing error
    with pytest.raises(RuntimeError, match=r"Embedding generation failed \(Processing Error\)"):
        await pipeline.get_embeddings_in_batches(chunks_data, batch_size=1)

    mock_make_request.assert_called_once()

@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_mismatched_data_length(mock_make_request):
    """
    Test handling of a response with mismatched 'data' length.
    """
    # Red Phase: Test response validation (mismatched 'data' length)
    chunks_data = [
        (1, "This is chunk 1.", 0),
        (1, "This is chunk 2.", 1),
    ]
    expected_dimension = config.TARGET_EMBEDDING_DIMENSION
    mock_embedding_1 = [0.1] * expected_dimension
    # Only return one embedding when two were requested

    # Mock the response from httpx client
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    async def mock_json():
        return {
            "data": [
                {"embedding": mock_embedding_1},
                # Missing embedding for chunk 2
            ],
            "model": "mock_model",
            "usage": {"prompt_tokens": 10, "total_tokens": 5} # Usage might be inaccurate
        }
    mock_response.json = mock_json
    mock_response.raise_for_status = MagicMock()

    mock_make_request.return_value = mock_response

    # Expect a RuntimeError due to processing error (specifically ValueError initially)
    with pytest.raises(RuntimeError, match=r"Embedding generation failed \(Processing Error\)"):
        await pipeline.get_embeddings_in_batches(chunks_data, batch_size=5)

    mock_make_request.assert_called_once()
@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_multiple_batches(mock_make_request):
    """
    Test successful embedding generation requiring multiple batches.
    """
    batch_size = 2
    chunks_data = [
        (1, "Chunk 1 text.", 0),
        (1, "Chunk 2 text.", 1),
        (2, "Chunk 3 text.", 0),
        (2, "Chunk 4 text.", 1),
        (3, "Chunk 5 text.", 0),
    ]
    expected_dimension = config.TARGET_EMBEDDING_DIMENSION
    mock_embeddings = [
        [float(i+1)/10.0] * expected_dimension for i in range(len(chunks_data))
    ]
    expected_result = mock_embeddings

    # Mock responses for each batch
    async def mock_response_batch_1(*args, **kwargs):
        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.status_code = 200
        async def mock_json():
            return {
                "data": [
                    {"embedding": mock_embeddings[0]},
                    {"embedding": mock_embeddings[1]},
                ], "model": "mock", "usage": {}
            }
        mock_resp.json = mock_json
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    async def mock_response_batch_2(*args, **kwargs):
        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.status_code = 200
        async def mock_json():
            return {
                "data": [
                    {"embedding": mock_embeddings[2]},
                    {"embedding": mock_embeddings[3]},
                ], "model": "mock", "usage": {}
            }
        mock_resp.json = mock_json
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    async def mock_response_batch_3(*args, **kwargs):
        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.status_code = 200
        async def mock_json():
            return {
                "data": [
                    {"embedding": mock_embeddings[4]},
                ], "model": "mock", "usage": {}
            }
        mock_resp.json = mock_json
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    # Set the side effects for consecutive calls
    mock_make_request.side_effect = [
        await mock_response_batch_1(),
        await mock_response_batch_2(),
        await mock_response_batch_3(),
    ]

    # Call the function
    result = await pipeline.get_embeddings_in_batches(chunks_data, batch_size=batch_size)

    # Assertions
    assert result == expected_result
    assert mock_make_request.call_count == 3

    # Check calls (optional, but good for verification)
    call1_args, call1_kwargs = mock_make_request.call_args_list[0]
    assert call1_kwargs['json_data']['input'] == ["Chunk 1 text.", "Chunk 2 text."]
@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_invalid_dimension(mock_make_request):
    """
    Test handling of embeddings received with an incorrect dimension.
    """
    # Red Phase: Test dimension validation
    chunks_data = [(1, "Chunk text", 0)]
    correct_dimension = config.TARGET_EMBEDDING_DIMENSION
    invalid_dimension = correct_dimension - 1 # Or any incorrect dimension
    mock_invalid_embedding = [0.5] * invalid_dimension

    # Mock the response from httpx client
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    async def mock_json():
        return {
            "data": [
                {"embedding": mock_invalid_embedding},
            ],
            "model": "mock_model",
            "usage": {"prompt_tokens": 5, "total_tokens": 5}
        }
    mock_response.json = mock_json
    mock_response.raise_for_status = MagicMock()

    mock_make_request.return_value = mock_response

    # Expect a RuntimeError due to processing error (specifically ValueError initially)
    with pytest.raises(RuntimeError, match=r"Embedding generation failed \(Processing Error\)"):
        await pipeline.get_embeddings_in_batches(chunks_data, batch_size=1)

    mock_make_request.assert_called_once()
    # No need to check call_args_list[1] as only one call is expected
    # Removed leftover assertion from previous test
    # Removed another leftover assertion from previous test
    # Removed final leftover assertion from previous test
# --- Tests for extract_content_and_metadata ---

@patch("philograph.ingestion.pipeline.text_processing.call_grobid_extractor", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.file_utils.get_file_extension")
async def test_extract_content_and_metadata_pdf(mock_get_ext, mock_call_grobid):
    """
    Test that extract_content_and_metadata calls call_grobid_extractor for PDF files.
    """
    # Red Phase: Test PDF dispatch
    mock_path = Path("/fake/path/document.pdf")
    mock_get_ext.return_value = ".pdf"
    expected_result = {"metadata": {"title": "PDF Title"}, "text_by_section": {"Abstract": "Text"}}
    mock_call_grobid.return_value = expected_result

    result = await pipeline.extract_content_and_metadata(mock_path)

    assert result == expected_result
    mock_get_ext.assert_called_once_with(mock_path)
@patch("philograph.ingestion.pipeline.text_processing.extract_epub_content")
@patch("philograph.ingestion.pipeline.file_utils.get_file_extension")
async def test_extract_content_and_metadata_epub(mock_get_ext, mock_extract_epub):
    """
    Test that extract_content_and_metadata calls extract_epub_content for EPUB files.
    """
    # Red Phase: Test EPUB dispatch
    mock_path = Path("/fake/path/document.epub")
    mock_get_ext.return_value = ".epub"
    expected_result = {"metadata": {"title": "EPUB Title"}, "text_by_section": {"Chapter 1": "Text"}}
    # Note: extract_epub_content is synchronous, so mock its return value directly
    mock_extract_epub.return_value = expected_result

    result = await pipeline.extract_content_and_metadata(mock_path)

    assert result == expected_result
    mock_get_ext.assert_called_once_with(mock_path)
    mock_extract_epub.assert_called_once_with(mock_path)
    # Removed incorrect assertion for mock_call_grobid
@pytest.mark.parametrize("ext", [".txt", ".md"])
@patch("philograph.ingestion.pipeline.text_processing.extract_text_content")
@patch("philograph.ingestion.pipeline.file_utils.get_file_extension")
async def test_extract_content_and_metadata_text(mock_get_ext, mock_extract_text, ext):
    """
    Test that extract_content_and_metadata calls extract_text_content for TXT/MD files.
    """
    # Red Phase: Test TXT/MD dispatch
    mock_path = Path(f"/fake/path/document{ext}")
    mock_get_ext.return_value = ext
    expected_result = {"metadata": {}, "text_by_section": {"body": "Plain text content."}}
    # Note: extract_text_content is synchronous
    mock_extract_text.return_value = expected_result

    result = await pipeline.extract_content_and_metadata(mock_path)

    assert result == expected_result
    mock_get_ext.assert_called_once_with(mock_path)
    mock_extract_text.assert_called_once_with(mock_path)
@patch("philograph.ingestion.pipeline.file_utils.get_file_extension")
async def test_extract_content_and_metadata_unsupported(mock_get_ext):
    """
    Test that extract_content_and_metadata returns None for unsupported file types.
    """
    # Red Phase: Test unsupported dispatch
    mock_path = Path("/fake/path/document.zip")
    mock_get_ext.return_value = ".zip"

    result = await pipeline.extract_content_and_metadata(mock_path)

    assert result is None
    mock_get_ext.assert_called_once_with(mock_path)
# --- Tests for extract_content_and_metadata ---

# TODO: Add tests for extract_content_and_metadata (dispatch logic, mocking text_processing)

# --- Tests for process_document ---

@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.db_layer.get_db_connection")
@patch("philograph.ingestion.pipeline.extract_content_and_metadata", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.get_embeddings_in_batches", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.text_processing.chunk_text_semantically")
@patch("philograph.ingestion.pipeline.text_processing.parse_references", new_callable=AsyncMock)
@patch("pathlib.Path.resolve") # Mock resolve to prevent FileNotFoundError
async def test_process_document_single_pdf_success(
    mock_resolve, # Add mock argument
    mock_parse_references,
    mock_chunk_text,
    mock_get_embeddings,
    mock_extract,
    mock_get_db_conn,
    mock_check_file,
    mock_check_dir,
):
    """
    Test successfully processing a single new PDF document.
    """
    relative_path_str = "subdir/document1.pdf"
    relative_path_obj = Path(relative_path_str)
    full_path = Path("/test/source") / relative_path_obj

    # --- Mock Setup ---
    mock_resolve.return_value = full_path # Configure mock resolve
    mock_check_dir.return_value = False
    mock_check_file.return_value = True

    # Mock DB connection and cursor
    mock_conn = AsyncMock()
    mock_cursor = AsyncMock()
    # Mock the async context manager returned by cursor()
    mock_cursor_cm = AsyncMock()
    mock_cursor_cm.__aenter__.return_value = mock_cursor
    # Make conn.cursor a MagicMock that returns the async context manager mock
    mock_conn.cursor = MagicMock(return_value=mock_cursor_cm)
    # Mock context manager entry for get_db_connection
    mock_get_db_conn.return_value.__aenter__.return_value = mock_conn

    # Mock DB calls within the connection context
    mock_check_doc_exists = AsyncMock(return_value=False)
    mock_add_doc = AsyncMock(return_value=123) # Mock document ID
    mock_add_section = AsyncMock(side_effect=[1, 2]) # Mock section IDs
    mock_add_chunks = AsyncMock(return_value=None)
    mock_add_ref = AsyncMock(return_value=None)
    # Mock the fetchone for finding the first chunk ID for reference linking
    mock_cursor.fetchone = AsyncMock(return_value={'id': 1001}) # Mock chunk ID

    # Assign mocks to the connection object's methods (or patch db_layer directly)
    # Patching db_layer directly might be cleaner
    with patch("philograph.ingestion.pipeline.db_layer.check_document_exists", mock_check_doc_exists), \
         patch("philograph.ingestion.pipeline.db_layer.add_document", mock_add_doc), \
         patch("philograph.ingestion.pipeline.db_layer.add_section", mock_add_section), \
         patch("philograph.ingestion.pipeline.db_layer.add_chunks_batch", mock_add_chunks), \
         patch("philograph.ingestion.pipeline.db_layer.add_reference", mock_add_ref):

        # Mock Extraction
        mock_extract.return_value = {
            "metadata": {"title": "Test PDF", "author": "Tester"},
            "text_by_section": {
                "Abstract": "This is the abstract.",
                "Section 1": "This is the first section content."
            },
            "references_raw": ["Ref 1", "Ref 2"]
        }

        # Mock Chunking
        mock_chunk_text.side_effect = [
            ["Abstract chunk 1"], # Chunks for Abstract
            ["Section 1 chunk 1", "Section 1 chunk 2"] # Chunks for Section 1
        ]

        # Mock Embeddings
        mock_embeddings = [[0.1]*config.TARGET_EMBEDDING_DIMENSION, [0.2]*config.TARGET_EMBEDDING_DIMENSION, [0.3]*config.TARGET_EMBEDDING_DIMENSION]
        mock_get_embeddings.return_value = mock_embeddings

        # Mock Reference Parsing
        mock_parse_references.return_value = [
            {"title": "Ref Title 1", "author": "Ref Author 1"},
            {"title": "Ref Title 2", "author": "Ref Author 2"}
        ]

        # --- Call Function ---
        result = await pipeline.process_document(relative_path_str)

    # --- Assertions ---
    assert result == {"status": "Success", "document_id": 123}

    # Check mocks were called correctly
    mock_check_dir.assert_called_once_with(full_path)
    mock_check_file.assert_called_once_with(full_path)
    assert mock_get_db_conn.call_count == 2 # Called twice: once for check, once for transaction
    mock_check_doc_exists.assert_called_once_with(mock_conn, relative_path_str)
    mock_extract.assert_called_once_with(full_path)
    mock_add_doc.assert_called_once_with(
        mock_conn, "Test PDF", "Tester", None, relative_path_str, {"title": "Test PDF", "author": "Tester"}
    )
    assert mock_add_section.call_count == 2
    mock_add_section.assert_any_call(mock_conn, 123, "Abstract", 0, 0)
    mock_add_section.assert_any_call(mock_conn, 123, "Section 1", 0, 1)

    assert mock_chunk_text.call_count == 2
    mock_chunk_text.assert_any_call("This is the abstract.", config.TARGET_CHUNK_SIZE)
    mock_chunk_text.assert_any_call("This is the first section content.", config.TARGET_CHUNK_SIZE)

    mock_get_embeddings.assert_called_once()
    # Check the structure passed to get_embeddings
    expected_embedding_input = [
        (1, "Abstract chunk 1", 0), # section_id 1 from first mock_add_section call
        (2, "Section 1 chunk 1", 0), # section_id 2 from second mock_add_section call
        (2, "Section 1 chunk 2", 1),
    ]
    call_args, _ = mock_get_embeddings.call_args
    assert call_args[0] == expected_embedding_input

    mock_add_chunks.assert_called_once()
    # Check the structure passed to add_chunks_batch
    expected_chunks_input = [
        (1, "Abstract chunk 1", 0, mock_embeddings[0]),
        (2, "Section 1 chunk 1", 0, mock_embeddings[1]),
        (2, "Section 1 chunk 2", 1, mock_embeddings[2]),
    ]
    call_args, _ = mock_add_chunks.call_args
    assert call_args[0] == mock_conn
    assert call_args[1] == expected_chunks_input

    mock_parse_references.assert_called_once_with(["Ref 1", "Ref 2"])
    # Check cursor execute for finding chunk id
    mock_cursor.execute.assert_called_once_with(
        "SELECT id FROM chunks WHERE section_id IN (SELECT id FROM sections WHERE doc_id = %s) ORDER BY sequence ASC LIMIT 1;",
        (123,)
    )
    mock_cursor.fetchone.assert_called_once()
    # Check add_reference calls
    assert mock_add_ref.call_count == 2
    mock_add_ref.assert_any_call(mock_conn, 1001, {"title": "Ref Title 1", "author": "Ref Author 1"})
    mock_add_ref.assert_any_call(mock_conn, 1001, {"title": "Ref Title 2", "author": "Ref Author 2"})

# TODO: Add tests for process_document (single file, directory, errors, existing doc)
@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.db_layer.get_db_connection")
@patch("philograph.ingestion.pipeline.extract_content_and_metadata", new_callable=AsyncMock) # Still need to mock this even if not called
@patch("pathlib.Path.resolve") # Mock resolve
async def test_process_document_existing_document_skipped(
    mock_resolve, # Add mock argument
    mock_extract,
    mock_get_db_conn,
    mock_check_file,
    mock_check_dir,
):
    """
    Test that processing is skipped if the document already exists in the DB.
    """
    relative_path_str = "existing_doc.txt"
    relative_path_obj = Path(relative_path_str)
    full_path = Path("/test/source") / relative_path_obj

    # --- Mock Setup ---
    mock_resolve.return_value = full_path # Configure mock resolve
    mock_check_dir.return_value = False
    mock_check_file.return_value = True

    # Mock DB connection
    mock_conn = AsyncMock()
    mock_get_db_conn.return_value.__aenter__.return_value = mock_conn

    # Mock DB check_document_exists to return True
    mock_check_doc_exists = AsyncMock(return_value=True)

    with patch("philograph.ingestion.pipeline.db_layer.check_document_exists", mock_check_doc_exists):
        # --- Call Function ---
        result = await pipeline.process_document(relative_path_str)

    # --- Assertions ---
    assert result == {"status": "Skipped", "message": "Document already exists"}

    # Check mocks
    mock_check_dir.assert_called_once_with(full_path)
    mock_check_file.assert_called_once_with(full_path)
    mock_get_db_conn.assert_called_once() # Only called once for the check
    mock_check_doc_exists.assert_called_once_with(mock_conn, relative_path_str)

    # Ensure extraction and further processing steps were NOT called
    mock_extract.assert_not_called()
@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.db_layer.get_db_connection") # Mock even if not expected to be called
@patch("philograph.ingestion.pipeline.extract_content_and_metadata", new_callable=AsyncMock)
@patch("pathlib.Path.resolve") # Mock resolve
async def test_process_document_file_not_found(
    mock_resolve, # Add mock argument
    mock_extract,
    mock_get_db_conn,
    mock_check_file,
    mock_check_dir,
):
    """
    Test handling when the specified file path does not exist.
    """
    relative_path_str = "non_existent_doc.pdf"
    relative_path_obj = Path(relative_path_str)
    full_path = Path("/test/source") / relative_path_obj

    # --- Mock Setup ---
    # Mock resolve to raise FileNotFoundError *after* the initial path construction
    # This simulates the case where resolve(strict=True) fails
    mock_resolve.side_effect = FileNotFoundError
    mock_check_dir.return_value = False
    mock_check_file.return_value = False # File does not exist

    # --- Call Function ---
    result = await pipeline.process_document(relative_path_str)

    # --- Assertions ---
    assert result == {"status": "Error", "message": "File or directory not found"}

    # Check mocks
    # mock_check_dir should NOT be called because resolve failed first
    mock_check_dir.assert_not_called()
    mock_check_file.assert_not_called() # Also should not be called

    # Ensure DB and extraction were NOT called
    mock_get_db_conn.assert_not_called()
    mock_extract.assert_not_called()
@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.db_layer.get_db_connection")
@patch("philograph.ingestion.pipeline.extract_content_and_metadata", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.db_layer.add_document", new_callable=AsyncMock) # Mock add_document to check it's not called
@patch("pathlib.Path.resolve") # Mock resolve
async def test_process_document_extraction_error(
    mock_resolve, # Add mock argument
    mock_add_doc, # Mocked to check it's not called
    mock_extract,
    mock_get_db_conn,
    mock_check_file,
    mock_check_dir,
):
    """
    Test handling when extract_content_and_metadata raises an error.
    """
    relative_path_str = "doc_extract_error.pdf"
    relative_path_obj = Path(relative_path_str)
    full_path = Path("/test/source") / relative_path_obj

    # --- Mock Setup ---
    mock_resolve.return_value = full_path # Configure mock resolve
    mock_check_dir.return_value = False
    mock_check_file.return_value = True

    # Mock DB connection
    mock_conn = AsyncMock()
    mock_get_db_conn.return_value.__aenter__.return_value = mock_conn

    # Mock DB check_document_exists to return False (new document)
    mock_check_doc_exists = AsyncMock(return_value=False)

    # Mock Extraction to raise an error
    mock_extract.side_effect = Exception("GROBID failed")

    with patch("philograph.ingestion.pipeline.db_layer.check_document_exists", mock_check_doc_exists):
        # --- Call Function ---
        result = await pipeline.process_document(relative_path_str)

    # --- Assertions ---
    assert result == {"status": "Error", "message": "Extraction failed: GROBID failed"}

    # Check mocks
    mock_check_dir.assert_called_once_with(full_path)
    mock_check_file.assert_called_once_with(full_path)
    mock_get_db_conn.assert_called_once() # Called once for the check
    mock_check_doc_exists.assert_called_once_with(mock_conn, relative_path_str)
    mock_extract.assert_called_once_with(full_path)

    # Ensure DB add_document was NOT called
    mock_add_doc.assert_not_called()
@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.db_layer.get_db_connection")
@patch("philograph.ingestion.pipeline.extract_content_and_metadata", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.get_embeddings_in_batches", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.text_processing.chunk_text_semantically")
# Mock add_chunks_batch to check it's not called after embedding error
@patch("philograph.ingestion.pipeline.db_layer.add_chunks_batch", new_callable=AsyncMock)
@patch("pathlib.Path.resolve") # Mock resolve
async def test_process_document_embedding_error(
    mock_resolve, # Add mock argument
    mock_add_chunks, # Mocked to check it's not called
    mock_chunk_text,
    mock_get_embeddings,
    mock_extract,
    mock_get_db_conn,
    mock_check_file,
    mock_check_dir,
):
    """
    Test handling when get_embeddings_in_batches raises an error.
    """
    relative_path_str = "doc_embed_error.pdf"
    relative_path_obj = Path(relative_path_str)
    full_path = Path("/test/source") / relative_path_obj

    # --- Mock Setup ---
    mock_resolve.return_value = full_path # Configure mock resolve
    mock_check_dir.return_value = False
    mock_check_file.return_value = True

    # Mock DB connection
    mock_conn = AsyncMock()
    mock_get_db_conn.return_value.__aenter__.return_value = mock_conn

    # Mock DB calls (assuming doc check passes and doc/section are added)
    mock_check_doc_exists = AsyncMock(return_value=False)
    mock_add_doc = AsyncMock(return_value=456) # Mock document ID
    mock_add_section = AsyncMock(return_value=3) # Mock section ID

    # Mock Extraction (successful)
    mock_extract.return_value = {
        "metadata": {"title": "Embed Error Doc"},
        "text_by_section": {"Intro": "Some text to embed."},
        "references_raw": []
    }

    # Mock Chunking (successful)
    mock_chunk_text.return_value = ["Chunk 1"]

    # Mock Embeddings to raise an error
    mock_get_embeddings.side_effect = RuntimeError("Embedding API down")

    with patch("philograph.ingestion.pipeline.db_layer.check_document_exists", mock_check_doc_exists), \
         patch("philograph.ingestion.pipeline.db_layer.add_document", mock_add_doc), \
         patch("philograph.ingestion.pipeline.db_layer.add_section", mock_add_section):

        # --- Call Function ---
        result = await pipeline.process_document(relative_path_str)

    # --- Assertions ---
    # Expecting the error to be caught and reported
    assert result == {"status": "Error", "message": "Ingestion transaction failed: Embedding generation failed: Embedding API down"}

    # Check mocks up to the point of failure
    mock_check_dir.assert_called_once_with(full_path)
    mock_check_file.assert_called_once_with(full_path)
    assert mock_get_db_conn.call_count == 2 # Check + Transaction
    mock_check_doc_exists.assert_called_once_with(mock_conn, relative_path_str)
    mock_extract.assert_called_once_with(full_path)
    mock_add_doc.assert_called_once()
    mock_add_section.assert_called_once()
    mock_chunk_text.assert_called_once()
    mock_get_embeddings.assert_called_once() # Should be called

    # Ensure indexing was NOT called
    mock_add_chunks.assert_not_called()
@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.db_layer.get_db_connection")
@patch("philograph.ingestion.pipeline.extract_content_and_metadata", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.get_embeddings_in_batches", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.text_processing.chunk_text_semantically")
@patch("philograph.ingestion.pipeline.db_layer.add_chunks_batch", new_callable=AsyncMock) # Mock to raise error
@patch("philograph.ingestion.pipeline.text_processing.parse_references", new_callable=AsyncMock) # Mock to check not called
@patch("pathlib.Path.resolve") # Mock resolve
async def test_process_document_indexing_error(
    mock_resolve, # Add mock argument
    mock_parse_references, # Mocked to check not called
    mock_add_chunks, # Mocked to raise error
    mock_chunk_text,
    mock_get_embeddings,
    mock_extract,
    mock_get_db_conn,
    mock_check_file,
    mock_check_dir,
):
    """
    Test handling when db_layer.add_chunks_batch raises an error.
    """
    relative_path_str = "doc_index_error.pdf"
    relative_path_obj = Path(relative_path_str)
    full_path = Path("/test/source") / relative_path_obj

    # --- Mock Setup ---
    mock_resolve.return_value = full_path # Configure mock resolve
    mock_check_dir.return_value = False
    mock_check_file.return_value = True

    # Mock DB connection
    mock_conn = AsyncMock()
    mock_get_db_conn.return_value.__aenter__.return_value = mock_conn

    # Mock DB calls (assuming doc check passes and doc/section are added)
    mock_check_doc_exists = AsyncMock(return_value=False)
    mock_add_doc = AsyncMock(return_value=789) # Mock document ID
    mock_add_section = AsyncMock(return_value=4) # Mock section ID

    # Mock Extraction (successful)
    mock_extract.return_value = {
        "metadata": {"title": "Index Error Doc"},
        "text_by_section": {"Body": "Some text to index."},
        "references_raw": ["Ref X"] # Include refs to check parse_references not called
    }

    # Mock Chunking (successful)
    mock_chunk_text.return_value = ["Chunk A"]

    # Mock Embeddings (successful)
    mock_embeddings = [[0.9]*config.TARGET_EMBEDDING_DIMENSION]
    mock_get_embeddings.return_value = mock_embeddings

    # Mock Indexing to raise an error
    mock_add_chunks.side_effect = Exception("DB connection lost during indexing")

    with patch("philograph.ingestion.pipeline.db_layer.check_document_exists", mock_check_doc_exists), \
         patch("philograph.ingestion.pipeline.db_layer.add_document", mock_add_doc), \
         patch("philograph.ingestion.pipeline.db_layer.add_section", mock_add_section):
        # Note: mock_add_chunks is patched via decorator

        # --- Call Function ---
        result = await pipeline.process_document(relative_path_str)

    # --- Assertions ---
    # Expecting the error to be caught and reported
    assert result == {"status": "Error", "message": "Ingestion transaction failed: DB chunk indexing failed: DB connection lost during indexing"}

    # Check mocks up to the point of failure
    mock_check_dir.assert_called_once_with(full_path)
    mock_check_file.assert_called_once_with(full_path)
    assert mock_get_db_conn.call_count == 2 # Check + Transaction
    mock_check_doc_exists.assert_called_once_with(mock_conn, relative_path_str)
    mock_extract.assert_called_once_with(full_path)
    mock_add_doc.assert_called_once()
    mock_add_section.assert_called_once()
    mock_chunk_text.assert_called_once()
    mock_get_embeddings.assert_called_once()
    mock_add_chunks.assert_called_once() # Should be called

    # Ensure reference parsing was NOT called
    mock_parse_references.assert_not_called()
@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.db_layer.get_db_connection")
@patch("philograph.ingestion.pipeline.extract_content_and_metadata", new_callable=AsyncMock) # Mock to check not called
@patch("pathlib.Path.resolve") # Mock resolve
async def test_process_document_db_check_error(
    mock_resolve, # Add mock argument
    mock_extract, # Mocked to check not called
    mock_get_db_conn,
    mock_check_file,
    mock_check_dir,
):
    """
    Test handling when the initial db_layer.check_document_exists call fails.
    """
    relative_path_str = "doc_db_check_error.txt"
    relative_path_obj = Path(relative_path_str)
    full_path = Path("/test/source") / relative_path_obj

    # --- Mock Setup ---
    mock_resolve.return_value = full_path # Configure mock resolve
    mock_check_dir.return_value = False
    mock_check_file.return_value = True

    # Mock DB connection
    mock_conn = AsyncMock()
    mock_get_db_conn.return_value.__aenter__.return_value = mock_conn

    # Mock DB check_document_exists to raise an error
    mock_check_doc_exists = AsyncMock(side_effect=Exception("DB connection pool exhausted"))

    with patch("philograph.ingestion.pipeline.db_layer.check_document_exists", mock_check_doc_exists):
        # --- Call Function ---
        result = await pipeline.process_document(relative_path_str)

    # --- Assertions ---
    assert result == {"status": "Error", "message": "DB check failed: DB connection pool exhausted"}

    # Check mocks
    mock_check_dir.assert_called_once_with(full_path)
    mock_check_file.assert_called_once_with(full_path)
    mock_get_db_conn.assert_called_once() # Called once for the check
    mock_check_doc_exists.assert_called_once_with(mock_conn, relative_path_str)

    # Ensure extraction was NOT called
    mock_extract.assert_not_called()
@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.db_layer.get_db_connection")
@patch("philograph.ingestion.pipeline.extract_content_and_metadata", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.db_layer.add_document", new_callable=AsyncMock) # Mock to raise error
@patch("philograph.ingestion.pipeline.db_layer.add_section", new_callable=AsyncMock) # Mock to check not called
@patch("pathlib.Path.resolve") # Mock resolve
async def test_process_document_db_add_doc_error(
    mock_resolve, # Add mock argument
    mock_add_section, # Mocked to check not called
    mock_add_doc, # Mocked to raise error
    mock_extract,
    mock_get_db_conn,
    mock_check_file,
    mock_check_dir,
):
    """
    Test handling when db_layer.add_document raises an error within the transaction.
    """
    relative_path_str = "doc_add_doc_error.pdf"
    relative_path_obj = Path(relative_path_str)
    full_path = Path("/test/source") / relative_path_obj

    # --- Mock Setup ---
    mock_resolve.return_value = full_path # Configure mock resolve
    mock_check_dir.return_value = False
    mock_check_file.return_value = True

    # Mock DB connection
    mock_conn = AsyncMock()
    mock_get_db_conn.return_value.__aenter__.return_value = mock_conn

    # Mock DB check_document_exists to return False (new document)
    mock_check_doc_exists = AsyncMock(return_value=False)

    # Mock Extraction (successful)
    mock_extract.return_value = {
        "metadata": {"title": "Add Doc Error"},
        "text_by_section": {"Body": "Some text."},
        "references_raw": []
    }

    # Mock add_document to raise an error
    mock_add_doc.side_effect = Exception("DB constraint violation on add_document")

    with patch("philograph.ingestion.pipeline.db_layer.check_document_exists", mock_check_doc_exists):
        # Note: mock_add_doc is patched via decorator

        # --- Call Function ---
        result = await pipeline.process_document(relative_path_str)

    # --- Assertions ---
    # Expecting the error to be caught by the transaction block and reported
    assert result == {"status": "Error", "message": "Ingestion transaction failed: DB document insert failed: DB constraint violation on add_document"}

    # Check mocks up to the point of failure
    mock_check_dir.assert_called_once_with(full_path)
    mock_check_file.assert_called_once_with(full_path)
    assert mock_get_db_conn.call_count == 2 # Check + Transaction
    mock_check_doc_exists.assert_called_once_with(mock_conn, relative_path_str)
    mock_extract.assert_called_once_with(full_path)
    mock_add_doc.assert_called_once() # Should be called

    # Ensure subsequent steps were NOT called
    mock_add_section.assert_not_called()
@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.db_layer.get_db_connection")
@patch("philograph.ingestion.pipeline.extract_content_and_metadata", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.db_layer.add_document", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.db_layer.add_section", new_callable=AsyncMock) # Mock to raise error
@patch("philograph.ingestion.pipeline.text_processing.chunk_text_semantically") # Mock to check not called
@patch("pathlib.Path.resolve") # Mock resolve
async def test_process_document_db_add_section_error(
    mock_resolve, # Add mock argument
    mock_chunk_text, # Mocked to check not called
    mock_add_section, # Mocked to raise error
    mock_add_doc,
    mock_extract,
    mock_get_db_conn,
    mock_check_file,
    mock_check_dir,
):
    """
    Test handling when db_layer.add_section raises an error within the transaction.
    """
    relative_path_str = "doc_add_section_error.pdf"
    relative_path_obj = Path(relative_path_str)
    full_path = Path("/test/source") / relative_path_obj

    # --- Mock Setup ---
    mock_resolve.return_value = full_path # Configure mock resolve
    mock_check_dir.return_value = False
    mock_check_file.return_value = True

    # Mock DB connection
    mock_conn = AsyncMock()
    mock_get_db_conn.return_value.__aenter__.return_value = mock_conn

    # Mock DB check_document_exists to return False (new document)
    mock_check_doc_exists = AsyncMock(return_value=False)

    # Mock add_document (successful)
    mock_add_doc.return_value = 999 # Mock document ID

    # Mock Extraction (successful)
    mock_extract.return_value = {
        "metadata": {"title": "Add Section Error"},
        "text_by_section": {"Body": "Some text."},
        "references_raw": []
    }

    # Mock add_section to raise an error
    mock_add_section.side_effect = Exception("DB constraint violation on add_section")

    with patch("philograph.ingestion.pipeline.db_layer.check_document_exists", mock_check_doc_exists):
        # Note: add_doc and add_section are patched via decorator

        # --- Call Function ---
        result = await pipeline.process_document(relative_path_str)

    # --- Assertions ---
    # Expecting the error to be caught by the transaction block and reported
    assert result == {"status": "Error", "message": "Ingestion transaction failed: Chunking/Section DB insert failed: DB constraint violation on add_section"}

    # Check mocks up to the point of failure
    mock_check_dir.assert_called_once_with(full_path)
    mock_check_file.assert_called_once_with(full_path)
    assert mock_get_db_conn.call_count == 2 # Check + Transaction
    mock_check_doc_exists.assert_called_once_with(mock_conn, relative_path_str)
    mock_extract.assert_called_once_with(full_path)
    mock_add_doc.assert_called_once()
    mock_add_section.assert_called_once() # Should be called

    # Ensure subsequent steps were NOT called
    mock_chunk_text.assert_not_called()
@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.db_layer.get_db_connection")
@patch("philograph.ingestion.pipeline.extract_content_and_metadata", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.get_embeddings_in_batches", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.text_processing.chunk_text_semantically")
@patch("philograph.ingestion.pipeline.text_processing.parse_references", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.db_layer.add_reference", new_callable=AsyncMock) # Mock to raise error
@patch("pathlib.Path.resolve") # Mock resolve
async def test_process_document_db_add_reference_error(
    mock_resolve, # Add mock argument
    mock_add_ref, # Mocked to raise error
    mock_parse_references,
    mock_chunk_text,
    mock_get_embeddings,
    mock_extract,
    mock_get_db_conn,
    mock_check_file,
    mock_check_dir,
):
    """
    Test handling when db_layer.add_reference raises an error within the transaction.
    """
    relative_path_str = "doc_add_ref_error.pdf"
    relative_path_obj = Path(relative_path_str)
    full_path = Path("/test/source") / relative_path_obj

    # --- Mock Setup ---
    mock_resolve.return_value = full_path # Configure mock resolve
    mock_check_dir.return_value = False
    mock_check_file.return_value = True

    # Mock DB connection and cursor
    mock_conn = AsyncMock()
    mock_cursor = AsyncMock()
    mock_cursor_cm = AsyncMock()
    mock_cursor_cm.__aenter__.return_value = mock_cursor
    mock_conn.cursor = MagicMock(return_value=mock_cursor_cm)
    mock_get_db_conn.return_value.__aenter__.return_value = mock_conn

    # Mock DB calls (assuming doc check, add doc/section/chunks pass)
    mock_check_doc_exists = AsyncMock(return_value=False)
    mock_add_doc = AsyncMock(return_value=1000) # Mock document ID
    mock_add_section = AsyncMock(return_value=5) # Mock section ID
    mock_add_chunks = AsyncMock(return_value=None)
    # Mock fetchone for finding the first chunk ID for reference linking
    mock_cursor.fetchone = AsyncMock(return_value={'id': 1002}) # Mock chunk ID

    # Mock Extraction (successful, with references)
    mock_extract.return_value = {
        "metadata": {"title": "Add Ref Error"},
        "text_by_section": {"Body": "Some text."},
        "references_raw": ["Ref 1"]
    }

    # Mock Chunking (successful)
    mock_chunk_text.return_value = ["Chunk A"]

    # Mock Embeddings (successful)
    mock_embeddings = [[0.1]*config.TARGET_EMBEDDING_DIMENSION]
    mock_get_embeddings.return_value = mock_embeddings

    # Mock Reference Parsing (successful)
    mock_parse_references.return_value = [{"title": "Ref Title 1"}]

    # Mock add_reference to raise an error
    mock_add_ref.side_effect = Exception("DB constraint violation on add_reference")

    with patch("philograph.ingestion.pipeline.db_layer.check_document_exists", mock_check_doc_exists), \
         patch("philograph.ingestion.pipeline.db_layer.add_document", mock_add_doc), \
         patch("philograph.ingestion.pipeline.db_layer.add_section", mock_add_section), \
         patch("philograph.ingestion.pipeline.db_layer.add_chunks_batch", mock_add_chunks):
        # Note: add_reference is patched via decorator

        # --- Call Function ---
        result = await pipeline.process_document(relative_path_str)

    # --- Assertions ---
    # Expecting the error to be caught by the transaction block and reported
    assert result == {"status": "Error", "message": "Ingestion transaction failed: Reference parsing/storing failed: DB reference insert failed: DB constraint violation on add_reference"}

    # Check mocks up to the point of failure
    mock_check_dir.assert_called_once_with(full_path)
    mock_check_file.assert_called_once_with(full_path)
    assert mock_get_db_conn.call_count == 2 # Check + Transaction
    mock_check_doc_exists.assert_called_once_with(mock_conn, relative_path_str)
    mock_extract.assert_called_once_with(full_path)
    mock_add_doc.assert_called_once()
    mock_add_section.assert_called_once()
    mock_chunk_text.assert_called_once()
    mock_get_embeddings.assert_called_once()
    mock_add_chunks.assert_called_once()
    mock_parse_references.assert_called_once()
    mock_cursor.execute.assert_called_once() # Check that chunk ID was queried
    mock_cursor.fetchone.assert_called_once()
    mock_add_ref.assert_called_once() # Should be called
@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.file_utils.list_files_in_directory")
@patch("philograph.ingestion.pipeline._process_single_file", new_callable=AsyncMock) # Mock the internal function
@patch("pathlib.Path.resolve") # Mock resolve
async def test_process_document_empty_directory(
    mock_resolve, # Add mock argument
    mock_process_single_file,
    mock_list_files,
    mock_check_file,
    mock_check_dir,
):
    """
    Test processing an empty directory. Expect success with 0 files processed.
    """
    relative_path_str = "empty_dir"
    full_path = Path("/test/source") / relative_path_str

    # --- Mock Setup ---
    mock_resolve.return_value = full_path # Configure mock resolve
    mock_check_dir.return_value = True  # It is a directory
    mock_check_file.return_value = False # It is not a file
    mock_list_files.return_value = iter([]) # Generator yielding nothing

    # --- Call Function ---
    result = await pipeline.process_document(relative_path_str)

    # --- Assertions ---
    assert result == {
        "status": "Directory Processed",
        "message": "Processed directory 'empty_dir'. Success: 0, Skipped: 0, Errors: 0",
        "details": []
    }


@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.file_utils.list_files_in_directory")
@patch("philograph.ingestion.pipeline._process_single_file", new_callable=AsyncMock) # Mock the internal function
@patch("pathlib.Path.resolve") # Mock resolve
async def test_process_document_directory_with_one_supported_file(
    mock_resolve, # Add mock argument
    mock_process_single_file,
    mock_list_files,
    mock_check_file,
    mock_check_dir,
):
    """
    Test processing a directory containing one supported file (.pdf).
    Expect _process_single_file to be called once with the correct relative path.
    """
    relative_dir_str = "dir_one_file"
    relative_file_str = f"{relative_dir_str}/doc.pdf"
    full_dir_path = Path("/test/source") / relative_dir_str
    full_file_path = Path("/test/source") / relative_file_str
    relative_file_path_obj = Path(relative_file_str) # Path object relative to source dir

    # --- Mock Setup ---
    mock_resolve.return_value = full_dir_path # Configure mock resolve for the directory path
    mock_check_dir.return_value = True  # It is a directory
    mock_check_file.return_value = False # It is not a file (when checking the dir path)

    # Mock list_files to yield the single PDF file path
    mock_list_files.return_value = iter([full_file_path])

    # Mock the result of _process_single_file for the PDF
    mock_process_single_file.return_value = {"status": "Success", "document_id": 1}

    # --- Call Function ---
    result = await pipeline.process_document(relative_dir_str)

    # --- Assertions ---
    expected_details = [{relative_file_str: {"status": "Success", "document_id": 1}}]
    assert result == {
        "status": "Directory Processed",
        "message": "Processed directory 'dir_one_file'. Success: 1, Skipped: 0, Errors: 0",
        "details": expected_details
    }

    # Check mocks
    mock_check_dir.assert_called_once_with(full_dir_path)
    mock_list_files.assert_called_once_with(full_dir_path, allowed_extensions=['.pdf', '.epub', '.md', '.txt'], recursive=True)
    # IMPORTANT: Assert _process_single_file was called with the Path object relative to SOURCE_FILE_DIR_ABSOLUTE
    mock_process_single_file.assert_called_once_with(relative_file_path_obj)
@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.file_utils.list_files_in_directory")
@patch("philograph.ingestion.pipeline._process_single_file", new_callable=AsyncMock) # Mock the internal function
@patch("pathlib.Path.resolve") # Mock resolve
async def test_process_document_directory_with_unsupported_files(
    mock_resolve, # Add mock argument
    mock_process_single_file,
    mock_list_files,
    mock_check_file,
    mock_check_dir,
):
    """
    Test processing a directory containing only unsupported files (.zip, .docx).
    Expect _process_single_file *not* to be called.
    """
    relative_dir_str = "dir_unsupported"
    full_dir_path = Path("/test/source") / relative_dir_str
    unsupported_file_1 = full_dir_path / "archive.zip"
    unsupported_file_2 = full_dir_path / "document.docx"

    # --- Mock Setup ---
    mock_resolve.return_value = full_dir_path # Configure mock resolve for the directory path
    mock_check_dir.return_value = True  # It is a directory
    mock_check_file.return_value = False # It is not a file (when checking the dir path)

    # Mock list_files to yield the unsupported file paths
    # Note: The implementation's list_files call *already* filters by allowed_extensions.
    # So, mocking list_files to return these shouldn't result in _process_single_file being called.
    # If the implementation *didn't* filter, this mock would need to be empty.
    mock_list_files.return_value = iter([]) # list_files filters internally

    # --- Call Function ---
    result = await pipeline.process_document(relative_dir_str)

    # --- Assertions ---
    # Expecting success, but 0 files processed as they are filtered out by list_files_in_directory
    assert result == {
        "status": "Directory Processed",
        "message": "Processed directory 'dir_unsupported'. Success: 0, Skipped: 0, Errors: 0",
        "details": []
    }

    # Check mocks
    mock_check_dir.assert_called_once_with(full_dir_path)
    # list_files is called, but it yields nothing because of the extension filter
    mock_list_files.assert_called_once_with(full_dir_path, allowed_extensions=['.pdf', '.epub', '.md', '.txt'], recursive=True)
    mock_process_single_file.assert_not_called() # No supported files yielded


@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.file_utils.list_files_in_directory")
@patch("philograph.ingestion.pipeline._process_single_file", new_callable=AsyncMock) # Mock the internal function
@patch("pathlib.Path.resolve") # Mock resolve
async def test_process_document_directory_with_mixed_files(
    mock_resolve, # Add mock argument
    mock_process_single_file,
    mock_list_files,
    mock_check_file,
    mock_check_dir,
):
    """
    Test processing a directory with a mix of supported (.md) and unsupported (.tmp) files.
    Expect _process_single_file to be called only for the supported file.
    """
    relative_dir_str = "dir_mixed"
    supported_file_rel_str = f"{relative_dir_str}/notes.md"
    unsupported_file_rel_str = f"{relative_dir_str}/temp.tmp" # Not used in mock below
    full_dir_path = Path("/test/source") / relative_dir_str
    supported_file_full_path = Path("/test/source") / supported_file_rel_str
    supported_file_rel_path_obj = Path(supported_file_rel_str)

    # --- Mock Setup ---
    mock_resolve.return_value = full_dir_path # Configure mock resolve for the directory path
    mock_check_dir.return_value = True
    mock_check_file.return_value = False

    # Mock list_files to yield *only* the supported file path, as the implementation filters
    mock_list_files.return_value = iter([supported_file_full_path])

    # Mock the result of _process_single_file for the MD file
    mock_process_single_file.return_value = {"status": "Success", "document_id": 2}

    # --- Call Function ---
    result = await pipeline.process_document(relative_dir_str)

    # --- Assertions ---
    expected_details = [{supported_file_rel_str: {"status": "Success", "document_id": 2}}]
    assert result == {
        "status": "Directory Processed",
        "message": "Processed directory 'dir_mixed'. Success: 1, Skipped: 0, Errors: 0",
        "details": expected_details
    }

    # Check mocks
    mock_check_dir.assert_called_once_with(full_dir_path)
    mock_list_files.assert_called_once_with(full_dir_path, allowed_extensions=['.pdf', '.epub', '.md', '.txt'], recursive=True)
    mock_process_single_file.assert_called_once_with(supported_file_rel_path_obj)
    mock_list_files.assert_called_once_with(full_dir_path, allowed_extensions=['.pdf', '.epub', '.md', '.txt'], recursive=True)
    # mock_check_file.assert_not_called() # This assertion was incorrect for this test
@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.file_utils.list_files_in_directory")
@patch("philograph.ingestion.pipeline._process_single_file", new_callable=AsyncMock) # Mock the internal function
@patch("pathlib.Path.resolve") # Mock resolve
async def test_process_document_directory_with_subdirectory(
    mock_resolve, # Add mock argument
    mock_process_single_file,
    mock_list_files,
    mock_check_file,
    mock_check_dir,
):
    """
    Test processing a directory containing a subdirectory with supported files.
    Expect _process_single_file to be called for files in both parent and child dirs.
    """
    relative_parent_dir_str = "parent_dir"
    relative_file1_str = f"{relative_parent_dir_str}/file1.pdf"
    relative_file2_str = f"{relative_parent_dir_str}/child_dir/file2.md"

    full_parent_dir_path = Path("/test/source") / relative_parent_dir_str
    full_file1_path = Path("/test/source") / relative_file1_str
    full_file2_path = Path("/test/source") / relative_file2_str

    relative_file1_path_obj = Path(relative_file1_str)
    relative_file2_path_obj = Path(relative_file2_str)

    # --- Mock Setup ---
    mock_resolve.return_value = full_parent_dir_path # Configure mock resolve for the directory path
    mock_check_dir.return_value = True  # It is a directory
    mock_check_file.return_value = False # It is not a file (when checking the dir path)

    # Mock list_files to yield files from parent and child directories
    mock_list_files.return_value = iter([full_file1_path, full_file2_path])

    # Mock the result of _process_single_file
    mock_process_single_file.side_effect = [
        {"status": "Success", "document_id": 10}, # Result for file1.pdf
        {"status": "Success", "document_id": 11}, # Result for file2.md
    ]

    # --- Call Function ---
    result = await pipeline.process_document(relative_parent_dir_str)

    # --- Assertions ---
    expected_details = [
        {relative_file1_str: {"status": "Success", "document_id": 10}},
        {relative_file2_str: {"status": "Success", "document_id": 11}},
    ]
    assert result == {
        "status": "Directory Processed",
        "message": "Processed directory 'parent_dir'. Success: 2, Skipped: 0, Errors: 0",
        "details": expected_details
    }

    # Check mocks
    mock_check_dir.assert_called_once_with(full_parent_dir_path)
    mock_list_files.assert_called_once_with(full_parent_dir_path, allowed_extensions=['.pdf', '.epub', '.md', '.txt'], recursive=True)
    # Assert _process_single_file was called with the correct relative Path objects
    assert mock_process_single_file.call_count == 2
    mock_process_single_file.assert_any_call(relative_file1_path_obj)
    mock_process_single_file.assert_any_call(relative_file2_path_obj)
@patch("philograph.ingestion.pipeline.config.SOURCE_FILE_DIR_ABSOLUTE", Path("/test/source"))
@patch("philograph.ingestion.pipeline.file_utils.check_directory_exists")
@patch("philograph.ingestion.pipeline.file_utils.check_file_exists")
@patch("philograph.ingestion.pipeline.file_utils.list_files_in_directory")
@patch("philograph.ingestion.pipeline._process_single_file", new_callable=AsyncMock) # Mock the internal function
@patch("pathlib.Path.resolve") # Mock resolve
async def test_process_document_directory_permission_error(
    mock_resolve, # Add mock argument
    mock_process_single_file,
    mock_list_files,
    mock_check_file,
    mock_check_dir,
):
    """
    Test processing a directory where iterating raises a PermissionError for one item.
    Expect the error to be logged for that item, but processing continues for others.
    """
    relative_dir_str = "dir_perm_error"
    relative_file1_str = f"{relative_dir_str}/file1.pdf"
    problematic_path_str = f"{relative_dir_str}/forbidden_dir_or_file" # Path causing error
    relative_file2_str = f"{relative_dir_str}/file2.md"

    full_dir_path = Path("/test/source") / relative_dir_str
    full_file1_path = Path("/test/source") / relative_file1_str
    full_problematic_path = Path("/test/source") / problematic_path_str # Path object
    full_file2_path = Path("/test/source") / relative_file2_str

    relative_file1_path_obj = Path(relative_file1_str)
    relative_file2_path_obj = Path(relative_file2_str)

    # --- Mock Setup ---
    mock_resolve.return_value = full_dir_path # Configure mock resolve for the directory path
    mock_check_dir.return_value = True
    mock_check_file.return_value = False

    # Mock list_files to yield one file, then raise PermissionError, then yield another
    # Note: The actual error might occur *during* iteration in list_files,
    # or when trying to access the yielded path. Here we simulate the error
    # being caught within the loop in process_document.
    # A more realistic mock might involve mocking Path.iterdir() if list_files uses it directly.
    # For now, assume the error happens when processing the yielded path.
    # Let's refine: Mock list_files to yield paths, and have the *processing* of one path to fail.
    # The loop in process_document catches exceptions *around* the call to _process_single_file
    # and path resolution. Let's mock list_files to yield paths, and have the relative_to call fail.

    def list_files_generator(*args, **kwargs):
        yield full_file1_path
        # Simulate error when trying to process the next path from the generator
        # The code tries `file_to_process.relative_to(...)`
        mock_problem_path = MagicMock(spec=Path)
        mock_problem_path.relative_to.side_effect = PermissionError("Cannot access path")
        mock_problem_path.__str__ = MagicMock(return_value=str(full_problematic_path)) # For logging
        yield mock_problem_path
        yield full_file2_path

    mock_list_files.side_effect = list_files_generator

    # Mock the result of _process_single_file for the successful calls
    mock_process_single_file.side_effect = [
        {"status": "Success", "document_id": 20}, # Result for file1.pdf
        {"status": "Success", "document_id": 21}, # Result for file2.md
    ]

    # --- Call Function ---
    result = await pipeline.process_document(relative_dir_str)

    # --- Assertions ---
    # Expecting 1 success, 1 error (PermissionError caught in the loop)
    # The error message comes from the exception caught in the loop (line 171)
    expected_details = [
        {relative_file1_str: {"status": "Success", "document_id": 20}},
        {str(full_problematic_path): {"status": "Error", "message": "Cannot access path"}},
        {relative_file2_str: {"status": "Success", "document_id": 21}},
    ]
    assert result["status"] == "Directory Processed"
    assert result["message"] == "Processed directory 'dir_perm_error'. Success: 2, Skipped: 0, Errors: 1"
    # Order might not be guaranteed, compare contents
    assert len(result["details"]) == 3
    assert expected_details[0] in result["details"]
    assert expected_details[1] in result["details"]
    assert expected_details[2] in result["details"]


    # Check mocks
    mock_check_dir.assert_called_once_with(full_dir_path)
    mock_list_files.assert_called_once_with(full_dir_path, allowed_extensions=['.pdf', '.epub', '.md', '.txt'], recursive=True)
    # Assert _process_single_file was called twice for the valid files
    assert mock_process_single_file.call_count == 2
    mock_process_single_file.assert_any_call(relative_file1_path_obj)
    mock_process_single_file.assert_any_call(relative_file2_path_obj)