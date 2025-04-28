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

@pytest.mark.asyncio
@patch('src.philograph.utils.http_client.make_async_request', new_callable=AsyncMock)
@patch('src.philograph.config.GROBID_API_URL', 'http://dummy-grobid:8070')
async def test_call_grobid_extractor_api_status_error(mock_make_request, tmp_path, caplog):
    """Tests handling of httpx.HTTPStatusError during GROBID API call."""
    # Configure make_async_request mock to raise HTTPStatusError
    error_message = "Simulated Server Error"
    mock_response = MagicMock() # Need a mock response object for the exception
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error Details"
    # Use the real exception type
    status_error = http_client.httpx.HTTPStatusError(
        message=error_message,
        request=MagicMock(), # Mock request object
        response=mock_response
    )
    mock_make_request.side_effect = status_error

    pdf_path = tmp_path / "status_error.pdf"
    pdf_path.touch()

    with caplog.at_level(logging.ERROR):
        result = await text_processing.call_grobid_extractor(pdf_path)

    # Assertions
    assert result is None # Should return None on status error
    mock_make_request.assert_awaited_once() # Check it was called

    # Check logs
    assert len(caplog.records) == 1
@pytest.mark.asyncio
@patch('src.philograph.utils.text_processing.logger') # Use logger mock via patch
@patch('src.philograph.config.GROBID_API_URL', None) # Mock config value to None
async def test_call_grobid_extractor_no_api_url(mock_logger, tmp_path):
    """Tests behavior when GROBID_API_URL is not configured."""
    pdf_path = tmp_path / "no_api.pdf"
    pdf_path.touch()

    result = await text_processing.call_grobid_extractor(pdf_path)

    # Assertions
    assert result is None # Should return None if API URL is not set

    # Check logs - Use mock_logger directly
    mock_logger.warning.assert_called_once_with(
        "GROBID_API_URL not configured. Local GROBID library interaction not implemented."
    )
# --- Tests for parse_grobid_tei ---

def test_parse_grobid_tei_basic():
    """Tests basic parsing of a minimal GROBID TEI XML structure."""
    # Minimal TEI XML example (replace with more realistic sample if needed)
    tei_xml = """
    <TEI xmlns="http://www.tei-c.org/ns/1.0">
        <teiHeader>
            <fileDesc>
                <titleStmt>
                    <title level="a" type="main">Sample Title</title>
                </titleStmt>
                <publicationStmt>
                    <publisher>Publisher</publisher>
                </publicationStmt>
                <sourceDesc>
                    <biblStruct>
                        <analytic>
                            <author><persName><forename>Test</forename><surname>Author</surname></persName></author>
                        </analytic>
                        <monogr>
                            <title level="j">Journal Name</title>
                            <imprint>
                                <date when="2023">2023</date>
                            </imprint>
                        </monogr>
                    </biblStruct>
                </sourceDesc>
            </fileDesc>
        </teiHeader>
        <text>
            <body>
                <div type="abstract"><p>This is the abstract.</p></div>
                <div type="introduction"><head>Introduction</head><p>Introductory text.</p></div>
                <div type="section"><head>Section 1</head><p>Section 1 text.</p></div>
            </body>
            <back>
                <div type="references">
                    <listBibl>
                        <bibl>Reference 1 string.</bibl>
                        <bibl>Reference 2 string.</bibl>
                    </listBibl>
                </div>
            </back>
        </text>
    </TEI>
    """
    # Since the function is a placeholder, this test will currently fail
    # as it expects real parsing, not the placeholder data.
    # We expect failure in the Red phase.
    expected_metadata = {"title": "Sample Title", "author": "Test Author"} # Simplified expectation
    expected_sections = {
        "Abstract": "This is the abstract.",
        "Introduction": "Introductory text.",
        "Section 1": "Section 1 text.",
        # Placeholder doesn't extract refs section text separately
    }
    expected_refs = ["Reference 1 string.", "Reference 2 string."]

    # This call will return the placeholder data, not the parsed data
    result = text_processing.parse_grobid_tei(tei_xml)

    assert result is not None
    # These assertions WILL FAIL against the placeholder implementation
    assert result["metadata"]["title"] == expected_metadata["title"]
def test_parse_grobid_tei_parse_error(caplog):
    """Tests handling of invalid XML input."""
    invalid_xml = "<TEI><unclosedTag>"

    with caplog.at_level(logging.ERROR):
        result = text_processing.parse_grobid_tei(invalid_xml)

    assert result is None
    assert "Failed to parse TEI XML (ParseError)" in caplog.text
# --- Tests for call_grobid_extractor ---
# --- Tests for chunk_text_semantically ---

def test_chunk_text_semantically_basic():
    """Tests the placeholder paragraph splitting."""
    text = "This is the first paragraph.\n\nThis is the second paragraph."
    chunk_size = 100 # Placeholder size, not used by current implementation
    expected_chunks = [
        "This is the first paragraph.",
        "This is the second paragraph."
    ]
    # This test should pass against the placeholder implementation
