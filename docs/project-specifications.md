# PhiloGraph: Philosophical Knowledge Platform - Specification v2.0

## Vision Document

### Executive Summary

PhiloGraph is envisioned as a specialized knowledge platform designed to revolutionize philosophical research and engagement. It integrates advanced semantic search capabilities (powered by vector embeddings) with sophisticated relationship modeling, allowing users to navigate the complex web of philosophical ideas, texts, and authors. Operating initially within the RooCode framework via a dedicated MCP server, and designed for future expansion into CLI and web interfaces, PhiloGraph aims to provide immediate utility for tasks like essay writing and research while building towards a comprehensive, extensible system. This platform uniquely seeks to support not only traditional analytical methods but also to facilitate exploratory approaches inspired by diverse philosophical traditions, including post-methodological thought. This document outlines the refined vision, architecture, technical specifications, and strategic roadmap based on initial concepts and subsequent research.

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

*(User stories remain largely the same as v1.0, covering Individual Researchers, AI Integration, and Community Features)*

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

## 3. System Architecture (Refined)

The overall architecture remains service-oriented, emphasizing modularity and API-driven communication.

```mermaid
flowchart TD
    subgraph "Storage Layer"
        style Storage Layer fill:#fdf,stroke:#333,stroke-width:2px
        DB[(**ArangoDB**<br/>Multi-Model: Graph, Document, Vector)]
        FSS[File Storage System<br/>(Local/Cloud)]
    end

    subgraph "Core Services (API-Driven)"
        style Core Services fill:#def,stroke:#333,stroke-width:2px
        TP[Text Processor<br/>(GROBID, OCR, Chunking, Embedding)]
        SM[Search Module<br/>(Hybrid Query Engine)]
        RM[Relationship Manager<br/>(Graph Operations)]
        IM[Inference Module<br/>(Rule/Graph-Based)]
        BM[Bibliography Manager<br/>(Citation/Collections)]

        TP -- Stores --> DB
        SM -- Queries --> DB
        RM -- Manages --> DB
        IM -- Analyzes --> DB
        BM -- Uses --> DB & SM & RM
    end

    subgraph "Interface Layer"
        style Interface Layer fill:#ffc,stroke:#333,stroke-width:2px
        CLI[Command Line Interface]
        MCPI[MCP Interface<br/>(RooCode Integration)]
        API[Internal REST/GraphQL API<br/>(Service Communication)]
        WUI[Web UI<br/>(Future Phase)]
        TR[Text Reader<br/>(Future Phase)]

        CLI --> API
        MCPI --> API
        WUI --> API
        TR --> API
    end

    subgraph "External Systems & Tools"
         style External Systems & Tools fill:#eee,stroke:#333,stroke-width:1px
         SourceAPIs{{Source APIs<br/>(DOAB, PhilPapers, etc.)}}
         LMSTools{{LMS Integration<br/>(Canvas API, etc.)}}
         ExtScripts[/Processing Scripts<br/>(Dockerized Python)/]
    end

    API -- Invokes --> Core Services
    TP -- Uses --> ExtScripts
    TP -- Uses --> SourceAPIs
    Core Services -- May Use --> LMSTools

    FSS <-. Stores/Reads .-> TP
    FSS <-. Optionally Reads .-> TR

```
**Key Architectural Changes:**
*   **Database Consolidation:** Recommending **ArangoDB** as the primary database to leverage its native multi-model capabilities (graph, document, vector) and AQL for powerful hybrid queries, simplifying the storage layer compared to separate relational + vector stores.
*   **Processing Environment:** Explicitly noting that external processing scripts (Python) should be containerized (Docker) for reliable execution invoked via Core Services (likely through an MCP server wrapper not shown in this high-level diagram).

## 4. Key Components (Refined)

### 4.1 Storage Layer

| Component         | Purpose                                                     | Recommended Tech | Considerations                                                                 |
| :---------------- | :---------------------------------------------------------- | :--------------- | :----------------------------------------------------------------------------- |
| **Database**      | Store metadata, relationships, text chunks, and embeddings. | **ArangoDB**     | Native multi-model (Graph, Document, Vector via FAISS). Powerful AQL for hybrid queries. Scalability features (SmartGraphs). Learning curve for AQL/graph concepts. Open-source core. |
| File Storage      | Store original source text files (optional mirror).         | Local / Cloud    | Accessibility, backup, linking DB entries to file paths/locations.             |

*(Fallback Database Option: PostgreSQL + pgvector. Requires careful schema design for relationships and potential performance limitations for complex graph queries.)*

### 4.2 Core Services (API Endpoints)

