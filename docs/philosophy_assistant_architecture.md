# Architecture: Philosophical Research Assistant RooCode System

## 1. Overview

This document outlines the architecture for a RooCode system designed for deep philosophical research, knowledge management, discourse, and study assistance. The system leverages multiple specialized RooCode modes, a Retrieval-Augmented Generation (RAG) system built on PostgreSQL+pgvector, custom MCP servers for database and external API interaction, and RooCode's Memory Bank for context management. The design emphasizes modularity, extensibility, and security, drawing inspiration from the project's philosophical goals (critique, discourse, self-understanding) and technical documentation.

## 2. Core Principles

*   **Modularity:** Components (modes, MCP servers, RAG) have well-defined responsibilities and interfaces.
*   **Extensibility:** The architecture allows for adding new modes, data sources, or methodologies.
*   **Context-Awareness:** Utilizes the Memory Bank and RAG context to inform interactions and retrieval.
*   **Philosophical Grounding:** Incorporates mechanisms for critique, discourse, and diverse methodologies.
*   **Security:** Emphasizes secure credential management and controlled access via MCP.
*   **Leverage RooCode:** Utilizes built-in tools, MCP framework, and Memory Bank features.

## 3. Proposed RooCode Mode Structure

A multi-mode structure is proposed to encapsulate distinct functions and potentially embody different philosophical approaches:

*   **`Philosopher` Mode:**
    *   **Responsibility:** Primary user interaction mode. Engages in philosophical discourse (Socratic questioning, dialectic), applies different methodologies (phenomenology, hermeneutics, etc.) based on context or user request, assists with study tasks (essay outlining, generating reading questions), synthesizes information from Researcher/RAG.
    *   **Interaction:** Interacts with User, `Researcher`, `Critic`, Memory Bank.
    *   **`.clinerules` Focus:** Logic for discourse patterns, applying methodologies, task decomposition, synthesis, Memory Bank context usage.

*   **`Researcher` Mode:**
    *   **Responsibility:** Handles information retrieval tasks delegated by the `Philosopher` mode. Formulates queries for the RAG system and external databases/APIs. Interacts with relevant MCP servers. Performs web searches. Pre-processes/summarizes retrieved information before passing it to the `Philosopher`.
    *   **Interaction:** Interacts with `Philosopher`, `DB-MCP`, `PhilAPI-MCP` (optional), Web Search Tools (Browser MCP/built-in), Memory Bank.
    *   **`.clinerules` Focus:** Query formulation (semantic search, API queries, web search terms), tool invocation (MCP calls), result parsing/summarization, Memory Bank logging (queries, summaries).

*   **`Critic` Mode:**
    *   **Responsibility:** Embodies the principle of critique (as discussed in `project_journal.md`). Challenges assumptions, identifies contradictions, questions premises presented by the `Philosopher` mode or found in research materials. Aims to induce *aporia*.
    *   **Interaction:** Interacts primarily with `Philosopher`, Memory Bank (potentially a dedicated section for maintaining critical stance/history).
    *   **`.clinerules` Focus:** Identifying premises/assumptions, formulating critical questions, applying deconstructive or critical theory techniques, potentially accessing specific critical texts via `Researcher`. May require rules to manage its "adversarial" nature constructively.

*   **`Librarian` Mode (or integrated into `Researcher`/MCP):**
    *   **Responsibility:** Manages the RAG knowledge base ingestion pipeline. Orchestrates document acquisition (potentially using `acquire_epub.py` or similar), text extraction, chunking, embedding, and database insertion via the `DB-MCP`.
    *   **Interaction:** Interacts with User (for initiating ingestion), `DB-MCP`, `Ingestion-MCP` (if used) or Shell MCP/Terminal (for running processing scripts), Filesystem tools, Memory Bank (logging ingestion progress/errors).
    *   **`.clinerules` Focus:** Workflow orchestration for ingestion pipeline steps, error handling during ingestion, interaction with processing tools/scripts.

## 4. RAG System Architecture

Based on `docs/roomodes/roocode-rag-research-assistant.md`:

*   **Database:** PostgreSQL with `pgvector` extension enabled.
*   **Schema:**
    *   `documents` table: Stores metadata (doc\_id, source\_uri, title, authors, pub\_date, hash, metadata\_jsonb, last\_processed\_at).
    *   `chunks` table: Stores text chunks (chunk\_id, document\_id, chunk\_text, chunk\_index, embedding vector).
    *   Indexes: HNSW/IVFFlat on `chunks.embedding`, indexes on `documents.source_uri`, `chunks.document_id`.
