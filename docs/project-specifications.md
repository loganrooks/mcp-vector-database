# PhiloGraph: Philosophical Knowledge Platform - Specification v2.3 (Hybrid LiteLLM + LangChain Strategy)

## Vision Document

### Executive Summary

PhiloGraph is envisioned as a specialized knowledge platform designed to revolutionize philosophical research and engagement. It integrates advanced semantic search capabilities (powered by vector embeddings) with sophisticated relationship modeling, allowing users to navigate the complex web of philosophical ideas, texts, and authors. Operating initially within the RooCode framework via a dedicated MCP server, and designed for future expansion into CLI and web interfaces, PhiloGraph aims to provide immediate utility for tasks like essay writing and research while building towards a comprehensive, extensible system. This platform uniquely seeks to support not only traditional analytical methods but also to facilitate exploratory approaches inspired by diverse philosophical traditions, including post-methodological thought.

Based on comparative analysis (`docs/reports/litellm_vs_langchain_philograph.md`), PhiloGraph adopts a **hybrid architectural strategy** leveraging both **LiteLLM** and **LangChain**. **LiteLLM** will serve as the dedicated, unified API gateway across all tiers, managing external LLM/embedding calls for operational robustness, cost control, and provider flexibility. **LangChain** will be introduced selectively (Tier 1+) for application-level orchestration (LCEL), advanced LLM features (Q&A, summarization), graph database interaction, and agentic workflows (LangGraph), making its external API calls *through* the LiteLLM proxy.

This document outlines the refined vision, architecture, technical specifications, and strategic roadmap incorporating this hybrid strategy, starting with the **Tier 0 Minimum Viable Product (MVP)** which utilizes the **LiteLLM proxy** to access **free cloud-based embedding APIs**.

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

*(Tier 0 primarily addresses core Individual Researcher and AI Integration stories. Community Features are deferred.)*

**Tier 0 Focus - Addressed User Stories:**
*   **Individual Researcher:**
    *   Searching across readings for specific concepts (Core Search).
    *   Finding supporting/contradicting evidence via search (Core Search).
    *   Discovering connections via semantic similarity (Core Search).
    *   Filtering search results by metadata (e.g., author, year - depends on extraction quality).
    *   Checking interpretation against specific passages (via search results).
    *   Managing basic collections of documents/chunks (Bibliography Mgr - basic).
*   **AI Integration:**
    *   AI querying PhiloGraph for relevant passages/metadata (MCP Interface).
    *   AI using relationship data (basic citation links) for analysis (MCP Interface).
    *   AI leveraging PhiloGraph data for essay drafting support (MCP Interface).

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

## 3. Deployment Tiers & Tier 0 MVP Definition (Revised: Cloud Embeddings)

Based on the synthesis report (`docs/reports/philograph_synthesis_and_recommendations.md`), the embedding middleware analysis (`docs/reports/embedding_middleware_for_philograph.md`), and the comparative framework analysis (`docs/reports/litellm_vs_langchain_philograph.md`), PhiloGraph adopts a **hybrid LiteLLM + LangChain strategy** across its deployment tiers. The initial development focuses on a **Tier 0 MVP** designed for local deployment, establishing the **LiteLLM proxy** as the core API gateway to access **free cloud-based embedding APIs**. LangChain is planned for introduction in later tiers.

### Tier 0: Minimal Cost / Local Deployment + Cloud Embeddings MVP (~$0 Software/API Cost + Hardware/Time Cost)

*   **Goal:** Provide core functionality (ingestion, *high-quality* semantic search, basic graph, note linking, CLI/MCP interfaces) deployable on typical developer hardware, utilizing free cloud embedding APIs accessed via local middleware to overcome local CPU embedding performance bottlenecks. Establish a foundation for future cloud migration.
*   **Target Environment:** Local Laptop (e.g., Intel i7-1260P, 16GB RAM, Integrated Graphics via WSL2) running Docker.
*   **Components:**
    *   **Database:** **PostgreSQL + pgvector** (Free, Self-hosted via Docker). Chosen for balance of local capability and easiest migration path to Tier 1 (Cloud Serverless Postgres).
    *   **Text Processing:** CPU-based tools: **GROBID** (CPU mode), **PyMuPDF**, **`semchunk`** (CPU), **AnyStyle** (Self-hosted, Docker).
    *   **Embeddings:** **Cloud API (Google Vertex AI Free Tier/Credits)** - e.g., `text-embedding-004` or `text-embedding-large-exp-03-07` (using MRL truncation). Accessed via **Middleware Proxy**. (Ref: Middleware Report Sec 4.3, 5.6).
    *   **Middleware Proxy (API Gateway):** **LiteLLM Proxy** (Free, Self-hosted via Docker). Serves as the **unified gateway** for all external LLM/embedding API calls. Manages routing, API keys (via Virtual Keys), cost tracking, rate limits, retries, and fallbacks. (Ref: Middleware Report Sec 2.6, 5.6; Framework Report Sec 8.1).
    *   **Backend/API:** Simple Python **Flask/FastAPI** (Self-hosted, Docker). Interacts with DB and makes embedding requests *through* the LiteLLM Proxy. (No LangChain in Tier 0).
    *   **Interface:** **CLI**, **MCP Server** (local).
*   **Estimated Cost:** **~$0 direct software/API cost** (assuming usage stays within Vertex AI free tier/credits). Minimal electricity cost. Significant unquantified cost in setup time (including GCP setup), maintenance, and potentially slower *text processing* time (still CPU-bound).
*   **Expected Performance:**
    *   **Bottleneck:** Local CPU performance for *text processing* (GROBID, chunking) and 16GB RAM limiting concurrent services (DB, Proxy, Backend, Processing). Embedding generation speed is now dependent on cloud API latency and rate limits, but significantly faster than local CPU for bulk tasks.
    *   **Ingestion:** Faster overall due to cloud embeddings, but potentially limited by API rate limits (mitigated by middleware strategies like batching/retries) and local text processing speed.
    *   **Query Latency:** Good for semantic search (cloud embeddings). Basic graph queries depend on local Postgres performance.
*   **Achievable Features (MVP Core):**
    *   Basic document ingestion (TXT, MD, simple PDF/EPUB via GROBID CPU).
    *   **High-quality semantic search** via cloud embeddings (Vertex AI).
    *   Basic graph relationship storage/querying (Postgres - potentially JSONB or simple tables).
    *   Personal note linking (manual, via external DB strategy - see Section 6).
    *   CLI and MCP interfaces.
*   **Explicit Sacrifices:**
    *   Local Text Processing Performance/Concurrency, Advanced Text Processing (no robust footnote linking, no GPU acceleration), Scalability (requires hardware upgrade for local components), Reliability (manual backups for local DB), Maintenance Burden (local Docker + GCP setup). **Dependency on Cloud API availability/limits.** **Requires GCP setup/billing enabled for usable Vertex AI quotas.** Potential middleware complexity.
*   **Migration Path:** This Tier 0 stack, particularly **PostgreSQL+pgvector** and the established **LiteLLM proxy pattern**, facilitates migration to Tier 1 (Cloud Serverless Postgres, Serverless Functions). The LiteLLM proxy will be deployed serverlessly, and backend logic shifted to functions. LangChain may be introduced in Tier 1 for orchestration, calling the deployed LiteLLM proxy.

