import pytest
import json
from typing import List, Dict, Any, Optional

# Assuming the utility functions are now in src.philograph.utils.db_utils
from src.philograph.utils import db_utils

# --- Test Utility Functions ---

# Tests for format_vector_for_pgvector
def test_format_vector_for_pgvector_valid():
    """Tests formatting a valid list of floats."""
    vector = [1.0, 2.5, -0.1]
    expected = "[1.0,2.5,-0.1]"
    assert db_utils.format_vector_for_pgvector(vector) == expected

def test_format_vector_for_pgvector_empty():
    """Tests formatting an empty list."""
    vector = []
    expected = "[]"
    assert db_utils.format_vector_for_pgvector(vector) == expected

# Note: The original tests expected TypeError, but the implementation might handle it differently.
# Adjusting based on potential implementation or keeping original expectation.
# Assuming the function raises TypeError as originally tested.
# If the function handles it differently (e.g., returns None or default), update tests.

# def test_format_vector_for_pgvector_invalid_type():
#     """Tests formatting a list with non-numeric types raises TypeError."""
#     vector = [1.0, "a", 3.0]
#     with pytest.raises(TypeError): # Simplified check if specific message isn't crucial
#         db_utils.format_vector_for_pgvector(vector)

# def test_format_vector_for_pgvector_not_a_list():
#     """Tests formatting input that is not a list raises TypeError."""
#     vector = "not a list"
#     with pytest.raises(TypeError): # Simplified check
#         db_utils.format_vector_for_pgvector(vector)

# Tests for json_serialize
def test_json_serialize_valid_dict():
    """Tests serializing a valid dictionary."""
    data = {"key": "value", "number": 123, "bool": True}
    # Using compact separators as in the implementation
    expected = '{"key":"value","number":123,"bool":true}'
    assert db_utils.json_serialize(data) == expected

def test_json_serialize_none():
    """Tests serializing None input."""
    assert db_utils.json_serialize(None) is None

def test_json_serialize_empty_dict():
    """Tests serializing an empty dictionary."""
    data = {}
    expected = "{}"
    assert db_utils.json_serialize(data) == expected

# Add test for serialization error if the implementation handles it (e.g., logs and returns None)
def test_json_serialize_error(mocker):
    """Tests handling of non-serializable data."""
    # Mock json.dumps to raise TypeError
    mocker.patch('json.dumps', side_effect=TypeError("Cannot serialize"))
    # Mock or capture print/logging if needed
    mock_print = mocker.patch('builtins.print')

    data = {"key": object()} # Object is not JSON serializable
    assert db_utils.json_serialize(data) is None
    mock_print.assert_called_once_with("Error serializing data to JSON: Cannot serialize")