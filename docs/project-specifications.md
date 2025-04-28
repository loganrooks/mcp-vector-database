# PhiloGraph: Philosophical Knowledge Platform - Specification v2.1 (Tier 0 Focus)

## Vision Document

### Executive Summary

PhiloGraph is envisioned as a specialized knowledge platform designed to revolutionize philosophical research and engagement. It integrates advanced semantic search capabilities (powered by vector embeddings) with sophisticated relationship modeling, allowing users to navigate the complex web of philosophical ideas, texts, and authors. Operating initially within the RooCode framework via a dedicated MCP server, and designed for future expansion into CLI and web interfaces, PhiloGraph aims to provide immediate utility for tasks like essay writing and research while building towards a comprehensive, extensible system. This platform uniquely seeks to support not only traditional analytical methods but also to facilitate exploratory approaches inspired by diverse philosophical traditions, including post-methodological thought. This document outlines the refined vision, architecture, technical specifications, and strategic roadmap, with a specific focus on the **Tier 0 Minimum Viable Product (MVP)** deployable on local hardware.

## 1. Core Vision

PhiloGraph will be a comprehensive tool for philosophical research that:

1.  **Connects Ideas:** Models explicit relationships (citation, influence, critique, etc.) and discovers implicit connections (semantic similarity) across texts and concepts.
2.  **Organizes Flexibly:** Supports traditional hierarchical structures (Book -> Chapter -> Section) while enabling non-hierarchical, rhizomatic exploration and user-defined organization.
3.  **Enables Sophisticated Queries:** Allows complex queries combining semantic search (vector similarity) with graph traversal and metadata filtering (e.g., by author, school, theme, course).
4.  **Supports Research Workflows:** Assists users throughout the research lifecycle, from discovery and analysis to synthesis, writing, and citation management.
5.  **Offers Multiple Interfaces:** Provides access via CLI (for power users), MCP (for AI agent integration), and a future Web UI (for broader access and community features).
6.  **Prioritizes Extensibility:** Built on a modular, API-first architecture with pluggable components for future growth and adaptation.
7.  **Facilitates Diverse Methodologies:** Provides tools and affordances that enable users to engage with texts using various philosophical approaches, including facilitating explorations inspired by post-methodological concepts.

## 2. User Stories

*(User stories remain largely the same as v2.0, covering Individual Researchers, AI Integration, and Community Features)*

### Individual Researcher
- As a philosophy student, I want to search across assigned readings to find passages related to specific concepts.
- As a researcher, I want to trace the evolution of ideas across philosophical traditions using explicit and semantic links.
- As an essay writer, I want to find supporting evidence or contradicting viewpoints for my thesis, with accurate citation data.
- As a reader, I want to discover connections between texts based on shared themes, influences, or semantic similarity.
- As a student, I want to filter search results by course (e.g., "PHL316"), time period, or philosophical school.
- As a writer, I want to check my interpretation against specific passages in assigned texts.
- As a researcher, I want to manage collections of quotes and notes linked to specific text passages.

### AI Integration
- As an AI assistant (via RooCode/MCP), I want to query PhiloGraph to retrieve relevant philosophical passages and metadata to answer user questions accurately.
- As an AI assistant, I want to use PhiloGraph's relationship data to perform comparative analysis or trace conceptual lineages.
- As an AI assistant, I want to leverage PhiloGraph to help users draft essays with proper citations.

### Community Features (Future Phases)
- As a philosophy professor, I want to create and share curated reading lists or knowledge graphs for my students.
- As a philosophy enthusiast, I want to discover new readings based on texts or concepts I've explored.
- As a debate participant, I want to easily reference specific passages with stable identifiers to support my arguments.
- As a researcher, I want to optionally share annotations or discovered relationships with a community.

## 3. Deployment Tiers & Tier 0 MVP Definition

Based on the synthesis report (`docs/reports/philograph_synthesis_and_recommendations.md`, lines 26-152), PhiloGraph's initial development focuses on a **Tier 0 MVP** designed for local deployment with minimal software cost, acknowledging performance constraints. Higher tiers represent future cloud-based targets.

