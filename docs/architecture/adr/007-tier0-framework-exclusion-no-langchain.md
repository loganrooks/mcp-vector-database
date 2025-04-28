# ADR 007: Tier 0 Framework Exclusion - No LangChain

*   **Status:** Proposed
*   **Date:** 2025-04-27
*   **Deciders:** Architect Mode
*   **Consulted:** `docs/project-specifications.md` v2.3 (Sections 3, 4, 7.1), `docs/reports/litellm_vs_langchain_philograph.md`
*   **Affected:** Tier 0 Implementation, Backend Service, Ingestion Service, Search Service, Developer Workflow, Future Migration Path.

## Context and Problem Statement

PhiloGraph aims to leverage advanced LLM capabilities in later tiers, and frameworks like LangChain offer powerful abstractions for building LLM-powered applications (chains, agents, tool integrations). However, Tier 0 focuses on establishing core functionality (ingestion, storage, basic search, API gateway) with minimal complexity and dependencies in a local environment. We need to decide whether to introduce LangChain in Tier 0 or defer its integration.

## Decision Drivers

*   **Tier 0 Scope:** Focus on core MVP features: local deployment, database setup, establishing the LiteLLM gateway, basic ingestion/search workflows.
*   **Complexity Management:** Avoid introducing unnecessary complexity and dependencies in the initial MVP.
*   **Hybrid Strategy:** The project adopted a hybrid strategy using LiteLLM as the unified gateway (ADR 003), with LangChain planned for selective introduction in Tier 1+ for application-level orchestration.
*   **Developer Workflow:** Ensure Tier 0 development is straightforward and focuses on foundational components.
*   **Specification v2.3:** Explicitly states "No LangChain in Tier 0" and outlines its introduction in Tier 1+.

## Considered Options

1.  **Exclude LangChain from Tier 0:** Implement backend logic, ingestion, and search using standard Python libraries (e.g., Flask/FastAPI, psycopg2, requests) making direct calls to the LiteLLM proxy endpoint.
2.  **Introduce LangChain Selectively in Tier 0:** Use LangChain components (e.g., LCEL for pipeline, document loaders, embedding classes) even for basic Tier 0 tasks, configured to call the LiteLLM proxy.
3.  **Use LangChain as Primary Framework in Tier 0:** Build the entire backend and pipeline primarily using LangChain abstractions.

## Decision Outcome

**Chosen Option:** 1. Exclude LangChain from Tier 0.

**Rationale:**

*   **Alignment with Spec & Strategy:** Directly implements the decision documented in spec v2.3 and aligns with the hybrid strategy of establishing LiteLLM first, then introducing LangChain selectively later.
*   **Reduced Complexity:** Avoids adding LangChain's significant dependency footprint and conceptual overhead to the initial MVP, allowing developers to focus on core components (DB setup, LiteLLM integration, basic API).
*   **Clearer Tier 0 Focus:** Keeps Tier 0 focused on validating the foundational architecture (local deployment, DB, LiteLLM gateway, cloud embeddings) without the added variable of LangChain integration.
*   **Sufficient Tier 0 Tooling:** Standard Python libraries are sufficient for implementing the required Tier 0 backend logic, database interactions, and HTTP calls to the LiteLLM proxy.
*   **Incremental Adoption:** Allows for a more measured and purposeful introduction of LangChain in Tier 1+, where its abstractions (LCEL, chains, agents) provide clearer benefits for more complex tasks (e.g., advanced Q&A, agentic workflows, graph DB integration).

**Rejection Rationale:**

*   *Introduce LangChain Selectively in Tier 0:* Adds unnecessary dependencies and complexity for tasks achievable with standard libraries. Blurs the lines of the phased hybrid strategy.
*   *Use LangChain as Primary Framework in Tier 0:* Significantly increases initial complexity and dependencies. Contradicts the spec and the strategic decision to establish the LiteLLM gateway independently first.

## Consequences

*   **Positive:**
    *   Simpler Tier 0 implementation with fewer dependencies.
    *   Faster initial development focused on core infrastructure.
    *   Clear separation between the API gateway layer (LiteLLM) and application logic framework (introduced later).
    *   Allows the team to gain experience with the core components before adding LangChain's abstractions.
*   **Negative:**
    *   Some logic implemented in standard Python for Tier 0 might be refactored later (Tier 1+) to use LangChain abstractions (e.g., replacing manual pipeline steps with LCEL). This represents planned, incremental refactoring rather than rework.
    *   Tier 0 misses out on potential development acceleration from LangChain's components (e.g., document loaders, embedding classes), but this is deemed an acceptable trade-off for reduced initial complexity.

## Validation

*   Tier 0 backend, ingestion, and search services are implemented successfully using standard Python libraries and direct HTTP calls to the LiteLLM proxy endpoint.
*   The implementation remains modular, allowing for future refactoring with LangChain in Tier 1+.

## Links

*   `docs/project-specifications.md` v2.3 (Sections 3, 4, 7.1)
*   `docs/architecture/tier0_mvp_architecture.md`
*   `docs/architecture/adr/003-tier0-api-gateway-litellm-proxy.md`
*   `docs/reports/litellm_vs_langchain_philograph.md`