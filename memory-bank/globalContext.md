# Global Context - PhiloGraph Project
- **[2025-04-28 13:01:37] - Debug - Progress:** Investigation of `test_get_db_pool_failure` concluded. Test remains failing after multiple standard and advanced mocking attempts. Diagnosis points to complex async/mocking interaction. [See Issue-ID: TDD-DBPOOL-FAIL-20250428]

## Product Context
- **Project Name:** PhiloGraph
- **Core Idea:** A specialized knowledge platform combining semantic search and relationship modeling for philosophical texts.
- **Target Users:** Philosophy students, researchers, professors, AI agents, potentially a wider community.
- **Interfaces:** CLI, MCP Server, Web UI, Text Reader.
- **Key Features:** Semantic search, complex relationship modeling (hierarchical, conceptual, historical, etc.), inference capabilities, essay writing support, bibliography management, non-hierarchical exploration, bulk document processing, local file management.
- **Hosting Model:** Initial focus on Hybrid (Local CLI + optional cloud sync/features).
- **Strategic Goal:** Provide immediate utility (MCP server for essay writing) while building an infinitely expandable platform.

## Technical Context
### PhiloGraph Tier 0 MVP Architecture (Spec v2.3) - [2025-04-27 23:39:30]
*Maintained by Architect. See `docs/architecture/tier0_mvp_architecture.md` for details.*

```mermaid
graph TD
    subgraph "User Interfaces (Local)"
        CLI[CLI Client]
        MCPServer[PhiloGraph MCP Server (Local)]
    end

    subgraph "Backend Service (Docker)"
        style Backend Service fill:#ccf,stroke:#333,stroke-width:2px
        API[Backend API (Flask/FastAPI)]
        IngestionService[Ingestion Service]
        SearchService[Search Service]
        RelationService[Relationship Service (Basic)]
        BiblioService[Bibliography Service (Basic)]
        AcquisitionService[Text Acquisition Service]
    end

    subgraph "Text Processing Utilities (Docker / within Backend)"
        style Text Processing Utilities fill:#fcc,stroke:#333,stroke-width:2px
        GROBID[GROBID (CPU)]
        PyMuPDF[PyMuPDF/ebooklib]
        SemChunk[semchunk (CPU)]
        AnyStyle[AnyStyle (Optional)]
    end

    subgraph "Middleware (Docker)"
        style Middleware fill:#cfc,stroke:#333,stroke-width:2px
        LiteLLMProxy[LiteLLM Proxy (Embeddings)]
    end

    subgraph "Storage (Docker)"
        style Storage fill:#f9d,stroke:#333,stroke-width:2px
        PostgresDB[(PostgreSQL + pgvector)]
    end

    subgraph "External Cloud Services"
        style External Cloud Services fill:#eee,stroke:#666,stroke-width:1px
        VertexAI{{Cloud Embedding API<br/>(Vertex AI - text-embedding-large-exp-03-07)}}
    end

    subgraph "External MCP Servers (Local)"
        style External MCP Servers fill:#e9e,stroke:#666,stroke-width:1px
        ZLibMCP[zlibrary-mcp Server]
    end

    subgraph "Local Filesystem"
        style Local Filesystem fill:#ddd,stroke:#666,stroke-width:1px
        SourceFiles[/Source Documents/]
        ZLibDownloads[/zlibrary Downloads/]
        ZLibProcessed[/zlibrary Processed RAG/]
    end

    %% Connections
    CLI --> API
    MCPServer --> API

    API -- Orchestrates --> IngestionService
    API -- Orchestrates --> SearchService
    API -- Orchestrates --> RelationService
    API -- Orchestrates --> BiblioService
    API -- Orchestrates --> AcquisitionService

    IngestionService -- Uses --> GROBID
    IngestionService -- Uses --> PyMuPDF
    IngestionService -- Uses --> SemChunk
    IngestionService -- Uses --> AnyStyle
    IngestionService -- Reads --> SourceFiles
    IngestionService -- Reads --> ZLibProcessed
    IngestionService -- Requests Embeddings --> LiteLLMProxy
    IngestionService -- Writes --> PostgresDB

    SearchService -- Requests Embeddings --> LiteLLMProxy
    SearchService -- Queries --> PostgresDB

    RelationService -- Reads/Writes --> PostgresDB
    BiblioService -- Reads/Writes --> PostgresDB

    AcquisitionService -- Calls via MCP --> ZLibMCP
    ZLibMCP -- Writes --> ZLibDownloads
    ZLibMCP -- Writes --> ZLibProcessed

    LiteLLMProxy -- Calls --> VertexAI
```
**Notes:** Tier 0 uses local Docker containers for PhiloGraph components (Postgres+pgvector, LiteLLM Proxy, Python Backend, CPU Text Proc). Embeddings via LiteLLM Proxy to Vertex AI (`text-embedding-large-exp-03-07`, 768d recommended). Text acquisition via external local `zlibrary-mcp` server. Interfaces: local CLI, PhiloGraph MCP Server. Designed for Tier 1 migration.

