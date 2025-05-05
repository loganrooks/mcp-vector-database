# tests/ingestion/test_pipeline_single_file.py
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx # Keep for potential exception types in dependencies

# Assuming config values are needed and potentially mocked
from philograph import config
from philograph.ingestion import pipeline
from philograph.data_access import db_layer # For mocking types if needed

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

# --- Tests for process_document (Single File Scenarios) ---

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
