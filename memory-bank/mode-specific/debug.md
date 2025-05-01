# Debug Specific Memory
<!-- Entries below should be added reverse chronologically (newest first) -->

### Issue: PYTEST-SIGKILL-DB-CONN-20250430 - Pytest SIGKILL / DB Connection Failure - [Status: Open] - [2025-04-30 07:31:51]
- **Reported**: [2025-04-30 07:15:15] (via TDD Feedback) / **Severity**: High / **Symptoms**: `pytest` in `philograph-backend` container terminates with `SIGKILL` or `ConnectionError: Database connection pool initialization failed ([Errno -2] Name or service not known)` when initializing `psycopg_pool`.
- **Investigation**:
    1. Confirmed `SIGKILL` persists with 2GB memory limit. [Ref: TDD Feedback 2025-04-30 07:15:15]
    2. Added `tracemalloc` to `api/main.py` lifespan - `SIGKILL` occurred before logs printed. [2025-04-30 07:24:29]
    3. Moved `tracemalloc` to top of `api/main.py` - `pytest` failed with `ConnectionError` before `SIGKILL`, `tracemalloc` logs not printed. [2025-04-30 07:26:13]
    4. Isolated DB pool init (`db_layer.get_db_pool()`) via `docker compose exec python -c "..."` - Failed with `SIGKILL` after logging `[Errno -2] Name or service not known`. [2025-04-30 07:29:43]
    5. Verified OS-level hostname resolution (`getent hosts db`) - Succeeded (`172.20.0.2 db`). [2025-04-30 07:30:07]
    6. Temporarily hardcoded DB IP (`172.20.0.2`) in `config.py`. Re-ran isolation test - Failed with `ConnectionError` / `PoolTimeout`, still logging `[Errno -2] Name or service not known`. [2025-04-30 07:31:25]
- **Root Cause**: Fundamental failure establishing connection from Python/`psycopg` to DB service (`db` or `172.20.0.2`) during pool initialization within the container. OS resolves hostname, but `psycopg` fails, leading to resource exhaustion (`SIGKILL`) or timeout. Reason for `psycopg` failure (reporting misleading error) is unclear (Network stack? IPv6? Library issue?).
- **Fix Applied**: None. Reverted diagnostic changes.
- **Verification**: N/A.
- **Related Issues**: Original TDD SIGKILL reports [Ref: TDD Feedback 2025-04-30 07:15:15], [Ref: TDD Feedback 2025-04-29 16:31:45].
### Issue: CLI-API-500-ERRORS-INGEST - `/ingest` 500 error for file not found - [Status: Fix Applied] - [2025-04-29 09:25:27]
- **Reported**: [2025-04-29 09:18:53] (via TDD Feedback) / **Severity**: Medium / **Symptoms**: `/ingest` API returns 500 Internal Server Error when the requested path does not exist.
- **Investigation**:
    1. Reviewed backend logs, confirmed `ingestion.pipeline` correctly logs "Path not found" error. [2025-04-29 09:23:46]
    2. Reviewed `api/main.py` `/ingest` endpoint handler. Found generic `except Exception` block returning 500. [2025-04-29 09:22:08]
- **Root Cause**: The `/ingest` endpoint handler in `src/philograph/api/main.py` did not specifically check for the "File or directory not found" error message from the pipeline and incorrectly raised a generic 500 error instead of a client-side 404 error.
- **Fix Applied**: Modified the `except` blocks in the `/ingest` handler in `src/philograph/api/main.py` to check for the "File or directory not found" message (from both the pipeline result dictionary and potential `ValueError`) and raise an `HTTPException` with status code 404. [2025-04-29 09:25:27]
- **Verification**: Pending. Requires restarting services and re-running `test_ingest_success`.
- **Related Issues**: [Ref: Issue-ID: CLI-API-500-ERRORS]

### Issue: CLI-API-500-ERRORS - `/search` 500 error (Embedding Generation) - [Status: Fix Applied] - [2025-04-29 09:25:27]
- **Reported**: [2025-04-29 05:07:42] (via TDD Feedback) / **Severity**: High / **Symptoms**: `/search` API returns `{"detail":"Embedding generation failed (HTTP 500)"}`.
- **Investigation**:
    1. Reviewed backend logs. Found `google.auth.exceptions.DefaultCredentialsError: ('File /app/gcp-key.json is not a valid json file.', JSONDecodeError('Expecting value: line 1 column 1 (char 0)'))` originating from `litellm-proxy` when attempting to load GCP credentials. [2025-04-29 09:23:46]
    2. Checked `docker-compose.yml`. Confirmed `GOOGLE_APPLICATION_CREDENTIALS` env var is used to mount a file to `/app/gcp-key.json` in the proxy container. [2025-04-29 09:24:09]
    3. Checked `.env`. Found `GOOGLE_APPLICATION_CREDENTIALS` was set to `/dev/null`. [2025-04-29 09:24:24]
