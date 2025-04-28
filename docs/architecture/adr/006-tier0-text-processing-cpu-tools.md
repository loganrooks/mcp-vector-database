# ADR 006: Tier 0 Text Processing Tools - CPU-Based

*   **Status:** Proposed
*   **Date:** 2025-04-27
*   **Deciders:** Architect Mode
*   **Consulted:** `docs/project-specifications.md` v2.3 (Sections 3, 5.2, 6.3)
*   **Affected:** Tier 0 Implementation, Ingestion Service, Infrastructure Setup, Performance.

## Context and Problem Statement

The PhiloGraph ingestion pipeline needs to process various document formats (PDF, EPUB, MD, TXT), extract structured text content, identify metadata and citations, and chunk the text appropriately for embedding. Tier 0 operates under the constraint of using standard developer hardware (no specialized GPU) and minimizing direct costs. We need to select text processing tools that meet these constraints while providing adequate quality for the MVP.

## Decision Drivers

*   **Functionality:** Must handle PDF, EPUB, MD, TXT formats. Needs to extract text, structure (sections/chapters), metadata, and ideally citations. Requires effective text chunking.
*   **Local Deployment (Tier 0):** Tools must run locally, preferably within Docker containers.
*   **CPU-Bound:** Must operate effectively without requiring a GPU.
*   **Cost:** Prefer free and open-source tools.
*   **Quality:** Extraction and chunking quality should be sufficient for good downstream search performance.
*   **Specification v2.3:** Recommends GROBID (CPU), PyMuPDF, `semchunk`, AnyStyle.

## Considered Options

1.  **CPU-Based Toolchain (GROBID, PyMuPDF, semchunk, AnyStyle):** Use GROBID (via Docker, CPU mode) for PDF parsing/metadata/citations, PyMuPDF/ebooklib for EPUB, `semchunk` Python library for semantic chunking, and optionally AnyStyle (via Docker) for refining citation parsing.
2.  **Cloud-Based Processing Services:** Utilize cloud APIs (e.g., Google Document AI, AWS Textract) for document parsing and structure extraction.
3.  **Simpler Python Libraries Only:** Rely solely on basic Python libraries (e.g., `PyPDF2`, basic regex chunking) without specialized tools like GROBID.

## Decision Outcome

**Chosen Option:** 1. CPU-Based Toolchain (GROBID, PyMuPDF, semchunk, AnyStyle).

**Rationale:**

*   **Functionality:** This combination covers the required formats and processing steps. GROBID is particularly strong for scholarly PDF parsing. `semchunk` offers semantic chunking superior to basic methods. PyMuPDF/ebooklib handle EPUBs well.
*   **CPU-Bound & Local:** All selected tools can run effectively on CPU and are suitable for local Docker deployment.
*   **Cost:** All are open-source and free to use.
*   **Alignment with Spec:** Directly implements the tool recommendations from spec v2.3.
*   **Quality:** Offers a good balance of quality for Tier 0. GROBID provides robust structure/metadata extraction from PDFs. Semantic chunking is generally preferred over naive fixed-size chunking.

**Rejection Rationale:**

*   *Cloud-Based Processing Services:* Violates the Tier 0 goal of minimal direct cost and primarily local processing (except for embeddings via proxy). Introduces significant cloud dependency and cost for processing.
*   *Simpler Python Libraries Only:* Likely to yield much lower quality results, especially for PDF structure/metadata extraction and text chunking, negatively impacting downstream search relevance and relationship extraction.

## Consequences

*   **Positive:**
    *   Achieves required text processing functionality using free, open-source tools.
    *   Runs entirely locally on CPU (within Docker), meeting Tier 0 constraints.
    *   Provides reasonably good quality extraction and chunking for the MVP.
*   **Negative:**
    *   **Performance Bottleneck:** CPU-bound processing (especially GROBID on complex PDFs) will likely be the main performance bottleneck during ingestion on standard hardware.
    *   **Complexity:** Requires managing multiple tools/libraries, potentially including separate Docker containers (e.g., for GROBID, AnyStyle).
    *   **Extraction Quality Limits:** No tool is perfect; errors in PDF parsing, citation extraction, or chunking are possible and may require manual correction or refinement in later tiers. Robust footnote/endnote linking is deferred.
    *   **Resource Intensive:** GROBID, even in CPU mode, can be memory-intensive.

## Validation

*   Successful ingestion and processing of sample PDF, EPUB, MD, and TXT documents.
*   Verify acceptable quality of extracted text, metadata, and chunk boundaries.
*   Monitor CPU and RAM usage during ingestion on target hardware.
*   Confirm tools run correctly within their Docker containers.

## Links

*   `docs/project-specifications.md` v2.3 (Sections 3, 5.2, 6.3)
*   `docs/architecture/tier0_mvp_architecture.md`
*   [GROBID Documentation](https://grobid.readthedocs.io/)
*   [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
*   [semchunk (Concept - Assumed Python library/implementation)](https://github.com/FullStackRetrieval/semantic_chunking) (Example implementation)
*   [AnyStyle.io](https://anystyle.io/)