| Component            | Purpose                                       | Key Features (Refined based on Research)                                                                                                                                                              |
| :------------------- | :-------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Text Processor**   | Ingests and processes raw texts.              | **PDF Extraction (GROBID recommended)**, **OCR (Kraken/Calamari + mLLM post-correction recommended)**, **Hybrid Semantic-Spatial Chunking**, Metadata/Footnote/Citation Extraction (GROBID/AnyStyle+NER), **Gemini Embedding Generation (via Vertex AI - MVP)**, Pluggable embedding models, Bulk processing, Error handling. |
| **Search Module**    | Handles complex search queries.               | Hybrid queries (AQL combining vector search, graph traversal, metadata filters), Weighted search, Relevance tuning, Contextual filtering (course, school, theme).                                       |
| **Relationship Mgr** | Manages explicit & implicit relationships.    | Graph database operations (CRUD), Relationship type management (plugin architecture), Bidirectional link maintenance, Validation.                                                                       |
| **Inference Module** | Generates insights from graph data.           | Pathfinding, Transitive inference, Relationship suggestion (semantic similarity), Conceptual drift analysis, Clustering/Community detection. Pluggable rules engine.                                    |
| **Bibliography Mgr** | Manages collections and citations.            | List/Collection management, Citation generation (handling PDF pages vs. EPUB CFIs/structure), Linking text elements to footnotes/citations, Quote management.                                          |

### 4.3 Interface Layer

| Component     | Purpose                               | Target Users / Integration                               |
| :------------ | :------------------------------------ | :------------------------------------------------------- |
| CLI           | Local research & administration       | Individual researchers, power users                      |
| MCP Interface | AI agent integration                  | RooCode Agents (Gemini 2.5 Pro, etc.), other AI tools    |
| REST/GraphQL API | Internal service communication        | Decouples interfaces from core services                  |
| Web UI        | General access, community features    | Casual users, students, professors (Future Phase)        |
| Text Reader   | Integrated reading & annotation       | Researchers, students (Future Phase, potentially in Web UI)|

## 5. Design Decisions & Considerations (Refined)

### 5.1 Hosting Model
*   **Recommendation:** Hybrid approach remains preferred. Start with local functionality (CLI, MCP server interacting with local DB/scripts) with a clear path to optional cloud sync/features.

### 5.2 Community Features (Future)
*   Features like shared lists, collaborative annotation, relationship suggestions remain relevant.
*   Social network integration requires significant design for privacy and moderation.

### 5.3 Processing Pipeline (Refined Tools)

```mermaid
flowchart LR
    Raw[Raw Files/Folders<br/>(PDF, EPUB, MD, TXT)] --> Parser{Format Parser}
    Parser -- PDF --> GROBID(GROBID<br/>+ OCR?)
    Parser -- EPUB --> EPUBCnv(EPUB Parser<br/>e.g., ebook-convert)
    Parser -- MD/TXT --> TxtRead(Direct Read)

    subgraph OCR [Optional OCR Flow]
        GROBID -- Scanned? --> ImgPrep(Image Prep) --> OCR_Engine(Kraken/Calamari) --> mLLM_Correct(mLLM Post-Correction) --> StructExtOCR
    end

    GROBID --> StructExtPDF(Structure/Note Extractor)
    EPUBCnv --> StructExtEPUB(Structure/Note Extractor)
    TxtRead --> StructExtTXT(Structure/Note Extractor)

    StructExtPDF --> Chunk(Hybrid Semantic-Spatial Chunker)
    StructExtEPUB --> Chunk
    StructExtTXT --> Chunk
    StructExtOCR --> Chunk

    Chunk -- Chunks --> Embed(Embedding Generator<br/>Gemini/Vertex AI - MVP)
    Embed -- Embeddings --> Indexer(DB Indexer<br/>ArangoDB)

    StructExtPDF -- Metadata/Refs --> CitParse(Citation Parser<br/>GROBID/AnyStyle+NER)
    StructExtEPUB -- Metadata/Refs --> CitParse
    StructExtTXT -- Metadata/Refs --> CitParse
    StructExtOCR -- Metadata/Refs --> CitParse

    CitParse -- Parsed Refs --> RelExt(Relationship Extractor)
    Indexer -- Stored Data --> RelExt

    RelExt --> FinalDB[(ArangoDB Storage)]
```
*   **Tools:** Prioritize GROBID for PDF, Kraken/Calamari + mLLM correction for OCR, Hybrid Semantic-Spatial Chunking, GROBID/AnyStyle + custom NER for citations.
*   **Embeddings (MVP):** Use **Google Gemini Embeddings via Vertex AI**. Ensure the architecture allows plugging in other models later.
*   **EPUB/PDF:** Do not attempt automated page mapping. Prioritize one format per source based on citation/accessibility needs. Use CFIs for EPUB internal linking.
*   **Execution:** Processing steps (chunking, embedding, citation parsing) implemented as Python scripts within **Docker containers**, invoked via dedicated MCP servers or core service APIs.

