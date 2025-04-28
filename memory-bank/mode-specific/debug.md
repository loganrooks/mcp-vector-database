# Debug Specific Memory
<!-- Entries below should be added reverse chronologically (newest first) -->

### Tool/Technique: Mocking Async Exception Side Effects - [2025-04-28 17:04:30]
- **Context**: Testing `try...except` blocks around `await` calls where the awaited async function needs to raise an exception.
- **Usage**: Use `@patch('path.to.async_func', new_callable=AsyncMock)` or ensure the mock is async. Set the `side_effect` directly to the exception instance: `mock_async_func.side_effect = MyException("Error message")`. The `AsyncMock` handles raising the exception when the mock is awaited. Avoid complex wrappers like `AsyncMock(side_effect=MyException(...))` unless needed for more advanced scenarios. Ensure test assertions only check behavior relevant to the error path (e.g., return value, logs), not steps that are skipped due to the exception.
- **Effectiveness**: High (Resolved `test_call_grobid_extractor_api_request_error` failure).
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
### Issue: TDD-GROBID-REQ-ERR-20250428 - `test_call_grobid_extractor_api_request_error` failed assertion - [Status: Resolved] - [2025-04-28 17:04:30]
- **Reported**: [2025-04-28 16:57:29] (via TDD Early Return / activeContext) / **Severity**: Medium / **Symptoms**: Test failed `assert result is None`. Mocked `httpx.RequestError` not caught by `call_grobid_extractor`.
- **Investigation**:
    1. Reviewed TDD feedback log (`memory-bank/feedback/tdd-feedback.md`). [2025-04-28 17:01:08]
    2. Read test code (`tests/utils/test_text_processing.py`). [2025-04-28 17:01:26]
    3. Read source code (`src/philograph/utils/text_processing.py`). [2025-04-28 17:01:39]
    4. Hypothesized incorrect async mock `side_effect` setup. [2025-04-28 17:01:39]
    5. Applied fix to mock setup (`side_effect = Exception(...)` directly on `AsyncMock`). [2025-04-28 17:02:05]
    6. Verified test - Failed (`NameError: call_kwargs`). [2025-04-28 17:02:19]
    7. Removed irrelevant assertion (`call_kwargs`). [2025-04-28 17:02:40]
    8. Verified test - Failed (`NameError: mock_parse_tei`). [2025-04-28 17:02:58]
    9. Removed irrelevant assertion (`mock_parse_tei`). [2025-04-28 17:03:19]
   10. Verified test - Passed. [2025-04-28 17:03:34]
- **Root Cause**: Incorrect async mock setup (`side_effect` assignment) and presence of irrelevant assertions copied from the success test case (`test_call_grobid_extractor_api_success`) which caused `NameError`s after the primary mocking issue was fixed. [2025-04-28 17:04:30]
- **Fix Applied**: Corrected `mock_make_request.side_effect` assignment in `test_call_grobid_extractor_api_request_error` to directly use the exception instance with an `AsyncMock`. Removed unnecessary `@patch` for `httpx`. Removed irrelevant assertions checking `call_kwargs` and `mock_parse_tei`. Commit: d07e7f4. [2025-04-28 17:04:30]
- **Verification**: `pytest tests/utils/test_text_processing.py::test_call_grobid_extractor_api_request_error` passed. [2025-04-28 17:03:34]
- **Related Issues**: [See TDD Feedback 2025-04-28 16:53:10]
<!-- Append new patterns using the format below -->

## Issue History
<!-- Append new issue details using the format below -->
### Issue: TDD-DBPOOL-FAIL-20250428 - Re-investigation of `test_get_db_pool_failure` - [Status: Confirmed Passing] - [2025-04-28 13:24:54]
- **Reported**: [2025-04-28 13:19:45] (via TDD Feedback) / **Severity**: Medium (Discrepancy) / **Symptoms**: TDD reported test failure (`DID NOT RAISE <class 'ConnectionError'>`) contradicting previous Debug report of success.
- **Investigation**:
    1. Reviewed TDD feedback confirming failure report. [2025-04-28 13:22:16]
    2. Executed `pytest tests/data_access/test_db_layer.py::test_get_db_pool_failure` - Result: PASSED. [2025-04-28 13:22:52]
    3. Read `tests/data_access/test_db_layer.py` - Confirmed test code uses correct mocking strategy. [2025-04-28 13:23:26]
    4. Read `src/philograph/data_access/db_layer.py` - Confirmed `get_db_pool` correctly handles `psycopg.Error` and raises `ConnectionError`. [2025-04-28 13:23:48]
    5. Re-executed `pytest tests/data_access/test_db_layer.py::test_get_db_pool_failure` - Result: PASSED. [2025-04-28 13:24:10]
- **Root Cause**: Discrepancy likely caused by TDD verifying against an older code state where the fix was not fully applied/committed. The current codebase contains the correct, working test and source code.
- **Fix Applied**: None required.
- **Verification**: Test passed consistently in current code state via `pytest`.
- **Related Issues**: [See Issue-ID: TDD-DBPOOL-FAIL-20250428] (Original entry below)
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