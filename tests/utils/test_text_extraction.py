# tests/utils/test_text_extraction.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging

# Try importing yaml, but don't fail if it's not there
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None # Define yaml as None if import fails

# Assuming the module is importable relative to the project root (src)
from src.philograph.utils import text_processing

# Helper to create dummy files within pytest's tmp_path
def create_dummy_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')

# --- Tests for extract_text_content ---

def test_extract_simple_txt(tmp_path):
    """Tests extracting content from a plain TXT file."""
    file_path = tmp_path / "simple.txt"
    content = "This is simple text.\nWith multiple lines."
    create_dummy_file(file_path, content)

    result = text_processing.extract_text_content(file_path)

    assert result is not None
    assert isinstance(result, dict)
    assert "metadata" in result
    assert "text_by_section" in result
    assert "references_raw" in result

    assert result["metadata"]["title"] == "simple" # Should use filename stem
    assert "main" in result["text_by_section"]
    assert result["text_by_section"]["main"] == content.strip() # .strip() matches implementation
    assert result["references_raw"] is None

def test_extract_simple_md(tmp_path):
    """Tests extracting content from a plain MD file (no frontmatter)."""
    file_path = tmp_path / "simple.md"
    content = "# Markdown Header\n\nThis is simple markdown text."
    create_dummy_file(file_path, content)

    result = text_processing.extract_text_content(file_path)

    assert result is not None
    assert result["metadata"]["title"] == "simple" # Should use filename stem
    assert "main" in result["text_by_section"]
    assert result["text_by_section"]["main"] == content.strip() # Should return raw markdown
    assert result["references_raw"] is None

# Test requires PyYAML to be installed, skip if not available
@pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
def test_extract_md_with_frontmatter(tmp_path):
    """Tests extracting content and YAML frontmatter from an MD file."""
    file_path = tmp_path / "metadata.md"
    frontmatter = """---
title: Test Document Title
author: Test Author
keywords: [test, yaml, markdown]
---"""
    main_content = "\n# Main Content\n\nThis follows the frontmatter."
    full_content = frontmatter + main_content
    create_dummy_file(file_path, full_content)

    result = text_processing.extract_text_content(file_path)

    assert result is not None
    assert result["metadata"]["title"] == "Test Document Title"
    assert result["metadata"]["author"] == "Test Author"
    assert result["metadata"]["keywords"] == ["test", "yaml", "markdown"]
    assert "main" in result["text_by_section"]
    assert result["text_by_section"]["main"] == main_content.strip()
    assert result["references_raw"] is None

# Test requires PyYAML to be installed, skip if not available
@pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
def test_extract_md_with_invalid_frontmatter(tmp_path, caplog):
    """Tests handling of invalid YAML frontmatter (should treat as text)."""
    file_path = tmp_path / "invalid_fm.md"
    # Invalid YAML: missing colon
    content = """---
title Test Document Title
author: Test Author
---
# Main Content"""
    create_dummy_file(file_path, content)

    with caplog.at_level(logging.WARNING):
        result = text_processing.extract_text_content(file_path)

    assert result is not None
    # Title should fall back to filename stem as frontmatter parsing failed
    assert result["metadata"]["title"] == "invalid_fm"
    assert "author" not in result["metadata"] # Failed parse
    assert "main" in result["text_by_section"]
    # The entire content should be treated as text
    assert result["text_by_section"]["main"] == content.strip()
    assert result["references_raw"] is None
    # Check for warning log
    assert "Error parsing YAML frontmatter" in caplog.text
    assert str(file_path) in caplog.text


def test_extract_md_no_closing_frontmatter(tmp_path):
    """Tests handling of frontmatter without a closing '---'."""
    file_path = tmp_path / "no_close_fm.md"
    content = """---
title: Test Document Title
author: Test Author
# Main Content starts here without closing fence"""
    create_dummy_file(file_path, content)

    result = text_processing.extract_text_content(file_path)

    assert result is not None
    # Title should fall back to filename stem as frontmatter parsing failed
    assert result["metadata"]["title"] == "no_close_fm"
    assert "author" not in result["metadata"] # Failed parse
    assert "main" in result["text_by_section"]
    # The entire content should be treated as text
    assert result["text_by_section"]["main"] == content.strip()
    assert result["references_raw"] is None