### 5.4 Local File Management
*   Strategy remains: Optional local mirror organized logically, linked via metadata in the database.

### 5.5 Relationship System
*   The comprehensive list of relationship types (Hierarchical, Conceptual, Historical, etc.) remains valid.
*   **Implementation:** Leverage ArangoDB's native graph capabilities and AQL for modeling and querying these relationships. Design relationship types as extensible plugins.

### 5.6 Inference Capabilities
*   The list of inference types remains valid.
*   **Implementation:** Utilize ArangoDB's graph traversal capabilities (AQL) and potentially its Pregel integration for graph algorithms. Implement rule-based inference in the Inference Module service.

### 5.7 Essay Support Features
*   Features remain valid. Implementation relies on effective Search, Relationship, and Bibliography modules.

### 5.8 Revenue Model Options (Future)
*   PWYC, Freemium, Academic Pricing, API Usage tiers remain potential options for later phases.

### 5.9 Facilitating Post-Methodological Exploration
*   **Core Principle:** Shift from *representing* concepts like rhizome/deconstruction to *facilitating* user actions inspired by them.
*   **Database:** ArangoDB's flexibility supports non-standard connections better than relational models.
*   **UI/UX (Future):** Design interfaces emphasizing graph visualization, non-linear navigation, annotation of margins/fragments, juxtaposition views, and potentially "meditative" modes that resist immediate closure or categorization.

## 6. Strategic Roadmap & Funding (Refined)

### 6.1 Strategic Approach: MCP MVP First
*   **Phase 0 (MVP):** Focus on building the core ArangoDB schema, the containerized text processing pipeline (basic PDF/EPUB extraction, semantic chunking, Gemini/Vertex AI embedding), and a functional **MCP Server**. This server provides core semantic search, basic metadata filtering, and citation data retrieval to RooCode agents. This delivers immediate value for AI-assisted research and writing.
*   **Subsequent Phases:** Build out the CLI, advanced relationship modeling, inference engine, Web UI, and community features iteratively, leveraging the extensible foundation.

### 6.2 Technical Implementation for Expandability
*   Principles (API-First, Plugins, DB Migrations, Component Separation) remain crucial and should be implemented from Phase 0.

### 6.3 Advanced Expandability Techniques
*   Event-Driven Architecture, Feature Flags, Extension Testing Strategy remain relevant for later phases to manage complexity.

### 6.4 Development Timeline
*   Timeline remains indicative. Phase 0 focuses on the MCP Server MVP.

### 6.5 Funding Narrative
*   Narrative remains valid, emphasizing the gap, impact, and sustainability path starting with the MCP MVP.

### 6.6 Resource Requirements
*   Costs need estimation, but initial phase focuses on developer time + potentially modest API costs for Vertex AI embeddings (check free tiers/pricing).

## 7. Implementation Phases (Refined Focus)

### Phase 0: MCP Server MVP & Core Foundation (1-2 months)
*   **Database:** Setup ArangoDB, implement core `documents`, `chunks` collections, basic `contains`/`cites` edges. Implement schema migrations.
*   **Text Processing:** Containerized Python pipeline: GROBID for PDF, basic EPUB parser, semantic chunking, Gemini/Vertex AI embedding via API, ArangoDB batch insertion. Support TXT, MD, EPUB, basic PDF. Bulk folder input.
*   **MCP Server:** Implement tools: `semantic_search(query_text, top_k, filters)`, `get_chunk_details(chunk_id)`, `get_document_metadata(doc_id)`. Secure credential handling.
*   **Operation:** Local deployment via Docker Compose (ArangoDB, MCP Server, Processing Containers).
*   **Expandability:** API-first internal structure, pluggable embedding function, basic feature flags.

### Phase 1: Richer Relationships, Inference & CLI (3-6 months)
*   **Relationship System:** Implement plugin architecture. Add core conceptual/historical relationships in ArangoDB.
*   **Inference Module:** Basic implementation (transitive, inverse relationships) using AQL graph traversals.
*   **Search Module:** Enhance MCP search tool with graph-based filtering.
*   **Text Processing:** Improve citation/footnote extraction (GROBID/AnyStyle+NER). Add more format support.
*   **CLI:** Develop CLI interface accessing core services via internal API.
*   **Expandability:** DB versioning, testing strategy for extensions.

