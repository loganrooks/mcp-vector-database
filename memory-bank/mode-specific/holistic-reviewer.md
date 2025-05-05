# Holistic Reviewer Specific Memory
<!-- Entries below should be added reverse chronologically (newest first) -->

## Delegated Tasks Log
### Delegated Task: HR-CLI-ACQ-04 - [2025-05-02 13:01:53]
- **Assigned To**: `docs-writer` (or `code` during refactoring)
- **Related Finding**: Finding: Documentation - [2025-05-02 13:01:04]
- **Task Description**: Add detailed inline comments to clarify the `acquire` confirmation flow in `src/philograph/cli/main.py`.
- **Status**: Completed [Ref: Code Completion 2025-05-02 15:01:50]

### Delegated Task: HR-CLI-ACQ-03 - [2025-05-02 13:01:53]
- **Assigned To**: `code`
- **Related Finding**: Finding: Organization - [2025-05-02 13:01:04], Finding: Hygiene - [2025-05-02 13:01:04]
- **Task Description**: Refactor the `acquire` command in `src/philograph/cli/main.py` by extracting confirmation flow and table display logic into helper functions. Clean up minor comments.
- **Status**: Completed [Ref: Code Completion 2025-05-02 14:54:19]

### Delegated Task: HR-CLI-ACQ-02 - [2025-05-02 13:01:53]
- **Assigned To**: `tdd`
- **Related Finding**: Finding: Hygiene - [2025-05-02 13:01:04]
- **Task Description**: Remove obsolete skipped tests (`acquire-missing-texts`) and consolidate redundant `status` tests in `tests/cli/test_cli_main.py` *after* blocker resolution and refactoring.
- **Status**: Completed [Ref: TDD Completion 2025-05-02 16:03:38]
### Delegated Task: HR-CLI-ACQ-01 - [2025-05-02 13:01:53]
- **Assigned To**: `debug`
- **Related Finding**: Finding: SPARC/TDD - [2025-05-02 13:01:04]
- **Task Description**: Investigate and resolve persistent `TypeError` in `acquire` command tests (`test_acquire_confirmation_flow_yes_flag`, `test_acquire_missing_texts_auto_confirm_yes`) related to mocking/`CliRunner` interaction.
- **Status**: Completed [Ref: Debug Feedback 2025-05-02 13:09:30] - Blocker deemed intractable with current test setup. Problematic test re-skipped, obsolete test removed.
<!-- Append tasks delegated to other modes using the format below -->

### Finding: Hygiene - [2025-05-03 14:07:25]
- **Category**: Hygiene
- **Location/File(s)**: `tests/cli/test_cli_main.py` (lines 815-856, 1211-1256, 904-924, 1257-1288)
- **Observation**: Some redundancy exists in tests covering API error handling for the `acquire` command. Specifically, `test_acquire_confirmation_api_error` appears duplicated, and `test_acquire_api_error` / `test_acquire_initial_api_error` seem to cover the same initial API call failure scenario.
- **Recommendation**: Consolidate redundant tests to improve maintainability. Delegate to `tdd` mode.
- **Severity/Priority**: Low
- **Delegated Task ID**: HR-CLI-ACQ-05 (To be created if delegation occurs)