- **Root Cause**: The `litellm-proxy` service requires a valid JSON file structure for the GCP credentials, even if the credentials themselves aren't used (e.g., in mocked tests). Mounting `/dev/null` resulted in an empty file, causing a `JSONDecodeError` during Google Auth library initialization within the proxy.
- **Fix Applied**: Created a minimal dummy JSON file (`dummy-gcp-key.json` containing `{}`) and updated `.env` to point `GOOGLE_APPLICATION_CREDENTIALS` to `./dummy-gcp-key.json`. [2025-04-29 09:25:03]
- **Verification**: Pending. Requires restarting services and re-running `test_search_success_query_only`.
- **Related Issues**: [Ref: Issue-ID: CLI-API-500-ERRORS-INGEST]
### Tool/Technique: YAML Indentation Sensitivity - [2025-04-29 05:04:50]
- **Context**: Resolving `AttributeError: 'str' object has no attribute 'get'` during LiteLLM proxy startup when parsing `litellm_config.yaml`.
- **Usage**: Ensure comments or other lines are not indented *under* a key-value pair like `general_settings: {}`. Incorrect indentation can cause the parser to misinterpret the structure, potentially treating a dictionary key as part of a string value. Correct indentation resolved the parsing error and subsequent `AttributeError`.
- **Effectiveness**: High (Resolved proxy startup crash). [Ref: Issue-ID: CLI-API-500-ERRORS]

### Issue: CLI-API-500-ERRORS - `/ingest` and `/search` 500 errors - [Status: Partially Resolved (Proxy Startup)] - [2025-04-29 05:04:50]
- **Reported**: [2025-04-29 04:48:59] / **Severity**: High / **Symptoms**: CLI tests failing due to backend 500 errors. `/search` showed `ConnectError` to `litellm-proxy`. `/ingest` showed invalid path. Proxy logs showed `AttributeError: 'str' object has no attribute 'get'`.
- **Investigation**:
    1. Reviewed TDD feedback, MB files. [2025-04-29 04:52:37]
    2. Confirmed CLI test failures. [2025-04-29 04:53:16]
    3. Checked backend logs (showed `ConnectError`, invalid path, missing DB table). [2025-04-29 04:53:29]
    4. Added network to `docker-compose.yml`. [2025-04-29 04:54:16]
    5. Enabled DB init in `api/main.py`. [2025-04-29 04:54:39]
    6. Checked proxy logs (showed `AttributeError`). [2025-04-29 04:57:02]
    7. Removed `pass` from `litellm_config.yaml`. [2025-04-29 04:57:34]
    8. Re-checked proxy logs (still `AttributeError`). [2025-04-29 05:01:48]
    9. Set `general_settings: {}` explicitly in `litellm_config.yaml`. [2025-04-29 05:02:05]
   10. Re-checked proxy logs (still `AttributeError`). [2025-04-29 05:02:27]
   11. Identified incorrect YAML indentation (comments under `general_settings: {}`). [2025-04-29 05:02:42]
   12. Corrected indentation in `litellm_config.yaml`. [2025-04-29 05:02:59]
   13. Restarted proxy. [2025-04-29 05:03:12]
   14. Checked proxy logs (Success!). [2025-04-29 05:03:26]
   15. Attempted `ping` from backend (failed: command not found). [2025-04-29 05:03:41]
   16. Attempted `curl` from backend (failed: command not found). [2025-04-29 05:03:55]