*   **Interaction:** Accessed exclusively via the `DB-MCP` server.
*   **Ingestion Pipeline (Leveraging ZLibrary MCP):**
    1.  **Acquisition & Initial Processing:** Use the existing `ZLibrary-MCP` server.
        *   The `Librarian` mode calls `ZLibrary-MCP`'s `download_book_to_file` tool, specifying the book ID/format and setting `process_for_rag: true`.
        *   The `ZLibrary-MCP` server handles downloading the book (e.g., EPUB, PDF) and then automatically calls its internal `process_document_for_rag` logic. This extracts text content into a usable format (e.g., Markdown or TXT) and saves it locally.
    2.  **Chunking:** The `Librarian` mode reads the processed text file (output from step 1) using Filesystem tools. It then invokes a Python script (via Shell MCP or potentially a small, dedicated `Chunker-MCP`) to split the text into meaningful chunks (e.g., recursive character splitting).
    3.  **Embedding:** The chunking script (or `Chunker-MCP`) generates vector embeddings for each chunk using a chosen model (e.g., OpenAI API, local sentence-transformer via Ollama/script), potentially in batches. API keys are read securely from environment variables.
    4.  **Storage:** The chunking script (or `Chunker-MCP`) gathers the document metadata (from ZLibrary MCP or user input) and the generated chunks/embeddings. It then calls the `DB-MCP`'s `add_document` and `batch_insert_chunks` tools to insert the data into PostgreSQL.
*   **Retrieval:**
    1.  `Researcher` mode receives task from `Philosopher`.
    2.  `Researcher` formulates semantic query, potentially augmented by Memory Bank context.
    3.  `Researcher` calls `DB-MCP` tool `query_similar_chunks`, passing the query embedding and any metadata filters.
    4.  `DB-MCP` executes vector similarity search in PostgreSQL.
    5.  `DB-MCP` returns relevant chunks and metadata to `Researcher`.
    6.  `Researcher` pre-processes/summarizes results and passes them to `Philosopher`.

## 5. MCP Server Design

Incorporating the existing ZLibrary MCP and specific need for PhilPapers:

*   **`DB-MCP` (Database Interaction - Essential):**
    *   **Purpose:** Securely mediates all interactions between RooCode modes and the PostgreSQL/pgvector database. Encapsulates database logic and credentials.
    *   **Technology:** Node.js/TypeScript or Python.
    *   **Tools:** (As previously defined: `query_similar_chunks`, `batch_insert_chunks`, `add_document`, `get_document_metadata`, `delete_document`).
    *   **Configuration:** Launched via `stdio`. Reads DB credentials securely from `env` variables set in RooCode's MCP settings.

*   **`ZLibrary-MCP` (Book Acquisition & Processing - Existing):**
    *   **Purpose:** Provides tools for searching ZLibrary, downloading books, and processing them for RAG ingestion (text extraction). Assumed to be running and accessible.
    *   **Technology:** (Assumed Node.js/Python based on typical MCP server development).
    *   **Key Tools (Assumed based on user description):**
        *   `search_books`: Input: `{ query: string, ...filters }`. Output: `{ results: Array<...> }`.
        *   `download_book_to_file`: Input: `{ id: string, format?: string, outputDir?: string, process_for_rag?: boolean }`. Output: `{ success: boolean, file_path?: string, processed_path?: string, error?: string }`. Downloads book and optionally triggers RAG processing.
        *   `process_document_for_rag`: Input: `{ file_path: string, output_format?: string }`. Output: `{ success: boolean, processed_path?: string, error?: string }`. Extracts text from downloaded file. (May be internal to `download_book_to_file` if `process_for_rag` is true).
    *   **Configuration:** Assumed to be configured in RooCode's MCP settings, potentially reading ZLibrary credentials/keys from `env`.