### Tier 1: Cost-Optimized Cloud (~$50/month)

*   **Goal:** Improve performance, reliability, and scalability over Tier 0 using cost-effective cloud services.
*   **Components:** Serverless Postgres+pgvector (Supabase/NeonDB), Serverless Functions (Lambda/GCF for Backend Logic), **Serverlessly Deployed LiteLLM Proxy** (e.g., Cloud Run/ACA), Embedding/LLM APIs (Vertex AI, OpenAI, Anthropic via LiteLLM), Object Storage (S3/GCS). **Optional:** Introduction of **LangChain (LCEL)** within Serverless Functions for pipeline orchestration, calling the LiteLLM proxy.
*   **Migration from Tier 0:** Migrate Postgres data. Deploy backend logic to serverless functions. Deploy LiteLLM proxy to a serverless container environment (e.g., Cloud Run/ACA) with persistent state (DB for virtual keys/costs). Update configurations. Optionally refactor pipeline logic within functions using LangChain (LCEL), ensuring it calls the deployed LiteLLM proxy.

### Tier 2: Balanced Cloud Performance (~$150/month)

*   **Goal:** Further enhance performance and enable more complex features using managed databases and potentially higher-quality embedding APIs.
*   **Components:** Managed ArangoDB (Oasis) or higher-tier Serverless Postgres, Serverless Functions, **Scaled LiteLLM Proxy Infrastructure**, Diverse Embedding/LLM APIs (via LiteLLM), Object Storage. **LangChain** used more extensively for backend logic, Q&A chains, and ArangoDB integration (via `langchain-arangodb`), calling the LiteLLM proxy.
*   **Migration from Tier 1/0:** If moving to ArangoDB, involves schema mapping (Relational -> Graph) and query translation (SQL -> AQL). Backend logic refactored to use LangChain's ArangoDB components (e.g., `ArangoGraph`, `ArangoGraphQAChain`) or custom AQL orchestration via LangChain, still calling LiteLLM proxy for external LLMs. Requires scaling LiteLLM proxy deployment.

## 4. System Architecture (Tier 0 - Cloud Embeddings Focus)

The architecture uses local Docker services but offloads embedding generation to a cloud API via a local middleware proxy.

```mermaid
flowchart TD
    subgraph "Storage Layer (Tier 0 - Local Docker)"
        style Storage Layer fill:#fdf,stroke:#333,stroke-width:2px
        DB[(**PostgreSQL + pgvector**<br/>Relational + Vector via Docker)]
        FSS[File Storage System<br/>(Local Filesystem)]
    end

    subgraph "Core Services (Tier 0 - Local Docker)"
        style Core Services fill:#def,stroke:#333,stroke-width:2px
        TP[Text Processor<br/>(GROBID CPU, PyMuPDF, semchunk)]
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
         Middleware[API Gateway<br/>(LiteLLM Docker)]
         CloudEmbedAPI{{Cloud Embedding API<br/>(Vertex AI Free Tier)}}
         ZLibMCP[Z-Library MCP Server<br/>(Local Node.js/Python)]
    end

    API -- Invokes --> Core Services
    TP -- Uses --> ExtScripts
    TP -- Requests Embeddings --> Middleware
    Middleware -- Calls --> CloudEmbedAPI
    TP -- May Use --> SourceAPIs
    Core Services -- Calls --> ZLibMCP
    ZLibMCP -- Provides Processed Text --> TP
    %% Core Services -- May Use --> LMSTools

    FSS <-. Stores/Reads .-> TP
    %% FSS <-. Optionally Reads .-> TR

```
**Key Architectural Notes (Tier 0 - Hybrid Strategy Foundation):**
*   **Database:** Utilizes **PostgreSQL with the pgvector extension**, running locally via Docker.
*   **API Gateway (Middleware):** Employs the **LiteLLM Proxy** (Docker) as the **single, unified gateway** for *all* external LLM/embedding API calls (currently Vertex AI for embeddings). This provides centralized management, cost control, and provider flexibility from the outset.
*   **Embeddings:** Embedding generation relies on calls made *through* the LiteLLM Proxy to the configured cloud provider (Vertex AI Free Tier).
*   **Processing:** Core services (Text Processor, Search Module) and processing scripts run locally via **Docker containers** (CPU-bound). They interact with the LiteLLM Proxy for any required embeddings.
*   **Text Acquisition:** Missing texts identified via citation analysis can be acquired using the external **Z-Library MCP Server (`zlibrary-mcp`)**. This server handles searching, downloading, and initial RAG processing (EPUB/PDF/TXT -> Text), providing a path to the processed text file for ingestion by the PhiloGraph Text Processor.
*   **Backend:** A simple Python backend (Flask/FastAPI) provides the internal API, running in Docker. It coordinates calls to the DB and invokes Core Services (which in turn call the LiteLLM Proxy and potentially the `zlibrary-mcp` server). **No LangChain components are used in Tier 0.**
*   **Interfaces:** Focus on local CLI and MCP server integration, interacting with the Backend API.
*   **Future Evolution:** This architecture establishes the LiteLLM gateway pattern early. LangChain will be introduced in later tiers (Tier 1+) within the Backend/Core Services layer for orchestration and advanced features, making its external API calls *through* the established LiteLLM Proxy.

## 5. Key Components (Tier 0 - Cloud Embeddings Focus)

### 5.1 Storage Layer

| Component         | Purpose                                                     | Tier 0 Tech                               | Considerations (Tier 0)                                                                 |
| :---------------- | :---------------------------------------------------------- | :---------------------------------------- | :-------------------------------------------------------------------------------------- |
| **Database**      | Store metadata, relationships, text chunks, and embeddings. | **PostgreSQL + pgvector** (Docker)        | **Schema:** Includes tables like `documents` (id, title, author, year, source_path, metadata_jsonb), `sections` (id, doc_id, title, level, sequence), `chunks` (id, section_id, text_content, sequence, embedding vector(`{{TARGET_EMBEDDING_DIMENSION}}`)), `references` (id, source_chunk_id, cited_doc_details_jsonb), `relationships` (id, source_node_id, target_node_id, relation_type, metadata_jsonb), `collections` (id, name), `collection_items` (collection_id, item_type, item_id). **Indexing:** Primary keys, foreign keys, GIN index on `documents.metadata_jsonb`, HNSW index on `chunks.embedding`. **Considerations:** Robust relational features, good vector search via pgvector. Requires Docker. Moderate RAM usage. Easiest migration path to Tier 1. Basic graph via `relationships` table + recursive CTEs. |
| File Storage      | Store original source text files (optional mirror).         | Local Filesystem                          | **Structure:** Mirror source directory structure within a configured base path (`{{SOURCE_FILE_DIR}}`). **Linking:** `documents.source_path` stores relative path from base. **Considerations:** Accessibility, backup strategy (manual for Tier 0), potential storage growth. |

### 5.2 Core Services (API Endpoints)

