import pytest
import zipfile
import io
from pathlib import Path
from lxml import etree

# Assuming generation scripts are importable this way.
# This might need adjustment based on actual project structure and PYTHONPATH.
from synthetic_test_data.common import ensure_output_directories
from synthetic_test_data.epub_generators.toc import create_epub_navdoc_full
from synthetic_test_data.epub_generators.notes import create_epub_pippin_style_endnotes

# Define expected paths based on generator defaults
# Generators output to synthetic_test_data/generated/epub/(toc or notes)/filename.epub
# Project root is Path(__file__).parent.parent.parent when __file__ is tests/synthetic_test_data/test_epub_generators.py
PROJECT_ROOT = Path(__file__).parent.parent.parent
BASE_SYNTHETIC_EPUB_DIR = PROJECT_ROOT / "synthetic_test_data" / "generated" / "epub"

NAVDOC_FULL_EPUB_NAME = "navdoc_full.epub" # Default filename in generator
NAVDOC_FULL_EPUB_PATH = BASE_SYNTHETIC_EPUB_DIR / "toc" / NAVDOC_FULL_EPUB_NAME

PIPPIN_STYLE_EPUB_NAME = "pippin_style_endnotes.epub" # Default filename in generator
PIPPIN_STYLE_EPUB_PATH = BASE_SYNTHETIC_EPUB_DIR / "notes" / PIPPIN_STYLE_EPUB_NAME


def test_generate_navdoc_full_epub_no_typeerror():
    """
    Test generation of navdoc_full.epub and attempt to parse nav.xhtml.
    Expected to FAIL due to "TypeError: Cannot read properties of undefined (reading 'indexOf')"
    during generation/validation, or when parsing the nav document if generation completes.
    The test asserts that parsing nav.xhtml *should* succeed.
    """
    try:
        ensure_output_directories() # Ensure output directory exists
        # Call with default filename, output path is handled by the function
        create_epub_navdoc_full()
        assert NAVDOC_FULL_EPUB_PATH.exists(), f"{NAVDOC_FULL_EPUB_NAME} was not created at {NAVDOC_FULL_EPUB_PATH}"

        # Attempt to read and parse nav.xhtml from the generated EPUB
        # This is where the 'indexOf' error might manifest if not during generation
        with zipfile.ZipFile(NAVDOC_FULL_EPUB_PATH, 'r') as epub_zip:
            # Try to find nav.xhtml, common paths are OEBPS/nav.xhtml or OPS/nav.xhtml or just nav.xhtml
            nav_xhtml_content = None
            expected_nav_filename = "nav.xhtml" # Reverted to default, as EpubNav() creates nav.xhtml
            for item in epub_zip.namelist():
                if item.endswith(expected_nav_filename):
                    nav_xhtml_content = epub_zip.read(item)
                    break
            
            assert nav_xhtml_content is not None, f"{expected_nav_filename} not found in EPUB"
            
            # Attempt to parse it - this might trigger the error if it's in the content
            # For TDD, we assert it *should* parse successfully.
            parser = etree.XMLParser(recover=False) # recover=False to fail on errors
            etree.parse(io.BytesIO(nav_xhtml_content), parser)
            # If it reaches here without error, the specific 'indexOf' bug related to nav.xhtml parsing
            # might not be triggered by this minimal parse, or the bug is purely in generation.
            # The primary failure is expected during create_epub_navdoc_full or validation.

    except TypeError as e:
        # This is the expected failure path if the TypeError occurs during generation or parsing
        # For a true failing test, we might assert the error message if it's consistent.
        # However, the goal is that this test *passes* when the bug is fixed.
        # So, if a TypeError occurs, the test currently fails, which is correct for TDD.
        # When the bug is fixed, no TypeError should occur, and the assertions above should pass.
        pytest.fail(f"TypeError encountered, this is the bug we want to fix: {e}")
    except Exception as e:
        # Catch any other exception during generation or parsing
        pytest.fail(f"An unexpected error occurred: {e}")

    # If no exception, the test will pass if assertions above pass.
    # This means the bug (if it's the TypeError) didn't manifest as expected by this test's logic,
    # or the bug is more subtle. The user feedback indicates a TypeError.


def test_generate_pippin_style_endnotes_epub_not_blank():
    """
    Test generation of pippin_style_endnotes.epub and check for content.
    Expected to FAIL because the EPUB renders blank.
    The test asserts that key content *should* be present.
    """
    try:
        ensure_output_directories() # Ensure output directory exists
        # Call with default filename, output path is handled by the function
        create_epub_pippin_style_endnotes()
        assert PIPPIN_STYLE_EPUB_PATH.exists(), f"{PIPPIN_STYLE_EPUB_NAME} was not created at {PIPPIN_STYLE_EPUB_PATH}"

        # Attempt to read a key content file and check if it's non-blank
        # (e.g., the first chapter or a content HTML file)
        with zipfile.ZipFile(PIPPIN_STYLE_EPUB_PATH, 'r') as epub_zip:
            # Specifically target the main content chapter file
            expected_content_filename = "chap_pippin_fn.xhtml" # As defined in notes.py
            content_html_path = None
            for item_name in epub_zip.namelist():
                if item_name.endswith(expected_content_filename):
                    content_html_path = item_name
                    break
            
            assert content_html_path is not None, f"{expected_content_filename} not found in pippin_style_endnotes.epub"
            
            content_bytes = epub_zip.read(content_html_path)
            content_str = content_bytes.decode('utf-8')

            # Assert that the content string is not empty or just whitespace
            # and contains some expected text.
            assert content_str.strip(), f"Content file {content_html_path} is blank."
            
            # More specific assertion for the "renders blank" issue.
            # Check for text that should definitely be in the main content.
            expected_text = "This is test chapter content with a note."
            assert expected_text in content_str, \
                f"Expected text '{expected_text}' not found in {content_html_path}. Content: '{content_str[:200]}...'"

    except Exception as e:
        # Catch any exception during generation or parsing
        pytest.fail(f"An unexpected error occurred: {e}")

    # If no exception and assertions pass, the "renders blank" bug didn't manifest as expected.
    # The test is written to fail if the content IS blank.