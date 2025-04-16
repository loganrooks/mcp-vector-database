# Specification Writer Specific Memory

## Functional Requirements
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
<!-- Append new pseudocode blocks using the format below -->
<!-- No pseudocode generated in this task -->