| Component            | Purpose                                       | Tier 0 Key Features & Tech                                                                                                                                                              |
| :------------------- | :-------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Text Processor**   | Ingests and processes raw texts into structured, indexed data. | **Input Handling:** Accepts file paths or directories. Identifies file types (PDF, EPUB, MD, TXT). **Extraction:** Uses GROBID (CPU Docker) for PDF structure, metadata, and citation extraction; PyMuPDF/ebooklib for EPUB content/structure. **Chunking:** Employs `semchunk` (CPU) with configurable strategies (e.g., sentence-based, fixed-size with overlap) targeting optimal size for embedding model (`{{TARGET_CHUNK_SIZE}}`). **Metadata/Ref Parsing:** Leverages GROBID/AnyStyle+NER for citation parsing; stores structured metadata (author, title, publication year, etc.) and potential relationship links. **Embedding Request:** Batches text chunks (`{{EMBEDDING_BATCH_SIZE}}`) and sends **HTTP requests to the LiteLLM Proxy endpoint** (`{{LITELLM_PROXY_URL}}`) using the configured internal model name (`{{EMBEDDING_MODEL_NAME}}`). Relies on the LiteLLM proxy for actual API call execution, retries, and error handling related to the external API. **Indexing:** Stores extracted text, structured metadata, parsed references, and received embeddings (from LiteLLM proxy response) in PostgreSQL+pgvector tables, linking chunks to source documents and structural elements (chapters, sections). **Coordination:** Manages bulk processing queues, tracks progress, logs errors. *(Tier 1+ may optionally refactor this pipeline using LangChain LCEL, still calling the LiteLLM proxy).* |
| **Search Module**    | Executes user queries against the indexed data. | **Query Parsing:** Accepts natural language or structured queries (CLI/MCP). **Query Embedding:** Sends the query text **via HTTP request to the LiteLLM Proxy** (`{{LITELLM_PROXY_URL}}`) to generate an embedding using the same internal model name (`{{EMBEDDING_MODEL_NAME}}`) as ingestion. **Vector Search:** Performs ANN search using `pgvector`'s HNSW or IVFFlat index (`vector_l2_ops` or `vector_cosine_ops`) to find top-k (`{{SEARCH_TOP_K}}`) similar text chunks based on the query embedding received from the LiteLLM proxy. **Metadata Filtering:** Applies pre-search or post-search filtering based on SQL `WHERE` clauses (author, year, source document ID, course tag, etc.). **Hybrid Ranking:** Optionally combines vector similarity scores with keyword matching (e.g., using `tsvector`) or other relevance signals (e.g., citation count - future). **Result Formatting:** Retrieves full text chunks, associated metadata, and source document information for presentation via API/CLI/MCP. Handles pagination. *(Tier 2+ may leverage LangChain retrieval chains, configured to use pgvector/ArangoDB and call the LiteLLM proxy for query embeddings).* |
| **Relationship Mgr** | Manages explicit & implicit relationships.    | **Storage:** Utilizes relational tables (e.g., `relationships` table with `source_node_id`, `target_node_id`, `relation_type`, `metadata_jsonb`) or potentially JSONB fields within document/chunk tables for basic graph structures. **Querying:** Implements SQL queries using JOINs, recursive CTEs (for pathfinding), or JSONB operators to retrieve connected nodes or relationship details. **Types:** Manages a predefined list of relationship types (e.g., `cites`, `responds_to`, `influences`, `discusses_concept`). **Validation:** Basic checks for node existence before creating relationships. (Tier 0 focuses on storing parsed citations; implicit relationship discovery is future work). |
| **Inference Module** | Generates insights from graph data.           | **Tier 0 Scope:** Very limited. May include simple SQL queries to identify frequently cited works or authors within a specific context (e.g., a course reading list). No complex graph algorithms or ML-based inference planned for Tier 0. *(Tier 3+ will leverage LangChain chains/agents, calling the LiteLLM proxy for LLM reasoning, to perform tasks like automated relationship inference or summarization based on graph context).* |
| **Bibliography Mgr** | Manages user collections, notes, and citations. | **Collections:** Allows users (via CLI/MCP) to create named collections of document IDs or chunk IDs. **Notes:** (Tier 0 Strategy TBD - likely external linking) Placeholder for linking external notes (e.g., Obsidian URIs) to specific document/chunk IDs stored in a dedicated table. **Citation Generation:** Retrieves metadata associated with a chunk/document and formats it into a standard citation style (e.g., Chicago, MLA - basic implementation). Handles page number retrieval where available (PDFs). **Quote Management:** Stores user-selected text snippets (quotes) linked to their source chunk ID. *(Tier 2+ may use LangChain for more advanced citation formatting or integration with external reference managers, with any necessary LLM calls routed via LiteLLM proxy).* |
| **API Gateway** <br/> *(Middleware Proxy)* | **Unified Gateway** for all external LLM/Embedding API calls. Abstracts providers, manages keys, costs, limits, retries, fallbacks. | **LiteLLM Proxy (Docker):** Configured via `config.yaml` (`{{LITELLM_CONFIG_PATH}}`) and environment variables. **Key Features:** Maps internal model names (e.g., `{{EMBEDDING_MODEL_NAME}}`, future LLM names) to specific provider models (e.g., `vertex_ai/text-embedding-004`, `openai/gpt-4o`) potentially with specific parameters (e.g., `output_dimensionality`). Manages provider API keys securely. Provides **Virtual Keys** for internal services/users. Implements **cost tracking/budgeting**, **rate limiting (TPM/RPM)**, configurable **retries**, and **fallbacks**. Provides an OpenAI-compatible endpoint (`{{LITELLM_PROXY_URL}}`) for all internal PhiloGraph components (including any future LangChain components) to call. *(Tier 1+ involves deploying this proxy serverlessly and potentially configuring a persistent DB for state).* |
| **Text Acquisition Service** | Acquires missing texts identified via citation analysis and prepares them for ingestion. | **Z-Library MCP Server (`zlibrary-mcp`):** External, locally running MCP server (Node.js/TypeScript with Python bridge). **Key Features:** Provides tools (`search_books`, `download_book_to_file`, `process_document_for_rag`) callable by PhiloGraph's backend/core services. Searches Z-Library for books based on metadata (e.g., from unresolved citations). Downloads specified books (PDF, EPUB, TXT) to a local directory (`./downloads/` by default). Processes downloaded files into plain text suitable for RAG/ingestion, saving output to a separate directory (`./processed_rag_output/` by default) and returning the path to the processed file. **Integration:** PhiloGraph backend identifies needed texts (e.g., documents referenced frequently but lacking text content), calls `zlibrary-mcp` tools via `use_mcp_tool`, receives the path to the processed text file, and triggers the PhiloGraph Text Processor to ingest it. **Note:** Requires separate setup, configuration (credentials), and running process. May require modification for better integration (e.g., configurable output paths). |

### 5.3 Interface Layer

| Component     | Purpose                               | Tier 0 Target Users / Integration                               |
| :------------ | :------------------------------------ | :-------------------------------------------------------------- |
| CLI           | Local research & administration       | **Tier 0:** Python CLI (e.g., Typer/Click) interacting with the backend API. Commands for: `ingest <path>`, `search <query> [--filter author="..."] [--limit N]`, `show document <id>`, `list collections`, `add-to-collection <name> <item_id>`, `acquire-missing-texts [--threshold N]`. Output formatted for terminal readability. |
| MCP Interface | AI agent integration                  | **Tier 0:** Local MCP Server (part of Backend container or separate). Exposes tools like `philograph_ingest(path: string)`, `philograph_search(query: string, filters: dict = None)`, `philograph_acquire_missing(threshold: int = 5)`. Tools interact with the backend API (which may call `zlibrary-mcp`). Allows RooCode agents to leverage PhiloGraph data and trigger acquisition. |
| REST/GraphQL API | Internal service communication        | **Tier 0:** Simple REST API via Flask/FastAPI (Docker). Endpoints like `/ingest`, `/search`, `/documents`, `/chunks`, `/collections`, `/acquire`. Primarily for CLI/MCP interaction. Not publicly exposed. Authentication minimal/absent for local Tier 0. |
| ~~Web UI~~    | General access, community features    | *(Future Phase)*                                                |
| ~~Text Reader~~ | Integrated reading & annotation       | *(Future Phase)*                                                |