### Tier 0: Minimal Cost / Local Laptop MVP (~$0 Software Cost + Hardware/Time Cost)

*   **Goal:** Provide core functionality (ingestion, semantic search, basic graph, note linking, CLI/MCP interfaces) deployable on typical developer hardware without incurring direct software costs. Establish a foundation for future cloud migration.
*   **Target Environment:** Local Laptop (e.g., Intel i7-1260P, 16GB RAM, Integrated Graphics via WSL2) - (Report Ref: Line 28).
*   **Components:**
    *   **Database:** **PostgreSQL + pgvector** (Free, Self-hosted via Docker). Chosen for balance of local capability and easiest migration path to Tier 1 (Cloud Serverless Postgres). (Report Ref: Lines 132-138, 149, 152).
    *   **Text Processing:** CPU-based tools: **GROBID** (CPU mode), **PyMuPDF**, **`semchunk`** (CPU), **AnyStyle** (Self-hosted, Docker). (Report Ref: Line 34).
    *   **Embeddings:** Quantized Open Source Model (e.g., `all-MiniLM-L6-v2` or `nomic-embed-text` Q4 GGUF) via **Ollama** (Free, Self-hosted via Docker, **CPU Inference Only**). (Report Ref: Line 35).
    *   **Backend/API:** Simple Python **Flask/FastAPI** (Self-hosted, Docker). (Report Ref: Line 36).
    *   **Interface:** **CLI**, **MCP Server** (local). (Report Ref: Line 37).
*   **Estimated Cost:** **$0 direct software cost.** Minimal electricity cost. Significant unquantified cost in setup time, maintenance effort, and very slow bulk processing time. (Report Ref: Line 38).
*   **Expected Performance:**
    *   **Bottleneck:** CPU performance for all ML tasks and 16GB RAM limiting concurrent services (DB, Ollama, processing). (Report Ref: Line 40).
    *   **Ingestion:** Very slow due to sequential processing and CPU-based text extraction. (Report Ref: Line 41).
    *   **Query Latency:** Acceptable for single-user interactive queries if DB/model fit in RAM. High load degrades performance. (Report Ref: Line 42).
*   **Achievable Features (MVP Core):** (Report Ref: Lines 43-48)
    *   Basic document ingestion (TXT, MD, simple PDF/EPUB via GROBID CPU).
    *   Semantic search via local embeddings.
    *   Basic graph relationship storage/querying (Postgres - potentially JSONB or simple tables).
    *   Personal note linking (manual, via external DB strategy - see Section 6).
    *   CLI and MCP interfaces.
*   **Explicit Sacrifices:** (Report Ref: Lines 49-55)
    *   Performance (esp. Bulk Ingestion), Concurrency, Advanced Text Processing (no robust footnote linking, no GPU acceleration), Scalability (requires hardware upgrade), Reliability (manual backups), High Maintenance Burden.
*   **Migration Path:** This Tier 0 stack, particularly **PostgreSQL+pgvector**, is explicitly chosen to facilitate the **easiest migration path to Tier 1** (Cloud Serverless Postgres like Supabase/NeonDB), requiring primarily data transfer and connection string updates. (Report Ref: Lines 134, 152).

### Tier 1: Cost-Optimized Cloud (~$50/month)

*   **Goal:** Improve performance, reliability, and scalability over Tier 0 using cost-effective cloud services.
*   **Components:** Serverless Postgres+pgvector (Supabase/NeonDB), Serverless Functions (Lambda/GCF), Embedding APIs (OpenAI Small/Voyage Lite), Object Storage (S3/GCS).
*   **Migration from Tier 0:** Relatively straightforward due to Postgres compatibility. Requires data migration and deploying backend logic to serverless functions.

### Tier 2: Balanced Cloud Performance (~$150/month)

