# Code Mode Specific Memory
<!-- Entries below should be added reverse chronologically (newest first) -->

### [2025-05-04 03:16:29] Acquisition Workflow (ADR 009) - TDD Green Phase
- **Purpose**: Implement minimal code for the two-stage discovery/confirmation acquisition workflow to pass failing tests.
- **Files**:
    - `src/philograph/acquisition/service.py`
    - `src/philograph/api/main.py`
    - `src/philograph/mcp/main.py`
- **Status**: Implemented (TDD Green Phase)
- **Dependencies**: `uuid`, `time` (in `service.py`), `fastapi`, `pydantic` (in `api/main.py`), `httpx` (in `mcp/main.py`). No new external libraries added.
- **API Surface**:
    - Added `POST /acquire/discover`
    - Added `POST /acquire/confirm/{discovery_id}`
    - Added `GET /acquire/status/{discovery_id}`
    - Marked `POST /acquire` and `POST /acquire/confirm/{acquisition_id}` as deprecated.
- **Tests**: Corresponding tests in `tests/acquisition/test_service.py`, `tests/api/test_main.py`, `tests/mcp/test_main.py` should now pass.
- **Details**: Implemented session management (in-memory dict) in `service.py`. Added new endpoints and Pydantic models in `api/main.py`. Updated MCP tool `philograph_acquire` in `mcp/main.py` to handle the two-stage workflow and call the new API endpoints. [Ref: Task 2025-05-04 03:07:51, ADR 009]
### [2025-05-02 22:21:49] Acquisition Service Security Fixes
- **Purpose**: Remediate security findings SR-ACQ-001 and SR-ACQ-002.
- **Files**: `src/philograph/acquisition/service.py`
- **Status**: Implemented
- **Dependencies**: Added `time`, `collections.deque`, `typing.Set`.
- **API Surface**: No change to external API. Internal behavior modified.
- **Tests**: Existing tests in `tests/acquisition/test_service.py` may need updates. Recommend TDD run.
- **Details**:
    - Added `_validate_book_details` helper function to check for required/expected keys and basic types in data passed to `download_book_to_file` MCP tool (SR-ACQ-001).
    - Implemented simple in-memory rate limiting using `deque` and timestamps for `start_acquisition_search` and `confirm_and_trigger_download` (SR-ACQ-002).
<!-- No interventions logged during this implementation phase. -->
## Intervention Log
<!-- Append intervention details using the format below -->
### [2025-04-29 04:18:51] Intervention: Fix CLI Test Syntax Errors
- **Trigger**: Task handover from TDD mode [Ref: TDD Feedback 2025-04-29 04:17:00].
- **Context**: Persistent syntax errors in `tests/cli/test_main.py` around line 597 after failed tool use in TDD.
- **Action Taken**: Identified and removed stray parenthesis and duplicate line using `apply_diff`.
- **Rationale**: Direct correction of syntax errors.
- **Outcome**: File `tests/cli/test_main.py` corrected.
- **Follow-up**: Recommend syntax verification (`pytest --collect-only`). Update MB. Proceed to `attempt_completion`. [See Code Feedback 2025-04-29 04:18:51]
### [2025-04-28 04:23:39] PhiloGraph Tier 0 Core Structure
- **Purpose**: Establish foundational code structure, configuration, utilities, API, CLI, MCP server, and Docker setup for Tier 0 MVP.
- **Files**:
    - `src/philograph/` (and submodules: `__init__.py`, `api/`, `cli/`, `config.py`, `data_access/`, `ingestion/`, `mcp/`, `search/`, `utils/`)
    - `tests/` (and submodules: `__init__.py`, `data_access/`, `utils/`)
    - `requirements.txt`
    - `.env.example`
    - `.gitignore`
    - `Dockerfile`
    - `litellm_config.yaml`
    - `docker-compose.yml`
    - `README.md`
- **Status**: Implemented (Initial structure and placeholders/basic implementations)
- **Dependencies**: See Dependencies section below.
- **API Surface**: Defined in `src/philograph/api/main.py` (FastAPI). Endpoints for `/ingest`, `/search`, `/documents`, `/collections`, `/acquire`.
- **Tests**: Initial tests created for `config.py` (`tests/test_config.py`) and `db_layer.py` (`tests/data_access/test_db_layer.py`). Further testing delegated.

## Components Implemented
### [2025-05-02 14:53:35] CLI `acquire` Command Refactoring
- **Purpose**: Improve maintainability and readability of the `acquire` command.
- **Files**: `src/philograph/cli/main.py`
- **Status**: Implemented
- **Dependencies**: None added/changed.
- **API Surface**: No change.
- **Tests**: Existing tests in `tests/cli/test_cli_main.py` cover functionality. Recommend TDD run.
- **Details**: Extracted confirmation flow (`_handle_acquire_confirmation`) and table display (`_display_confirmation_options`) into private helper functions. Removed minor comments.
### [2025-04-28 04:23:39] Initial Tier 0 Dependencies
- **Purpose**: Core framework, DB access, API calls, CLI, config, testing.
- **Scope**: Tier 0 MVP implementation.
- **Dependencies**:
    - `fastapi`: Web framework for API.
    - `uvicorn[standard]`: ASGI server.
    - `psycopg[binary,pool]`: Async PostgreSQL driver.
    - `pgvector`: Vector support (via SQL).
    - `python-dotenv`: Environment variable loading.
    - `httpx`: Async HTTP client.
    - `typer[all]`: CLI framework.
    - `pymupdf`: PDF/EPUB processing.
    - `ebooklib`: EPUB processing.
    - `pytest`: Testing framework.
    - `pytest-asyncio`: Async test support.
    - `rich`: CLI output formatting.
    - `PyYAML`: For parsing `litellm_config.yaml` and potential Markdown frontmatter.
- **Alternatives Considered**: Flask (for API), requests (sync HTTP), click (CLI), SQLAlchemy (ORM).
- **Decision Rationale**: FastAPI chosen for async performance and features. `psycopg` for async DB access. `httpx` for async HTTP. Typer for modern CLI. See ADRs 002, 005. `semchunk` noted as placeholder in `requirements.txt`.
<!-- Track components implemented and their status -->

## Technical Debt
<!-- Track identified technical debt items -->

## Dependencies
<!-- Track key external dependencies -->