### Finding: SPARC/TDD - [2025-05-03 14:07:25]
- **Category**: SPARC/TDD
- **Location/File(s)**: `tests/cli/test_cli_main.py` (line 771)
- **Observation**: The critical test `test_acquire_confirmation_flow_yes_flag`, which verifies the `--yes` auto-confirmation success path, remains skipped due to a previously identified intractable mocking issue [Ref: Task HR-CLI-ACQ-01, Debug Feedback 2025-05-02 13:09:30]. This leaves a significant gap in automated test coverage for core functionality.
- **Recommendation**: Re-prioritize resolving the mocking blocker for this test. Delegate to `debug` or `tdd` with a specific focus on finding a viable mocking strategy or necessary code adjustment to enable the test.
- **Severity/Priority**: High
- **Delegated Task ID**: (Relates to unresolved HR-CLI-ACQ-01)
### Finding: [SPARC/TDD] - [2025-05-04 21:12:07]
- **Category**: SPARC/TDD
- **Location/File(s)**: `src/philograph/api/main.py`, `src/philograph/data_access/db_layer.py`, `tests/data_access/test_db_layer.py`, `tests/api/test_main.py`, `tests/acquisition/test_service.py`, `tests/cli/test_cli_main.py`, `tests/utils/test_text_processing.py`, `tests/ingestion/test_pipeline.py`
- **Observation**: Multiple source and test files significantly exceed the SPARC <500 line guideline, violating modularity principles.
- **Recommendation**: Prioritize refactoring these large files.
- **Severity/Priority**: Critical

### Finding: [SPARC/TDD] - [2025-05-04 21:12:07]
- **Category**: SPARC/TDD
- **Location/File(s)**: `tests/cli/test_cli_main.py`
- **Observation**: Critical test `test_acquire_confirmation_flow_yes_flag` remains skipped due to a persistent mocking issue.
- **Recommendation**: Re-prioritize resolving the blocker for this skipped test.
- **Severity/Priority**: High

### Finding: [Future-Proofing] - [2025-05-04 21:12:07]
- **Category**: Future-Proofing
- **Location/File(s)**: `docker-compose.yml`, `Dockerfile`
- **Observation**: Docker setup relies on host volume mounts for source code, preventing creation of a self-contained, deployable artifact.
- **Recommendation**: Modify `Dockerfile` to copy source code and remove host volume mounts for production-like builds.
- **Severity/Priority**: Major

### Finding: [Future-Proofing] - [2025-05-04 21:12:07]
- **Category**: Future-Proofing
- **Location/File(s)**: Workspace-wide
- **Observation**: Overall maintainability is impacted by large files, unpinned dependencies, documentation inconsistencies, and incomplete functionality (TODOs).
- **Recommendation**: Address specific findings related to refactoring, dependency pinning, documentation updates, and TODO completion.
- **Severity/Priority**: Major

### Finding: [Hygiene] - [2025-05-04 21:11:46]
- **Category**: Hygiene
- **Location/File(s)**: `src/philograph/utils/file_utils.py`, `src/philograph/ingestion/pipeline.py`, `src/philograph/search/service.py`
- **Observation**: Small blocks of commented-out code (likely debugging/example usage) exist.
- **Recommendation**: Remove the commented-out code blocks.
- **Severity/Priority**: Minor

### Finding: [Hygiene] - [2025-05-04 21:11:04]
- **Category**: Hygiene
- **Location/File(s)**: `src/philograph/utils/text_processing.py`
- **Observation**: Multiple TODO comments indicate significant incomplete functionality (GROBID parsing, semantic chunking, AnyStyle integration, basic reference parsing).
- **Recommendation**: Implement the missing logic or remove placeholders.
- **Severity/Priority**: Major

### Finding: [Organization] - [2025-05-04 21:10:16]
- **Category**: Organization
- **Location/File(s)**: `tests/utils/test_text_processing.py`
- **Observation**: Test file exceeds SPARC guidelines (~657 lines), testing multiple distinct functionalities.
- **Recommendation**: Split tests into smaller, more focused files.
- **Severity/Priority**: Major

### Finding: [Organization] - [2025-05-04 21:08:48]
- **Category**: Organization
- **Location/File(s)**: `tests/ingestion/test_pipeline.py`
- **Observation**: Test file exceeds SPARC guidelines (~1824 lines).
- **Recommendation**: Refactor by removing duplication and potentially splitting tests.
- **Severity/Priority**: Critical