## 6. Design Decisions & Considerations (Tier 0 - Cloud Embeddings Focus)

### 6.1 Hosting Model
*   **Tier 0:** Hybrid local deployment. Core logic, DB, text processing, and middleware proxy run locally via Docker Compose. **Embedding generation relies on external Cloud API (Vertex AI).** Requires internet connectivity for embedding.

### 6.2 Community Features
*   **Explicitly Deferred from Tier 0:** Features requiring user accounts, shared spaces, or public access (e.g., sharing collections, collaborative annotation, public browsing).
    *   *Why Deferred:* Tier 0 focuses on single-user, local core functionality. Community features necessitate robust user authentication, authorization, data isolation, and scalable cloud infrastructure not planned until later phases.
    *   *Target Phase:* Tier 2 (Web Interface & Basic Community) and later.

### 6.3 Processing Pipeline (Tier 0 - Cloud Embeddings)

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

    Chunk -- Chunks --> EmbedReq(Request Embedding<br/>via Middleware)
    EmbedReq --> Middleware(Middleware Proxy<br/>LiteLLM Docker)
    Middleware -- API Call --> CloudAPI{{Cloud API<br/>Vertex AI Free Tier}}
    CloudAPI -- Embedding --> Middleware
    Middleware -- Embedding --> EmbedResp(Receive Embedding)

    EmbedResp -- Embeddings --> Indexer(DB Indexer<br/>PostgreSQL+pgvector)

    StructExtPDF -- Metadata/Refs --> CitParse(Citation Parser<br/>GROBID CPU/AnyStyle+NER)
    StructExtEPUB -- Metadata/Refs --> CitParse
    StructExtTXT -- Metadata/Refs --> CitParse

    CitParse -- Parsed Refs --> RelExt(Relationship Extractor<br/>Basic SQL/Python)
    Indexer -- Stored Data --> RelExt

    RelExt --> FinalDB[(PostgreSQL+pgvector Storage)]
