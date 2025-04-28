# SPARC Mode Feedback Log
<!-- Entries below should be added reverse chronologically (newest first) -->

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