*   **Goal:** Further enhance performance and enable more complex features using managed databases and potentially higher-quality embedding APIs.
*   **Components:** Managed ArangoDB (Oasis) or higher-tier Serverless Postgres, Serverless Functions, Embedding APIs (Voyage Lite/OpenAI Large), Object Storage.
*   **Migration from Tier 0:** More complex, involving schema mapping (Relational -> Document/Graph if moving to ArangoDB) and query translation (SQL -> AQL).

## 4. System Architecture (Tier 0 Focus)

The overall architecture remains service-oriented, emphasizing modularity and API-driven communication, adapted for the Tier 0 local deployment.

```mermaid
flowchart TD
    subgraph "Storage Layer (Tier 0 - Local Docker)"
        style Storage Layer fill:#fdf,stroke:#333,stroke-width:2px
        DB[(**PostgreSQL + pgvector**<br/>Relational + Vector via Docker)]
        FSS[File Storage System<br/>(Local Filesystem)]
    end

    subgraph "Core Services (Tier 0 - Local Docker)"
        style Core Services fill:#def,stroke:#333,stroke-width:2px
        TP[Text Processor<br/>(GROBID CPU, PyMuPDF, semchunk, Ollama CPU)]
        SM[Search Module<br/>(SQL/pgvector Query Engine)]
        RM[Relationship Manager<br/>(SQL Operations)]
        IM[Inference Module<br/>(Basic SQL/Python Rules)]
        BM[Bibliography Manager<br/>(Citation/Collections)]

        TP -- Stores --> DB
        SM -- Queries --> DB
        RM -- Manages --> DB
        IM -- Analyzes --> DB
        BM -- Uses --> DB & SM & RM
    end

    subgraph "Interface Layer (Tier 0 - Local)"
        style Interface Layer fill:#ffc,stroke:#333,stroke-width:2px
        CLI[Command Line Interface]
        MCPI[MCP Interface<br/>(Local RooCode Integration)]
        API[Internal REST/GraphQL API<br/>(Flask/FastAPI via Docker)]
        %% WUI[Web UI<br/>(Future Phase)]
        %% TR[Text Reader<br/>(Future Phase)]

        CLI --> API
        MCPI --> API
        %% WUI --> API
        %% TR --> API
    end

    subgraph "External Systems & Tools (Tier 0)"
         style External Systems & Tools fill:#eee,stroke:#333,stroke-width:1px
         SourceAPIs{{Source APIs<br/>(DOAB, PhilPapers, etc. - Manual/Scripted Access)}}
         %% LMSTools{{LMS Integration<br/>(Future Phase)}}
         ExtScripts[/Processing Scripts<br/>(Local Python/Docker)/]
         Ollama[Ollama Server<br/>(Local Docker - CPU)]
    end

    API -- Invokes --> Core Services
    TP -- Uses --> ExtScripts
    TP -- Uses --> Ollama
    TP -- May Use --> SourceAPIs
    %% Core Services -- May Use --> LMSTools

    FSS <-. Stores/Reads .-> TP
    %% FSS <-. Optionally Reads .-> TR

```
**Key Architectural Notes (Tier 0):**
*   **Database:** Utilizes **PostgreSQL with the pgvector extension**, running locally via Docker.
*   **Embeddings:** Relies on a locally running **Ollama server** (via Docker) for generating embeddings using a quantized open-source model on the **CPU**.
*   **Processing:** All core services and processing scripts run locally via **Docker containers**. Text processing tools (GROBID, AnyStyle) run in CPU mode.
*   **Backend:** A simple Python backend (Flask/FastAPI) provides the internal API, running in Docker.
*   **Interfaces:** Focus on local CLI and MCP server integration.

## 5. Key Components (Tier 0 Focus)

### 5.1 Storage Layer

| Component         | Purpose                                                     | Tier 0 Tech                               | Considerations (Tier 0)                                                                 |
| :---------------- | :---------------------------------------------------------- | :---------------------------------------- | :-------------------------------------------------------------------------------------- |
| **Database**      | Store metadata, relationships, text chunks, and embeddings. | **PostgreSQL + pgvector** (Docker)        | Robust relational features, good vector search via pgvector. Requires Docker. Moderate RAM usage. Easiest migration path to Tier 1. Basic graph via CTEs/JSONB. |
| File Storage      | Store original source text files (optional mirror).         | Local Filesystem                          | Accessibility, backup, linking DB entries to file paths.                                |