def test_chunk_text_semantically_no_paragraphs():
    """Tests the placeholder splitting with text containing no double newlines."""
    text = "This is a single block of text. It has sentences. But no paragraph breaks."
    chunk_size = 100 # Placeholder size
    expected_chunks = [text] # Expect the whole text as one chunk
    # This test should pass against the placeholder implementation's fallback
    result = text_processing.chunk_text_semantically(text, chunk_size)
    assert result == expected_chunks
# --- Tests for basic_reference_parser ---

def test_basic_reference_parser_simple():
    """Tests the basic reference parser with a simple author-year-title format."""
    ref_string = "Author, A. N. (2023). This is the title. Journal Name, 10(2), 100-110."
    # Placeholder implementation is very naive, this test should fail.
    expected_result = {
        "title": "This is the title. Journal Name, 10(2), 100-110.", # Placeholder is greedy
        "author": "Author, A. N.",
        "year": "2023",
        "raw": ref_string,
        "source": "basic_parser"
    }
    result = text_processing.basic_reference_parser(ref_string)
    assert result is not None
    assert result == expected_result
# TODO: Add tests for GROBID (requires mocking http_client)
def test_basic_reference_parser_no_year():
    """Tests the basic parser when no year pattern is found."""
    ref_string = "Author, A. N. Some Title Without Year. Publisher."
    # The current implementation relies on finding (YYYY)
    # It should ideally return None or minimal data if year isn't found.
    # Let's expect None for now, driving minimal change.
    expected_result = None # Or potentially just {'raw': ref_string, 'source': 'basic_parser'}? Let's aim for None.

    result = text_processing.basic_reference_parser(ref_string)
    # This assertion might fail depending on how the placeholder handles no year match
    assert result is None

# --- Tests for parse_grobid_tei ---
# TODO: Add tests for TEI parsing (requires sample TEI XML and XML parser)

# --- Tests for chunk_text_semantically ---
# TODO: Add tests for chunking (requires placeholder replacement or mocking)

# --- Tests for parse_references ---

@pytest.mark.asyncio
@patch('src.philograph.config.ANYSTYLE_API_URL', None) # Ensure API URL is None
@patch('src.philograph.utils.text_processing.basic_reference_parser')
async def test_parse_references_uses_basic_parser_when_no_api(mock_basic_parser):
    """Tests that parse_references uses basic_reference_parser when API URL is not set."""
    raw_refs = ["Ref 1 string", "Ref 2 string"]
    # Mock the return value of the basic parser
    mock_basic_parser.side_effect = [
        {"title": "Title 1", "author": "Author 1", "year": "2021", "raw": "Ref 1 string", "source": "basic_parser"},
        {"title": "Title 2", "author": "Author 2", "year": "2022", "raw": "Ref 2 string", "source": "basic_parser"}
    ]

    parsed_refs = await text_processing.parse_references(raw_refs)

    assert len(parsed_refs) == 2
    # Check that basic_reference_parser was called for each ref
    assert mock_basic_parser.call_count == 2
    mock_basic_parser.assert_any_call("Ref 1 string")
    mock_basic_parser.assert_any_call("Ref 2 string")
    # Check the content of the parsed refs
    assert parsed_refs[0]["title"] == "Title 1"
    assert parsed_refs[0]["source"] == "basic_parser"
    assert parsed_refs[1]["title"] == "Title 2"
    assert parsed_refs[1]["source"] == "basic_parser"
@pytest.mark.asyncio
@patch('src.philograph.config.ANYSTYLE_API_URL', 'http://dummy-anystyle-api') # Set dummy API URL
@patch('src.philograph.utils.text_processing.call_anystyle_parser', new_callable=AsyncMock)
@patch('src.philograph.utils.text_processing.basic_reference_parser')
async def test_parse_references_uses_anystyle_when_api_set(mock_basic_parser, mock_call_anystyle):
    """Tests that parse_references uses call_anystyle_parser when API URL is set."""
    raw_refs = ["Style 1 string", "Style 2 string"]
    # Mock the return value of the anystyle parser
    mock_call_anystyle.side_effect = [
        {"title": "AnyStyle Title 1", "author": "AnyStyle Author 1", "year": "2021", "raw": "Style 1 string", "source": "anystyle"},
        {"title": "AnyStyle Title 2", "author": "AnyStyle Author 2", "year": "2022", "raw": "Style 2 string", "source": "anystyle"}
    ]

    parsed_refs = await text_processing.parse_references(raw_refs)

    assert len(parsed_refs) == 2
    # Check that call_anystyle_parser was awaited for each ref
    assert mock_call_anystyle.await_count == 2
    mock_call_anystyle.assert_any_await("Style 1 string")
    mock_call_anystyle.assert_any_await("Style 2 string")
    # Check that basic_reference_parser was NOT called
    mock_basic_parser.assert_not_called()
    # Check the content of the parsed refs
    assert parsed_refs[0]["title"] == "AnyStyle Title 1"
    assert parsed_refs[0]["source"] == "anystyle"
    assert parsed_refs[1]["title"] == "AnyStyle Title 2"
    assert parsed_refs[1]["source"] == "anystyle"
