import pytest
import os
from unittest.mock import patch

# Import the functions to be tested
# Assuming config.py is importable from the tests directory context
# Adjust the import path if necessary based on project structure/PYTHONPATH
from src.philograph import config

# Reload config module for each test function to isolate environment changes
@pytest.fixture(autouse=True)
def reload_config():
    import importlib
    # Reload the config module to pick up patched env vars within tests
    importlib.reload(config)

@patch.dict(os.environ, {"EXISTING_VAR": "existing_value"})
def test_get_env_variable_exists():
    """Test retrieving an existing environment variable."""
    assert config.get_env_variable("EXISTING_VAR") == "existing_value"

@patch.dict(os.environ, {}, clear=True) # Start with a clean environment
def test_get_env_variable_not_exists_with_default():
    """Test retrieving a non-existent variable with a default value."""
    assert config.get_env_variable("NON_EXISTENT_VAR", "default_value") == "default_value"

@patch.dict(os.environ, {}, clear=True) # Start with a clean environment
def test_get_env_variable_not_exists_no_default_raises_error():
    """Test retrieving a non-existent variable without a default raises ValueError."""
    with pytest.raises(ValueError) as excinfo:
        config.get_env_variable("MISSING_VAR_NO_DEFAULT")
    assert "Missing required environment variable: MISSING_VAR_NO_DEFAULT" in str(excinfo.value)

@patch.dict(os.environ, {}, clear=True) # Start with a clean environment
def test_get_env_variable_not_exists_default_none_returns_none():
    """Test retrieving a non-existent variable with default=None returns None."""
    assert config.get_env_variable("MISSING_VAR_DEFAULT_NONE", default=None) is None
# TODO: Add tests for get_int_env_variable
# TODO: Add tests for get_bool_env_variable
# TODO: Add tests for specific config constants (e.g., DATABASE_URL format) using mocks
# --- Tests for get_int_env_variable ---

@patch.dict(os.environ, {"EXISTING_INT": "123"})
def test_get_int_env_variable_exists():
    """Test retrieving an existing integer environment variable."""
    assert config.get_int_env_variable("EXISTING_INT") == 123

@patch.dict(os.environ, {}, clear=True)
def test_get_int_env_variable_not_exists_with_default():
    """Test retrieving a non-existent int variable with a default value."""
    assert config.get_int_env_variable("NON_EXISTENT_INT", 456) == 456

@patch.dict(os.environ, {}, clear=True)
def test_get_int_env_variable_not_exists_default_none():
    """Test retrieving a non-existent int variable with default=None returns None."""
    assert config.get_int_env_variable("NON_EXISTENT_INT_NONE", default=None) is None

@patch.dict(os.environ, {"INVALID_INT": "not-a-number"})
def test_get_int_env_variable_invalid_value_raises_error():
    """Test retrieving an int variable with an invalid value raises ValueError."""
    with pytest.raises(ValueError) as excinfo:
        config.get_int_env_variable("INVALID_INT")
    assert "Invalid integer value for environment variable: INVALID_INT" in str(excinfo.value)

@patch.dict(os.environ, {}, clear=True)
def test_get_int_env_variable_no_default_raises_error():
    """Test retrieving a non-existent int variable with no default raises ValueError."""
    # This relies on the underlying get_env_variable raising the error
    with pytest.raises(ValueError) as excinfo:
        # We need to bypass the type hint for default to test the sentinel logic
        config.get_int_env_variable("MISSING_INT_NO_DEFAULT", default=config._NO_DEFAULT_SENTINEL) # type: ignore
    assert "Missing required environment variable: MISSING_INT_NO_DEFAULT" in str(excinfo.value)


# --- Tests for get_bool_env_variable ---

@pytest.mark.parametrize("true_val", ['true', '1', 'yes', 'y', 'TRUE', 'YES'])
@patch.dict(os.environ, {}) # Start clean for each param
def test_get_bool_env_variable_true_values(true_val):
    """Test retrieving boolean 'true' from various string representations."""
    os.environ["BOOL_VAR"] = true_val
    # Need to reload config because the module-level call to get_bool_env_variable
    # might have already happened with a different default or value.
    # The fixture doesn't help here as the parametrization runs before the fixture.
    import importlib
    importlib.reload(config)
    assert config.get_bool_env_variable("BOOL_VAR", default=False) is True
    del os.environ["BOOL_VAR"] # Clean up for next param

@pytest.mark.parametrize("false_val", ['false', '0', 'no', 'n', 'FALSE', 'NO'])
@patch.dict(os.environ, {}) # Start clean for each param
def test_get_bool_env_variable_false_values(false_val):
    """Test retrieving boolean 'false' from various string representations."""
    os.environ["BOOL_VAR"] = false_val
    import importlib
    importlib.reload(config)
    assert config.get_bool_env_variable("BOOL_VAR", default=True) is False
    del os.environ["BOOL_VAR"] # Clean up for next param

@patch.dict(os.environ, {}, clear=True)
def test_get_bool_env_variable_not_exists_defaults_false():
    """Test retrieving a non-existent bool variable defaults to False."""
    import importlib
    importlib.reload(config)
    assert config.get_bool_env_variable("NON_EXISTENT_BOOL") is False

@patch.dict(os.environ, {"INVALID_BOOL": "maybe"})
def test_get_bool_env_variable_invalid_value_defaults_false():
    """Test retrieving an invalid bool variable defaults to False."""
    import importlib
    importlib.reload(config)
    assert config.get_bool_env_variable("INVALID_BOOL", default=False) is False

@patch.dict(os.environ, {"INVALID_BOOL_TRUE_DEFAULT": "maybe"})
def test_get_bool_env_variable_invalid_value_uses_explicit_default():
    """Test retrieving an invalid bool variable uses the explicit default (True)."""
    import importlib
    importlib.reload(config)
    assert config.get_bool_env_variable("INVALID_BOOL_TRUE_DEFAULT", default=True) is True