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
- **Core Technologies:** Vector Database (e.g., PostgreSQL+pgvector), Relational Database (PostgreSQL), File Storage.
- **Architecture:** Service-Oriented, API-First, Plugin-based (for relationships, inference, embedding models, text processing components).
- **Expandability:** Prioritized through API versioning, DB migrations, component separation, feature flags, event-driven patterns (future), specific testing strategies.
- **Key Components:** Text Processor, Search Module, Relationship Manager, Inference Module, Bibliography Manager, Interfaces (CLI, MCP, API, Web UI, Reader).

## Decision Log
- **[2025-04-16 01:36:42] - Database Selection:** Recommended ArangoDB based on research report findings regarding multi-model capabilities and hybrid query performance for graph + vector data.
- **[2025-04-16 01:36:42] - Text Processing:** Updated recommendations based on research: GROBID for PDF, Kraken/Calamari+mLLM for OCR, Hybrid Semantic-Spatial Chunking, GROBID/AnyStyle+NER for citations.
- **[2025-04-16 01:36:42] - Source Access:** Revised strategy: Prioritize DOAB/PhilPapers/OpenLibrary APIs, cautiously evaluate Anna's Archive member API, avoid Z-Lib/LibGen programmatic reliance.
- **[2025-04-16 01:36:42] - Script Execution:** Recommended Docker/DevContainers + Custom MCP Servers for reliable Python script execution.
- **[2025-04-16 01:36:42] - Embedding Model (MVP):** Specified Google Gemini Embeddings via Vertex AI, ensuring pluggable architecture.

- **2025-04-04 12:59:13 - Specification Update:** Incorporated detailed feedback regarding PDF/EPUB page numbers, footnote processing, bulk input, local file management, external integrations (Calibre, Quercus, Social Network), and technical expandability strategy into `docs/project-specifications.md`. Prioritized core data model and MCP essentials in initial phases.

## Project Files
- `docs/project_idea.md`: Initial brainstorming and requirements.
- `docs/project-specifications.md`: Detailed specification document (updated 2025-04-04 12:59:13).