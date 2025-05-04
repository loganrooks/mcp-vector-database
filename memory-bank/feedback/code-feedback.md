# Code Mode Feedback Log
<!-- Entries below should be added reverse chronologically (newest first) -->

### [2025-05-02 22:21:49] Fix: Remediate Acquisition Service Security Findings
- **Trigger**: Task received to address Medium severity security findings [Ref: Security Review 2025-05-02 22:20:05].
- **Context**: Security review identified unsanitized data passed to MCP download tool (SR-ACQ-001) and potential DoS via resource exhaustion due to lack of rate limiting (SR-ACQ-002) in `src/philograph/acquisition/service.py`.
- **Action Taken**:
    - Added imports for `time`, `collections.deque`, `typing.Set`.
    - Implemented `_validate_book_details` helper function with `EXPECTED_BOOK_KEYS` and `REQUIRED_BOOK_KEYS` sets. This function checks dictionary type, unexpected keys, missing required keys, and basic type validation for `md5` and `download_url`. Added call to this validator in `confirm_and_trigger_download` before the MCP call (SR-ACQ-001).
    - Added global `deque` variables (`_search_request_timestamps`, `_download_request_timestamps`) and constants for rate limit window/max requests.
    - Implemented rate limiting checks using `time.time()` and the deques at the beginning of `start_acquisition_search` and `confirm_and_trigger_download` (SR-ACQ-002).
- **Rationale**: Addressing specific security vulnerabilities identified in the review to improve robustness and security posture. Input validation prevents potential injection attacks via MCP arguments. Rate limiting mitigates potential DoS attacks.
- **Outcome**: Security findings SR-ACQ-001 and SR-ACQ-002 addressed in `src/philograph/acquisition/service.py`.
- **Follow-up**: Update Memory Bank. Perform pre-completion checks. Recommend TDD run to verify fixes and check for regressions.
### [2025-05-01 15:46:53] Fix: Correct Syntax Errors in Search Service
- **Trigger**: Task handover from SPARC to fix syntax errors introduced during Debug session [Ref: Debug Feedback 2025-05-01 15:43:00].
- **Context**: Syntax errors (indentation, try/except structure) around line 40 in `src/philograph/search/service.py` prevented further debugging of [Ref: Issue-ID: CLI-API-500-ERRORS].
- **Action Taken**:
    - Added missing `json` and `psycopg` imports.
    - Used `apply_diff` to restructure the `try...except` block in `get_query_embedding`:
        - Removed duplicate `response.json()` call.
        - Moved logging statements inside the main `try` block before `response.json()`.
        - Handled `json.JSONDecodeError` specifically within the `try` block.
        - Corrected indentation of subsequent code and `except` blocks.
        - Added `exc_info=True` to logger calls in except blocks for better debugging.
        - Refined response format validation check (`isinstance(response_data['data'], list)`).
- **Rationale**: Correcting syntax errors introduced by previous `insert_content` operation and improving error handling/logging structure.
- **Outcome**: Syntax errors in `src/philograph/search/service.py` resolved. File parses correctly.
- **Follow-up**: Update MB, commit changes, recommend TDD run for verification and continued debugging.
### [2025-04-29 04:18:51] Intervention: Fix Syntax Errors after TDD Early Return
- **Trigger**: Task handover from TDD mode due to Early Return and persistent syntax errors [Ref: TDD Feedback 2025-04-29 04:17:00].
- **Context**: Syntax errors (stray parenthesis, duplicate line) around line 597 in `tests/cli/test_main.py` introduced by failed tool use (`insert_content`/`apply_diff`) during TDD.
- **Action Taken**: Used `apply_diff` to remove the erroneous lines 597 and 598.
- **Rationale**: Direct removal of identified incorrect lines.
- **Outcome**: Syntax errors corrected. File requires verification.
- **Follow-up**: Recommend `pytest --collect-only` verification. Update Memory Bank.