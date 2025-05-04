# Documentation Writer Feedback Log
<!-- Entries below should be added reverse chronologically (newest first) -->

### Feedback: [2025-05-02 16:19:21]
- **Source**: Task: Update CLI Documentation for `acquire` Command
- **Document**: `README.md`
- **Feedback**: Updated the CLI Usage section for the `acquire` command to reflect current functionality after recent refactoring. Included details on options (`--title`, `--author`, `--find-missing-threshold`, `--yes`), workflow (search, confirmation table, selection/cancellation, auto-confirm), and provided updated examples.
- **Analysis**: The previous documentation was minimal and outdated. The new section accurately describes the command based on `src/philograph/cli/main.py` and recent feedback logs.
- **Action**: Applied changes to `README.md` using `apply_diff`.