*   **`PhilAPI-MCP` (External Philosophy APIs - Essential):**
    *   **Purpose:** Provides a stable interface specifically for PhilPapers API and potentially other relevant philosophy databases (Open Library, DOAB). Abstracts away direct API calls.
    *   **Technology:** Node.js/TypeScript or Python.
    *   **Tools:**
        *   `search_philpapers`: Input: `{ query: string, filters?: Record<string, any> }`. Output: `{ results: Array<{ title: string, authors: string[], abstract?: string, url?: string, source_id: string }> }`. (Uses PhilPapers JSON API).
        *   `get_philpapers_details`: Input: `{ source_id: string }`. Output: `{ details: Record<string, any> }`.
        *   `search_other_apis`: Input: `{ query: string, source: 'openlibrary' | 'doab' | '...', filters?: Record<string, any> }`. Output: `{ results: Array<{ title: string, authors: string[], source_id: string, url?: string }> }`. (Optional extension).
    *   **Configuration:** Launched via `stdio`. Reads any necessary API keys (if required by PhilPapers or others) from `env` variables.

*   **`ChunkerEmbedder-MCP` (Chunking & Embedding - Optional Alternative):**
    *   **Purpose:** Encapsulates the chunking and embedding logic, potentially simplifying the `Librarian` mode's interaction if direct script execution via Shell MCP proves difficult to manage.
    *   **Technology:** Python (preferred for NLP/embedding libraries).
    *   **Tools:**
        *   `process_text_file`: Input: `{ file_path: string, doc_metadata: Record<string, any> }`. Output: `{ success: boolean, doc_id?: number, chunk_count?: number, error?: string }`. Reads text file, chunks, embeds, calls `DB-MCP` to store.
    *   **Configuration:** Launched via `stdio`. Manages its own Python environment. Reads embedding API keys from `env`.

## 6. System Interaction Flow (Updated)

```mermaid
graph TD
    subgraph RooCode Agent Modes
        User -- Interacts --> Philosopher
        Philosopher -- Delegates Research --> Researcher
        Philosopher -- Engages/Invokes --> Critic
        Critic -- Critiques --> Philosopher
        User -- Initiates Ingestion --> Librarian
    end

    subgraph External Systems & Tools
        DB[(PostgreSQL + pgvector)]
        ExtAPIs{{External APIs (PhilPapers, etc.)}}
        Web((Internet))
        LocalFS[/Local Filesystem/]
    end

    subgraph MCP Servers
        DB_MCP[DB-MCP Server]
        ZLibrary_MCP[ZLibrary-MCP Server (Existing)]
        PhilAPI_MCP[PhilAPI-MCP Server]
        Chunker_MCP[ChunkerEmbedder-MCP (Optional)]
        Shell_MCP[Shell MCP (Alternative for Chunking)]
        Browser_MCP[Browser MCP / Built-in]
    end

    subgraph Memory Bank (Filesystem)
        MB[Memory Bank Files (.md)]
    end

    %% Mode Interactions
    Philosopher -- Reads/Writes --> MB
    Researcher -- Reads/Writes --> MB
    Critic -- Reads/Writes --> MB
    Librarian -- Reads/Writes --> MB

    %% Researcher Interactions
    Researcher -- Uses Tool --> DB_MCP
    Researcher -- Uses Tool --> PhilAPI_MCP
    Researcher -- Uses Tool --> Browser_MCP

    %% Librarian Interactions (Ingestion)
    Librarian -- Uses Tool --> ZLibrary_MCP -- Downloads/Processes --> LocalFS
    Librarian -- Reads Processed File --> LocalFS
    Librarian -- Uses Tool --> Chunker_MCP -- Calls --> DB_MCP
    Librarian -- Uses Tool (Alternative) --> Shell_MCP -- Runs --> ChunkingScript{Chunking/Embedding Script} -- Calls --> DB_MCP
    ChunkingScript -- Reads --> LocalFS

    %% MCP Server Interactions
    DB_MCP -- Accesses --> DB
    PhilAPI_MCP -- Accesses --> ExtAPIs
    Browser_MCP -- Accesses --> Web

    style DB fill:#f9f,stroke:#333,stroke-width:2px
    style ExtAPIs fill:#ccf,stroke:#333,stroke-width:2px
    style Web fill:#9cf,stroke:#333,stroke-width:2px
    style LocalFS fill:#fcc,stroke:#333,stroke-width:2px
    style MB fill:#ff9,stroke:#333,stroke-width:2px
    style ZLibrary_MCP fill:#f6b26b,stroke:#333,stroke-width:2px
```

**Explanation (Updated):**