*(Alternative Tier 0 DBs considered: ArangoDB Community (higher RAM, best Tier 2 migration), SQLite+VSS (lowest RAM, hardest migration). See Report Ref: Lines 121-152)*

### 5.2 Core Services (API Endpoints)

| Component            | Purpose                                       | Tier 0 Key Features & Tech                                                                                                                                                              |
| :------------------- | :-------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Text Processor**   | Ingests and processes raw texts.              | **PDF Extraction (GROBID CPU)**, **EPUB Parsing (PyMuPDF/ebooklib)**, **CPU-based Chunking (`semchunk`)**, Metadata/Citation Extraction (GROBID CPU/AnyStyle+NER), **OS Embedding Generation (Ollama CPU)**, Pluggable embedding models, Bulk processing (slow), Error handling. |
| **Search Module**    | Handles complex search queries.               | Hybrid queries (SQL combining vector search `pgvector`, metadata filters), Weighted search, Relevance tuning, Contextual filtering.                                                    |
| **Relationship Mgr** | Manages explicit & implicit relationships.    | Basic Graph storage/query via SQL (JSONB, adjacency lists, or recursive CTEs). Relationship type management. Validation.                                                              |
| **Inference Module** | Generates insights from graph data.           | Minimal for Tier 0. Basic pathfinding or rule application via SQL or Python logic.                                                                                                      |
| **Bibliography Mgr** | Manages collections and citations.            | List/Collection management, Citation generation (handling PDF pages vs. EPUB structure), Linking text elements to notes (manual focus), Quote management.                               |

### 5.3 Interface Layer

| Component     | Purpose                               | Tier 0 Target Users / Integration                               |
| :------------ | :------------------------------------ | :-------------------------------------------------------------- |
| CLI           | Local research & administration       | Individual researchers, power users                             |
| MCP Interface | AI agent integration                  | Local RooCode Agents (Gemini 2.5 Pro, etc.), other AI tools   |
| REST/GraphQL API | Internal service communication        | Decouples interfaces from core services (Flask/FastAPI Docker)|
| ~~Web UI~~    | General access, community features    | *(Future Phase)*                                                |
| ~~Text Reader~~ | Integrated reading & annotation       | *(Future Phase)*                                                |

## 6. Design Decisions & Considerations (Tier 0 Focus)

### 6.1 Hosting Model
*   **Tier 0:** Strictly **local deployment** via Docker Compose. All components (DB, Ollama, Backend, Processing Scripts) run on the user's machine.

### 6.2 Community Features
*   Deferred to future cloud-based phases.

### 6.3 Processing Pipeline (Tier 0 Tools)

