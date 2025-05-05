import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

# Assuming config values are needed and potentially mocked
from philograph import config
from philograph.ingestion import pipeline
from philograph.utils import text_processing # For mocking extraction functions
from philograph.utils import file_utils # For mocking file utils

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

# --- Tests for get_embeddings_in_batches ---

async def test_get_embeddings_in_batches_empty_input():
    """
    Test that get_embeddings_in_batches returns an empty list for empty input.
    """
    result = await pipeline.get_embeddings_in_batches([])
    assert result == []

@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_success(mock_make_request):
    """
    Test successful embedding generation for a single batch.
    """
    chunks_data = [
        (1, "This is chunk 1.", 0),
        (1, "This is chunk 2.", 1),
    ]
    expected_dimension = config.TARGET_EMBEDDING_DIMENSION
    mock_embedding_1 = [0.1] * expected_dimension
    mock_embedding_2 = [0.2] * expected_dimension
    expected_embeddings = [mock_embedding_1, mock_embedding_2]

    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
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
    mock_response.raise_for_status = MagicMock()
    mock_make_request.return_value = mock_response

    result = await pipeline.get_embeddings_in_batches(chunks_data, batch_size=5)

    assert result == expected_embeddings
    mock_make_request.assert_called_once()
    call_args, call_kwargs = mock_make_request.call_args
    assert call_args[0] == "POST"
    assert call_args[1] == f"{config.LITELLM_PROXY_URL}/embeddings"
    assert call_kwargs['json_data']['model'] == config.EMBEDDING_MODEL_NAME
    assert call_kwargs['json_data']['input'] == ["This is chunk 1.", "This is chunk 2."]
    assert call_kwargs['timeout'] == 120.0
    if config.LITELLM_API_KEY:
        assert "Authorization" in call_kwargs['headers']
        assert call_kwargs['headers']["Authorization"] == f"Bearer {config.LITELLM_API_KEY}"

@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_http_status_error(mock_make_request):
    """
    Test handling of HTTPStatusError during embedding generation.
    """
    chunks_data = [(1, "Chunk text", 0)]
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.request = MagicMock(spec=httpx.Request)
    error = httpx.HTTPStatusError("Server error", request=mock_response.request, response=mock_response)
    mock_response.raise_for_status = MagicMock(side_effect=error)
    mock_make_request.return_value = mock_response

    with pytest.raises(RuntimeError, match=r"Embedding generation failed \(HTTP 500\)"):
        await pipeline.get_embeddings_in_batches(chunks_data, batch_size=1)
    mock_make_request.assert_called_once()

@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_request_error(mock_make_request):
    """
    Test handling of RequestError during embedding generation.
    """
    chunks_data = [(1, "Chunk text", 0)]
    error = httpx.RequestError("Network error", request=MagicMock(spec=httpx.Request))
    mock_make_request.side_effect = error

    with pytest.raises(RuntimeError, match=r"Embedding generation failed \(Request Error\)"):
        await pipeline.get_embeddings_in_batches(chunks_data, batch_size=1)
    mock_make_request.assert_called_once()

@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_missing_data_field(mock_make_request):
    """
    Test handling of a successful response missing the 'data' field.
    """
    chunks_data = [(1, "Chunk text", 0)]
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    async def mock_json():
        return {"model": "mock_model", "usage": {}}
    mock_response.json = mock_json
    mock_response.raise_for_status = MagicMock()
    mock_make_request.return_value = mock_response

    with pytest.raises(RuntimeError, match=r"Embedding generation failed \(Processing Error\)"):
        await pipeline.get_embeddings_in_batches(chunks_data, batch_size=1)
    mock_make_request.assert_called_once()

@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_mismatched_data_length(mock_make_request):
    """
    Test handling of a response with mismatched 'data' length.
    """
    chunks_data = [(1, "Chunk 1", 0), (1, "Chunk 2", 1)]
    mock_embedding_1 = [0.1] * config.TARGET_EMBEDDING_DIMENSION
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    async def mock_json():
        return {"data": [{"embedding": mock_embedding_1}], "model": "mock", "usage": {}} # Only one embedding
    mock_response.json = mock_json
    mock_response.raise_for_status = MagicMock()
    mock_make_request.return_value = mock_response

    with pytest.raises(RuntimeError, match=r"Embedding generation failed \(Processing Error\)"):
        await pipeline.get_embeddings_in_batches(chunks_data, batch_size=5)
    mock_make_request.assert_called_once()