### Finding: [Hygiene] - [2025-05-04 21:08:48]
- **Category**: Hygiene
- **Location/File(s)**: `tests/ingestion/test_pipeline.py`
- **Observation**: Significant duplication of test code blocks exists within the file.
- **Recommendation**: Remove duplicated test code urgently.
- **Severity/Priority**: Major

### Finding: [Organization] - [2025-05-04 21:07:19]
- **Category**: Organization
- **Location/File(s)**: `tests/acquisition/test_service.py`
- **Observation**: Test file exceeds SPARC guidelines (~663 lines).
- **Recommendation**: Split tests into multiple files based on functionality.
- **Severity/Priority**: Major

### Finding: [Organization] - [2025-05-04 21:06:11]
- **Category**: Organization
- **Location/File(s)**: `tests/api/test_main.py`
- **Observation**: Test file exceeds SPARC guidelines (~1670 lines).
- **Recommendation**: Split tests into multiple files, mirroring API router structure.
- **Severity/Priority**: Critical

### Finding: [Organization] - [2025-05-04 21:05:35]
- **Category**: Organization
- **Location/File(s)**: `tests/data_access/test_db_layer.py`
- **Observation**: Test file exceeds SPARC guidelines (~1970 lines).
- **Recommendation**: Split tests into multiple files mirroring source module structure.
- **Severity/Priority**: Critical

### Finding: [Organization] - [2025-05-04 21:03:21]
- **Category**: Organization
- **Location/File(s)**: `src/philograph/search/service.py`
- **Observation**: `SearchResult` Pydantic model defined inline.
- **Recommendation**: Move model to a shared location.
- **Severity/Priority**: Suggestion

### Finding: [Hygiene] - [2025-05-04 21:03:21]
- **Category**: Hygiene
- **Location/File(s)**: `src/philograph/search/service.py`
- **Observation**: Potential redundancy between `SearchService` class and standalone `perform_search` function.
- **Recommendation**: Clarify usage and remove redundant code if applicable.
- **Severity/Priority**: Minor

### Finding: [Organization] - [2025-05-04 21:02:34]
- **Category**: Organization
- **Location/File(s)**: `src/philograph/data_access/db_layer.py`
- **Observation**: Pydantic models (`Document`, `Section`, etc.) defined inline.
- **Recommendation**: Move models to a shared location.
- **Severity/Priority**: Suggestion

### Finding: [Organization] - [2025-05-04 21:02:34]
- **Category**: Organization
- **Location/File(s)**: `src/philograph/data_access/db_layer.py`
- **Observation**: File exceeds SPARC guidelines (~665 lines), mixing connection management, schema, models, and CRUD logic.
- **Recommendation**: Refactor by separating concerns into different modules/files.
- **Severity/Priority**: Major

### Finding: [Organization] - [2025-05-04 21:01:26]
- **Category**: Organization
- **Location/File(s)**: `src/philograph/cli/main.py`
- **Observation**: CLI command `status` uses outdated argument `acquisition_id` instead of `discovery_id`.
- **Recommendation**: Update CLI command to align with API endpoint.
- **Severity/Priority**: Minor

### Finding: [Integration] - [2025-05-04 21:01:26]
- **Category**: Integration
- **Location/File(s)**: `src/philograph/cli/main.py`
- **Observation**: CLI command `acquire` uses outdated arguments and API endpoint inconsistent with current two-stage workflow.
- **Recommendation**: Refactor CLI command to support `discover` and `confirm` subcommands/logic.
- **Severity/Priority**: Major

### Finding: [Organization] - [2025-05-04 20:12:37]
- **Category**: Organization
- **Location/File(s)**: `src/philograph/api/main.py`
- **Observation**: Pydantic models defined inline, contributing to excessive file length.
- **Recommendation**: Move models to a dedicated schemas file.
- **Severity/Priority**: Suggestion

