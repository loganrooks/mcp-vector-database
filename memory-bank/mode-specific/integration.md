# Integration Specific Memory
<!-- Entries below should be added reverse chronologically (newest first) -->

### Release Notes - feature/relationship-service Integration (Completion) - [2025-05-05 20:43:18]
#### Changes:
- Verified `docs/readme-fixes` was already merged into `feature/relationship-service`.
- Verified `fix/devops-holistic-review` was already merged into `feature/relationship-service`.
- Verified `feat/cli-api-alignment` was already merged into `feature/relationship-service`.
- Merged `fix/text-processing-todos` into `feature/relationship-service` (fast-forward).
#### Verification:
- Ran `pytest` suite (`docker-compose exec philograph-backend pytest`).
- Result: 357 passed, 8 skipped.
#### Known Issues:
- CLI-ACQUIRE-TYPER-INTRACTABLE-20250505: 7 tests in `tests/cli/test_cli_acquire.py` related to `acquire discover --yes` and `acquire confirm` remain skipped due to persistent Typer subcommand interference.
- 1 unrelated test skip persists (`tests/utils/test_text_extraction.py::test_extract_md_frontmatter_no_yaml_installed`).
### Release Notes - feature/relationship-service Integration - [2025-05-05 15:14:49]
#### Changes:
- Merged `docs/readme-fixes` into `feature/relationship-service`.
- Merged `fix/devops-holistic-review` into `feature/relationship-service`.
- Verified `feat/cli-api-alignment` was already merged.
#### Known Issues:
- CLI-ACQUIRE-TYPER-INTRACTABLE-20250505: 7 tests in `tests/cli/test_cli_acquire.py` related to `acquire discover --yes` and `acquire confirm` are skipped due to persistent Typer subcommand interference.
## Integration Release Notes
<!-- Append release notes using the format below -->

## Integration Issues Log
<!-- Append issues using the format below -->

## Integration Test Scenarios
<!-- Append test scenarios using the format below -->

## System Dependency Map
<!-- Update dependency map using the format below (consider if this should be newest first or overwrite) -->

## Integration Points Catalog
<!-- Append integration point details using the format below -->