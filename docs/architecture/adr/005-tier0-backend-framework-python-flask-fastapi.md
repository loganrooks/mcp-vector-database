# ADR 005: Tier 0 Backend Framework - Python (Flask/FastAPI)

*   **Status:** Proposed
*   **Date:** 2025-04-27
*   **Deciders:** Architect Mode
*   **Consulted:** `docs/project-specifications.md` v2.3 (Sections 3, 5.2)
*   **Affected:** Tier 0 Implementation, Backend Service, API Design, Developer Workflow.

## Context and Problem Statement

PhiloGraph Tier 0 requires a backend service to orchestrate workflows (ingestion, search), interact with the database (PostgreSQL+pgvector), manage calls to the middleware (LiteLLM Proxy), and expose an internal API for the CLI and MCP Server interfaces. We need a suitable framework for building this backend service that is efficient, easy to use for API development, well-supported, and runs within the local Docker environment.

## Decision Drivers

*   **API Development:** Need a framework suitable for building REST APIs.
*   **Python Ecosystem:** Leverage the rich Python ecosystem for data processing, database interaction, and potential future ML/NLP tasks.
*   **Performance:** Should be reasonably performant for Tier 0 needs.
*   **Developer Experience:** Ease of development, good documentation, and community support.
*   **Containerization:** Must run well within a Docker container.
*   **Specification v2.3:** Recommends Flask or FastAPI.

## Considered Options

1.  **Flask:** Mature, lightweight, and flexible Python microframework for web/API development. Large ecosystem of extensions.
2.  **FastAPI:** Modern, high-performance Python framework based on Starlette and Pydantic. Offers automatic data validation, serialization, and interactive API documentation (Swagger UI/ReDoc). Uses async/await for concurrency.
3.  **Django/Django REST Framework (DRF):** Full-featured, "batteries-included" Python web framework. Steeper learning curve, potentially overkill for a simple Tier 0 API.
4.  **Node.js (e.g., Express):** JavaScript-based backend framework. Requires managing a separate language ecosystem.

## Decision Outcome

**Chosen Option:** 1 or 2 - Python with Flask or FastAPI. The final choice between Flask and FastAPI can be deferred to the implementation phase (Code Mode), but both are suitable.

**Rationale:**

*   **Python Ecosystem:** Both Flask and FastAPI leverage the extensive Python libraries needed for PhiloGraph (database drivers, HTTP clients, data manipulation).
*   **API Focus:** Both are excellent choices for building REST APIs. FastAPI offers more built-in features for modern API development (async, data validation, auto-docs), while Flask provides simplicity and flexibility.
*   **Performance:** FastAPI generally offers higher performance due to its async nature (based on Starlette/uvicorn), which could be beneficial. Flask's performance is typically sufficient for many applications, especially in Tier 0.
*   **Developer Experience:** Both have excellent documentation and strong community support. FastAPI's automatic data validation (via Pydantic) and interactive docs can speed up development and reduce errors. Flask's simplicity might be preferred for smaller teams or simpler APIs.
*   **Containerization:** Both frameworks are easily containerized using standard Python Docker practices.
*   **Alignment with Spec:** Both options align with the recommendation in spec v2.3.

**Rejection Rationale:**

*   *Django/DRF:* Considered too heavyweight and opinionated for the relatively simple internal API needed in Tier 0. The focus is on core orchestration, not complex web application features (like ORM, admin interface, templating) provided by Django.
*   *Node.js:* While capable, introduces a different language and ecosystem, potentially increasing complexity compared to using Python consistently across the backend and data processing scripts.

## Consequences

*   **Positive:**
    *   Leverages Python's strengths for backend development and data handling.
    *   Provides a solid foundation for building the internal REST API.
    *   Good performance and developer experience (especially with FastAPI's features).
    *   Easy to containerize and integrate with the Docker environment.
*   **Negative:**
    *   If choosing FastAPI, requires understanding async programming concepts in Python.
    *   The specific choice between Flask and FastAPI needs to be finalized during implementation, though the impact is relatively contained within the backend service.

## Validation

*   Successful implementation of core API endpoints (`/ingest`, `/search`) using the chosen framework (Flask or FastAPI).
*   API endpoints correctly orchestrate calls to other services (DB, LiteLLM Proxy).
*   Service runs reliably within its Docker container.
*   (If FastAPI) Automatic API documentation is generated and accessible.

## Links

*   `docs/project-specifications.md` v2.3 (Sections 3, 5.2)
*   `docs/architecture/tier0_mvp_architecture.md`
*   [Flask Documentation](https://flask.palletsprojects.com/)
*   [FastAPI Documentation](https://fastapi.tiangolo.com/)