# Mocking the import of yaml to simulate it not being installed
# This requires careful handling of when the import happens in the target module.
# If 'import yaml' is at the top level, this patch needs to happen *before*
# text_processing is imported by the test module.
# The production code handles ImportError, and skipif handles test execution.
# Patching is not needed here.
# @patch('src.philograph.utils.text_processing.yaml', None) # Removed - Unnecessary and caused AttributeError
# @patch('src.philograph.utils.text_processing.logger') # Removed - Use caplog fixture instead
@pytest.mark.skipif(HAS_YAML, reason="PyYAML is installed, test requires it to be absent")
def test_extract_md_frontmatter_no_yaml_installed(tmp_path, caplog):
    """
    Tests frontmatter handling when PyYAML is not installed.
    Relies on the try/except ImportError in the production code.
    """
    # This test will only run if HAS_YAML is False (meaning import yaml failed)
    file_path = tmp_path / "metadata_no_yaml.md"
    frontmatter = """---
title: Test Document Title
author: Test Author
---"""
    main_content = "\n# Main Content"
    full_content = frontmatter + main_content
    create_dummy_file(file_path, full_content)

    with caplog.at_level(logging.WARNING):
        result = text_processing.extract_text_content(file_path)

    assert result is not None
    # Title should fall back to filename stem
    assert result["metadata"]["title"] == "metadata_no_yaml"
    assert "author" not in result["metadata"]
    assert "main" in result["text_by_section"]
    # The entire content should be treated as text because PyYAML is mocked as unavailable
    assert result["text_by_section"]["main"] == full_content.strip()
    assert result["references_raw"] is None

    # Check if the warning was logged via caplog
    assert "PyYAML not installed, cannot parse frontmatter. Treating as plain text." in caplog.text


# --- Tests for extract_epub_content ---

@patch('ebooklib.epub.read_epub')
def test_extract_epub_content_success(mock_read_epub, tmp_path):
    """Tests successful extraction of content and metadata from a mock EPUB."""
    # Mock the book object returned by read_epub
    mock_book = MagicMock()
    mock_read_epub.return_value = mock_book

    # Mock metadata
    mock_book.get_metadata.side_effect = lambda namespace, name: {
        ('DC', 'title'): [('Test EPUB Title', {})],
        ('DC', 'creator'): [('Test Author', {})],
        ('DC', 'language'): [('en', {})],
        ('DC', 'identifier'): [('urn:uuid:12345', {})],
    }.get((namespace, name), [])

    # Mock TOC
    mock_toc_item1 = MagicMock()
    mock_toc_item1.href = 'chap1.xhtml'
    mock_toc_item1.title = 'Chapter 1: The Beginning'
    mock_toc_item2 = MagicMock()
    mock_toc_item2.href = 'chap2.xhtml#section1' # Include anchor to test splitting
    mock_toc_item2.title = 'Chapter 2: The Middle'
    mock_book.toc = [mock_toc_item1, mock_toc_item2]

    # Mock items (content documents)
    mock_item1 = MagicMock()
    mock_item1.get_name.return_value = 'chap1.xhtml'
    mock_item1.get_body_content.return_value = b'<html><body><p>Content for chapter 1.</p></body></html>'

    mock_item2 = MagicMock()
    mock_item2.get_name.return_value = 'chap2.xhtml'
    mock_item2.get_body_content.return_value = b'<html><body><h2>Section 1</h2><p>Content for chapter 2.</p> More text.</body></html>'

    mock_item_other = MagicMock() # Non-content item
    mock_item_other.get_name.return_value = 'cover.jpg'
    mock_item_other.get_body_content.return_value = b'' # Should be ignored

    # Simulate the order items might be returned
    mock_book.get_items_of_type.return_value = [mock_item1, mock_item2, mock_item_other]

    # Create a dummy file path (doesn't need content as read_epub is mocked)
    dummy_epub_path = tmp_path / "test.epub"
    dummy_epub_path.touch()

    # Call the function under test
    result = text_processing.extract_epub_content(dummy_epub_path)

    # Assertions
    assert result is not None
    assert result["metadata"]["title"] == "Test EPUB Title"
    assert result["metadata"]["author"] == "Test Author"
    assert result["metadata"]["language"] == "en"
    assert result["metadata"]["identifier"] == "urn:uuid:12345"

    assert "Chapter 1: The Beginning" in result["text_by_section"]
    assert "Content for chapter 1." in result["text_by_section"]["Chapter 1: The Beginning"]
    assert "Chapter 2: The Middle" in result["text_by_section"]
    assert "Content for chapter 2." in result["text_by_section"]["Chapter 2: The Middle"]
    assert "Section 1" in result["text_by_section"]["Chapter 2: The Middle"] # Check if h2 was included
    assert "cover.jpg" not in result["text_by_section"] # Ensure non-content is ignored

    mock_read_epub.assert_called_once_with(dummy_epub_path)


@patch('ebooklib.epub.read_epub')
def test_extract_epub_content_read_error(mock_read_epub, tmp_path, caplog):
    """Tests handling of exceptions during epub.read_epub."""
    # Configure the mock to raise an exception
    error_message = "Simulated EPUB read error (e.g., DRM or corruption)"
    mock_read_epub.side_effect = Exception(error_message)

    dummy_epub_path = tmp_path / "error.epub"
    dummy_epub_path.touch()

    with caplog.at_level(logging.ERROR):
        result = text_processing.extract_epub_content(dummy_epub_path)

    # Assertions
    mock_read_epub.assert_called_once_with(dummy_epub_path)
    assert result is None # Function should return None on error

    # Check logs
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "ERROR"
    assert f"Failed to extract EPUB content from {dummy_epub_path}" in caplog.text
    assert error_message in caplog.text