### Finding: [Organization] - [2025-05-04 20:12:37]
- **Category**: Organization
- **Location/File(s)**: `src/philograph/api/main.py`
- **Observation**: File exceeds SPARC guidelines (~691 lines), containing app setup, models, and all endpoint logic.
- **Recommendation**: Refactor by moving models and using API Routers.
- **Severity/Priority**: Major

### Finding: [Documentation] - [2025-05-04 20:11:39]
- **Category**: Documentation
- **Location/File(s)**: `docs/architecture/adr/001-tier0-local-docker-deployment.md`
- **Observation**: ADR status is "Proposed" but decision is implemented.
- **Recommendation**: Update ADR status.
- **Severity/Priority**: Minor

### Finding: [Documentation] - [2025-05-04 20:11:17]
- **Category**: Documentation
- **Location/File(s)**: `docs/architecture/adr/002-tier0-database-postgres-pgvector.md`
- **Observation**: ADR status is "Proposed" but decision is implemented.
- **Recommendation**: Update ADR status.
- **Severity/Priority**: Minor

### Finding: [Documentation] - [2025-05-04 20:10:46]
- **Category**: Documentation
- **Location/File(s)**: `docs/architecture/adr/003-tier0-api-gateway-litellm-proxy.md`
- **Observation**: ADR status is "Proposed" but decision is implemented.
- **Recommendation**: Update ADR status.
- **Severity/Priority**: Minor

### Finding: [Process] - [2025-05-04 20:10:09]
- **Category**: Process
- **Location/File(s)**: `docs/architecture/adr/004-tier0-embedding-strategy-cloud-via-proxy.md`
- **Observation**: ADR 004 includes a validation plan for embedding dimensionality (768d vs 1024d) that has not yet been executed.
- **Recommendation**: Execute the validation plan and document results.
- **Severity/Priority**: Suggestion

### Finding: [Documentation] - [2025-05-04 20:10:09]
- **Category**: Documentation
- **Location/File(s)**: `docs/architecture/adr/004-tier0-embedding-strategy-cloud-via-proxy.md`
- **Observation**: ADR status is "Proposed" but decision is implemented.
- **Recommendation**: Update ADR status.
- **Severity/Priority**: Minor

### Finding: [Documentation] - [2025-05-04 20:09:42]
- **Category**: Documentation
- **Location/File(s)**: `docs/architecture/adr/005-tier0-backend-framework-python-flask-fastapi.md`
- **Observation**: ADR status is "Proposed" but decision (FastAPI) is implemented.
- **Recommendation**: Update ADR status.
- **Severity/Priority**: Minor

### Finding: [Documentation] - [2025-05-04 20:09:11]
- **Category**: Documentation
- **Location/File(s)**: `docs/architecture/adr/006-tier0-text-processing-cpu-tools.md`
- **Observation**: ADR status is "Proposed" but decision is implemented.
- **Recommendation**: Update ADR status.
- **Severity/Priority**: Minor

### Finding: [Documentation] - [2025-05-04 20:08:43]
- **Category**: Documentation
- **Location/File(s)**: `docs/architecture/adr/007-tier0-framework-exclusion-no-langchain.md`
- **Observation**: ADR status is "Proposed" but decision is implemented.
- **Recommendation**: Update ADR status.
- **Severity/Priority**: Minor

### Finding: [Documentation] - [2025-05-04 20:08:04]
- **Category**: Documentation
- **Location/File(s)**: `docs/architecture/adr/008-tier0-text-acquisition-zlibrary-mcp.md`
- **Observation**: ADR status is "Proposed" but decision is implemented.
- **Recommendation**: Update ADR status.
- **Severity/Priority**: Minor

### Finding: [Documentation] - [2025-05-04 20:07:21]
- **Category**: Documentation
- **Location/File(s)**: `docs/architecture/adr/009-flexible-acquisition-workflow.md`
- **Observation**: ADR status is "Proposed" but decision is implemented.
- **Recommendation**: Update ADR status.
- **Severity/Priority**: Minor