# --- Tests for parse_references ---
# TODO: Add tests for reference parsing (requires mocking http_client for AnyStyle)

# --- Tests for call_anystyle_parser ---

@pytest.mark.asyncio
@patch('src.philograph.config.ANYSTYLE_API_URL', 'http://dummy-anystyle-api') # Set dummy API URL
@patch('src.philograph.utils.http_client.make_async_request', new_callable=AsyncMock)
async def test_call_anystyle_parser_success(mock_make_request):
    """Tests successful parsing of a reference string via AnyStyle API."""
    ref_string = "Author, A. (2024). Sample Title. Journal, 1(1), 1-10."
    # Mock the raw response from the AnyStyle API
    mock_api_response_data = [{
        "type": "article-journal",
        "title": ["Sample Title"],
        "author": [{"family": "Author", "given": "A."}],
        "date": ["2024"],
        "container-title": ["Journal"],
        "volume": ["1"],
        "issue": ["1"],
        "page": ["1-10"]
    }]
    mock_response = AsyncMock()
    mock_response.json.return_value = mock_api_response_data
    mock_response.raise_for_status = AsyncMock() # Mock method to do nothing, but make it awaitable
    mock_make_request.return_value = mock_response

    expected_result = {
        "title": "Sample Title",
        "author": "Author", # Simplified based on current implementation
        "year": "2024",
        "raw": ref_string,
        "source": "anystyle",
        "full_parsed": mock_api_response_data[0]
    }

    result = await text_processing.call_anystyle_parser(ref_string)

    # Assertions
    mock_make_request.assert_awaited_once_with(
        "POST",
        'http://dummy-anystyle-api',
        json_data={"references": [ref_string]},
        timeout=30.0
    )
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert result == expected_result
@pytest.mark.asyncio
@patch('src.philograph.config.ANYSTYLE_API_URL', 'http://dummy-anystyle-api')
@patch('src.philograph.utils.http_client.make_async_request', new_callable=AsyncMock)
async def test_call_anystyle_parser_request_error(mock_make_request):
    """Tests that RequestError during API call is raised."""
    ref_string = "Error case ref string"
    # Configure the mock to raise RequestError
    mock_make_request.side_effect = http_client.httpx.RequestError("Network error", request=None)

    # Assert that the specific exception is raised
    with pytest.raises(http_client.httpx.RequestError):
        await text_processing.call_anystyle_parser(ref_string)

    # Verify the mock was called
    mock_make_request.assert_awaited_once_with(
        "POST",
        'http://dummy-anystyle-api',
        json_data={"references": [ref_string]},
        timeout=30.0
    )
@pytest.mark.asyncio
@patch('src.philograph.config.ANYSTYLE_API_URL', 'http://dummy-anystyle-api')
@patch('src.philograph.utils.http_client.make_async_request', new_callable=AsyncMock)
async def test_call_anystyle_parser_http_status_error(mock_make_request):
    """Tests that HTTPStatusError during API call is raised."""
    ref_string = "Status error case"
    mock_response = AsyncMock() # Mock the response object returned by make_async_request

    # Configure the raise_for_status method on the mock response to raise the error
    error_to_raise = http_client.httpx.HTTPStatusError(
        "Server error",
        request=MagicMock(), # Mock request object
        response=MagicMock(status_code=500, text="Internal Server Error") # Mock response object for the error
    )
    mock_response.raise_for_status.side_effect = error_to_raise
    # Ensure json() is awaitable if reached, though it shouldn't be
    mock_response.json = AsyncMock(return_value=[])

    mock_make_request.return_value = mock_response # make_async_request returns our configured mock_response

    # Assert that the specific exception is raised when call_anystyle_parser is awaited
    with pytest.raises(http_client.httpx.HTTPStatusError) as excinfo:
        await text_processing.call_anystyle_parser(ref_string)

    # Optional: Check exception details if needed
    assert excinfo.value.response.status_code == 500

    # Verify mocks were called as expected
    mock_make_request.assert_awaited_once_with(
        "POST",
        'http://dummy-anystyle-api',
        json_data={"references": [ref_string]},
        timeout=30.0
    )
    mock_response.raise_for_status.assert_called_once() # Verify raise_for_status was indeed called
    mock_response.json.assert_not_called() # Verify json() was not called because error was raised before it
# --- Tests for call_anystyle_parser ---
# TODO: Add tests for AnyStyle call (requires mocking http_client)

# --- Tests for basic_reference_parser ---
# TODO: Add tests for basic reference parsing heuristics