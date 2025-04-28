# Global Context - PhiloGraph Project

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
        MCPServer[MCP Server (Local)]
    end

    subgraph "Backend Service (Docker)"
        style Backend Service fill:#ccf,stroke:#333,stroke-width:2px
        API[Backend API (Flask/FastAPI)]
        IngestionService[Ingestion Service]
        SearchService[Search Service]
        RelationService[Relationship Service (Basic)]
        BiblioService[Bibliography Service (Basic)]
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
        LiteLLMProxy[LiteLLM Proxy]
    end

    subgraph "Storage (Docker)"
        style Storage fill:#f9d,stroke:#333,stroke-width:2px
        PostgresDB[(PostgreSQL + pgvector)]
    end

    subgraph "External Cloud Services"
        style External Cloud Services fill:#eee,stroke:#666,stroke-width:1px
        VertexAI{{Vertex AI Embeddings API}}
    end

    subgraph "Local Filesystem"
        style Local Filesystem fill:#ddd,stroke:#666,stroke-width:1px
        SourceFiles[/Source Documents/]
    end

    %% Connections
    CLI --> API
    MCPServer --> API

    API -- Orchestrates --> IngestionService
    API -- Orchestrates --> SearchService
    API -- Orchestrates --> RelationService
    API -- Orchestrates --> BiblioService

    IngestionService -- Uses --> GROBID
    IngestionService -- Uses --> PyMuPDF
    IngestionService -- Uses --> SemChunk
    IngestionService -- Uses --> AnyStyle
    IngestionService -- Reads --> SourceFiles
    IngestionService -- Requests Embeddings --> LiteLLMProxy
    IngestionService -- Writes --> PostgresDB

    SearchService -- Requests Embeddings --> LiteLLMProxy
    SearchService -- Queries --> PostgresDB

    RelationService -- Reads/Writes --> PostgresDB
    BiblioService -- Reads/Writes --> PostgresDB

    LiteLLMProxy -- Calls --> VertexAI
```
**Notes:** Tier 0 uses local Docker containers for Postgres+pgvector, LiteLLM Proxy, Python Backend (Flask/FastAPI), and CPU-based text processing tools. Embeddings are generated via calls through the LiteLLM Proxy to the Vertex AI API (`text-embedding-large-exp-03-07`). Interfaces are local CLI and MCP Server. Designed for migration to Tier 1 (Cloud Serverless).

- **Core Technologies:** Vector Database (e.g., PostgreSQL+pgvector), Relational Database (PostgreSQL), File Storage.
- **Architecture:** Service-Oriented, API-First, Plugin-based (for relationships, inference, embedding models, text processing components).
- **Expandability:** Prioritized through API versioning, DB migrations, component separation, feature flags, event-driven patterns (future), specific testing strategies.
- **Key Components:** Text Processor, Search Module, Relationship Manager, Inference Module, Bibliography Manager, Interfaces (CLI, MCP, API, Web UI, Reader).

## Decision Log
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

## Project Files
- `docs/project_idea.md`: Initial brainstorming and requirements.
- `docs/project-specifications.md`: Detailed specification document (updated 2025-04-04 12:59:13).