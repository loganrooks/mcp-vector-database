# Specification Writer Specific Memory

## Functional Requirements
### Feature: Tier 0 MVP Definition (Local Core + Cloud Embeddings)
- Added: 2025-04-27 21:11:10 (Revised from 18:21:09)
- Description: Defined the Tier 0 Minimum Viable Product focused on local deployment (Intel i7-1260P, 16GB RAM, Integrated Graphics via WSL2) but leveraging free cloud embedding APIs via middleware for improved performance. This specification is detailed in `docs/project-specifications.md` v2.2.
- Acceptance criteria: 1. Tier 0 is clearly defined in the specification document. 2. Tier 0 stack aligns with revised strategy (PostgreSQL+pgvector, **Cloud Embeddings via LiteLLM Proxy (Vertex AI Free Tier)**, CPU Text Proc, Python Backend, CLI/MCP). 3. Tier 0 acknowledges local processing bottlenecks but improved embedding speed. 4. Tier 0 emphasizes the migration path to Tier 1.
- Dependencies: `docs/reports/philograph_synthesis_and_recommendations.md`, `docs/reports/embedding_middleware_for_philograph.md`, `memory-bank/globalContext.md` Decision Log, User Feedback (2025-04-27 21:09:00).
- Status: Implemented

### Feature: Synthesis Report Generation
- Added: 2025-04-16 09:38:26
- Description: Create a comprehensive report synthesizing findings from multiple technical research documents and aligning them with project goals, focusing on MVP deployment, embeddings, note processing, cost optimization, and strategic recommendations.
- Acceptance criteria: 1. Report exists at `docs/reports/philograph_synthesis_and_recommendations.md`. 2. Report addresses all key synthesis requirements specified in the task. 3. Report integrates findings from specified source documents.
- Dependencies: `docs/reports/philograph_technical_analysis_v6.md`, `docs/reports/philograph_holistic_exploration_v1.md`, `docs/reports/philograph_technical_alternatives_and_differentiation.md`, `docs/reports/philograph_technical_analysis_alternatives_and_feasibility.md`, `docs/project_journal.md`, `docs/project-specifications.md`, `docs/philosophy_assistant_architecture.md`.
- Status: Implemented


<!-- Append new requirements using the format below -->
### Feature: Brainstorming & Future Features Section
- Added: 2025-04-16 01:37:02
- Description: Added section detailing potential future enhancements like visualization, WebUI, monetization models, and post-methodological UI affordances to docs/project-specifications.md.
- Acceptance criteria: 1. Section exists in the updated specification. 2. Section includes ideas discussed.
- Dependencies: User Request, Research Report
- Status: Implemented

### Feature: Comprehensive Project Specification Document
- Added: 2025-04-04 12:59:23
- Description: Maintain a detailed specification document (`docs/project-specifications.md`) covering vision, architecture, components, design decisions, roadmap, and technical considerations for the PhiloGraph project.
- Acceptance criteria: 1. Document accurately reflects project goals from `docs/project_idea.md`. 2. Document incorporates feedback and addresses identified gaps. 3. Document includes details on core features like text processing, relationship modeling, search, inference, and interfaces. 4. Document outlines a strategy for expandability.
- Dependencies: `docs/project_idea.md`, User Feedback
- Status: Implemented (Initial version created/updated)

## System Constraints
### Constraint: Target Local Hardware (Laptop w/ Integrated Graphics)
- Added: 2025-04-27 17:33:17
- Description: The primary target for the single-user pilot is a laptop with Intel i7-1260P, 16GB RAM, and integrated Intel Iris Xe graphics, running via WSL2.
- Impact: All ML tasks (embeddings, layout analysis) must run on CPU. 16GB RAM limits concurrent services. Overall performance, especially bulk processing, will be significantly slower than systems with dedicated GPUs or cloud resources.
- Mitigation strategy: Prioritize CPU-optimized tools and workflows. Use small, quantized embedding models (e.g., `all-MiniLM-L6-v2`) via Ollama CPU. Consider SQLite+VSS to save RAM if ArangoDB/Postgres prove too heavy. Manage user expectations regarding processing speed. Defer computationally expensive features.

