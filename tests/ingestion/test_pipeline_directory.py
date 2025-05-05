# tests/ingestion/test_pipeline_directory.py
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Assuming config values are needed and potentially mocked
from philograph import config
from philograph.ingestion import pipeline
# No db_layer needed directly for these tests, but keep file_utils
from philograph.utils import file_utils

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

# --- Tests for process_document (Directory Scenarios) ---

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