```mermaid
flowchart LR
    Raw[Raw Files/Folders<br/>(PDF, EPUB, MD, TXT)] --> Parser{Format Parser}
    Parser -- PDF --> GROBID(GROBID CPU<br/>(Docker))
    Parser -- EPUB --> EPUBCnv(EPUB Parser<br/>PyMuPDF/ebooklib)
    Parser -- MD/TXT --> TxtRead(Direct Read)

    GROBID --> StructExtPDF(Structure/Note Extractor)
    EPUBCnv --> StructExtEPUB(Structure/Note Extractor)
    TxtRead --> StructExtTXT(Structure/Note Extractor)

    StructExtPDF --> Chunk(CPU Chunker<br/>semchunk)
    StructExtEPUB --> Chunk
    StructExtTXT --> Chunk

    Chunk -- Chunks --> Embed(Embedding Generator<br/>Ollama CPU - OS Model)
    Embed -- Embeddings --> Indexer(DB Indexer<br/>PostgreSQL+pgvector)

    StructExtPDF -- Metadata/Refs --> CitParse(Citation Parser<br/>GROBID CPU/AnyStyle+NER)
    StructExtEPUB -- Metadata/Refs --> CitParse
    StructExtTXT -- Metadata/Refs --> CitParse

    CitParse -- Parsed Refs --> RelExt(Relationship Extractor<br/>Basic SQL/Python)
    Indexer -- Stored Data --> RelExt

    RelExt --> FinalDB[(PostgreSQL+pgvector Storage)]
```
*   **Tools:** Prioritize **GROBID (CPU mode)** for PDF structure/metadata, **PyMuPDF/ebooklib** for EPUB, **`semchunk`** for CPU-based chunking, **AnyStyle** (Docker) for citations.
*   **Embeddings (Tier 0):** Use a **Quantized Open Source Model** (e.g., `all-MiniLM-L6-v2`, `nomic-embed-text`) via **Ollama running on CPU**. Ensure architecture allows plugging in other models later (e.g., API models for Tier 1/2). Configuration via `{{EMBEDDING_MODEL_NAME}}` and `{{OLLAMA_API_BASE}}`.
*   **EPUB/PDF:** Do not attempt automated page mapping. Prioritize one format per source. Use CFIs/structure for EPUB internal linking.
*   **Execution:** Processing steps implemented as Python scripts within **Docker containers**, invoked via the backend API.

### 6.4 Local File Management
*   Strategy remains: Optional local mirror organized logically, linked via metadata in the database.

### 6.5 Relationship System
*   **Tier 0 Implementation:** Basic relationships (e.g., `contains`, `cites`) stored in Postgres using standard relational tables, JSONB columns, or potentially recursive CTEs for simple traversals. Full graph database features deferred.

### 6.6 Inference Capabilities
*   **Tier 0 Implementation:** Minimal. Basic rule application or simple pathfinding implemented in Python service logic or SQL queries.

### 6.7 Essay Support Features
*   Tier 0 focuses on providing the core data via MCP for external AI agents to use for essay support (semantic search, citation retrieval).

### 6.8 Revenue Model Options
*   Deferred to future cloud-based phases.

### 6.9 Facilitating Post-Methodological Exploration
*   Tier 0 provides the basic building blocks (semantic search, text access). UI/UX features facilitating specific post-methodological actions are deferred to future phases.

### 6.10 Configuration Management
*   **No Hardcoding:** All environment-specific variables (database credentials, API endpoints, model names, file paths) MUST be managed via configuration files (e.g., `.env`, `config.yaml`) or environment variables, NOT hardcoded in source code. Use placeholders like `{{DB_USER}}`, `{{DB_PASSWORD}}`, `{{DB_HOST}}`, `{{DB_PORT}}`, `{{DB_NAME}}`, `{{OLLAMA_API_BASE}}`, `{{EMBEDDING_MODEL_NAME}}`.

## 7. Strategic Roadmap & Funding (Tier 0 Focus)

### 7.1 Strategic Approach: Local MVP First
*   **Phase 0 (Tier 0 MVP):** Focus on building the core **PostgreSQL+pgvector** schema, the containerized **CPU-based text processing pipeline** (basic PDF/EPUB extraction, semantic chunking, **Ollama CPU embedding**), and a functional **local MCP Server**. This server provides core semantic search, basic metadata filtering, and citation data retrieval to RooCode agents running locally. This delivers immediate value for AI-assisted research and writing on the user's machine.
*   **Subsequent Phases:** Migrate to Tier 1 (Cloud Serverless Postgres) by leveraging the compatible database structure. Then build out advanced relationships, inference, CLI, Web UI, etc., iteratively.

### 7.2 Technical Implementation for Expandability
*   Principles (API-First, Plugins, DB Migrations, Component Separation) remain crucial and should be implemented from Phase 0, even within the local Docker context.

### 7.3 Advanced Expandability Techniques
*   Deferred to later phases.

### 7.4 Development Timeline
*   Timeline remains indicative. Phase 0 focuses on the Tier 0 Local MCP Server MVP.

