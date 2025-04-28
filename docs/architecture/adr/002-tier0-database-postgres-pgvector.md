# ADR 002: Tier 0 Database Choice - PostgreSQL + pgvector

*   **Status:** Proposed
*   **Date:** 2025-04-27
*   **Deciders:** Architect Mode
*   **Consulted:** `docs/project-specifications.md` v2.3 (Sections 3, 5.1), `memory-bank/globalContext.md` (Decision Log entries [2025-04-27 21:18:07], [2025-04-27 18:21:09], [2025-04-27 17:49:10])
*   **Affected:** Tier 0 Implementation, Data Modeling, Search Module, Relationship Manager, Migration Path to Tier 1.

## Context and Problem Statement

PhiloGraph Tier 0 requires a database capable of storing structured metadata, text chunks, vector embeddings for semantic search, and basic relationship information. It needs to run locally (via Docker) with minimal cost and provide a reasonable migration path to cloud-based solutions in Tier 1 (Cloud Serverless) and potentially Tier 2 (Managed Multi-Model DB).

## Decision Drivers

*   **Vector Search Capability:** Essential for core semantic search functionality.
*   **Relational Data Storage:** Needed for structured metadata (author, title, year), document structure, and potentially basic relationship tables.
*   **Local Deployment (Tier 0):** Must run efficiently within a local Docker environment.
*   **Cost (Tier 0):** Should be free and open-source.
*   **Migration Path:** Should facilitate migration to Tier 1 (Cloud Serverless, likely Postgres-based) and ideally not preclude migration to Tier 2 (potentially ArangoDB).
*   **Maturity & Community Support:** Prefer well-established technologies.
*   **Specification v2.3:** Explicitly selects PostgreSQL + pgvector for Tier 0.

## Considered Options

1.  **PostgreSQL + pgvector:** Mature open-source relational database with a popular extension for vector storage and ANN search. Runs well in Docker.
2.  **SQLite + vector extension (e.g., `sqlite-vss`):** Simple, file-based database. Lightweight for local use. Vector extensions are available but less mature/standardized than pgvector.
3.  **ArangoDB:** Open-source multi-model database (Document, Graph, Key/Value) with integrated ArangoSearch for vector search. Runs in Docker.
4.  **Dedicated Vector Databases (e.g., Milvus, Weaviate, Qdrant - Local Mode):** Specialized for vector search, often with advanced features. Can run locally via Docker.

## Decision Outcome

**Chosen Option:** 1. PostgreSQL + pgvector.

**Rationale:**

*   **Balanced Capabilities:** Provides robust relational features *and* good vector search capabilities via the `pgvector` extension, meeting Tier 0 needs for metadata, chunks, and embeddings.
*   **Local Deployment:** Runs reliably and efficiently within Docker.
*   **Cost:** Free and open-source.
*   **Excellent Tier 1 Migration Path:** PostgreSQL is widely available as a managed serverless offering in the cloud (Supabase, Neon, RDS Serverless, Cloud SQL). Migrating from local Docker Postgres to cloud Postgres is a standard, well-supported process.
*   **Maturity:** Both PostgreSQL and `pgvector` are mature and widely used with strong community support.
*   **Alignment with Spec:** Directly implements the choice specified in v2.3, which was based on previous analysis favoring the Tier 1 migration path.

**Rejection Rationale:**

*   *SQLite + vector extension:* While simple locally, migration to scalable cloud relational databases (like Postgres) is significantly harder. Vector extensions are less mature. Lacks robust concurrent write performance.
*   *ArangoDB:* Offers compelling multi-model features (especially graph) potentially beneficial for Tier 2+, but migrating from ArangoDB *back* to a relational cloud database in Tier 1 (if Tier 2 plans change) is more complex than Postgres-to-Postgres. Considered a better fit for Tier 2+.
*   *Dedicated Vector Databases:* Primarily focus on vector search and may require integrating a separate relational DB for metadata/structured data, adding complexity to the Tier 0 stack. While powerful, potentially overkill for Tier 0 needs and adds another component to manage.

## Consequences

*   **Positive:**
    *   Single database manages relational metadata, text chunks, and vector embeddings.
    *   Leverages mature, well-supported open-source technology.
    *   Provides the smoothest migration path to Tier 1 cloud serverless Postgres solutions.
    *   Good performance for combined metadata filtering and vector search.
*   **Negative:**
    *   Graph capabilities are limited to basic relational modeling (e.g., relationship tables, recursive CTEs) compared to a native graph database like ArangoDB. Complex graph traversals might be less performant.
    *   Requires managing the `pgvector` extension installation and updates within the Docker setup.
    *   HNSW index build time/memory usage for `pgvector` needs consideration during ingestion.

## Validation

*   Successful creation of tables including `vector` columns.
*   Successful creation of HNSW index on the embedding column.
*   Ability to perform combined SQL `WHERE` clause filtering and `ORDER BY <embedding_column> <=> <query_vector>` searches.
*   Performance testing of ingestion and query times with representative data volume locally.

## Links

*   `docs/project-specifications.md` v2.3 (Sections 3, 5.1)
*   `docs/architecture/tier0_mvp_architecture.md`
*   `memory-bank/globalContext.md` (Decision Log)
*   [pgvector GitHub](https://github.com/pgvector/pgvector)