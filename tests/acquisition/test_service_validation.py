import pytest

# Import the module/functions under test
from src.philograph.acquisition import service

# --- Tests for _validate_book_details (Kept from previous version, slightly adapted) ---

def test_validate_book_details_success():
    """Test validation passes with required and optional keys."""
    details = {
        "title": "Valid Book", "author": "Author", "md5": "validmd5",
        "download_url": "http://example.com/dl", "extension": "pdf",
        "unexpected_key": "allowed" # Unexpected keys are allowed but warned
    }
    assert service._validate_book_details(details) is True

def test_validate_book_details_missing_required_md5():
    """Test validation fails if md5 is missing."""
    details = {"title": "Missing MD5", "download_url": "http://example.com/dl"}
    assert service._validate_book_details(details) is False

def test_validate_book_details_missing_required_url():
    """Test validation fails if download_url is missing."""
    details = {"title": "Missing URL", "md5": "somemd5"}
    assert service._validate_book_details(details) is False

def test_validate_book_details_invalid_type_md5():
    """Test validation fails if md5 is not a string."""
    details = {"title": "Invalid MD5", "md5": 12345, "download_url": "http://example.com/dl"}
    assert service._validate_book_details(details) is False

def test_validate_book_details_invalid_type_url():
    """Test validation fails if download_url is not a string."""
    details = {"title": "Invalid URL", "md5": "somemd5", "download_url": None}
    assert service._validate_book_details(details) is False

def test_validate_book_details_not_dict():
    """Test validation fails if input is not a dictionary."""
    assert service._validate_book_details("not a dict") is False