1.  User interacts with `Philosopher`.
2.  `Philosopher` delegates research to `Researcher` and engages `Critic`.
3.  `Researcher` uses `DB-MCP` (for RAG), `PhilAPI-MCP` (for PhilPapers), and `Browser-MCP` (for web).
4.  `Librarian` uses `ZLibrary-MCP` to download books and process them (extract text) to the `LocalFS`.
5.  `Librarian` then reads the processed text and uses either a dedicated `ChunkerEmbedder-MCP` or a script via `Shell_MCP` to perform chunking/embedding and store results via `DB-MCP`.
6.  All modes use the Memory Bank (`MB`).

## 7. Integration of Philosophical Concepts

*   **Discourse:** Facilitated by the `Philosopher` mode's core function, potentially using specific `.clinerules` for Socratic dialogue or dialectical exchange with the user or the `Critic` mode.
*   **Critique:** Embodied by the dedicated `Critic` mode, designed to challenge assumptions and identify contradictions, drawing inspiration from Critical Theory, Deconstruction, or Socratic methods.
*   **Methodologies:** The `Philosopher` mode can be designed to explicitly adopt different methodologies (Phenomenology, Hermeneutics, etc.) based on user prompts or task requirements. This influences its reasoning, questioning style, and how it interprets information from the `Researcher`. The RAG system's metadata (`documents.metadata_jsonb`) could potentially store methodological tags for sources.
*   **Heideggerian Concepts:**
    *   *Situatedness/Context:* Addressed through heavy reliance on the Memory Bank to ground interactions and queries in the ongoing research context.
    *   *Critique of Calculation:* The `Critic` and `Philosopher` modes aim for more than just information retrieval, engaging in deeper analysis and questioning (moving towards *besinnliches Denken*).
    *   *Language as Disclosure:* The system aims for deeper understanding by synthesizing information from multiple sources (RAG, web, APIs) and engaging in discourse, rather than just statistical NLP.
    *   *Gelassenheit (Letting-be):* Could be explored in the `Philosopher` or `Critic` mode's behavior, allowing for ambiguity tolerance or a more receptive stance during discourse, rather than always driving towards a definitive answer.

## 8. Memory Bank Integration

Utilizes the structure proposed in `roocode-rag-research-assistant.md` and adapted based on `docs/project_journal.md`:

*   **Core Files:** `activeContext.md`, `globalContext.md` (for Product Context, System Patterns, Decision Log, Progress), `scratchpad.md`.
*   **Research-Specific Files:**
    *   `researchQueries.md`: Logs user queries and agent-generated search/DB queries. Used by `Researcher`.
    *   `documentSummaries.md`: Stores agent-generated summaries of key retrieved documents (linked to `doc_id`/URI). Used by `Philosopher` and `Researcher`.
    *   `keyFindings.md`: Accumulates synthesized insights with citations. Used by `Philosopher` and `Researcher` to build knowledge and augment queries.
*   **Mode-Specific Files:**
    *   `mode-specific/philosopher.md`: Could store discourse patterns, preferred methodologies, study task templates.
    *   `mode-specific/researcher.md`: Could store preferred query strategies, source reliability notes.
    *   `mode-specific/critic.md`: Could store critical stances, history of critiques, potentially isolated context if needed.
    *   `mode-specific/librarian.md`: Could store ingestion logs, pipeline configurations.
*   **Feedback File:** `feedback/architect-feedback.md` (and potentially feedback files for other modes) will be used to log learnings, challenges, and user feedback during operation, as requested.
*   **Updates:** Managed via `.clinerules` triggered by specific workflow steps (query analysis, retrieval, synthesis, critique). `UMB` command provides manual override. Reverse chronological order maintained.

## 9. Security and Optimization

*   **Security:**
    *   Credentials for DB and external APIs managed via `env` variables in MCP server configurations. No hardcoding.
    *   `DB-MCP` enforces controlled access to the database.
    *   Shell access (if used for ingestion) should be restricted (e.g., via Shell MCP whitelisting) or encapsulated within the `Ingestion-MCP`.
    *   Filesystem access restricted via MCP configuration.
*   **Optimization:**
    *   Batch operations used for DB insertion (`DB-MCP`) and embedding generation (`Ingestion-MCP`/script).
    *   Memory Bank caching (`documentSummaries.md`, `keyFindings.md`) reduces redundant processing/retrieval.
    *   Targeted Memory Bank loading in `.clinerules` to manage context size.
    *   Efficient RAG queries combining vector search with metadata filtering.

This architecture provides a modular and extensible foundation for the Philosophical Research Assistant, integrating core RooCode features with specialized components to meet the complex requirements of philosophical research and discourse.