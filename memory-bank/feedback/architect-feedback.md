# Architect Feedback
<!-- Entries below should be added reverse chronologically (newest first) -->

### [2025-04-27 23:59:06] - User Feedback on Research Prompt Tool Use
*   **Trigger:** User denied `use_mcp_tool` attempt for `vectorize` server's `deep-research` tool.
*   **Context:** Attempting to generate research prompt for embedding dimensionality via MCP tool.
*   **Feedback:** User clarified that the `vectorize` tool is not appropriate; I should provide the research prompt text directly for the user to submit to Gemini Deep Research manually.
*   **Action:** Will provide the research prompt text instead of using the tool.
*   **Rationale:** Follow user clarification on how to handle research prompt generation.
*   **Outcome:** Task continuation to provide prompt text.
*   **Follow-up:** Provide research prompt text.

### [2025-04-27 23:53:18] - User Feedback on Tier 0 Architecture Attempt
*   **Trigger:** User denied `attempt_completion` after creation of `docs/architecture/tier0_mvp_architecture.md`.
*   **Context:** Initial Tier 0 architecture document created based on spec v2.3. Memory Bank updated.
*   **Feedback:**
    1.  Missing Architecture Decision Records (ADRs) for key decisions.
    2.  Architecture document and Memory Bank did not specify the chosen Vertex AI embedding model (`text-embedding-large-exp-03-07`).
    3.  Decision on embedding dimensionality is pending research; requires a research prompt for Gemini Deep Research.
*   **Action:** Will create ADRs, update documents with the specific embedding model, and generate the research prompt for dimensionality.
*   **Rationale:** Address user feedback to ensure completeness and accuracy of architectural documentation and decisions.
*   **Outcome:** Task continuation to incorporate feedback.
*   **Follow-up:** Create ADRs, update docs, generate research prompt.