# QA Tester Specific Memory
<!-- Entries below should be added reverse chronologically (newest first) -->

## Test Plans
<!-- Append new test plans (E2E, UAT, Integration, Exploratory) using the format below -->
### Test Plan: E2E - PhiloGraph Tier 0 MVP - 2025-05-06
- **Objective**: Perform comprehensive end-to-end testing of the PhiloGraph Tier 0 MVP core functionalities.
- **Scope**: CLI and MCP interfaces for Ingestion, Search, Acquisition.
- **Status**: **Deferred (2025-05-09)**. Pending generation of synthetic test data to cover diverse formatting possibilities as per user directive and `docs/reports/epub_formatting_analysis_report.md`. Original plan at `docs/qa/tier0_e2e_plan_20250506.md`.
- **Prerequisites**: Availability of synthetic test data.
- **Associated Bugs**: N/A (Pre-execution).

## Test Coverage Analysis
<!-- Append coverage analysis notes using the format below -->
### Coverage Analysis: Ingestion Preprocessing & Chunking - 2025-05-09
- **Method**: Review of current test data strategy.
- **Coverage**: Current E2E plan relies on limited real-world samples.
- **Gaps Identified**: Lack of systematic coverage for diverse document formatting (titles, subtitles, sections, citations, footnotes, endnotes, references, page numbers) as detailed in `docs/reports/epub_formatting_analysis_report.md`.
- **Recommendations**: Generate a comprehensive suite of synthetic EPUB, PDF, and Markdown files to address these gaps. This will improve testing for ingestion, preprocessing, chunking, and metadata/relationship extraction.

## Test Execution Results
<!-- Append summaries of test runs using the format below -->

## Bug Reports Log
<!-- Append new bug reports using the format below -->

## Exploratory Testing Log
<!-- Append notes from exploratory sessions using the format below -->