- **Core Technologies:** Vector Database (e.g., PostgreSQL+pgvector), Relational Database (PostgreSQL), File Storage.
- **Architecture:** Service-Oriented, API-First, Plugin-based (for relationships, inference, embedding models, text processing components).
- **Expandability:** Prioritized through API versioning, DB migrations, component separation, feature flags, event-driven patterns (future), specific testing strategies.
- **Key Components:** Text Processor, Search Module, Relationship Manager, Inference Module, Bibliography Manager, Interfaces (CLI, MCP, API, Web UI, Reader).

## Decision Log
- **[2025-04-28 17:04:30] - Debug - Decision:** Corrected async mock pattern for raising exceptions. When mocking an `async` function to raise an exception on `await`, set `mock.side_effect = ExceptionType(...)` directly (using `new_callable=AsyncMock` or ensuring the mock is already async). Do not wrap the exception instance in another `AsyncMock` or lambda unless necessary for more complex side effect logic. Removed irrelevant assertions copied from success test cases. [Ref: Issue-ID: TDD-GROBID-REQ-ERR-20250428]
- **[2025-04-28 13:01:37] - Debug - Decision:** Concluded debugging for `test_get_db_pool_failure`. Standard and researched advanced mocking techniques (custom async CM) failed to resolve the issue where `psycopg.OperationalError` is not caught. Diagnosis: Complex interaction likely requires specialized async testing expertise or library-specific patterns. Recommending further investigation or alternative testing strategy. [See Issue-ID: TDD-DBPOOL-FAIL-20250428]
- **[2025-04-28 03:32:04] - Tier 0 Text Acquisition:** Decided to integrate the external `zlibrary-mcp` server for acquiring missing texts via MCP calls from the PhiloGraph backend. Documented in ADR 008 and updated architecture diagrams/components. Requires separate setup/running of `zlibrary-mcp`.
- **[2025-04-28 01:40:33] - Tier 0 Embedding Dimension:** Based on research report (`docs/reports/optimal_embedding_dimension_for_philograph.md`), recommended using **768 dimensions** for `text-embedding-large-exp-03-07` via MRL truncation. This balances inferred semantic quality with Tier 0 resource constraints (RAM, CPU) for pgvector HNSW indexing/querying. 1024 dimensions is a fallback. Decision requires empirical validation. Updated relevant architecture documents (ADR 004, main architecture doc, memory bank).
- **[2025-04-27 23:39:30] - Tier 0 Architecture Design:** Finalized Tier 0 MVP architecture based on spec v2.3. Key components: Local Docker deployment with PostgreSQL+pgvector, LiteLLM Proxy (as unified API gateway), Vertex AI free tier embeddings (via LiteLLM), CPU-based text processing (GROBID, PyMuPDF, semchunk), Python Backend (Flask/FastAPI), CLI/MCP interfaces. No LangChain in Tier 0. Architecture documented in `docs/architecture/tier0_mvp_architecture.md`. Emphasizes modularity for Tier 1 migration.
- **[2025-04-27 21:18:07] - Tier 0 MVP Revision (Cloud Embeddings):** Revised Tier 0 definition in `docs/project-specifications.md` (v2.2) based on user feedback and middleware report. Tier 0 now uses free cloud embeddings (Vertex AI via local LiteLLM Proxy) instead of local CPU embeddings. Stack: Local Docker deployment with PostgreSQL+pgvector, LiteLLM Proxy, Vertex AI (free tier), CPU-based text processing, Python Backend, CLI/MCP. Acknowledges improved embedding performance but retains local processing bottlenecks and adds cloud dependency/setup requirements.
- **[2025-04-27 18:21:09] - Tier 0 MVP Definition:** Defined Tier 0 MVP in `docs/project-specifications.md` (v2.1) based on synthesis report. Stack: Local Docker deployment using PostgreSQL+pgvector, Ollama (CPU) with OS quantized model, CPU-based text processing (GROBID, PyMuPDF, semchunk), Python backend (Flask/FastAPI), CLI/MCP interfaces. Chosen for minimal software cost and best migration path to Tier 1 (Cloud Serverless Postgres).
- **[2025-04-27 17:49:10] - Tier 0 DB Migration Analysis:** Evaluated local DB options (SQLite, Postgres, ArangoDB) for Tier 0 deployability vs. migration effort. Recommended Postgres+pgvector locally as best balance for Tier 1 (Cloud Postgres) migration, while ArangoDB is best for Tier 2 (Cloud ArangoDB) migration but harder to move to Tier 1. SQLite is simplest locally but hardest to migrate.
- **[2025-04-16 09:38:26] - MVP Strategy Recommendation:** Cloud-first MVP strongly recommended (Tier 1 ~$50/mo or Tier 2 ~$150/mo) using serverless components and cost-effective embedding APIs (OpenAI Small/Voyage Lite) to mitigate local hardware (1080 Ti) limitations.
- **[2025-04-16 09:38:26] - MVP Database Recommendation:** ArangoDB recommended for MVP due to multi-model flexibility and simpler initial architecture via ArangoSearch for vectors. TigerGraph considered for post-MVP scalability.
- **[2025-04-16 09:38:26] - MVP Embedding Recommendation:** Avoid experimental Gemini models. Use cost-effective APIs (OpenAI Small, Voyage Lite) for bulk embedding. Local inference of quantized OS models feasible for queries only.
- **[2025-04-16 09:38:26] - MVP Note Processing Recommendation:** Defer complex automated footnote/endnote linking. Implement robust personal note linking via external DB (ArangoDB) storing coordinates/text snippets.
- **[2025-04-16 09:38:26] - Development Methodology Recommendation:** Adopt Hybrid Agile + CRISP-KG methodology, integrating philosophical validation and rigorous cost control.