### Finding: [Documentation] - [2025-05-04 20:06:28]
- **Category**: Documentation
- **Location/File(s)**: `docs/project-specifications.md`, `README.md`
- **Observation**: Spec does not clarify the ambiguous DB initialization process noted in README.
- **Recommendation**: Reinforces need to clarify/document DB init process.
- **Severity/Priority**: N/A (Cross-reference)

### Finding: [Documentation] - [2025-05-04 20:06:28]
- **Category**: Documentation
- **Location/File(s)**: `docs/project-specifications.md`, `README.md`
- **Observation**: Spec confirms README is outdated regarding acquisition workflow/MCP tools.
- **Recommendation**: Reinforces need to update README.
- **Severity/Priority**: N/A (Cross-reference)

### Finding: [Documentation] - [2025-05-04 20:06:28]
- **Category**: Documentation
- **Location/File(s)**: `docs/project-specifications.md`
- **Observation**: Schema migration tooling (e.g., Alembic) mentioned but not confirmed/detailed.
- **Recommendation**: Clarify tooling choice and document usage.
- **Severity/Priority**: Suggestion

### Finding: [Consistency] - [2025-05-04 20:06:28]
- **Category**: Consistency
- **Location/File(s)**: `docs/project-specifications.md`, `requirements.txt`
- **Observation**: Spec assumes `semchunk` is used, but it's a placeholder in requirements.
- **Recommendation**: Resolve `semchunk` dependency status.
- **Severity/Priority**: Minor

### Finding: [Consistency] - [2025-05-04 20:06:28]
- **Category**: Consistency
- **Location/File(s)**: `docs/project-specifications.md`, `.env.example`, ADR 004
- **Observation**: Discrepancy in example/recommended embedding dimension (1024 vs 768).
- **Recommendation**: Align documentation/config (likely to 768).
- **Severity/Priority**: Minor

### Finding: [Documentation] - [2025-05-04 20:05:18]
- **Category**: Documentation
- **Location/File(s)**: `README.md`
- **Observation**: CLI command examples (ingest, search, show, collection) need verification against implementation.
- **Recommendation**: Cross-reference examples with `cli/main.py`.
- **Severity/Priority**: Minor

### Finding: [Documentation] - [2025-05-04 20:05:18]
- **Category**: Documentation
- **Location/File(s)**: `README.md`
- **Observation**: Database schema initialization instructions are ambiguous and potentially unreliable. (Updated based on code review).
- **Recommendation**: Update README to reflect automatic initialization via API lifespan; consider making init failure fatal or providing explicit CLI command.
- **Severity/Priority**: Minor

### Finding: [Documentation] - [2025-05-04 20:05:18]
- **Category**: Documentation
- **Location/File(s)**: `README.md`
- **Observation**: Listed MCP tool names are outdated (`philograph_acquire_missing`).
- **Recommendation**: Update README with correct tool names (`philograph_acquire`, etc.).
- **Severity/Priority**: Major

