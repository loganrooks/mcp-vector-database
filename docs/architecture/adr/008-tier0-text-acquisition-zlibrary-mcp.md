# ADR 008: Tier 0 Text Acquisition via zlibrary-mcp Server

*   **Status:** Proposed
*   **Date:** 2025-04-28
*   **Deciders:** Architect Mode, User Input
*   **Consulted:** `docs/project-specifications.md` v2.3 (Sections 4, 5, 8, 10), `zlibrary-mcp` README (provided by user)
*   **Affected:** Tier 0 Implementation, Backend Service, CLI/MCP Interfaces, Deployment/Operations, User Workflow.

## Context and Problem Statement

PhiloGraph aims to build a comprehensive knowledge graph from philosophical texts. While users provide initial source documents, the system needs a mechanism to acquire additional texts, particularly those identified as missing through citation analysis or explicit user requests. Tier 0 requires a functional, locally-operable solution for this text acquisition.

## Decision Drivers

*   **Functionality:** Need a way to search for and download missing texts programmatically.
*   **Integration:** Solution should integrate with the PhiloGraph backend service.
*   **Tier 0 Constraints:** Must be operable within the local Docker environment or alongside it.
*   **Existing Tool:** The user has an existing `zlibrary-mcp` server designed for interacting with Z-Library, including search, download, and RAG pre-processing capabilities.
*   **Specification v2.3:** Explicitly incorporates `zlibrary-mcp` integration for text acquisition.

## Considered Options

1.  **Integrate `zlibrary-mcp`:** Utilize the existing external `zlibrary-mcp` server, having the PhiloGraph backend call its tools (`search_books`, `download_book_to_file`) via MCP (`use_mcp_tool`).
2.  **Build Native Acquisition Module:** Develop a new module within the PhiloGraph backend service to directly interact with Z-Library (or other sources) for text acquisition.
3.  **Manual Acquisition Only:** Require users to manually find and add all texts to the source directory.

## Decision Outcome

**Chosen Option:** 1. Integrate `zlibrary-mcp`.

**Rationale:**

*   **Leverages Existing Tool:** Utilizes a pre-existing, specialized tool (`zlibrary-mcp`) developed by the user, reducing the need to build redundant functionality within PhiloGraph itself.
*   **MCP Integration:** Aligns with the project's use of the Model Context Protocol for inter-service communication, particularly between the AI assistant (or backend acting on its behalf) and specialized tools.
*   **Functionality Match:** The `zlibrary-mcp` server provides the necessary core functions: searching Z-Library, downloading files, and crucially, pre-processing downloads for RAG (`process_document_for_rag`), which simplifies the ingestion pipeline for acquired texts.
*   **Decoupling:** Keeps the potentially complex and fragile logic of interacting with external library sites (like Z-Library) isolated within the dedicated `zlibrary-mcp` server, separating concerns from the core PhiloGraph backend.
*   **Alignment with Spec:** Directly implements the integration specified in `project-specifications.md` v2.3.

**Rejection Rationale:**

*   *Build Native Acquisition Module:* Rejected as it would duplicate functionality already present in `zlibrary-mcp` and tightly couple the PhiloGraph backend to the specifics of Z-Library interaction.
*   *Manual Acquisition Only:* Rejected as it fails to meet the requirement for programmatic acquisition of missing texts identified by the system.

## Consequences

*   **Positive:**
    *   Faster implementation of text acquisition functionality by reusing `zlibrary-mcp`.
    *   Clear separation of concerns between PhiloGraph core logic and external library interaction.
    *   Utilizes the established MCP communication pattern.
    *   Includes valuable RAG pre-processing capability.
*   **Negative:**
    *   Introduces an external dependency: `zlibrary-mcp` must be running and configured separately for PhiloGraph to function fully.
    *   Requires managing the setup and configuration of `zlibrary-mcp` (Node.js, Python venv, credentials) alongside PhiloGraph's Docker setup.
    *   Potential for brittleness if the `zlibrary-mcp` server's interface or underlying Z-Library website changes (though this risk exists regardless of where the logic resides).
    *   The `zlibrary-mcp` server might require modifications for better integration (e.g., configurable output paths for downloaded/processed files, improved error handling).
    *   Legal/ethical considerations of using Z-Library remain the user's responsibility.

## Implementation Details (Tier 0)

1.  **Setup:** The `zlibrary-mcp` server must be installed, configured (env vars `ZLIBRARY_EMAIL`, `ZLIBRARY_PASSWORD`), built (`npm run build`), and running locally, accessible to the PhiloGraph backend (likely via stdio integration configured in the AI assistant/agent running PhiloGraph).
2.  **Workflow:**
    *   PhiloGraph Backend (e.g., via a dedicated "Acquisition Manager" component or triggered by CLI/MCP command) identifies a missing text (e.g., based on citation data).
    *   Backend uses `use_mcp_tool` to call `zlibrary-mcp`'s `search_books` tool with relevant metadata (title, author, etc.).
    *   Backend presents search results to the user for confirmation (Tier 0 requires user confirmation before download).
    *   Upon confirmation, Backend uses `use_mcp_tool` to call `zlibrary-mcp`'s `download_book_to_file` tool, passing the selected `bookDetails` and setting `process_for_rag: true`.
    *   `zlibrary-mcp` downloads the book (e.g., to `./downloads/`) and processes it (e.g., to `./processed_rag_output/`), returning the *path* to the processed plain text file.
    *   PhiloGraph Backend receives the path to the processed file.
    *   Backend triggers its own `/ingest` endpoint/workflow, providing the path to the processed file (now treated like any other source document).
3.  **Configuration:** Consider making the output directories (`./downloads/`, `./processed_rag_output/`) in `zlibrary-mcp` configurable via environment variables or tool arguments to allow better coordination with PhiloGraph's expected source directories.

## Validation

*   PhiloGraph backend can successfully use `use_mcp_tool` to call `zlibrary-mcp` tools (`search_books`, `download_book_to_file` with RAG processing).
*   `zlibrary-mcp` successfully downloads and processes a test book, returning the correct path to the processed file.
*   PhiloGraph backend successfully receives the path and triggers ingestion for the processed file.
*   End-to-end workflow functions as expected for acquiring and ingesting a missing text.

## Links

*   `docs/project-specifications.md` v2.3 (Sections 4, 5, 8, 10)
*   `docs/architecture/tier0_mvp_architecture.md`
*   `zlibrary-mcp` README (provided by user)