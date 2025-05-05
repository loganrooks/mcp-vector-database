import os
import logging
import urllib.parse
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file if it exists
# Searches parent directories for .env file as well
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path, verbose=True)

logger = logging.getLogger(__name__)

# Sentinel object to distinguish between no default and default=None
_NO_DEFAULT_SENTINEL = object()

def get_env_variable(var_name: str, default: str | None | object = _NO_DEFAULT_SENTINEL) -> str | None:
    """
    Gets an environment variable.

    Args:
        var_name: The name of the environment variable.
        default: The default value to return if the variable is not set.
                 If not provided (value is _NO_DEFAULT_SENTINEL),
                 a ValueError is raised for missing mandatory variables.
                 If set to None, None is returned if the variable is missing.

    Returns:
        The value of the environment variable as a string, the default value,
        or None if the variable is missing and default was None.

    Raises:
        ValueError: If the variable is not set and no default was provided.
    """
    value = os.getenv(var_name)
    if value is None:
        if default is _NO_DEFAULT_SENTINEL:
            logger.error(f"Mandatory environment variable '{var_name}' not set.")
            raise ValueError(f"Missing required environment variable: {var_name}")
        # If default is None or any other value, return it
        logger.warning(f"Environment variable '{var_name}' not set, using default value: '{default}'")
        # We explicitly allow returning None if default is None
        return default # type: ignore
    return value

def get_int_env_variable(var_name: str, default: int | None = None) -> int | None:
    """Gets an integer environment variable or returns a default. Returns None if default is None and var is not set."""
    # Use the sentinel for get_env_variable if default is None here
    internal_default: str | None | object
    if default is None:
        internal_default = None # Explicitly pass None as default to get_env_variable
    elif default is _NO_DEFAULT_SENTINEL:
         internal_default = _NO_DEFAULT_SENTINEL # Pass sentinel if no default given here
    else:
        internal_default = str(default)

    str_value = get_env_variable(var_name, default=internal_default)

    if str_value is None:
        # This happens if default was None and the env var was not set
        return None

    try:
        return int(str_value)
    except ValueError:
        logger.error(f"Environment variable '{var_name}' has invalid integer value: '{str_value}'.")
        # If a non-None default was provided originally, but value is invalid, raise error.
        # If default was None, str_value wouldn't be None here, so this error is valid.
        raise ValueError(f"Invalid integer value for environment variable: {var_name}")

def get_bool_env_variable(var_name: str, default: bool = False) -> bool:
    """Gets a boolean environment variable or returns a default."""
    # Bool default is never None, so we don't need special handling for None return from get_env_variable
    # We pass the string representation of the boolean default.
    str_value = get_env_variable(var_name, str(default))

    # If env var is not set, get_env_variable returns the default string ('True' or 'False')
    # which is then processed correctly below.
    str_value_lower = str_value.lower() if str_value is not None else ''

    if str_value_lower in ('true', '1', 'yes', 'y'):
        return True
    elif str_value_lower in ('false', '0', 'no', 'n'):
        return False
    else:
        # This case should only be reached if the env var exists but has an invalid boolean value.
        # The default value (False) is returned as per the original logic's warning.
        logger.warning(f"Invalid boolean value '{str_value}' for environment variable '{var_name}'. Using default: {default}")
        return default

# --- Database Settings ---
DB_HOST = get_env_variable("DB_HOST", "localhost")
DB_PORT = get_int_env_variable("DB_PORT", 5432)
DB_USER = get_env_variable("DB_USER", "philograph_user")
DB_PASSWORD_RAW = get_env_variable("DB_PASSWORD") # No default for password
DB_PASSWORD_ENCODED = urllib.parse.quote_plus(DB_PASSWORD_RAW) if DB_PASSWORD_RAW else None
DB_NAME = get_env_variable("DB_NAME", "philograph_db")
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# Async version for psycopg pool
ASYNC_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}" # Using hostname
# ASYNC_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD_ENCODED}@172.20.0.2:{DB_PORT}/{DB_NAME}" # Using explicit IP - REVERTED

DB_POOL_MIN_SIZE = get_int_env_variable("DB_POOL_MIN_SIZE", 1)
DB_POOL_MAX_SIZE = get_int_env_variable("DB_POOL_MAX_SIZE", 10)
# --- Backend API Settings ---
BACKEND_HOST = get_env_variable("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = get_int_env_variable("BACKEND_PORT", 8000)
API_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}" # Construct API_URL

# --- LiteLLM Proxy Settings ---
LITELLM_PROXY_URL = get_env_variable("LITELLM_PROXY_URL", "http://litellm-proxy:4000")
LITELLM_API_KEY = get_env_variable("LITELLM_API_KEY", None) # Optional, depends on proxy config
EMBEDDING_MODEL_NAME = get_env_variable("EMBEDDING_MODEL_NAME", "philo-embed")

# --- Text Processing Settings ---
SOURCE_FILE_DIR = get_env_variable("SOURCE_FILE_DIR", "./data/source_documents")
TARGET_CHUNK_SIZE = get_int_env_variable("TARGET_CHUNK_SIZE", 512)
# pgvector HNSW index parameters (adjust based on performance testing)
PGVECTOR_HNSW_M = get_int_env_variable("PGVECTOR_HNSW_M", 16)
PGVECTOR_HNSW_EF_CONSTRUCTION = get_int_env_variable("PGVECTOR_HNSW_EF_CONSTRUCTION", 64)
EMBEDDING_BATCH_SIZE = get_int_env_variable("EMBEDDING_BATCH_SIZE", 32)
TARGET_EMBEDDING_DIMENSION = get_int_env_variable("TARGET_EMBEDDING_DIMENSION", 768) # From ADR 004

# Optional external service URLs
GROBID_API_URL = get_env_variable("GROBID_API_URL", None)
ANYSTYLE_API_URL = get_env_variable("ANYSTYLE_API_URL", None)

# --- Search Settings ---
SEARCH_TOP_K = get_int_env_variable("SEARCH_TOP_K", 10)

# --- Text Acquisition Settings ---
ZLIBRARY_MCP_SERVER_NAME = get_env_variable("ZLIBRARY_MCP_SERVER_NAME", "zlibrary-mcp")

# --- Logging Settings ---
LOG_LEVEL = get_env_variable("LOG_LEVEL", "INFO").upper()

# --- Application Root Path ---
# Useful for finding project files relative to the source code location
APP_ROOT_DIR = Path(__file__).parent.parent # Points to the 'src' directory

# Ensure SOURCE_FILE_DIR is an absolute path or relative to project root
# Assuming project root is one level above APP_ROOT_DIR (i.e., above 'src')
PROJECT_ROOT_DIR = APP_ROOT_DIR.parent
_source_dir_path = Path(SOURCE_FILE_DIR)
if not _source_dir_path.is_absolute():
    SOURCE_FILE_DIR_ABSOLUTE = (PROJECT_ROOT_DIR / _source_dir_path).resolve()
else:
    SOURCE_FILE_DIR_ABSOLUTE = _source_dir_path

# Basic logging configuration (can be expanded)
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Enable DEBUG logging specifically for psycopg
psycopg_logger = logging.getLogger('psycopg')
psycopg_logger.setLevel(logging.DEBUG)
logger.info("Enabled DEBUG logging for psycopg.")

logger.info("Configuration loaded.")
logger.info(f"Source file directory resolved to: {SOURCE_FILE_DIR_ABSOLUTE}")

# You can add more complex validation or configuration logic here if needed