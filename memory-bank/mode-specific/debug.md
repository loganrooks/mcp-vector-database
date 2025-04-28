# Debug Specific Memory
<!-- Entries below should be added reverse chronologically (newest first) -->

## Debugging Tools & Techniques
<!-- Append tool notes using the format below -->
### Tool/Technique: Nested Async Mocking for Exception - [2025-04-28 13:05:04]
- **Context**: Testing exception handling (`try...except psycopg.Error`) within nested `async with` blocks (`pool.connection()` and `conn.cursor()`) in `psycopg_pool`.
- **Usage**: Mock the chain: `AsyncConnectionPool` -> `pool_instance` -> `pool_conn_cm` -> `mock_conn` -> `cursor_cm` -> `mock_cur`. Set `mock_cur.execute.side_effect = psycopg.OperationalError(...)`. This ensures the exception originates from the correct point within the nested contexts, allowing the `except` block in the tested function (`get_db_pool`) to catch it. Standard `AsyncMock` was sufficient; custom `AsyncContextManagerMock` was not needed for this specific scenario, and raising the exception too early (e.g., from `pool_conn_cm.__aenter__`) caused `TypeError`.
- **Effectiveness**: High (Resolved the test failure).

## Performance Observations
<!-- Append performance notes using the format below -->

## Environment-Specific Notes
<!-- Append environment notes using the format below -->

## Recurring Bug Patterns
<!-- Append new patterns using the format below -->

## Issue History
<!-- Append new issue details using the format below -->
### Issue: TDD-DBPOOL-FAIL-20250428 - `test_get_db_pool_failure` not raising ConnectionError - [Status: Resolved] - [2025-04-28 13:05:04]
- **Reported**: ~[2025-04-28 12:26:14] (via TDD Early Return) / **Severity**: High / **Symptoms**: `AssertionError: ConnectionError was not raised` in `tests/data_access/test_db_layer.py::test_get_db_pool_failure`.
- **Investigation**:
    1. Reviewed TDD logs (`memory-bank/feedback/tdd-feedback.md`) - multiple mocking attempts failed. [2025-04-28 12:48:29]
    2. Searched web for mocking async context managers raising exceptions. Found blog post suggesting custom mock class. [2025-04-28 12:51:04]
    3. Attempted custom `AsyncContextManagerMock` raising error in `__aenter__`. Failed with `TypeError: 'coroutine' object does not support the asynchronous context manager protocol`. [2025-04-28 13:04:09]
    4. Corrected mocking strategy based on `TypeError`: needed to raise exception from `mock_cursor.execute()` within nested contexts. [2025-04-28 13:04:29]
- **Root Cause**: Incorrect mocking strategy. The `psycopg.OperationalError` needed to be raised from the mock `cursor.execute()` method, simulating failure during the `SELECT 1` check within the nested `async with` blocks of `get_db_pool`. Previous attempts raised the error too early in the context management chain. [2025-04-28 13:05:04]
- **Fix Applied**: Modified `test_get_db_pool_failure` to correctly mock the chain `AsyncConnectionPool` -> `pool_instance` -> `pool_conn_cm` -> `mock_conn` -> `cursor_cm` -> `mock_cur`, and set `mock_cur.execute.side_effect = psycopg.OperationalError(...)`. [2025-04-28 13:04:51]
- **Verification**: `pytest tests/data_access/test_db_layer.py::test_get_db_pool_failure` passed. [2025-04-28 13:05:04]
- **Related Issues**: None.