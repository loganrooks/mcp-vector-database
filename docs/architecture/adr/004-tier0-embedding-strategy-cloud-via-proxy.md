# ADR 004: Tier 0 Embedding Strategy - Cloud Embeddings (Vertex AI) via LiteLLM Proxy

*   **Status:** Proposed
*   **Date:** 2025-04-27
*   **Deciders:** Architect Mode, User Feedback
*   **Consulted:** `docs/project-specifications.md` v2.3 (Sections 3, 5.2, 6.3, 10.1), `docs/reports/philograph_synthesis_and_recommendations.md`, `docs/reports/embedding_middleware_for_philograph.md`, User Feedback (2025-04-27)
*   **Affected:** Tier 0 Implementation, Ingestion Service, Search Service, LiteLLM Proxy Configuration, Cost Model, Infrastructure Setup.

## Context and Problem Statement

PhiloGraph's core functionality relies on high-quality semantic search, which requires generating vector embeddings for text chunks. Tier 0 aims for minimal direct cost and local deployment on standard hardware. Initial considerations involved local CPU-based embedding models (e.g., via Ollama), but performance analysis (Ref: `docs/reports/philograph_synthesis_and_recommendations.md`) indicated significant speed limitations for bulk ingestion and potentially lower quality compared to state-of-the-art cloud models. We need an embedding strategy for Tier 0 that balances cost, performance, quality, and local deployability constraints.

## Decision Drivers

*   **Search Quality:** Need high-quality embeddings for effective semantic search.
*   **Ingestion Speed:** Bulk embedding generation should be reasonably fast.
*   **Cost (Tier 0):** Aim for ~$0 direct API cost.
*   **Local Hardware Constraints:** Avoid requiring local GPUs for embedding generation.
*   **Flexibility:** Allow easy switching to different models/providers in future tiers.
*   **Specification v2.3:** Revised Tier 0 definition to use free cloud embeddings via a local proxy based on prior analysis.
*   **User Feedback:** Explicitly choose `text-embedding-large-exp-03-07` as the initial model.

## Considered Options

1.  **Local CPU Embeddings:** Use models like those available via Ollama (e.g., quantized `nomic-embed-text`) running entirely locally on the CPU.
2.  **Local GPU Embeddings:** Use GPU-accelerated models locally (requires suitable GPU hardware).
3.  **Cloud Embeddings via Direct SDK:** Integrate directly with a cloud provider's SDK (e.g., Vertex AI) in the backend services.
4.  **Cloud Embeddings via LiteLLM Proxy:** Use a local LiteLLM Proxy instance to call a cloud provider's embedding API (e.g., Vertex AI free tier).

## Decision Outcome

**Chosen Option:** 4. Cloud Embeddings via LiteLLM Proxy.
*   **Provider:** Google Cloud Vertex AI
*   **Model:** `text-embedding-large-exp-03-07` (as specified by user feedback, acknowledging its experimental status). Dimensionality TBD via research (ADR pending).
*   **Access:** Via local LiteLLM Proxy instance.

**Rationale:**

*   **Quality & Performance:** Leverages powerful cloud models (like Vertex AI's) for potentially higher search quality and significantly faster embedding generation (especially for bulk ingestion) compared to local CPU models, overcoming a key bottleneck identified in earlier analysis.
*   **Cost:** Utilizes Vertex AI's free tier/credits, aligning with the Tier 0 minimal cost goal (requires monitoring usage).
*   **Local Hardware:** Avoids the need for a local GPU, making Tier 0 accessible on standard developer hardware.
*   **Flexibility (via LiteLLM):** The LiteLLM proxy abstracts the specific provider. Switching to `text-embedding-004` (stable) or other providers/models later requires only configuration changes in LiteLLM, not application code.
*   **Alignment with Spec & Gateway Strategy:** Implements the revised Tier 0 definition in spec v2.3 and reinforces the strategic decision to use LiteLLM as the unified API gateway (ADR 003).
*   **Addresses User Feedback:** Explicitly incorporates the chosen model `text-embedding-large-exp-03-07`.

**Rejection Rationale:**

*   *Local CPU Embeddings:* Rejected due to significant performance limitations for bulk ingestion and potentially lower embedding quality compared to cloud options, hindering the core user experience.
*   *Local GPU Embeddings:* Rejected as it violates the Tier 0 requirement of running on standard developer hardware without specialized GPUs.
*   *Cloud Embeddings via Direct SDK:* Rejected because it tightly couples the application to a specific provider SDK, hindering future flexibility and violating the API gateway strategy (ADR 003).

## Consequences

*   **Positive:**
    *   Enables high-quality semantic search in Tier 0.
    *   Significantly improves embedding generation speed compared to local CPU.
    *   Maintains accessibility on standard hardware (no local GPU needed).
    *   Keeps direct API costs potentially at $0 (within free tier limits).
    *   Highly flexible for future model/provider changes via LiteLLM config.
*   **Negative:**
    *   Requires internet connectivity for embedding generation.
    *   Dependent on Google Cloud / Vertex AI availability and free tier limitations/terms.
    *   Requires GCP project setup, billing enablement (for quotas), and credential management (`{{GOOGLE_APPLICATION_CREDENTIALS}}`).
    *   Introduces cloud dependency into the otherwise local Tier 0 setup.
    *   Chosen model `text-embedding-large-exp-03-07` is experimental; stability and future availability need monitoring. Consider fallback to `text-embedding-004` in LiteLLM config.
    *   Decision on optimal embedding dimensionality (via MRL truncation in LiteLLM) is pending further research (see Research Prompt).

## Validation

*   LiteLLM Proxy successfully configured to use `vertex_ai/text-embedding-large-exp-03-07`.
*   Ingestion and search workflows successfully generate/use embeddings via the proxy.
*   Monitor Vertex AI usage to ensure it stays within expected free tier limits.
*   Evaluate search quality using the chosen model.

## Links

*   `docs/project-specifications.md` v2.3 (Sections 3, 5.2, 6.3, 10.1)
*   `docs/architecture/tier0_mvp_architecture.md`
*   `docs/architecture/adr/003-tier0-api-gateway-litellm-proxy.md`
*   `memory-bank/feedback/architect-feedback.md` (User Feedback Entry)
*   [Vertex AI Text Embeddings Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/embeddings/get-text-embeddings)
*   [LiteLLM Vertex AI Provider Docs](https://docs.litellm.ai/docs/providers/vertex)