- **Root Cause**: Proxy startup failure caused by incorrect YAML indentation in `litellm_config.yaml`. Network connectivity remains unverified due to missing tools in backend container. `/ingest` error is separate test path issue.
- **Fix Applied**: Corrected indentation in `litellm_config.yaml`.
- **Verification**: Proxy logs show successful startup. Network connectivity verification blocked.
- **Related Issues**: [See TDD Feedback 2025-04-29 04:48:59], [See Debug Feedback 2025-04-29 04:58:20], [See Debug Feedback 2025-04-29 05:03:55]
### Issue: CLI-API-500-ERRORS - `/ingest` and `/search` 500 errors - [Status: Open] - [2025-04-29 04:58:20]
- **Reported**: [2025-04-29 04:48:59] (via TDD Feedback) / **Severity**: High / **Symptoms**: 6 CLI tests failing (`test_ingest_success`, `test_ingest_api_error`, `test_search_success_query_only`, `test_search_success_with_filters`, `test_search_api_error`, `test_search_empty_results`) due to backend API returning 500 errors. `/search` returns `{"detail":"Embedding generation failed (Request Error)"}`. `/ingest` returns `{"detail":"An unexpected error occurred during ingestion."}`.
- **Investigation**:
    1. Reviewed TDD feedback, Memory Bank files, pseudocode, and relevant source code (`api/main.py`, `ingestion/pipeline.py`, `search/service.py`, `data_access/db_layer.py`, `utils/http_client.py`). [2025-04-29 04:52:37]
    2. Ran CLI tests (`docker compose exec philograph-backend pytest tests/cli/test_main.py`). Confirmed 6 failures with reported 500 errors. [2025-04-29 04:53:16]
    3. Checked `philograph-backend` logs (`docker compose logs philograph-backend`). Found `/search` errors caused by `ConnectError(gaierror(-3, 'Temporary failure in name resolution'))` when contacting `litellm-proxy`. Found `/ingest` errors caused by `Path not found or is not a file/directory: /app/data/source_documents/some/document.pdf`. Also found earlier `psycopg.errors.UndefinedTable: relation "documents" does not exist` error. [2025-04-29 04:53:29]
    4. Inspected `docker-compose.yml`. Found no explicit network defined. Added `philograph-net` network and assigned services. [2025-04-29 04:54:16]
    5. Inspected `api/main.py` lifespan. Found DB schema initialization commented out. Uncommented initialization block. [2025-04-29 04:54:39]
    6. Re-ran CLI tests after applying fixes. Failures persisted. [2025-04-29 04:55:24]
    7. Checked `.env` file. Confirmed `LITELLM_PROXY_URL` uses correct service name (`http://litellm-proxy:4000`). [2025-04-29 04:56:41]
    8. Checked `litellm-proxy` logs (`docker compose logs litellm-proxy`). Found service crashing on startup with `AttributeError: 'str' object has no attribute 'get'` in `litellm/proxy/proxy_cli.py`, line 640. [2025-04-29 04:57:02]
    9. Inspected `litellm_config.yaml`. Found `pass` under `general_settings`, likely causing the parsing error. Removed `pass`. [2025-04-29 04:57:34]
   10. Re-ran CLI tests after fixing `litellm_config.yaml` and recreating services. Failures persisted. [2025-04-29 04:58:20]
- **Root Cause**: `/search` errors: Persistent connection issue to `litellm-proxy`, likely due to proxy service still failing to run correctly despite config fix. `/ingest` errors: Invalid path (`some/document.pdf`) used in tests.
- **Fix Applied**: Corrected `litellm_config.yaml` by removing `pass`. Uncommented DB initialization in `api/main.py`. Added network definition in `docker-compose.yml`.
- **Verification**: Test re-run failed.
- **Related Issues**: [See TDD Feedback 2025-04-29 04:48:59]
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
### Issue: CLI-API-500-ERRORS-INGEST - `/ingest` 500 error for file not found - [Status: Resolved] - [2025-04-29 11:26:19]
- **Reported**: [2025-04-29 09:18:53] (via TDD Feedback) / **Severity**: Medium / **Symptoms**: `/ingest` API returns 500 Internal Server Error when the requested path does not exist.
- **Investigation**:
    1. Reviewed backend logs, confirmed `ingestion.pipeline` correctly logs "Path not found" error. [2025-04-29 09:23:46]
    2. Reviewed `api/main.py` `/ingest` handler. Found generic `except Exception` block returning 500. [2025-04-29 09:22:08]
    3. Attempted fix in `api/main.py` to catch "not found" message. Failed verification (still 500). [2025-04-29 09:26:29] -> [Ref: TDD Feedback 2025-04-29 10:14:40]
    4. Hypothesized error during path resolution in `pipeline.py`. Modified `pipeline.py` to catch `FileNotFoundError` during `.resolve(strict=True)` and return standard "not found" message. Failed verification (still 500). [2025-04-29 11:15:19]
    5. Added detailed logging to `api/main.py` exception handlers. [2025-04-29 11:17:25]
    6. Reviewed backend logs after test run. Identified `AttributeError: 'str' object has no attribute 'HTTP_404_NOT_FOUND'` caused by local `status` variable shadowing `fastapi.status` import. [2025-04-29 11:19:32]
    7. Renamed local variable to `result_status`. Failed verification (still 500, generic detail). [2025-04-29 11:20:31] -> [2025-04-29 11:22:33]
    8. Reviewed backend logs again. Found the correctly raised `HTTPException(404)` was being caught by the final `except Exception:` block, which then failed with another `AttributeError` due to the same shadowing issue when trying to raise a 500. [2025-04-29 11:22:53]
- **Root Cause**: 1) Local variable `status` shadowed the imported `fastapi.status` module, causing `AttributeError` when accessing status codes. 2) The final `except Exception:` block was too broad and caught the `HTTPException(404)` that should have propagated. 3) The final `except Exception:` block *also* contained the shadowing bug when trying to raise its own 500 error.
- **Fix Applied**: Renamed local variable to `result_status`. Added `import fastapi`. Modified final `except Exception:` block to check `isinstance(e, HTTPException)` and re-raise if true, otherwise raise 500 using `fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR`. Commit: 0da0aea. [2025-04-29 11:23:38]
- **Verification**: `docker compose exec philograph-backend pytest tests/cli/test_main.py -k "test_ingest_success"` failed with exit code 1, but CLI logs confirmed API returned `404 - {"detail":"Ingestion source file not found"}`. [2025-04-29 11:25:14]
- **Related Issues**: [Ref: Issue-ID: CLI-API-500-ERRORS]
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