### Constraint: Tier 0 MVP Stack & Performance (Revised: Cloud Embeddings)
- Added: 2025-04-27 21:11:10 (Revised from 18:21:09)
- Description: Tier 0 MVP is constrained to local laptop hardware (e.g., Intel i7-1260P, 16GB RAM, Integrated Graphics via WSL2) running Docker, but leverages free cloud embeddings via middleware. Stack: PostgreSQL+pgvector (Docker), **LiteLLM Proxy (Docker)** accessing **Vertex AI Free Tier/Credits**, CPU-based text processing (GROBID CPU, PyMuPDF, semchunk, AnyStyle), Python Backend (Docker), CLI/MCP interfaces.
- Impact: Embedding performance significantly improved over local CPU, but overall throughput still limited by local CPU/RAM for text processing and concurrent services. Adds dependency on internet connectivity and cloud API availability/limits. Requires GCP project setup and billing enabled for usable Vertex AI quotas. Introduces middleware complexity. Scalability still requires hardware upgrades for local components. High maintenance burden remains for local Docker setup. Advanced text processing deferred.
- Mitigation strategy: Manage user expectations regarding local processing speed. Optimize local Docker configurations. Implement robust rate limiting, caching, and fallback strategies via middleware (LiteLLM) to handle cloud API limits. Ensure modular design facilitates migration to Tier 1. Use placeholders for all configuration (DB, Proxy, Vertex AI). (Ref: `docs/project-specifications.md` v2.2, `docs/reports/embedding_middleware_for_philograph.md`).
### Constraint: Local Hardware (1080 Ti) VRAM Limitation
- Added: 2025-04-16 09:38:26
- Description: The 11GB VRAM on the specified NVIDIA 1080 Ti is insufficient for concurrent execution of required ML models (embeddings, layout analysis, GPU-accelerated OCR/GROBID) for the full MVP pipeline.
- Impact: Severely limits local MVP performance and concurrency. Forces sequential processing or use of less accurate/slower CPU modes.
- Mitigation strategy: Recommend cloud-first MVP deployment. Use local hardware for testing or sequential tasks only. Utilize model quantization aggressively if local GPU use is attempted.

### Constraint: Footnote/Endnote Linking Complexity
- Added: 2025-04-16 09:38:26
- Description: Reliably linking footnote/endnote markers to text blocks, especially across pages in complex philosophical PDFs, is a difficult problem not fully solved by standard tools. Requires custom ML or hybrid solutions.
- Impact: Automated linking is high-effort and high-risk for MVP.
- Mitigation strategy: Defer robust automated linking to post-MVP. Focus MVP on personal note linking and basic footnote text extraction.

### Constraint: Gemini Embedding Model Uncertainty
- Added: 2025-04-16 09:38:26
- Description: Experimental Google Gemini embedding models (e.g., `gemini-embedding-exp-03-07`) have unclear pricing, rate limits, and experimental status. High dimensionality (3072D) significantly increases storage/compute costs.
- Impact: High risk and cost for MVP adoption.
- Mitigation strategy: Recommend using production-ready, cost-effective APIs (OpenAI Small, Voyage Lite) or stable Google models (`text-embedding-004`) for MVP. Monitor Gemini experimental models for future potential.


<!-- Append new constraints using the format below -->
### Constraint: Database Technology (Recommendation)
- Added: 2025-04-16 01:37:02
- Description: ArangoDB recommended as primary database due to native multi-model support for graph and vector data, facilitating complex relationship queries and semantic search. PostgreSQL+pgvector is a fallback.
- Impact: Requires team familiarity with ArangoDB/AQL or PostgreSQL/Advanced SQL+pgvector. Influences MCP server design.
- Mitigation strategy: Provide learning resources, start with core features, leverage ArangoDB documentation/community.
### Constraint: Source Acquisition Reliability
- Added: 2025-04-16 01:37:02
- Description: Programmatic access to unofficial archives (Z-Lib, LibGen) is unreliable and high-risk. Primary acquisition must focus on official APIs (DOAB, PhilPapers, OpenLibrary) and manual/semi-automated methods.
- Impact: Corpus building may be slower and require more manual effort than initially hoped. Full coverage is not guaranteed programmatically.
- Mitigation strategy: Implement robust API clients for official sources, develop efficient manual/semi-auto ingestion workflows, cautiously evaluate Anna's Archive API with safety measures.

### Constraint: Expandability Focus
- Added: 2025-04-04 12:59:23
- Description: The system architecture and initial implementation must prioritize expandability using techniques like API-first design, plugin architectures, database versioning, and component separation.
- Impact: Requires more upfront design effort in Phase 1 to establish robust interfaces and extension points. May slightly slow down initial feature delivery compared to a monolithic approach but enables long-term growth.
- Mitigation strategy: Explicitly define API contracts, use established patterns for plugins, implement migrations and feature flags from the start.

