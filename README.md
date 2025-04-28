# PhiloGraph - Philosophical Knowledge Platform (Tier 0 MVP)

PhiloGraph is a specialized knowledge platform combining semantic search and relationship modeling for philosophical texts. This README covers the setup and usage for the Tier 0 Minimum Viable Product (MVP).

**Tier 0 Architecture Overview:**

*   **Local Deployment:** Runs via Docker Compose.
*   **Database:** PostgreSQL + pgvector (Docker container).
*   **Backend API:** Python FastAPI application (Docker container).
*   **Embeddings:** Google Vertex AI (`text-embedding-large-exp-03-07`) accessed via a local LiteLLM Proxy.
*   **Middleware:** LiteLLM Proxy (Docker container) acts as the gateway to Vertex AI.
*   **Text Processing:** CPU-based tools (GROBID, PyMuPDF, semchunk) run within the backend container or potentially separate containers (GROBID).
*   **Text Acquisition:** Relies on an external, separately running `zlibrary-mcp` server for acquiring missing texts.
*   **Interfaces:** CLI and PhiloGraph MCP Server.

## Prerequisites

1.  **Docker & Docker Compose:** Install Docker Desktop or Docker Engine with Docker Compose.
2.  **Python:** (Optional, for direct script execution or development) Python 3.11+.
3.  **Google Cloud Platform (GCP) Account:**
    *   Enable the Vertex AI API.
    *   Create a Service Account with permissions to use Vertex AI (e.g., "Vertex AI User" role).
    *   Download the Service Account key file (JSON).
    *   **Enable Billing:** Even for free tier usage, GCP often requires billing to be enabled for API quotas.
4.  **`zlibrary-mcp` Server:**
    *   Clone the `zlibrary-mcp` repository separately.
    *   Follow its README instructions for setup (install Node.js, dependencies, Python venv, configure Z-Library credentials via environment variables).
    *   Ensure the `zlibrary-mcp` server is running before attempting text acquisition via PhiloGraph.

## Setup Instructions

1.  **Clone this Repository:**
    ```bash
    git clone <repository_url>
    cd mcp-vector-database # Or your project directory name
    ```

2.  **Create `.env` File:**
    *   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    *   **Edit `.env` and fill in the required values:**
        *   `DB_PASSWORD`: Choose a secure password for the PostgreSQL database.
        *   `VERTEX_AI_PROJECT_ID`: Your GCP project ID.
        *   `VERTEX_AI_LOCATION`: Your GCP region (e.g., `us-central1`).
        *   `GOOGLE_APPLICATION_CREDENTIALS`: **Absolute path** to your downloaded GCP service account key JSON file on your host machine. This file will be mounted into the LiteLLM container.
        *   `LITELLM_API_KEY`: (Optional) If you configure virtual keys in `litellm_config.yaml`, set the key here for the backend to use.
        *   `SOURCE_FILE_DIR`: (Optional) Change the default path (`./data/source_documents`) where PhiloGraph looks for local files to ingest. Ensure this directory exists.
        *   Review other variables and adjust if necessary (ports, model names, etc.).

3.  **Create Source Directory:**
    *   If you changed `SOURCE_FILE_DIR` in `.env`, create that directory. Otherwise, create the default:
        ```bash
        mkdir -p ./data/source_documents
        ```
    *   Place your initial philosophical texts (PDF, EPUB, MD, TXT) into this directory.

4.  **Build and Start Docker Containers:**
    ```bash
    docker-compose up --build -d
    ```
    *   This will build the `philograph-backend` image and start the `db`, `litellm-proxy`, and `philograph-backend` containers.
    *   The first time `db` starts, it might take a moment to initialize. The `philograph-backend` and `litellm-proxy` services depend on the database being ready (via healthcheck).

5.  **Initialize Database Schema (First Time Only):**
    *   The `db_layer.py` includes an `initialize_schema` function. You can run this manually via the backend container or integrate it into an application startup hook (the current FastAPI lifespan attempts this, but manual execution might be safer initially).
    *   To run manually:
        ```bash
        docker-compose exec philograph-backend python -m src.philograph.data_access.db_layer
        ```
        *(Note: This assumes `if __name__ == "__main__":` block is added to `db_layer.py` to call `initialize_schema`)*
        *Alternatively, if schema initialization is robustly handled in the FastAPI startup lifespan event, this step might not be needed.*

## Usage

### Command Line Interface (CLI)

Access the CLI by executing commands within the running `philograph-backend` container:

```bash
docker-compose exec philograph-backend python -m src.philograph.cli.main [COMMAND] [ARGS]...
```

**Common Commands:**

*   **Ingest a file or directory:**
    ```bash
    # Ingest a single file (path relative to SOURCE_FILE_DIR)
    docker-compose exec philograph-backend python -m src.philograph.cli.main ingest path/to/your/document.pdf

    # Ingest all supported files in a directory (recursive)
    docker-compose exec philograph-backend python -m src.philograph.cli.main ingest path/to/your/directory
    ```

*   **Search:**
    ```bash
    docker-compose exec philograph-backend python -m src.philograph.cli.main search "concept of Being in Heidegger" --limit 5
    docker-compose exec philograph-backend python -m src.philograph.cli.main search "critique of judgment" --author Kant --limit 10
    ```

*   **Show Document Details:**
    ```bash
    docker-compose exec philograph-backend python -m src.philograph.cli.main show document <document_id>
    ```

*   **Manage Collections:**
    ```bash
    # Create a collection
    docker-compose exec philograph-backend python -m src.philograph.cli.main collection create --name "My Essay Notes"

    # Add a document to a collection
    docker-compose exec philograph-backend python -m src.philograph.cli.main collection add --collection-id <coll_id> --item-type document --item-id <doc_id>

    # List items in a collection
    docker-compose exec philograph-backend python -m src.philograph.cli.main collection list --collection-id <coll_id>
    ```

*   **Acquire Missing Text (Requires running `zlibrary-mcp`):**
    ```bash
    # Search for a specific text
    docker-compose exec philograph-backend python -m src.philograph.cli.main acquire --title "Being and Time" --author "Heidegger"
    # Follow prompts to select and confirm download/ingestion.
    ```

### PhiloGraph MCP Server

*   The PhiloGraph MCP server tools (`philograph_ingest`, `philograph_search`, `philograph_acquire_missing`) can be called by compatible MCP clients (like RooCode) if the PhiloGraph backend container is running.
*   Ensure the MCP client is configured to connect to the `philograph-mcp-server` (the name defined in the simulated MCP framework in `src/philograph/mcp/main.py`). The actual connection mechanism (stdio, network) depends on the MCP client runner.

## Development

*   **Hot Reloading:** The `docker-compose.yml` mounts the `src` directory into the `philograph-backend` container. If you run the FastAPI app directly with `uvicorn src.philograph.api.main:app --reload --host 0.0.0.0 --port 8000` inside the container (or modify the CMD), changes to the Python code should trigger automatic reloading.
*   **Testing:** Run tests using `pytest` inside the container:
    ```bash
    docker-compose exec philograph-backend pytest tests/
    ```
*   **Database Access:** You can connect to the PostgreSQL database directly using tools like `psql` or a GUI client via the exposed port (default 5432) using the credentials from your `.env` file.
    ```bash
    psql -h localhost -p ${DB_PORT:-5432} -U ${DB_USER:-philograph_user} -d ${DB_NAME:-philograph_db}
    ```

## Stopping Services

```bash
docker-compose down
```

To remove the database volume (WARNING: Deletes all data):
```bash
docker-compose down -v