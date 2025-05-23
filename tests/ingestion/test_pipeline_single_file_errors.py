# tests/ingestion/test_pipeline_single_file_errors.py
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

# --- Tests for process_document (Single File Error Scenarios) ---

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