```
*   **Tools:** Prioritize **GROBID (CPU mode)** via Docker for robust PDF parsing, metadata, and reference extraction. Use **PyMuPDF/ebooklib** for EPUB parsing. Employ **`semchunk`** for semantic chunking (CPU-based). Use **AnyStyle** (Docker) potentially augmented with custom NER rules for citation parsing if GROBID's output needs refinement.
*   **Embeddings (Tier 0):** Utilize **Google Vertex AI Free Tier/Credits** via the **LiteLLM Proxy**. Target model: `text-embedding-004` or `text-embedding-large-exp-03-07` (experimental, monitor status). Use **MRL (Matryoshka Representation Learning)** truncation via LiteLLM's `output_dimensionality` parameter to standardize on a dimension suitable for `pgvector` (e.g., `{{TARGET_EMBEDDING_DIMENSION}} = 1024`). Configuration requires setting up LiteLLM's `config.yaml` (`{{LITELLM_CONFIG_PATH}}`) to map an internal model name (e.g., `philo-embed`) to the Vertex AI model and dimension. The proxy needs GCP credentials (`{{GOOGLE_APPLICATION_CREDENTIALS}}`) and project details (`{{VERTEX_AI_PROJECT_ID}}`, `{{VERTEX_AI_LOCATION}}`) passed via environment variables.
*   **Execution Flow:**
    1.  **Input:** Receive file path(s) via CLI or MCP command.
    2.  **Format Detection:** Identify file type (PDF, EPUB, MD, TXT).
    3.  **Extraction (PDF):** Call GROBID container's API (`processHeaderDocument`, `processFulltextDocument`) to get TEI XML output. Parse XML for metadata, section structure, body text, and bibliography entries.
    4.  **Extraction (EPUB):** Use PyMuPDF/ebooklib to extract chapters/sections and text content. Attempt metadata extraction from OPF file.
    5.  **Extraction (MD/TXT):** Read directly. Use frontmatter for metadata if present.
    6.  **Chunking:** Pass extracted text (per section/chapter) to `semchunk` with appropriate parameters (`{{TARGET_CHUNK_SIZE}}`, overlap settings).
    7.  **Embedding:** Batch chunks (`{{EMBEDDING_BATCH_SIZE}}`). Send batches to LiteLLM Proxy endpoint (`{{LITELLM_PROXY_URL}}`) specifying the internal model name (`{{EMBEDDING_MODEL_NAME}}`). Handle responses, including potential errors/retries managed by the proxy or the calling script.
    8.  **Citation Parsing:** Process bibliography entries extracted by GROBID or parsed by AnyStyle/NER to identify structured references (author, title, year, etc.).
    9.  **Indexing:** Store document metadata, section/chunk text, embeddings, and parsed references in PostgreSQL tables. Establish foreign key relationships between documents, sections, chunks, and potentially references. Create `pgvector` HNSW index on the embedding column (`USING hnsw (embedding_column vector_l2_ops)` or `vector_cosine_ops`).
*   **Error Handling:** Implement robust error logging at each stage. For embedding failures after retries, flag chunks for later reprocessing.

### 6.4 Local File Management
*   **Strategy:** An optional local mirror of the original source files can be maintained. This is primarily for user reference or potential future features needing direct file access (e.g., an integrated text reader).
*   **Implementation (Tier 0):**
    *   A base directory path will be configured via an environment variable (`{{SOURCE_FILE_DIR}}`).
    *   When a document is ingested, its original relative path within `{{SOURCE_FILE_DIR}}` will be stored in the `documents.source_path` column in the PostgreSQL database.
    *   The system itself (API, search) primarily interacts with the structured data (metadata, chunks, embeddings) in the database, not the mirrored files directly.
    *   **No automatic synchronization:** If source files are updated, they must be manually re-ingested.
    *   **Backup:** Responsibility for backing up the mirrored source files lies entirely with the user in Tier 0.

### 6.5 Relationship System
*   **Tier 0 Implementation:** Focuses on storing explicit relationships derived primarily from parsed citations.
    *   **Storage:** A dedicated `relationships` table will store links (e.g., `id`, `source_node_id`, `target_node_id`, `relation_type`, `metadata_jsonb`). `source_node_id` and `target_node_id` could refer to document IDs or potentially chunk IDs. `relation_type` will initially focus on `'cites'`. `metadata_jsonb` can store context like the specific text snippet containing the citation.
    *   **Creation:** Relationships are created during the ingestion pipeline based on output from the Citation Parser (GROBID/AnyStyle).
    *   **Querying:** Basic graph traversal (e.g., finding all documents cited by a specific document, or all documents citing a given one) will be implemented using SQL JOINs on the `relationships` table. More complex pathfinding (e.g., multi-step influence chains) can be explored using PostgreSQL's recursive Common Table Expressions (CTEs), but performance on large datasets locally needs evaluation.
    *   **Limitations:** Implicit relationship discovery (based on semantic similarity) and management of relationship types beyond basic citations are deferred to future phases.

### 6.6 Inference Capabilities
*   **Tier 0 Implementation:** Explicitly minimal to focus on core functionality.
    *   **No Complex Algorithms:** Tier 0 will *not* implement complex graph algorithms (e.g., community detection, centrality analysis) or machine learning models for inference (e.g., automated topic modeling, relationship prediction beyond basic citation linking).
    *   **Potential Simple Queries:** The *only* inference might involve basic SQL aggregation queries run directly against the database (e.g., counting citations to identify highly referenced works within a specific collection or search result set). These will be implemented on an ad-hoc basis if needed by the CLI or MCP tools, not as a dedicated "Inference Module".

### 6.7 Essay Support Features
*   **Tier 0 Focus:** Provide foundational data retrieval capabilities to *external* agents or users for essay writing, rather than performing writing tasks itself.
    *   **MCP Integration:** The primary support mechanism is the MCP server. Tools like `philograph_search` will allow AI agents (e.g., RooCode's essay writing mode) to query PhiloGraph for relevant text chunks based on a topic or thesis.
    *   **Data Provided:** Search results will include the text content of relevant chunks, along with associated metadata: source document title, author, publication year, and potentially page numbers or section identifiers if successfully extracted during ingestion.
    *   **Citation Support:** The retrieved metadata facilitates accurate citation by the external agent/user. The Bibliography Manager component (Section 5.2) may offer a basic API endpoint (`/cite?chunk_id=...`) to format this metadata into a standard style (e.g., Chicago), callable by the MCP agent.
    *   **Limitations:** Tier 0 does *not* include features like automated argument generation, draft composition, reference management integration (beyond providing data), or plagiarism checking.

### 6.8 Revenue Model Options
*   **Explicitly Deferred from Tier 0/1:** Defining specific monetization strategies (e.g., subscriptions for advanced features/support, tiered access, organizational licenses).
    *   *Why Deferred:* The primary focus of initial phases (Tier 0, Tier 1) is on building core utility, establishing technical feasibility, and potentially gathering user feedback. Exploring revenue models is premature before demonstrating value and understanding potential user segments/markets.
    *   *Target Phase:* Tier 3+ or contingent on significant user adoption and strategic decisions.

### 6.9 Facilitating Post-Methodological Exploration
*   **Explicitly Deferred from Tier 0:** Development of specific UI affordances or analytical tools explicitly designed to support post-methodological approaches (e.g., visualizing rhizomatic connections differently, tools for deconstructive reading).
    *   *Why Deferred:* Tier 0 focuses on foundational data structures (text, embeddings, basic relationships) and core search/retrieval. Designing effective tools for specific, advanced philosophical methodologies requires a stable core platform and dedicated design/research effort. The core features (semantic search, graph exploration) may implicitly support such exploration, but dedicated features are out of scope for the MVP.
    *   *Target Phase:* Tier 2 or Tier 3, potentially informed by user feedback and further research into specific methodological needs.

### 6.10 Configuration Management
*   **No Hardcoding:** All sensitive information (API keys, DB credentials) and environment-specific settings (ports, paths, model names) MUST NOT be hardcoded in source code.
*   **Strategy:** Utilize a combination of:
    *   **Environment Variables:** For secrets (DB password, GCP credentials path) and top-level configuration (e.g., `ENV=development/production`). Docker Compose will inject these into containers.
    *   **`.env` File:** Store non-sensitive, environment-specific variables (e.g., `{{DB_HOST}}`, `{{DB_PORT}}`, `{{DB_USER}}`, `{{DB_NAME}}`, `{{LITELLM_PORT}}`, `{{LITELLM_HOST}}`, `{{VERTEX_AI_PROJECT_ID}}`, `{{VERTEX_AI_LOCATION}}`, `{{EMBEDDING_MODEL_NAME}}`, `{{TARGET_EMBEDDING_DIMENSION}}`, `{{SOURCE_FILE_DIR}}`, `{{TARGET_CHUNK_SIZE}}`, `{{EMBEDDING_BATCH_SIZE}}`, `{{EMBEDDING_RETRY_COUNT}}`). This file should be sourced by local development environments and potentially used to populate environment variables for Docker Compose. **Crucially, `.env` MUST be added to `.gitignore`**.
    *   **Configuration Files (Optional):** For more complex, non-sensitive configurations (e.g., LiteLLM's `config.yaml` at `{{LITELLM_CONFIG_PATH}}`, logging settings), referenced via environment variables.
*   **Loading:** Python applications (Backend, Processing Scripts) should use libraries like `python-dotenv` to load `.env` variables and `os.getenv` to access all environment variables, providing sensible defaults where possible.

## 7. Strategic Roadmap & Funding (Tier 0 - Cloud Embeddings Focus)

### 7.1 Strategic Approach: Hybrid LiteLLM Gateway + Selective LangChain Orchestration
*   **Core Principle:** Employ a **hybrid strategy** across all tiers, leveraging LiteLLM's strengths for API management and LangChain's strengths for application development, as recommended in `docs/reports/litellm_vs_langchain_philograph.md`.
*   **LiteLLM Role (All Tiers):** The **LiteLLM proxy** serves as the **persistent, unified API gateway** for all external LLM and embedding service calls. This ensures consistent management of API keys, costs, rate limits, retries, and fallbacks, while maximizing provider flexibility.
*   **LangChain Role (Tier 1+):** **LangChain** is introduced **selectively and progressively**:
    *   *Tier 1 (Optional):* May be used via **LCEL** within serverless functions to orchestrate the data processing pipeline (calling the LiteLLM proxy for embeddings).
    *   *Tier 2:* Used more broadly for backend logic, integrating with databases (Postgres/ArangoDB via `langchain-community` integrations), and implementing initial LLM features like structured Q&A chains (calling the LiteLLM proxy).
    *   *Tier 3+ & Speculative:* Heavily utilized for advanced LLM tasks (summarization, inference), complex graph interactions, and building sophisticated, stateful **agentic workflows** using **LangGraph** (calling the LiteLLM proxy for LLM reasoning steps and tool interactions).
*   **Interaction Model:** All components requiring external LLM/embedding access (including any LangChain chains or agents) will make HTTP requests to the deployed LiteLLM proxy endpoint, not directly to the provider APIs.

### 7.2 Technical Implementation for Expandability
*   **API-First Design:** Although Tier 0 interfaces are local (CLI, MCP), the backend is built around a REST API (Flask/FastAPI). This enforces modularity and simplifies future integration of a Web UI (Phase 2) or other clients.
*   **Containerization (Docker):** All core components (Postgres, LiteLLM, Backend/MCP, Text Processing Tools) are containerized using Docker and orchestrated with Docker Compose. This ensures consistent deployment environments and simplifies dependency management.
*   **Modular Codebase:** The Python backend and processing scripts will be structured into logical modules (e.g., `database`, `search`, `ingestion`, `embeddings`, `api`) to promote separation of concerns and maintainability.
*   **API Gateway (LiteLLM):** Using the **LiteLLM proxy** as the dedicated gateway provides crucial abstraction from specific LLM/embedding providers (Vertex AI in Tier 0, potentially others later). Switching providers (OpenAI, Anthropic, Cohere, etc.) or models becomes a configuration change in the LiteLLM proxy, requiring **no changes** to the core application logic (including any LangChain components calling the proxy). This maximizes long-term flexibility and cost optimization.
*   **Orchestration Framework (LangChain - Tier 1+):** Selectively introducing LangChain allows leveraging its powerful abstractions (LCEL, Chains, Agents, Tool Integrations) for complex tasks where they provide significant development acceleration (e.g., agentic workflows, structured LLM interactions, graph DB Q&A). This avoids introducing LangChain's complexity where simple scripting suffices (Tier 0) and contains its architectural influence.
*   **Database Choice (PostgreSQL):** Selecting PostgreSQL+pgvector provides a robust, free local solution with a well-defined and relatively straightforward migration path to managed cloud services (e.g., Supabase, NeonDB, RDS) in Tier 1, compared to potentially more complex migrations from NoSQL or specialized graph databases initially considered.

### 7.3 Advanced Expandability Techniques
*   **Explicitly Deferred from Tier 0:** Implementing advanced software engineering patterns like event-driven architecture, microservices (beyond basic container separation), formal plugin systems, or feature flagging frameworks.
    *   *Why Deferred:* Tier 0 prioritizes simplicity and rapid development of core features in a local environment. While modularity is a goal (API-first, containerization), introducing these advanced patterns adds significant architectural complexity, infrastructure overhead, and development time unsuitable for the initial MVP. Basic modularity via Python modules and API endpoints is sufficient for Tier 0/1.
    *   *Target Phase:* Considered during Tier 1 (Cloud Migration) and more likely for Tier 2/3 as the system scales and feature complexity increases.

### 7.4 Development Timeline
*   **Phase 0 (Tier 0 MVP) Estimate:** The estimated duration for Phase 0 is **1-2 months**, assuming dedicated developer resources. This focuses exclusively on delivering the core local functionality with cloud embedding integration as defined in Section 8. Timelines for subsequent phases remain indicative and depend on resources and evolving priorities.

### 7.5 Funding Narrative
*   **Tier 0 Funding Narrative:** The core narrative emphasizes delivering significant immediate value (high-quality semantic search across personal philosophical corpora) with minimal direct software/API cost by leveraging free cloud embedding tiers via local middleware. This approach validates the core technical architecture and user value proposition quickly, providing a strong foundation and clear migration path (Postgres -> Serverless Postgres) to justify investment in subsequent, more scalable cloud-native phases (Tier 1+). It demonstrates feasibility and utility on standard developer hardware before committing to recurring cloud expenses.

### 7.6 Resource Requirements
*   Tier 0 requires developer time, local hardware, and **GCP project setup (including enabling billing for usable quotas, even if aiming for $0 cost via free tier/credits)**.

## 8. Implementation Phases (Tier 0 - Cloud Embeddings Focus)

### Phase 0: Tier 0 Local Core + LiteLLM API Gateway MVP (1-2 months)
*   **Goal:** Establish core ingestion, storage, high-quality semantic search (via cloud embeddings), and basic interface functionality locally, establishing the **LiteLLM proxy as the robust API gateway**. **No LangChain components** are introduced in this phase.
*   **Database Setup:**
    *   Create Dockerfile/Compose entry for **PostgreSQL + pgvector**.
    *   Define core SQL schema (as previously detailed).
    *   Configure DB connection via environment variables.
    *   Implement schema migrations (e.g., using Alembic).
    *   Create HNSW index on `chunks.embedding`.
*   **API Gateway (LiteLLM) Setup:**
    *   Create Dockerfile/Compose entry for **LiteLLM Proxy**.
    *   Create `config.yaml` (`{{LITELLM_CONFIG_PATH}}`) defining model mapping (e.g., `philo-embed` -> `vertex_ai/text-embedding-004`) and setting `output_dimensionality: {{TARGET_EMBEDDING_DIMENSION}}`.
    *   Implement **Virtual Keys** in LiteLLM config for internal service access.
    *   Configure basic cost tracking and logging within LiteLLM.
    *   Pass GCP credentials (`{{GOOGLE_APPLICATION_CREDENTIALS}}`, etc.) as environment variables.
    *   Expose proxy port (`{{LITELLM_PORT}}`).
*   **Text Processing Pipeline (Python Scripts):**
    *   Develop Python scripts/modules (containerized) for ingestion workflow.
    *   Implement format detection, GROBID/PyMuPDF integration, `semchunk` integration.
    *   Implement embedding request logic: batching, making **HTTP requests to the LiteLLM proxy endpoint** (`http://{{LITELLM_HOST}}:{{LITELLM_PORT}}/embeddings`) using a virtual key.
    *   Implement database insertion logic.
    *   Create a main ingestion script callable via CLI/API.
