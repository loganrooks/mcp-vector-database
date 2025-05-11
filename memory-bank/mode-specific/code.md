# Code Mode Specific Memory
<!-- Entries below should be added reverse chronologically (newest first) -->

### [2025-05-10 16:40:15] Synthetic Data Generation Path Refactor
- **Purpose**: Reorganize output directory structure for all synthetic test data.
- **Files**:
    - `synthetic_test_data/common.py` (path definitions updated)
    - `tests/synthetic_test_data/test_epub_generators.py` (test paths updated)
    - `synthetic_test_data/README.md` (documentation updated)
- **Status**: Implemented
- **Dependencies**: N/A (internal path changes)
- **API Surface**: N/A (internal path changes)
- **Tests**: Test paths updated in `test_epub_generators.py`. Other tests using these files might need updates if they hardcode paths.
- **Details**: All synthetic data (EPUBs, PDFs, Markdown) will now be generated into `synthetic_test_data/generated/<type>/<category>/` subdirectories. This change was primarily achieved by modifying base path constants in `common.py`.
### [2025-05-09 05:38:00] Synthetic Test Data Generation Script (Initial)
- **Purpose**: Create initial script and sample files for synthetic test data.
- **Files**:
    - `synthetic_test_data/generate_data.py`
    - `synthetic_test_data/README.md`
    - `synthetic_test_data/epub/toc/ncx_simple.epub` (Generated)
    - `synthetic_test_data/markdown/basic/all_basic_elements.md` (Generated)
- **Status**: Implemented (Initial Version)
- **Dependencies**: `ebooklib` (from `requirements.txt`).
- **API Surface**: N/A (Script for local data generation).
- **Tests**: N/A (This script generates test data, not tested itself in this step).
- **Details**: Created a Python script `generate_data.py` to programmatically create synthetic test files. Currently, it generates a simple EPUB with an NCX ToC and a basic Markdown file. A README was added to explain usage. The script is designed to be extensible for more complex data generation as per `docs/qa/synthetic_data_requirements.md`.
### [2025-05-05 06:50:31] CLI Refactor: Acquire/Status Commands (ADR 009)
- **Purpose**: Align CLI `acquire` and `status` commands with the two-stage acquisition API.
- **Files**:
    - `src/philograph/cli/main.py`
    - `tests/cli/test_cli_acquire.py`
    - `tests/cli/test_cli_status.py`
- **Status**: Implemented & Verified
- **Dependencies**: Added `uuid` import to `src/philograph/cli/main.py`.
- **API Surface**: CLI commands changed:
    - Removed `philograph acquire ...`
    - Added `philograph acquire discover ...`
    - Added `philograph acquire confirm <discovery_id> ...`
    - Modified `philograph status <acquisition_id>` to `philograph status <discovery_id>`
- **Tests**: Updated tests in affected files. Verified with `pytest tests/cli/` (49 passed).
- **Details**: Refactored `main.py` to use Typer subcommands for `acquire`. Updated command logic to call new API endpoints (`/acquire/discover`, `/acquire/confirm/{id}`, `/acquire/status/{id}`). Updated tests to match new structure and API calls. [Ref: Task 2025-05-05 06:45:17, ADR 009]
### [2025-05-04 18:56:30] TDD Green Phase Review: Relationship Service
- **Purpose**: Review existing implementation of `add_relationship` and `get_relationships` in `db_layer.py` against TDD Green phase requirements.
- **Files**: `src/philograph/data_access/db_layer.py` (Lines 380-442 reviewed)
- **Status**: Reviewed - Existing implementation meets requirements. No code changes needed.
- **Dependencies**: None changed.
- **API Surface**: None changed.
- **Tests**: Tests in `tests/data_access/test_db_layer.py` (specifically relationship tests) should now pass.
- **Details**: Verified that the existing functions handle SQL execution, parameter passing, JSON serialization, dynamic WHERE clauses, error propagation, and return values as required by the task and pseudocode. [Ref: Task 2025-05-04 18:55:07, ActiveContext 2025-05-04 18:54:00]
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