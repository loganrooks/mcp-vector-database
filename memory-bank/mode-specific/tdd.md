# TDD Specific Memory
<!-- Entries below should be added reverse chronologically (newest first) -->

### Test Execution: Unit - [2025-04-28 09:54:06]
- **Trigger**: Manual run after adding tests for `mcp_utils`
- **Outcome**: PASS / **Summary**: 6 tests passed
- **Failed Tests**: None
- **Coverage Change**: N/A
- **Notes**: Confirmed simulated MCP tool calls and error handling work as expected.
### Test Execution: Unit - [2025-04-28 09:51:12]
### TDD Cycle: MCP Utils - [2025-04-28 09:54:06]
- **Red**: Wrote tests for `call_mcp_tool` simulation in `tests/test_mcp_utils.py`.
- **Green**: All 6 tests passed immediately as the function contains mock logic.
- **Refactor**: N/A.
- **Files Changed**: `tests/test_mcp_utils.py`
- **Outcome**: Cycle completed. Simulated MCP tool calls and error handling tested.
- **Trigger**: Manual run after adding tests for `http_client`
- **Outcome**: PASS / **Summary**: 12 tests passed
- **Failed Tests**: None
- **Coverage Change**: N/A
- **Notes**: Confirmed async client management and request function (`make_async_request`) work correctly using `pytest-httpx` for mocking. Fixed initial `ImportError` by adding `h2` via `httpx[http2]` extra. Fixed POST test assertion to compare parsed JSON.
### Test Execution: Unit - [2025-04-28 09:40:31]
### TDD Cycle: HTTP Client - [2025-04-28 09:51:12]
- **Red**: Wrote initial tests for `get_async_client` and `close_async_client` in `tests/test_http_client.py`. Tests failed due to `ImportError: Using http2=True, but the 'h2' package is not installed`.
- **Green**: Added `[http2]` extra to `httpx` in `requirements.txt` and installed dependencies. Initial tests passed. Added tests for `make_async_request` using `pytest-httpx`. One test failed due to assertion comparing raw bytes instead of parsed JSON. Fixed assertion. All 12 tests passed.
- **Refactor**: N/A.
- **Files Changed**: `requirements.txt`, `tests/test_http_client.py`
- **Outcome**: Cycle completed. Async HTTP client management and request functions tested using mocking.
- **Trigger**: Manual run after adding tests for `file_utils`
- **Outcome**: PASS / **Summary**: 23 tests passed
- **Failed Tests**: None
- **Coverage Change**: N/A
- **Notes**: Confirmed basic file utility functions pass.
### Test Execution: Unit - [2025-04-28 09:34:12]
### TDD Cycle: File Utils - [2025-04-28 09:40:31]
- **Red**: Wrote tests for `check_file_exists`, `check_directory_exists`, `get_file_extension`, `join_paths` in `tests/test_file_utils.py`. Test collection failed due to `NameError: name 'Optional' is not defined` in `src/philograph/utils/file_utils.py`.
- **Green**: Added `from typing import List, Optional, Generator` to `src/philograph/utils/file_utils.py`. Ran tests, 16 passed. Added tests for `list_files_in_directory`. Ran tests again, all 23 passed.
- **Refactor**: N/A.
- **Files Changed**: `src/philograph/utils/file_utils.py`, `tests/test_file_utils.py`
- **Outcome**: Cycle completed. Basic file utility functions tested and import error fixed.
- **Trigger**: Manual run after refactoring config helpers
- **Outcome**: PASS / **Summary**: 24 tests passed
- **Failed Tests**: None
- **Coverage Change**: N/A (Initial tests for module)
- **Notes**: Confirmed `get_env_variable`, `get_int_env_variable`, `get_bool_env_variable` work correctly, including handling of `default=None` and mandatory variables via `.env` loaded by `pytest-dotenv`.
## Test Execution Results
### TDD Cycle: Config Helpers - [2025-04-28 09:34:12]
- **Red**: Wrote initial tests for `get_env_variable` in `tests/test_config.py`. Tests failed during collection due to `ValueError` for mandatory `DB_PASSWORD` accessed at module level in `src/philograph/config.py`.
- **Green**: Refactored `get_env_variable` (and related int/bool helpers) in `src/philograph/config.py` to use a sentinel object, correctly handling `default=None`. Added `pytest-dotenv` to `requirements.txt`, created `.env` with dummy `DB_PASSWORD`. Added test case for `default=None`. Ran `pytest tests/test_config.py`, 4 tests passed. Added tests for int/bool helpers. Ran `pytest tests/test_config.py`, all 24 tests passed.
- **Refactor**: N/A for this cycle (refactoring was part of Green phase to fix collection error).
- **Files Changed**: `src/philograph/config.py`, `tests/test_config.py`, `requirements.txt`, `.env`
- **Outcome**: Cycle completed. Configuration helper functions are tested and correctly handle mandatory and optional environment variables, resolving test collection issues.
<!-- Append test run summaries using the format below -->

## TDD Cycles Log
<!-- Append TDD cycle outcomes using the format below -->

## Test Fixtures
<!-- Append new fixtures using the format below -->

## Test Coverage Summary
<!-- Update coverage summary using the format below -->

## Test Plans (Driving Implementation)
<!-- Append new test plans using the format below -->