*   **Backend & MCP Server (Python - No LangChain):**
    *   Develop Flask/FastAPI application (containerized).
    *   Implement API endpoints:
        *   `POST /ingest`: Triggers the Python text processing script.
        *   `POST /search`: Accepts query, sends query text **via HTTP request to LiteLLM proxy** for embedding, performs search using SQL/pgvector with the returned embedding, returns results.
        *   Basic CRUD endpoints.
    *   Implement MCP server tools calling the backend API (e.g., `philograph_ingest`, `philograph_search`, `philograph_acquire_missing`).
*   **CLI:**
    *   Develop simple CLI interacting with the Backend API (e.g., `ingest`, `search`, `acquire-missing-texts`).
*   **Text Acquisition Service Integration:**
    *   Implement logic in the Backend API (`/acquire`) to identify missing texts (e.g., query DB for documents with high citation counts but no associated chunks).
    *   For each missing text, call the `zlibrary-mcp` server's `search_books` tool via `use_mcp_tool` to find potential matches.
    *   (Manual/Semi-Automated Step for Tier 0): Present potential matches to the user via CLI/log for confirmation.
    *   Upon confirmation, call `zlibrary-mcp`'s `download_book_to_file` tool (with `process_for_rag=true`) via `use_mcp_tool`, passing the confirmed `bookDetails`.
    *   Receive the path to the processed text file from `zlibrary-mcp`.
    *   Trigger the PhiloGraph `/ingest` endpoint with the path to the processed text file.
*   **Operations & Deployment:**
    *   Create `docker-compose.yml` orchestrating Postgres, LiteLLM Proxy, Backend/MCP, Text Processing Tools. **Note:** `zlibrary-mcp` runs as a separate process, requiring its own setup as per its README.
    *   Use `.env` file for PhiloGraph configuration. Ensure `zlibrary-mcp` is configured separately (e.g., via its own environment variables for credentials).
    *   Write detailed `README.md` covering setup for PhiloGraph (including LiteLLM config and GCP setup) **and** instructions/link for setting up the required `zlibrary-mcp` server.
*   **Expandability Focus:** Establish the LiteLLM gateway pattern. Define clear API/MCP interactions for text acquisition. Keep backend logic simple and modular.
*   **Testing:** Unit tests for core Python logic. Integration tests for API endpoints, ensuring correct interaction with the LiteLLM proxy **and basic interaction patterns with `zlibrary-mcp` (potentially using mocks for the external MCP server)**.

