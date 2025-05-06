# tests/utils/test_text_chunking.py
import pytest
from src.philograph.utils import text_processing

# --- Tests for chunk_text_semantically ---

def test_chunk_text_semantically_basic():
    """Tests the placeholder paragraph splitting."""
    text = "This is the first paragraph.\n\nThis is the second paragraph."
    chunk_size = 100 # Placeholder size, not used by current implementation
    # With semchunk and word count, the whole text fits in one chunk
    expected_chunks = [text]
    # This test verifies the actual semchunk behavior with the simple counter
    result = text_processing.chunk_text_semantically(text, chunk_size)
    assert result == expected_chunks

def test_chunk_text_semantically_no_paragraphs():
    """Tests the placeholder splitting with text containing no double newlines."""
    text = "This is a single block of text. It has sentences. But no paragraph breaks."
    chunk_size = 100 # Placeholder size
    expected_chunks = [text] # Expect the whole text as one chunk
    # This test should pass against the placeholder implementation's fallback
    result = text_processing.chunk_text_semantically(text, chunk_size)
    assert result == expected_chunks