### Phase 2: Web Interface & Basic Community (7-12 months)
*   **Web UI:** Develop basic interface for search, browsing, reading. Integrate graph visualization (e.g., using ArangoDB Oasis or libraries like D3.js).
*   **User Accounts:** Implement basic user management.
*   **Bibliography Manager:** Implement quote collection/list features in UI.
*   **Community:** Basic shared lists.

### Phase 3: Advanced Features & Scale (13+ months)
*   **Advanced Inference:** Implement more complex inference rules/algorithms.
*   **Post-Methodology UI:** Experiment with UI affordances for non-linear exploration, juxtaposition, marginalia.
*   **Collaboration:** Enhance community features (collaborative annotation, etc.).
*   **Hosting & Monetization:** Implement cloud deployment strategy and chosen revenue model.
*   **Integrations:** Deeper integration with Calibre, LMS, Reference Managers.

## 8. Brainstorming: Future Features & Directions

*   **Advanced Visualization:**
    *   Interactive 3D graph visualizations.
    *   Temporal visualizations showing concept evolution or influence spread over time.
    *   "Argument mapping" visualizations linking premises, conclusions, critiques.
    *   Rhizomatic maps emphasizing connections and intensities over hierarchy.
    *   Visualizations highlighting "zones of indistinction" or conceptual overlaps/ambiguities.
*   **Web UI / Platform Features:**
    *   Integrated web-based reader with annotation capabilities (linking annotations to graph nodes).
    *   User profiles showcasing research interests, collections, contributions.
    *   Forums or discussion areas linked to specific texts or concepts.
    *   Tools for collaborative knowledge graph building/curation.
    *   Personalized discovery feeds based on reading history and graph proximity.
*   **Monetization Models (Modular):**
    *   **Core (Free/PWYC):** Basic search, limited personal library size, core relationship types.
    *   **Researcher Tier:** Advanced inference capabilities, larger library, advanced visualization tools, API access.
    *   **Institutional Tier:** Site licenses, LMS integration, dedicated support.
    *   **Modular Add-ons:** Sell access to specialized "Philosopher Packs" (pre-loaded corpora + relationship models for specific thinkers/schools), advanced methodology toolkits (e.g., Deconstruction Explorer, Phenomenological Reduction Assistant), or specific inference rule sets.
*   **AI Agent Enhancements:**
    *   Specialized RooCode modes pre-configured for different philosophical tasks (e.g., `HegelDialecticMode`, `DerridaCritiqueMode`).
    *   AI agents capable of autonomously suggesting new relationships or identifying gaps in the knowledge graph.
    *   Integration with NeSy frameworks for more robust reasoning.
*   **Post-Methodological Affordances:**
    *   "Deterritorialize" function: Randomly shuffles connections or juxtaposes unrelated concepts to spark new insights.
    *   "Trace Explorer": Visualizes the multiple meanings and historical baggage associated with a term.
    *   "Marginalia Focus Mode": UI that prioritizes user annotations and footnotes over the main text.
    *   "Infinite Conversation" simulator: Juxtaposes text fragments in a non-conclusive dialogue format.
*   **External Integrations:**
    *   Deeper Calibre integration (metadata sync, direct ingestion).
    *   Zotero/Mendeley integration (import/export, potentially citation linking).
    *   LMS integration (Canvas API for course readings).
    *   Potential API for integration with academic social networks or writing tools.

## 9. Technical Considerations (Refined)

### 9.1 Embedding Model Selection
*   **MVP:** **Google Gemini Embeddings via Vertex AI**. Monitor usage and costs; leverage free tiers where possible.
*   **Architecture:** Must be pluggable to allow switching to OpenAI, open-source models (e.g., Sentence Transformers run locally/containerized), or fine-tuned models later.

### 9.2 Scalability Concerns
*   ArangoDB offers clustering and SmartGraphs for scaling graph operations.
*   Vector index tuning (HNSW parameters in FAISS via ArangoDB) will be crucial.
*   Optimize AQL queries for performance, especially complex traversals combined with vector search.

### 9.3 Integration Possibilities
*   **Calibre:** Plugin development or fork remain options for deep integration (Future Phase).
*   **Quercus/LMS:** Feasible via REST APIs (Canvas first) using OAuth 2.0, requires institutional coordination.
*   **Reference Managers:** Prioritize BibTeX/RIS import/export. Deeper API integration if available.

### 9.4 Privacy and Ethics
*   Crucial, especially if community features or cloud hosting are implemented. Clear data ownership policies, opt-in sharing, secure authentication, responsible sourcing.

## 10. Key Questions for Dialogue
*(Questions remain the same as v1.0)*
1.  Scale Expectations?
2.  Specific Research Workflow Pain Points?
3.  Most Valuable Community Features?
4.  Specialized AI Agent Capabilities Needed?
5.  Monetization Philosophy/Comfort?