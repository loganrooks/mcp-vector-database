import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

# Assuming config values are needed and potentially mocked
from philograph import config
from philograph.ingestion import pipeline
from philograph.data_access import db_layer # For mocking types if needed

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


# --- Tests for get_embeddings_in_batches ---
# TODO: Add tests

# --- Tests for extract_content_and_metadata ---
# TODO: Add tests (dispatch logic, mocking text_processing)

# --- Tests for process_document (Moved) ---
# Single file tests moved to tests/ingestion/test_pipeline_single_file.py
# Directory tests moved to tests/ingestion/test_pipeline_directory.py