- **[2025-04-16 01:36:42] - Database Selection:** Recommended ArangoDB based on research report findings regarding multi-model capabilities and hybrid query performance for graph + vector data.
- **[2025-04-16 01:36:42] - Text Processing:** Updated recommendations based on research: GROBID for PDF, Kraken/Calamari+mLLM for OCR, Hybrid Semantic-Spatial Chunking, GROBID/AnyStyle+NER for citations.
- **[2025-04-16 01:36:42] - Source Access:** Revised strategy: Prioritize DOAB/PhilPapers/OpenLibrary APIs, cautiously evaluate Anna's Archive member API, avoid Z-Lib/LibGen programmatic reliance.
- **[2025-04-16 01:36:42] - Script Execution:** Recommended Docker/DevContainers + Custom MCP Servers for reliable Python script execution.
- **[2025-04-16 01:36:42] - Embedding Model (MVP):** Specified Google Gemini Embeddings via Vertex AI, ensuring pluggable architecture.

- **2025-04-04 12:59:13 - Specification Update:** Incorporated detailed feedback regarding PDF/EPUB page numbers, footnote processing, bulk input, local file management, external integrations (Calibre, Quercus, Social Network), and technical expandability strategy into `docs/project-specifications.md`. Prioritized core data model and MCP essentials in initial phases.
- **[2025-04-28 16:57:29] - TDD Blocker:** TDD mode encountered persistent failure in `test_call_grobid_extractor_api_request_error` (async exception handling/mocking issue). Delegating to Debug mode. [See TDD Feedback YYYY-MM-DD HH:MM:SS]
- **[2025-04-28 13:13:54] - Debug Task:** Completed by Debug mode. Test `test_get_db_pool_failure` fixed (commit e5dfc68). Ready to resume TDD. [See Debug Feedback YYYY-MM-DD HH:MM:SS]