### Phase 1: Migration to Tier 1 (Cloud Serverless) & Optional LangChain Introduction (3-6 months)
*   **Migration:**
    *   Migrate Postgres database to Cloud Serverless Postgres (e.g., Supabase, NeonDB).
    *   Deploy **LiteLLM Proxy** to a serverless container environment (e.g., Cloud Run, ACA), configured with a persistent DB (e.g., the Serverless Postgres instance) for state (virtual keys, costs, limits). Ensure robust configuration for cloud deployment.
    *   Deploy backend/MCP server logic to Serverless Functions (Lambda/GCF/Azure Functions), potentially packaging with Docker if dependencies are large. Update functions to call the deployed LiteLLM proxy endpoint.
*   **Embeddings/LLMs:** Configure LiteLLM proxy to handle potentially more providers or models. Implement more robust rate limiting, cost budgeting, and fallback strategies within LiteLLM configuration.
*   **Optional LangChain Introduction:**
    *   *Evaluate:* Assess if the complexity of the text processing pipeline or initial backend logic warrants refactoring using **LangChain (LCEL)** for better orchestration and maintainability within the serverless functions.
    *   *Implementation (If Adopted):* Refactor relevant function logic using LCEL chains. Ensure these chains make external API calls **exclusively through the deployed LiteLLM proxy endpoint**. Carefully manage LangChain dependencies for serverless deployment (containerization likely required).
*   **Enhanced Features:** Implement more robust relationship management, improve search relevance. Begin work on automated linking/inference (logic likely resides in serverless functions, potentially using LangChain chains calling the LiteLLM proxy for any LLM steps).
*   **Testing:** Expand integration and end-to-end tests for the cloud environment, including testing the deployed LiteLLM proxy and any introduced LangChain components.

### Phase 2: Web Interface, Community & LangChain Integration (7-12 months)
*   **Web UI Development:** Implement core features in a web interface interacting with the serverless backend API (functions).
*   **User Authentication & Community:** Implement user accounts, authentication, and basic sharing features. Ensure LiteLLM proxy configuration supports user-level API key management, budgeting, and rate limiting if needed.
*   **LangChain Integration:**
    *   Utilize **LangChain (LCEL, Chains)** more extensively within serverless functions to structure backend logic for the Web UI, implement Q&A features, and potentially summarization.
    *   If migrating to **ArangoDB**, leverage `langchain-community` integrations (`ArangoGraph`, `ArangoGraphQAChain`) for graph interaction, anticipating the need for custom AQL orchestration via LangChain for advanced queries.
    *   All LangChain components continue to make external LLM/embedding calls **via the LiteLLM proxy**.
*   **Deployment:** Deploy frontend to static hosting. Ensure serverless functions and the LiteLLM proxy infrastructure scale appropriately.

### Phase 3: Advanced Features, Agents & Scale (13+ months)
*   **Advanced Graph Features:** Implement sophisticated graph algorithms, likely involving custom AQL queries orchestrated via LangChain workflows.
*   **Advanced Inference & LLM Tasks:** Heavily utilize **LangChain chains** for complex Q&A, summarization, automated relationship inference, argument mapping, etc., making reasoning/generation calls through the scaled **LiteLLM proxy**.
*   **Agentic Workflows:** Implement sophisticated research assistant agents using **LangGraph**. These agents will leverage tools (interacting with the PhiloGraph database, external APIs via custom LangChain tools) and perform multi-step reasoning, with LLM calls managed by the **LiteLLM proxy**.
*   **Enhanced Text Reader & Collaboration:** Develop advanced UI features.
*   **Scalability & Optimization:** Optimize database queries (SQL/AQL), serverless function performance, LangChain/LangGraph execution, and LiteLLM proxy throughput. Implement advanced cost management and routing strategies in LiteLLM.

## 9. Brainstorming: Future Features & Directions
*   **Advanced Graph Analytics:** Implement sophisticated graph algorithms (e.g., community detection, centrality measures, pathfinding between concepts/authors) to uncover deeper structural insights within the philosophical corpus.
*   **LLM Integration for Summarization/Q&A:** Integrate Large Language Models (LLMs) via API to provide natural language summaries of search results, answer questions based on retrieved context, or even generate initial drafts of arguments based on linked text extracts.
*   **Richer Visualizations:** Develop interactive graph visualizations (beyond basic maps) to explore connections, timelines, and conceptual clusters within the data.
*   **User Collaboration & Annotation:** Allow multiple users to collaboratively build collections, share annotations, and potentially engage in discussions linked to specific texts or concepts (requires robust authentication and authorization).
*   **Automated Relationship Inference:** Move beyond citation-based links to automatically infer relationships (e.g., "critiques," "builds upon," "contrasts with") between texts or concepts based on semantic similarity and contextual analysis, potentially using fine-tuned models.
*   **Enhanced Text Reader Integration:** Develop a dedicated web-based or integrated text reader that allows seamless linking between the text, user notes, graph visualizations, and related concepts/passages.

*   **Mobile Application & Novel Interfaces:** (Expanded) Explore a dedicated mobile application leveraging the backend API (likely developed in Phase 3+). This could offer different interaction paradigms beyond traditional search/browse, specifically targeting more engaging or exploratory use cases:
    *   **Simulated Dialogues ("Philo-Feed"):** Present text extracts related to a specific topic or question from different philosophers in a dynamic, feed-like conversational format. For instance, a user query about "the nature of Being" could surface a key extract from Parmenides, followed by relevant "reply" extracts from Plato, Aristotle, Hegel, Heidegger, etc., retrieved via semantic search and relationship traversal (e.g., identifying texts explicitly citing or critiquing the source). This requires sophisticated backend logic to identify relevant conversational threads or thematic connections.
    *   **Concept Exploration:** Provide an interactive interface for visually navigating concept maps derived from the graph database, allowing users to tap on concepts or authors to see connections and related texts.
    *   **Personalized Discovery:** Offer curated feeds or push notifications based on user-defined interests (favorite philosophers, concepts, schools of thought) or reading history tracked within the app.
    *   **Quote Capture & Linking:** Allow users to easily capture quotes via camera/OCR or manual input and link them to existing texts or concepts within their PhiloGraph library via the mobile interface.

## 10. Technical Considerations (Tier 0 - Cloud Embeddings Focus)

### 10.1 Embedding Model Selection
*   **Strategy:** Leverage the **LiteLLM proxy** across all tiers to abstract providers.
*   **Tier 0:** Start with **Google Vertex AI (Free Tier/Credits)** configured in LiteLLM. Standardize dimension (e.g., 1024) using MRL truncation via LiteLLM config if needed. Requires GCP setup.
*   **Tier 1+:** Easily switch or add providers (OpenAI, Anthropic, Cohere, Voyage, etc.) by updating the **LiteLLM proxy configuration** without changing application code. LiteLLM handles the different API formats. This allows selecting models based on performance, cost, or features specific to each tier's needs.

### 10.2 Scalability Concerns (Hybrid Approach)
*   **Tier 0:**
    *   **Local Bottlenecks:** CPU (GROBID, chunking, backend) and RAM (Docker services) remain limits.
    *   **API Gateway (LiteLLM):** Performance depends on local resources allocated to the proxy container. Handles retries, but throughput limited by local hardware and external API quotas.
    *   **Scaling:** Primarily vertical (better hardware).