### Finding: [Documentation] - [2025-05-04 20:05:18]
- **Category**: Documentation
- **Location/File(s)**: `README.md`
- **Observation**: CLI `acquire` command documentation is outdated (doesn't reflect two-stage workflow).
- **Recommendation**: Update README `acquire` documentation to match ADR 009/implementation.
- **Severity/Priority**: Major

### Finding: [Clarity] - [2025-05-04 20:04:24]
- **Category**: Clarity
- **Location/File(s)**: `.env.example`
- **Observation**: Placeholder path for `GOOGLE_APPLICATION_CREDENTIALS` might not clearly indicate it refers to the host machine path.
- **Recommendation**: Add comment clarifying host path context for volume mount.
- **Severity/Priority**: Suggestion

### Finding: [Clarity] - [2025-05-04 20:04:24]
- **Category**: Clarity
- **Location/File(s)**: `.env.example`
- **Observation**: `LITELLM_API_KEY` description doesn't mention where the key needs to be configured in LiteLLM itself.
- **Recommendation**: Add comment clarifying key needs to be set in `litellm_config.yaml`.
- **Severity/Priority**: Suggestion

### Finding: [Clarity] - [2025-05-04 20:04:24]
- **Category**: Clarity
- **Location/File(s)**: `.env.example`
- **Observation**: Default `DB_HOST=localhost` might be confusing given container networking uses `db`.
- **Recommendation**: Add comment clarifying `localhost` vs `db` context.
- **Severity/Priority**: Minor

### Finding: [Verification] - [2025-05-04 20:03:59]
- **Category**: Verification
- **Location/File(s)**: `requirements.txt`
- **Observation**: Comment suggests minimal usage of `pgvector` library.
- **Recommendation**: Verify actual usage; remove if unnecessary.
- **Severity/Priority**: Suggestion

### Finding: [Optimization] - [2025-05-04 20:03:59]
- **Category**: Optimization
- **Location/File(s)**: `requirements.txt`, `Dockerfile`
- **Observation**: Use of `psycopg[binary]` likely makes build tools in Dockerfile unnecessary.
- **Recommendation**: Confirm and remove build tools from Dockerfile if possible.
- **Severity/Priority**: Minor

### Finding: [Completeness] - [2025-05-04 20:03:59]
- **Category**: Completeness
- **Location/File(s)**: `requirements.txt`
- **Observation**: `semchunk` dependency listed as placeholder.
- **Recommendation**: Resolve placeholder: implement, select library, or remove.
- **Severity/Priority**: Minor

### Finding: [Stability] - [2025-05-04 20:03:59]
- **Category**: Stability
- **Location/File(s)**: `requirements.txt`
- **Observation**: Dependencies lack pinned versions.
- **Recommendation**: Pin all dependencies to specific versions.
- **Severity/Priority**: Major

### Finding: [Robustness] - [2025-05-04 20:03:23]
- **Category**: Robustness
- **Location/File(s)**: `docker-compose.yml`
- **Observation**: Backend depends on `litellm-proxy` using `service_started`, not `service_healthy`.
- **Recommendation**: Use `service_healthy` if LiteLLM provides a healthcheck.
- **Severity/Priority**: Suggestion

### Finding: [Hygiene] - [2025-05-04 20:03:23]
- **Category**: Hygiene
- **Location/File(s)**: `docker-compose.yml`
- **Observation**: DB service command forces IPv4 listening.
- **Recommendation**: Review necessity; remove if possible.
- **Severity/Priority**: Suggestion

### Finding: [Stability] - [2025-05-04 20:03:23]
- **Category**: Stability
- **Location/File(s)**: `docker-compose.yml`
- **Observation**: `litellm-proxy` uses `main-latest` image tag.
- **Recommendation**: Pin to a specific version tag.
- **Severity/Priority**: Suggestion

### Finding: [Organization] - [2025-05-04 20:03:23]
- **Category**: Organization
- **Location/File(s)**: `docker-compose.yml`
- **Observation**: Backend service relies on host-mounted volumes for source/tests.
- **Recommendation**: Ensure Dockerfile copies source; remove mounts for production builds.
- **Severity/Priority**: Major

### Finding: [Optimization] - [2025-05-04 20:02:55]
- **Category**: Optimization
- **Location/File(s)**: `Dockerfile`
- **Observation**: Build/debug tools included in final image.
- **Recommendation**: Use multi-stage builds; check if build tools needed with `psycopg[binary]`.
- **Severity/Priority**: Suggestion

### Finding: [Organization] - [2025-05-04 20:02:55]
- **Category**: Organization
- **Location/File(s)**: `Dockerfile`
- **Observation**: Explicit `COPY tests /app/tests` seems like a workaround.
- **Recommendation**: Investigate necessity; ideally remove from final image.
- **Severity/Priority**: Suggestion

### Finding: [Hygiene] - [2025-05-04 20:02:55]
- **Category**: Hygiene
- **Location/File(s)**: `Dockerfile`
- **Observation**: Leftover debug command `RUN ls -l /app`.
- **Recommendation**: Remove the command.
- **Severity/Priority**: Minor

### Finding: [Organization] - [2025-05-04 20:02:55]
- **Category**: Organization
- **Location/File(s)**: `Dockerfile`
- **Observation**: Application source code (`src/`) is not copied into the image.
- **Recommendation**: Add `COPY src/ /app/src` instruction.
- **Severity/Priority**: Major
## Review Findings & Recommendations
### Finding: Hygiene - [2025-05-02 13:01:04]
- **Category**: Hygiene
- **Location/File(s)**: `src/philograph/cli/main.py` (lines 334-337)
- **Observation**: Minor leftover comments ("Corrected from...") exist in the table creation logic within the `acquire` command's confirmation flow.
- **Recommendation**: Clean up these comments during refactoring.
- **Severity/Priority**: Low
- **Delegated Task ID**: HR-CLI-ACQ-03 (To be created)

### Finding: Documentation - [2025-05-02 13:01:04]
- **Category**: Documentation
- **Location/File(s)**: `src/philograph/cli/main.py` (lines 267-404)
- **Observation**: The complex confirmation flow logic within the `acquire` command lacks sufficient inline comments to explain the different states and decision points, particularly around the `--yes` flag handling.
- **Recommendation**: Add detailed inline comments to clarify the `acquire` confirmation flow.
- **Severity/Priority**: Medium
- **Delegated Task ID**: HR-CLI-ACQ-04 (To be created)

### Finding: Hygiene - [2025-05-02 13:01:04]
- **Category**: Hygiene
- **Location/File(s)**: `tests/cli/test_cli_main.py` (lines 1015-1103, 1149-1171)
- **Observation**: Several tests related to the old, merged `acquire-missing-texts` command are marked as skipped but remain in the file. Some redundancy also exists in `status` command tests.
- **Recommendation**: Remove obsolete skipped tests and consolidate redundant `status` tests after the primary refactoring and blocker resolution.
- **Severity/Priority**: Low
- **Delegated Task ID**: HR-CLI-ACQ-02 (To be created)

### Finding: SPARC/TDD - [2025-05-02 13:01:04]
- **Category**: SPARC/TDD
- **Location/File(s)**: `tests/cli/test_cli_main.py` (lines 767-814, 1173-1219)
- **Observation**: Critical tests for the `acquire` command's `--yes` auto-confirmation logic (`test_acquire_confirmation_flow_yes_flag`, `test_acquire_missing_texts_auto_confirm_yes`) are skipped due to a persistent, intractable `TypeError` related to mocking and `CliRunner` interaction [Ref: Debug Feedback 2025-05-02 05:28:06]. This represents a significant gap in test coverage for core functionality.
- **Recommendation**: Delegate investigation of the mocking/`CliRunner` `TypeError` to `debug` mode to unblock these tests.
- **Severity/Priority**: Critical
- **Delegated Task ID**: HR-CLI-ACQ-01 (To be created)

### Finding: Organization - [2025-05-02 13:01:04]
- **Category**: Organization
- **Location/File(s)**: `src/philograph/cli/main.py` (lines 267-404)
- **Observation**: The `acquire` command function is complex (~140 lines) and handles multiple responsibilities: argument validation, initial API call, and the multi-step confirmation flow (including `--yes` logic and user prompting). The code for displaying the confirmation options table is also duplicated.
- **Recommendation**: Refactor the `acquire` command. Extract the confirmation flow logic and the table display logic into separate helper functions to improve readability, maintainability, and reduce complexity.
- **Severity/Priority**: High
- **Delegated Task ID**: HR-CLI-ACQ-03 (To be created)
<!-- Append findings categorized by area using the format below -->