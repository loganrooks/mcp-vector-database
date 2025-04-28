### [2025-04-28 17:14:13] Intervention: Incorrect Context Percentage Calculation
- **Trigger**: User Feedback denying handover `new_task`.
- **Context**: SPARC initiated handover due to reported context size exceeding threshold (e.g., 181%).
- **Action Taken**: User clarified that the percentage in `environment_details` is incorrect. Correct calculation is `(Reported Tokens / 1,000,000) * 100`. SPARC recalculated (e.g., 21%) and aborted handover.
- **Rationale**: Avoid unnecessary handover based on faulty system reporting. Follow user guidance for accurate context monitoring.
- **Outcome**: Handover aborted. Workflow continues.
- **Follow-up**: SPARC and delegated modes must manually calculate context percentage until the reporting bug is fixed. Include this instruction in future delegations. Logged as system issue.
# SPARC Mode Feedback Log
<!-- Entries below should be added reverse chronologically (newest first) -->

### [2025-04-28 10:02:37] Delegation: Git Initialization and Commit Task

*   **Trigger**: Early Return from `tdd` mode due to user request to address version control.
*   **Context**: `tdd` mode completed initial tests for 4 utility modules after `code` mode finished initial implementation. Need to establish git history before proceeding.
*   **Action Taken**: Delegating task to `devops` mode to initialize git, review changes, and create logical commits.
*   **Rationale**: Address user requirement for version control before accumulating more changes ("git debt"). `devops` mode is suitable for establishing repository practices.
*   **Outcome**: Pending `devops` mode completion.
*   **Follow-up**: Resume `tdd` testing task after git history is established.
*   **Note**: Due to SPARC file restrictions, this log entry serves as the record instead of `sparc.md#Delegations Log`. Core MB files (`activeContext.md`, `globalContext.md`) cannot be updated by SPARC.
### [2025-04-28 03:53:15] Intervention: Premature Handover due to Context Misjudgment

*   **Trigger**: User Correction.
*   **Context**: SPARC incorrectly assessed the context window size (reported 81% when it was lower, e.g., 13% then 68%) and prematurely initiated the DELEGATE CLAUSE handover procedure.
*   **Action Taken**: Logged the error. Cancelled the handover `new_task` call.
*   **Rationale**: Misinterpretation or misreading of the context window size metric provided in the environment details.
*   **Outcome**: Unnecessary handover attempt aborted. Workflow continues under the current instance for now.
*   **Follow-up**: SPARC must pay closer attention to the actual context window percentage provided in `environment_details` and apply the 40-50% threshold accurately before triggering the DELEGATE CLAUSE.
### [2025-04-28 03:50:05] Intervention: Memory Bank Update Failed (File Restriction)

*   **Trigger**: `FileRestrictionError` during `insert_content` tool use.
*   **Context**: Attempting to update `memory-bank/activeContext.md` with the status that Tier 0 pseudocode generation was complete.
*   **Action Taken**: Logged the error. Halted direct update attempt.
*   **Rationale**: The SPARC mode has restricted write access, only permitted for files matching `.*sparc.*\.md$ (Feedback files only)`. Core Memory Bank files like `activeContext.md` are protected from direct modification by this mode.
*   **Outcome**: `activeContext.md` was not updated with the latest status.
*   **Follow-up**: Need to investigate alternative mechanisms for updating core Memory Bank files (`activeContext.md`, `globalContext.md`). Potential options include delegating updates to `memory-bank-doctor` mode or requesting user intervention/guidance. This restriction must be considered in future Memory Bank update planning.
### [2025-04-28 03:38:36] User Feedback: Version Control Guidance in Delegations

*   **Source:** User interaction following Architect mode completion summary.
*   **Issue:** SPARC delegation messages lack instructions regarding version control practices.
*   **Action:** SPARC must include guidance in `new_task` messages specifying:
    *   When commits are appropriate (e.g., before successful `attempt_completion`).
    *   That commits are *not* needed before an `attempt_completion` triggered by an Early Return.
    *   That workspace clearing is not needed when resuming after an Early Return, especially if only memory bank files changed.
*   **Learnings:** Providing clear version control expectations within task delegations improves workflow consistency and reduces ambiguity for delegated modes.
### [2025-04-27 23:36:16] User Feedback: Delegation Process Refinement

*   **Source:** User interaction during SPARC task delegation.
*   **Issue:** SPARC's `new_task` messages lack explicit initialization instructions for the receiving mode.
*   **Action:** SPARC must include clear instructions in `new_task` messages specifying what context the receiving mode needs to establish (e.g., "Read file X", "Review Decision Log in globalContext.md").
*   **Learnings:** Providing explicit context-setting steps improves clarity and reduces potential errors for delegated modes.

### [2025-04-27 23:35:14] User Feedback: Delegation Process Refinement

*   **Source:** User interaction during SPARC task delegation.
*   **Issue:**
    1.  SPARC did not read the relevant specification file (`docs/project-specifications.md`) before formulating instructions for the `architect` mode based on that spec.
    2.  SPARC did not explicitly instruct the `architect` mode (and other modes) to provide detailed completion messages summarizing work, challenges, learnings, etc.
*   **Action:**
    1.  SPARC must read necessary source documents before creating delegation instructions based on them.
    2.  SPARC must include explicit instructions in `new_task` messages requiring detailed completion summaries from the receiving mode.
*   **Learnings:** Reading source files ensures delegation instructions are accurate. Requiring detailed completion messages improves transparency and context transfer upon task completion.

### [2025-04-27 23:32:36] User Feedback: Memory Bank Reading Optimization

*   **Source:** User interaction during SPARC Memory Bank synchronization.
*   **Issue:** SPARC reads entire `activeContext.md` and `globalContext.md` files even when only recent or specific information is needed.
*   **Action:** SPARC should use partial reads (`read_file` with `start_line`/`end_line`) for `activeContext.md` (focusing on recent entries) and attempt targeted reads or analysis for `globalContext.md` where possible.
*   **Learnings:** Optimizing Memory Bank reads reduces token usage and improves efficiency.