*   **Tier 1+ (Cloud Serverless):**
    *   **API Gateway (LiteLLM):** Scalability depends on the chosen serverless container platform (e.g., Cloud Run/ACA auto-scaling) and the performance of its backing database (for state). Needs monitoring for resource usage and potential bottlenecks under high load. LiteLLM's features (load balancing, routing) help manage underlying API provider limits.
    *   **Application Logic (Serverless Functions / LangChain):** Scalability depends on function concurrency limits, cold starts, and efficient implementation. LangChain application complexity and dependencies can impact deployment size and cold start times, potentially favoring container-based serverless deployments (Fargate, Cloud Run, ACA) over traditional function packaging. Careful dependency management is crucial.
    *   **Database:** Scalability depends on the chosen Serverless Postgres or managed ArangoDB tier.
    *   **Overall:** Requires managing scalability across multiple components: the LiteLLM proxy infrastructure, the serverless functions executing backend/LangChain logic, and the database. Cost management involves tracking usage across cloud functions, databases, *and* external API calls (monitored via LiteLLM).

### 10.3 Integration Possibilities

*   **Tier 0 Planned Integrations:**
    *   **PhiloGraph MCP Server:** The core integration for Tier 0, enabling interaction with AI agents like RooCode via defined tools (`philograph_ingest`, `philograph_search`, `philograph_acquire_missing`).
    *   **Z-Library MCP Server (`zlibrary-mcp`):** An external, locally run MCP server used by PhiloGraph's backend to acquire missing texts.
        *   *What:* Provides tools (`search_books`, `download_book_to_file`, `process_document_for_rag`) to find, download, and pre-process texts from Z-Library.
        *   *Why Included (Tier 0):* Directly addresses the requirement to populate the database with texts identified through citation analysis but not yet available locally. Leverages an existing, specialized tool for this acquisition task.
        *   *Integration Workflow:* PhiloGraph backend identifies needed texts -> Calls `zlibrary-mcp` tools via `use_mcp_tool` -> Receives path to processed text -> Triggers PhiloGraph ingestion.
        *   *Considerations:* Requires separate setup/configuration of `zlibrary-mcp`. Potential need to modify `zlibrary-mcp` for better integration (e.g., configurable output paths). Reliability depends on Z-Library website stability and the server's scraping logic. User must provide Z-Library credentials.

*   **Deferred Integrations (Targeted for Tier 1+):** The following integrations are deferred beyond Tier 0 due to added complexity, reliance on external APIs, or focus on features beyond the core MVP scope:
    *   **Zotero/Reference Managers:**
        *   *What:* Bi-directional synchronization of bibliographic metadata and potentially annotations/notes with Zotero (or similar tools like Mendeley).
        *   *Why Deferred:* Requires understanding and implementing potentially complex external APIs (Zotero API), handling authentication, managing sync conflicts, and mapping data models. This adds significant scope beyond the core Tier 0 goal of establishing the local knowledge base.
        *   *Target Phase:* Tier 1 or Tier 2, depending on API stability and development priorities.
    *   **Obsidian/Note-Taking Apps:**
        *   *What:* Deeper integration than simple URI linking. This could involve creating/updating notes in Obsidian based on PhiloGraph content, embedding PhiloGraph search results in notes, or linking specific blocks/headings.
        *   *Why Deferred:* Requires developing custom Obsidian plugins or leveraging existing ones (like URI commands), which involves understanding Obsidian's plugin architecture and API. This is secondary to building the core PhiloGraph backend. Tier 0 will likely rely on manual copy/paste or simple URI links.
        *   *Target Phase:* Tier 1 or Tier 2, potentially driven by user demand.
    *   **External Philosophical Databases (e.g., PhilPapers):**
        *   *What:* Connecting to APIs (if available and accessible) of databases like PhilPapers to automatically enrich document metadata (e.g., publication details, abstracts, keywords) or find related works not yet in the local corpus.
        *   *Why Deferred:* Relies on the availability, stability, and usage terms of external APIs. Adds complexity in data mapping, API call management, and potential cost/rate limits. Tier 0 focuses on processing user-provided documents and acquiring missing ones via `zlibrary-mcp`.
        *   *Target Phase:* Tier 2 or later, once the core system is stable and scalable.
    *   **Learning Management Systems (LMS):**
        *   *What:* Integrating PhiloGraph as a resource within platforms like Moodle, Canvas, etc., allowing instructors to link course readings or students to access research tools.
        *   *Why Deferred:* Requires understanding specific LMS integration standards (e.g., LTI) and developing corresponding interfaces. This targets a specific educational use case not central to the initial research tool focus of Tier 0/1.
        *   *Target Phase:* Tier 3 or later, if educational use cases become a priority.

### 10.4 Privacy and Ethics
*   **Tier 0:**
    *   **Local Data:** Security relies on standard local filesystem and Docker security practices. Postgres data is stored in a Docker volume; backups are manual unless scripted.
    *   **Cloud Interaction:** Text chunks are sent to Google Cloud Vertex AI for embedding generation. While Google has strong security practices, this involves transmitting potentially sensitive research data outside the local machine. Users must be aware of and accept Google Cloud's terms of service and privacy policy regarding data processed by Vertex AI. The use of a service account key (`{{GOOGLE_APPLICATION_CREDENTIALS}}`) requires secure storage and handling.
*   **Tier 1+:** Cloud provider's security measures (IAM, VPCs, encryption at rest/transit) become paramount. Data residency choices (if offered by services) may be relevant. Implementing user authentication/authorization for multi-user access is critical. Explicit user consent for data processing and storage is required. Compliance with regulations like GDPR may apply depending on user base and data scope.

## 11. Key Questions for Dialogue (Hybrid Strategy Focus)

*   **LiteLLM Proxy Performance & Configuration (Tier 0/1):** What are the practical throughput limits and resource usage patterns of the LiteLLM proxy (local Docker and serverless container)? What specific LiteLLM configurations (timeouts, retries, routing, DB state) are optimal for Vertex AI and future providers? How robust is cost tracking and budgeting?
*   **Embedding Strategy (Tier 0/1):** How does the chosen Vertex AI model perform *through the LiteLLM proxy*? Is MRL truncation effective? How easily can alternative providers be tested via LiteLLM config?
*   **Chunking & Extraction (Tier 0):** (Questions remain the same regarding `semchunk` and GROBID/AnyStyle effectiveness).
*   **Database Choice & Indexing (Tier 0/1/2):** (pgvector indexing questions remain). If migrating to ArangoDB (Tier 2), how effectively can LangChain's `ArangoGraphQAChain` handle typical queries vs. the need for custom AQL?
*   **LangChain Introduction (Tier 1+):** When is the optimal point to introduce LangChain (LCEL) for pipeline orchestration? What are the deployment challenges (package size, cold starts) in the target serverless environment, and how are they best mitigated (containers vs. functions)?
*   **LangGraph Suitability (Tier 3+):** How suitable is LangGraph for implementing the envisioned complex, stateful philosophical research agents? What are the development and debugging challenges?
*   **Hybrid Interaction:** Are there performance or complexity issues arising from LangChain components calling the LiteLLM proxy endpoint versus using direct SDK integrations (while acknowledging the loss of operational benefits)?
*   **Overall Maintainability:** How does the combined complexity of managing the LiteLLM proxy infrastructure *and* the LangChain application framework impact overall development and operational overhead across the tiers?