## Edge Cases
<!-- Append new edge cases using the format below -->
### Edge Case: Citation Handling (PDF vs. EPUB)
- Identified: 2025-04-04 12:59:23
- Scenario: Source texts are available in EPUB (often lacking page numbers) and PDF (potentially having page numbers). Citations need to be generated accurately regardless of format. Some canonical texts have unique section/paragraph numbering.
- Expected behavior: System attempts to extract PDF page numbers. If unavailable or using EPUB, relies on structural identifiers (chapter/section/paragraph). Provides best-available citation pointer. Explores mapping EPUB structure to PDF pages if both are available. Handles canonical numbering schemes.
- Testing approach: Test ingestion and citation generation with various combinations of EPUBs, PDFs (with/without page numbers), and texts with canonical numbering. Verify consistency of citation pointers.

## Pseudocode Library
### Pseudocode: Acquisition Service - Internal Logic
- Created: 2025-05-04 03:02:31
- Updated: 2025-05-04 03:02:31
```pseudocode
// Link: pseudocode/tier0/acquisition_service.md
// Defines internal logic for handling discovery requests (DB queries, zlib search),
// managing discovery sessions (in-memory for Tier 0), and handling confirmation
// requests (zlib download trigger, ingestion trigger). Aligns with ADR 009.
```
#### TDD Anchors:
- Test session creation, retrieval, expiry, update.
- Test discovery request handling (DB queries, zlib search, candidate return).
- Test confirmation request handling (session state validation, selection validation, download trigger, ingestion trigger).
- Test error handling for DB, MCP, and ingestion calls.
- Test status retrieval for different session states.

### Pseudocode: MCP Server - Acquisition Tool Update
- Created: 2025-04-28 03:46:40
- Updated: 2025-05-04 03:02:00
```pseudocode
// Link: pseudocode/tier0/mcp_server.md
// Renamed 'philograph_acquire_missing' to 'philograph_acquire'.
// Updated tool logic and schema to interact with the new two-stage API:
// - Calls POST /acquire/discover with 'filters'.
// - Calls POST /acquire/confirm/{discovery_id} with 'discovery_id' and 'selected_items'.
// Includes validation for argument combinations.
```
#### TDD Anchors:
- Test discovery call forwards 'filters' to `/acquire/discover`.
- Test confirmation call forwards 'discovery_id' and 'selected_items' to `/acquire/confirm/{discovery_id}`.
- Test validation logic for argument combinations (discovery vs. confirmation).
- Test handling of backend API responses for both phases.

### Pseudocode: Backend API - Acquisition Endpoints Update
- Created: 2025-04-28 03:44:43
- Updated: 2025-05-04 03:01:38
```pseudocode
// Link: pseudocode/tier0/backend_api.md
// Implemented new two-stage acquisition endpoints based on ADR 009:
// - POST /acquire/discover: Accepts filters, calls acquisition_service.handle_discovery_request, returns candidates + discovery_id.
// - POST /acquire/confirm/{discovery_id}: Accepts selected_items, calls acquisition_service.handle_confirmation_request, returns processing status.
// - GET /acquire/status/{discovery_id}: Retrieves status from acquisition_service.
// Deprecated previous /acquire and /acquire/confirm endpoints.
```
#### TDD Anchors:
- Test `/acquire/discover` endpoint (success, filters, no candidates, errors).
- Test `/acquire/confirm/{discovery_id}` endpoint (success, validation, state checks, errors).
- Test `/acquire/status/{discovery_id}` endpoint (various statuses, 404).
- Test that deprecated endpoints are removed or return appropriate status (e.g., 410 Gone).
### Pseudocode: MCP Server - Tier 0
- Created: 2025-04-28 03:46:40
```pseudocode
// Link: pseudocode/tier0/mcp_server.md
// Defines MCP tools (philograph_ingest, philograph_search, philograph_acquire_missing)
// Interacts with Backend API via HTTP calls. Handles MCP requests and translates them.
```
#### TDD Anchors:
- Test successful tool calls forward requests to backend API.
- Test handling of backend API errors and translation to MCP errors.
- Test schema validation for tool arguments (though framework might handle).