@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_multiple_batches(mock_make_request):
    """
    Test successful embedding generation requiring multiple batches.
    """
    batch_size = 2
    chunks_data = [(1,"C1",0),(1,"C2",1),(2,"C3",0),(2,"C4",1),(3,"C5",0)]
    mock_embeddings = [[float(i+1)/10.0]*config.TARGET_EMBEDDING_DIMENSION for i in range(5)]
    expected_result = mock_embeddings

    async def mock_response_batch_1(*args, **kwargs):
        mock_resp = AsyncMock(spec=httpx.Response); mock_resp.status_code = 200
        async def mj(): return {"data": [{"embedding": mock_embeddings[0]}, {"embedding": mock_embeddings[1]}], "model": "mock", "usage": {}}
        mock_resp.json = mj; mock_resp.raise_for_status = MagicMock(); return mock_resp
    async def mock_response_batch_2(*args, **kwargs):
        mock_resp = AsyncMock(spec=httpx.Response); mock_resp.status_code = 200
        async def mj(): return {"data": [{"embedding": mock_embeddings[2]}, {"embedding": mock_embeddings[3]}], "model": "mock", "usage": {}}
        mock_resp.json = mj; mock_resp.raise_for_status = MagicMock(); return mock_resp
    async def mock_response_batch_3(*args, **kwargs):
        mock_resp = AsyncMock(spec=httpx.Response); mock_resp.status_code = 200
        async def mj(): return {"data": [{"embedding": mock_embeddings[4]}], "model": "mock", "usage": {}}
        mock_resp.json = mj; mock_resp.raise_for_status = MagicMock(); return mock_resp

    mock_make_request.side_effect = [await mock_response_batch_1(), await mock_response_batch_2(), await mock_response_batch_3()]

    result = await pipeline.get_embeddings_in_batches(chunks_data, batch_size=batch_size)

    assert result == expected_result
    assert mock_make_request.call_count == 3
    call1_args, call1_kwargs = mock_make_request.call_args_list[0]
    assert call1_kwargs['json_data']['input'] == ["C1", "C2"]
    call2_args, call2_kwargs = mock_make_request.call_args_list[1]
    assert call2_kwargs['json_data']['input'] == ["C3", "C4"]
    call3_args, call3_kwargs = mock_make_request.call_args_list[2]
    assert call3_kwargs['json_data']['input'] == ["C5"]

@patch("philograph.utils.http_client.make_async_request")
async def test_get_embeddings_in_batches_invalid_dimension(mock_make_request):
    """
    Test handling of embeddings received with an incorrect dimension.
    """
    chunks_data = [(1, "Chunk text", 0)]
    invalid_embedding = [0.5] * (config.TARGET_EMBEDDING_DIMENSION - 1)
    mock_response = AsyncMock(spec=httpx.Response); mock_response.status_code = 200
    async def mj(): return {"data": [{"embedding": invalid_embedding}], "model": "mock", "usage": {}}
    mock_response.json = mj; mock_response.raise_for_status = MagicMock()
    mock_make_request.return_value = mock_response

    with pytest.raises(RuntimeError, match=r"Embedding generation failed \(Processing Error\)"):
        await pipeline.get_embeddings_in_batches(chunks_data, batch_size=1)
    mock_make_request.assert_called_once()

# --- Tests for extract_content_and_metadata ---

@patch("philograph.ingestion.pipeline.text_processing.call_grobid_extractor", new_callable=AsyncMock)
@patch("philograph.ingestion.pipeline.file_utils.get_file_extension")
async def test_extract_content_and_metadata_pdf(mock_get_ext, mock_call_grobid):
    """
    Test that extract_content_and_metadata calls call_grobid_extractor for PDF files.
    """
    mock_path = Path("/fake/path/document.pdf")
    mock_get_ext.return_value = ".pdf"
    expected_result = {"metadata": {"title": "PDF Title"}, "text_by_section": {"Abstract": "Text"}}
    mock_call_grobid.return_value = expected_result

    result = await pipeline.extract_content_and_metadata(mock_path)

    assert result == expected_result
    mock_get_ext.assert_called_once_with(mock_path)
    mock_call_grobid.assert_awaited_once_with(mock_path) # Check await

@patch("philograph.ingestion.pipeline.text_processing.extract_epub_content")
@patch("philograph.ingestion.pipeline.file_utils.get_file_extension")
async def test_extract_content_and_metadata_epub(mock_get_ext, mock_extract_epub):
    """
    Test that extract_content_and_metadata calls extract_epub_content for EPUB files.
    """
    mock_path = Path("/fake/path/document.epub")
    mock_get_ext.return_value = ".epub"
    expected_result = {"metadata": {"title": "EPUB Title"}, "text_by_section": {"Chapter 1": "Text"}}
    mock_extract_epub.return_value = expected_result # It's sync

    result = await pipeline.extract_content_and_metadata(mock_path)

    assert result == expected_result
    mock_get_ext.assert_called_once_with(mock_path)
    mock_extract_epub.assert_called_once_with(mock_path)

@pytest.mark.parametrize("ext", [".txt", ".md"])
@patch("philograph.ingestion.pipeline.text_processing.extract_text_content")
@patch("philograph.ingestion.pipeline.file_utils.get_file_extension")
async def test_extract_content_and_metadata_text(mock_get_ext, mock_extract_text, ext):
    """
    Test that extract_content_and_metadata calls extract_text_content for TXT/MD files.
    """
    mock_path = Path(f"/fake/path/document{ext}")
    mock_get_ext.return_value = ext
    expected_result = {"metadata": {}, "text_by_section": {"body": "Plain text content."}}
    mock_extract_text.return_value = expected_result # It's sync

    result = await pipeline.extract_content_and_metadata(mock_path)

    assert result == expected_result
    mock_get_ext.assert_called_once_with(mock_path)
    mock_extract_text.assert_called_once_with(mock_path)

@patch("philograph.ingestion.pipeline.file_utils.get_file_extension")
async def test_extract_content_and_metadata_unsupported(mock_get_ext):
    """
    Test that extract_content_and_metadata returns None for unsupported file types.
    """
    mock_path = Path("/fake/path/document.zip")
    mock_get_ext.return_value = ".zip"

    result = await pipeline.extract_content_and_metadata(mock_path)

    assert result is None
    mock_get_ext.assert_called_once_with(mock_path)