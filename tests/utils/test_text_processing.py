# tests/utils/test_text_processing.py
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
# TODO: Add tests for EPUB extraction

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