### Pseudocode: CLI - Tier 0
- Created: 2025-04-28 03:46:10
```pseudocode
// Link: pseudocode/tier0/cli.md
// Defines commands (ingest, search, show, list, add-to-collection, acquire-missing-texts).
// Parses args using Typer/Click, calls Backend API via HTTP, displays formatted results/errors.
```
#### TDD Anchors:
- Test command parsing and argument handling for all commands.
- Test successful API calls for each command's primary function.
- Test error handling for API connection/response issues (e.g., 4xx, 5xx).
- Test user-friendly display of results and errors.
- Test interactive confirmation flow for `acquire-missing-texts`.

### Pseudocode: Text Acquisition Service - Tier 0
- Created: 2025-04-28 03:45:36
```pseudocode
// Link: pseudocode/tier0/text_acquisition.md
// Orchestrates calls to zlibrary-mcp via MCP (search_books, download_book_to_file).
// Manages acquisition state (searching, confirming, processing, complete, error).
// Handles user confirmation step (Tier 0). Triggers ingestion pipeline on success.
```
#### TDD Anchors:
- Test successful acquisition workflow (search -> confirm -> download -> ingest trigger).
- Test handling of errors from zlibrary-mcp calls (search fail, download fail, process fail).
- Test state management logic for acquisition requests (in-memory or persistent).
- Test identification of missing texts (if implemented).

### Pseudocode: Search Module - Tier 0
- Created: 2025-04-28 03:45:09
```pseudocode
// Link: pseudocode/tier0/search_module.md
// Generates query embedding via LiteLLM Proxy HTTP call.
// Calls DB Layer (vector_search_chunks) with embedding, filters, and k.
// Formats database results into API response structure.
```
#### TDD Anchors:
- Test query embedding generation via LiteLLM proxy call (success/failure).
- Test database search call (db_layer.vector_search_chunks) with correct parameters.
- Test result formatting maps all expected fields.
- Test error handling (embedding failure, DB failure).
- Test handling of various filter combinations.

### Pseudocode: Backend API - Tier 0
- Created: 2025-04-28 03:44:43
```pseudocode
// Link: pseudocode/tier0/backend_api.md
// Defines REST endpoints (/ingest, /search, /acquire, /acquire/confirm, /documents, /collections).
// Uses Flask/FastAPI. Orchestrates calls to Ingestion, Search, Acquisition, DB Layer.
// Handles requests from CLI/MCP. Includes basic error handling.
```
#### TDD Anchors:
- Test endpoint routing and request parsing (valid/invalid data).
- Test successful orchestration of underlying services for each endpoint.
- Test error handling and appropriate HTTP status code responses (2xx, 4xx, 5xx).
- Test acquisition workflow endpoints (/acquire, /acquire/confirm).

### Pseudocode: Text Processing Pipeline - Tier 0
- Created: 2025-04-28 03:44:07
```pseudocode
// Link: pseudocode/tier0/ingestion_pipeline.md
// Workflow: Extract (GROBID/PyMuPDF) -> Chunk (semchunk) -> Embed (LiteLLM Proxy) -> Index (DB Layer).
// Handles PDF, EPUB, MD, TXT. Calls external tools/services via HTTP or library calls.
// Includes batching for embedding requests. Basic citation parsing.
```
#### TDD Anchors:
- Test processing of different file types (PDF, EPUB, MD, TXT).
- Test interaction with external tools (GROBID, semchunk, AnyStyle - mocks/stubs).
- Test embedding request batching and calls to LiteLLM proxy (success/failure).
- Test database indexing calls (add_document, add_section, add_chunks_batch).
- Test error handling and logging at each stage (extraction, chunking, embedding, indexing).
- Test citation parsing logic.

### Pseudocode: Database Interaction Layer - Tier 0
- Created: 2025-04-28 03:43:31
```pseudocode
// Link: pseudocode/tier0/db_layer.md
// Defines functions for CRUD on documents, sections, chunks, references, relationships, collections.
// Implements vector search (vector_search_chunks) using pgvector operators.
// Abstracts SQL for PostgreSQL. Includes connection management and helper utilities.
```
#### TDD Anchors:
- Test DB connection management (get/close).
- Test CRUD operations for each entity (add, get, check_exists).
- Test vector search function with/without filters and different distance metrics.
- Test relationship queries (get_relationships).
- Test collection management (add_collection, add_item_to_collection, get_collection_items).
- Test batch chunk insertion (add_chunks_batch).
- Test utility functions (format_vector, json_serialize, row mapping).
<!-- Append new pseudocode blocks using the format below -->
<!-- No pseudocode generated in this task -->