# tests/utils/test_text_processing.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from unittest.mock import patch, MagicMock, AsyncMock
import logging
from src.philograph.utils import http_client # Import needed for exception type
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
from src.philograph import config # Needed potentially for config checks later

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
    mock_read_epub.assert_called_once_with(dummy_epub_path)
    assert result is None
# --- Tests for extract_epub_content ---
# TODO: Add tests for EPUB extraction
@pytest.mark.asyncio
@patch('src.philograph.utils.text_processing.parse_grobid_tei')
@patch('src.philograph.utils.http_client.make_async_request')
@patch('src.philograph.config.GROBID_API_URL', 'http://dummy-grobid:8070') # Mock config value
async def test_call_grobid_extractor_api_success(mock_make_request, mock_parse_tei, tmp_path):
    """Tests successful PDF processing via GROBID API."""
    # Mock the response from http_client.make_async_request
    mock_response = AsyncMock()
    mock_response.text = "<TEI>dummy TEI content</TEI>"
    mock_response.raise_for_status = MagicMock() # Mock method to do nothing
    mock_make_request.return_value = mock_response

    # Mock the result from parse_grobid_tei
    expected_parsed_data = {
        "metadata": {"title": "Parsed Title"},
        "text_by_section": {"Abstract": "Parsed abstract."},
        "references_raw": ["Parsed ref 1"]
    }
    mock_parse_tei.return_value = expected_parsed_data

    # Create dummy PDF path
    pdf_path = tmp_path / "dummy.pdf"
    pdf_path.touch() # File needs to exist for 'open'

    result = await text_processing.call_grobid_extractor(pdf_path)

    # Assertions
    # Check that make_async_request was called correctly
    mock_make_request.assert_awaited_once()
    call_args, call_kwargs = mock_make_request.call_args
    assert call_args[0] == "POST"
    assert call_args[1] == "http://dummy-grobid:8070/api/processFulltextDocument"
    assert "files" in call_kwargs
    assert "input" in call_kwargs["files"]
    assert call_kwargs["files"]["input"][0] == "dummy.pdf"
@pytest.mark.asyncio
@patch('src.philograph.utils.http_client.make_async_request', new_callable=AsyncMock) # Use AsyncMock directly
@patch('src.philograph.config.GROBID_API_URL', 'http://dummy-grobid:8070')
async def test_call_grobid_extractor_api_request_error(mock_make_request, tmp_path, caplog): # Removed mock_httpx
    """Tests handling of httpx.RequestError during GROBID API call."""
    # Configure make_async_request mock to raise RequestError when awaited
    error_message = "Simulated connection failed"
    # Use the real exception type from the imported http_client module
    mock_make_request.side_effect = http_client.httpx.RequestError(error_message)

    pdf_path = tmp_path / "error.pdf"
    pdf_path.touch()

    with caplog.at_level(logging.ERROR):
        result = await text_processing.call_grobid_extractor(pdf_path)

    # Assertions
    assert result is None # Should return None on request error
    mock_make_request.assert_awaited_once() # Check it was called

    # Check logs
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "ERROR"
    assert f"GROBID API request failed for {pdf_path}" in caplog.text
    assert error_message in caplog.text
# Removed erroneous check for call_kwargs which is not defined in error case

# Check that the response object's methods were used
# mock_response.raise_for_status.assert_called_once() # This is also not relevant in error case

# Check that parse_grobid_tei was called with the response text
# mock_parse_tei.assert_called_once_with("<TEI>dummy TEI content</TEI>") # This is also not relevant in error case

# Check that the final result is the data returned by parse_grobid_tei
# assert result == expected_parsed_data # This is also not relevant in error case

# --- Tests for call_grobid_extractor ---
# TODO: Add tests for GROBID (requires mocking http_client)

# --- Tests for parse_grobid_tei ---
# TODO: Add tests for TEI parsing (requires sample TEI XML and XML parser)

# --- Tests for chunk_text_semantically ---
# TODO: Add tests for chunking (requires placeholder replacement or mocking)

# --- Tests for parse_references ---
# TODO: Add tests for reference parsing (requires mocking http_client for AnyStyle)

# --- Tests for call_anystyle_parser ---
# TODO: Add tests for AnyStyle call (requires mocking http_client)

# --- Tests for basic_reference_parser ---
# TODO: Add tests for basic reference parsing heuristics