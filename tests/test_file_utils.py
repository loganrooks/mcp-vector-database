import pytest
import os
from pathlib import Path

# Assuming utils is importable from tests context
from src.philograph.utils import file_utils

# --- Tests for check_file_exists ---

def test_check_file_exists_true(tmp_path):
    """Test check_file_exists returns True for an existing file."""
    file_path = tmp_path / "test_file.txt"
    file_path.touch() # Create the file
    assert file_utils.check_file_exists(file_path) is True

def test_check_file_exists_false_nonexistent(tmp_path):
    """Test check_file_exists returns False for a non-existent file."""
    file_path = tmp_path / "non_existent_file.txt"
    assert file_utils.check_file_exists(file_path) is False

def test_check_file_exists_false_directory(tmp_path):
    """Test check_file_exists returns False for a directory."""
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    assert file_utils.check_file_exists(dir_path) is False

# --- Tests for check_directory_exists ---

def test_check_directory_exists_true(tmp_path):
    """Test check_directory_exists returns True for an existing directory."""
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    assert file_utils.check_directory_exists(dir_path) is True

def test_check_directory_exists_false_nonexistent(tmp_path):
    """Test check_directory_exists returns False for a non-existent directory."""
    dir_path = tmp_path / "non_existent_dir"
    assert file_utils.check_directory_exists(dir_path) is False

def test_check_directory_exists_false_file(tmp_path):
    """Test check_directory_exists returns False for a file."""
    file_path = tmp_path / "test_file.txt"
    file_path.touch()
    assert file_utils.check_directory_exists(file_path) is False

# --- Tests for get_file_extension ---

@pytest.mark.parametrize("filename, expected_ext", [
    ("document.pdf", ".pdf"),
    ("image.JPEG", ".jpeg"),
    ("archive.tar.gz", ".gz"),
    ("no_extension", ""),
    (".hiddenfile", ""), # Standard library behavior
    ("file.with.dots.txt", ".txt"),
])
def test_get_file_extension(filename, expected_ext):
    """Test get_file_extension returns the correct lowercase extension."""
    assert file_utils.get_file_extension(filename) == expected_ext

def test_get_file_extension_path_object(tmp_path):
    """Test get_file_extension works with Path objects."""
    file_path = tmp_path / "test.DOCX"
    assert file_utils.get_file_extension(file_path) == ".docx"

# --- Tests for join_paths ---

def test_join_paths_basic():
    """Test join_paths joins basic string components."""
    expected = Path("a/b/c")
    assert file_utils.join_paths("a", "b", "c") == expected

def test_join_paths_mixed_types():
    """Test join_paths joins mixed string and Path components."""
    expected = Path("a/b/c")
    assert file_utils.join_paths("a", Path("b"), "c") == expected

def test_join_paths_leading_slash():
    """Test join_paths handles leading slashes correctly (os.path.join behavior)."""
    # os.path.join treats components starting with '/' as absolute paths
    expected = Path("/c")
    assert file_utils.join_paths("a", "/b", "/c") == expected
# --- Tests for list_files_in_directory ---

@pytest.fixture
def setup_test_directory(tmp_path):
    """Creates a temporary directory structure for list_files tests."""
    base = tmp_path / "list_test"
    base.mkdir()
    (base / "file1.txt").touch()
    (base / "file2.PDF").touch()
    sub = base / "subdir"
    sub.mkdir()
    (sub / "subfile1.txt").touch()
    (sub / "subfile2.log").touch()
    (sub / "subfile3.TXT").touch()
    (base / "empty_subdir").mkdir()
    return base

def test_list_files_non_recursive_no_filter(setup_test_directory):
    """Test non-recursive listing without extension filters."""
    base_path = setup_test_directory
    expected = {
        base_path / "file1.txt",
        base_path / "file2.PDF",
    }
    # Convert generator to set for comparison
    result = set(file_utils.list_files_in_directory(base_path, recursive=False))
    assert result == expected

def test_list_files_recursive_no_filter(setup_test_directory):
    """Test recursive listing without extension filters."""
    base_path = setup_test_directory
    expected = {
        base_path / "file1.txt",
        base_path / "file2.PDF",
        base_path / "subdir" / "subfile1.txt",
        base_path / "subdir" / "subfile2.log",
        base_path / "subdir" / "subfile3.TXT",
    }
    result = set(file_utils.list_files_in_directory(base_path, recursive=True))
    assert result == expected

def test_list_files_non_recursive_single_filter(setup_test_directory):
    """Test non-recursive listing with a single extension filter."""
    base_path = setup_test_directory
    expected = {base_path / "file1.txt"}
    result = set(file_utils.list_files_in_directory(base_path, allowed_extensions=['.txt'], recursive=False))
    assert result == expected

def test_list_files_recursive_multiple_filters(setup_test_directory):
    """Test recursive listing with multiple extension filters (case-insensitive)."""
    base_path = setup_test_directory
    expected = {
        base_path / "file1.txt",
        base_path / "subdir" / "subfile1.txt",
        base_path / "subdir" / "subfile3.TXT", # Should match .txt filter
    }
    result = set(file_utils.list_files_in_directory(base_path, allowed_extensions=['.txt'], recursive=True))
    assert result == expected

def test_list_files_recursive_multiple_filters_pdf_log(setup_test_directory):
    """Test recursive listing with multiple different extension filters."""
    base_path = setup_test_directory
    expected = {
        base_path / "file2.PDF",
        base_path / "subdir" / "subfile2.log",
    }
    result = set(file_utils.list_files_in_directory(base_path, allowed_extensions=['.pdf', '.log'], recursive=True))
    assert result == expected

def test_list_files_empty_directory(setup_test_directory):
    """Test listing an empty directory yields nothing."""
    empty_dir = setup_test_directory / "empty_subdir"
    result_non_recursive = list(file_utils.list_files_in_directory(empty_dir, recursive=False))
    result_recursive = list(file_utils.list_files_in_directory(empty_dir, recursive=True))
    assert result_non_recursive == []
    assert result_recursive == []

def test_list_files_non_existent_directory(tmp_path):
    """Test listing a non-existent directory yields nothing and logs warning."""
    non_existent_dir = tmp_path / "does_not_exist"
    # We don't check log output here, assume function handles it
    result = list(file_utils.list_files_in_directory(non_existent_dir))
    assert result == []

# TODO: Add tests for list_files_in_directory