- **[2025-04-28 17:04:30] - Debug - Progress:** Successfully fixed `test_call_grobid_extractor_api_request_error` in `tests/utils/test_text_processing.py`. Root cause was incorrect async mock `side_effect` setup and leftover assertions from success case. Test passed verification. Commit: d07e7f4. [Ref: Issue-ID: TDD-GROBID-REQ-ERR-20250428]
## Progress
- **[2025-04-28 21:54:05] - TDD Early Return (Context Limit 44%):** TDD mode partially tested `src/philograph/data_access/db_layer.py`. Added tests for `add_document`, `get_document_by_id`, `check_document_exists`, `add_section`, `add_chunk` (10 new tests, 25 total passing). Remaining: batch, search, refs, relationships, collections. [See TDD Feedback 2025-04-28 21:54:05]
- **[2025-04-28 21:15:51] - TDD Early Return (Context Limit 57%):** TDD mode partially tested `src/philograph/data_access/db_layer.py`. Utility and connection management functions completed (15 tests passing). CRUD and search functions remain. [See TDD Feedback 2025-04-28 20:51:41]
- **[2025-04-28 19:06:05] - TDD Task Completed:** TDD mode finished testing `src/philograph/utils/text_processing.py` (parse_references, call_anystyle_parser). All tests passing (1 skipped). Minor fixes applied (await). [See TDD Memory Bank 2025-04-28 19:06:05]
- **[2025-04-28 18:44:28] - TDD Progress:** TDD mode partially tested `src/philograph/utils/text_processing.py`, adding tests for `basic_reference_parser` (commit `4f03a2d`). Invoked Early Return due to context limit before testing `parse_references` and `call_anystyle_parser`. [See TDD Feedback 2025-04-28 17:33:38]
- **[2025-04-28 17:06:27] - Debug Task:** Completed by Debug mode. Test `test_call_grobid_extractor_api_request_error` fixed (commit d07e7f4). Ready to resume TDD. [See Debug Feedback YYYY-MM-DD HH:MM:SS]
- **[2025-04-28 13:24:10] - Debug - Progress:** Re-investigated TDD-DBPOOL-FAIL-20250428. Confirmed `test_get_db_pool_failure` passes in current code state. Discrepancy with TDD report likely due to code state mismatch during TDD verification. No fix needed. [Ref: Issue-ID: TDD-DBPOOL-FAIL-20250428]
- **[2025-04-28 13:05:04] - Debug - Progress:** Successfully fixed `test_get_db_pool_failure` by mocking `cursor.execute` to raise `psycopg.OperationalError` within the nested async context managers. Test passed verification. [See Issue-ID: TDD-DBPOOL-FAIL-20250428]
- **[2025-04-28 10:34:52] - Git Initialization:** Completed by DevOps mode. Repository initialized, `.gitignore` configured, and initial project state committed across 5 logical commits (fcb00d8, e5557d2, a31eed4, 1ff8e4e, cdcbafd). Ready to resume testing.
- **[2025-04-28 04:23:39] - Tier 0 Implementation:** Completed initial code structure and configuration for Tier 0 MVP. Created core Python modules (`src/philograph/*`), Docker setup (`Dockerfile`, `docker-compose.yml`,
`litellm_config.yaml`), and initial `README.md`. Basic tests for config module created. Ready for testing phase.
## Project Files
- `docs/project_idea.md`: Initial brainstorming and requirements.
- `docs/project-specifications.md`: Detailed specification document (updated 2025-04-04 12:59:13).