### 7.5 Funding Narrative
*   Narrative remains valid, emphasizing the gap, impact, and sustainability path starting with the local Tier 0 MVP and migrating towards cloud tiers.

### 7.6 Resource Requirements
*   Tier 0 requires developer time and local hardware. Cloud costs are deferred.

## 8. Implementation Phases (Tier 0 Focus)

### Phase 0: Tier 0 Local MVP (1-2 months)
*   **Database:** Setup **PostgreSQL+pgvector** via Docker. Implement core `documents`, `chunks` tables, basic `contains`/`cites` relationships (e.g., linking tables). Implement schema migrations (e.g., using Alembic). Configure via `{{DB_...}}` variables.
*   **Text Processing:** Containerized Python pipeline: **GROBID CPU** for PDF, **PyMuPDF/ebooklib** for EPUB, **`semchunk`** (CPU), **Ollama CPU embedding** via local server (`{{OLLAMA_API_BASE}}`, `{{EMBEDDING_MODEL_NAME}}`), Postgres batch insertion. Support TXT, MD, EPUB, basic PDF. Bulk folder input.
*   **MCP Server:** Implement local MCP server (Dockerized Flask/FastAPI) with tools: `semantic_search(query_text, top_k, filters)`, `get_chunk_details(chunk_id)`, `get_document_metadata(doc_id)`. Secure credential handling via config.
*   **Operation:** Local deployment via Docker Compose (Postgres+pgvector, Ollama, Backend/MCP Server, Processing Containers). Provide clear setup instructions.
*   **Expandability:** API-first internal structure, pluggable embedding function, basic feature flags. **Crucially, ensure schema and logic facilitate easy migration to Tier 1 Cloud Postgres.**
*   **Documentation:** Basic README covering setup, usage, and configuration.

### Phase 1: Migration to Tier 1 & Enhanced Features (3-6 months)
*   **Migration:** Migrate database to Cloud Serverless Postgres (Supabase/NeonDB). Deploy backend/MCP server to Serverless Functions (Lambda/GCF). Update configuration.
*   **Embeddings:** Switch bulk/query embedding to cost-effective API (OpenAI Small/Voyage Lite).
*   **Relationship System:** Enhance relationship modeling in Postgres (potentially using JSONB or exploring AGE extension if available on cloud provider). Implement plugin architecture.
*   **Search Module:** Enhance search capabilities leveraging cloud database features.
*   **Text Processing:** Improve citation/footnote extraction (potentially adding AnyStyle+NER).
*   **CLI:** Develop CLI interface accessing cloud API.

### Phase 2: Web Interface & Basic Community (7-12 months)
*   *(Remains largely the same as v2.0, targeting cloud deployment)*

### Phase 3: Advanced Features & Scale (13+ months)
*   *(Remains largely the same as v2.0, targeting cloud deployment)*

## 9. Brainstorming: Future Features & Directions
*(Remains the same as v2.0)*

## 10. Technical Considerations (Tier 0 Focus)

### 10.1 Embedding Model Selection
*   **Tier 0:** **Quantized OS Model via Ollama CPU**. Pluggable architecture is essential.
*   **Tier 1+:** Switch to API models (OpenAI, Voyage) or potentially self-hosted models on cloud GPUs.

### 10.2 Scalability Concerns
*   **Tier 0:** Limited by local hardware (CPU, RAM). Not scalable without hardware upgrades.
*   **Tier 1+:** Scalability depends on chosen cloud services (database tier, serverless limits).

### 10.3 Integration Possibilities
*   Deferred to later phases.

### 10.4 Privacy and Ethics
*   **Tier 0:** Primarily concerns local data security. Ensure container configurations are secure.
*   **Tier 1+:** Cloud privacy policies, data residency, user consent become critical.

## 11. Key Questions for Dialogue
*(Remains the same as v2.0)*
1.  Scale Expectations?
2.  Specific Research Workflow Pain Points?
3.  Most Valuable Community Features?
4.  Specialized AI Agent Capabilities Needed?
5.  Monetization Philosophy/Comfort?