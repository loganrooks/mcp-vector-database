# **Building an Advanced RAG Research Assistant as a Custom RooCode Agent Mode with PostgreSQL+pgvector Integration**

## **1\. Introduction**

**Purpose:** This report provides a comprehensive, expert-level technical guide for implementing an advanced Retrieval-Augmented Generation (RAG) Research Assistant. This assistant is designed to function as a custom Agent Mode within the RooCode framework, leveraging RooCode's specific toolset, particularly the Model Context Protocol (MCP), for online research and integrating with a local PostgreSQL database equipped with the pgvector extension for persistent, searchable document storage. The primary objective is to furnish actionable implementation patterns, reference architectures, code examples, and configuration details directly applicable within the RooCode environment.

**Target Audience:** The intended audience comprises experienced AI Engineers and Senior Software Developers who possess familiarity with the RooCode agent framework 1 and core RAG concepts. This guide assumes a need for practical, low-level implementation details rather than theoretical discourse.

**Scope:** The report encompasses the critical aspects of building this specialized agent mode, including:

* A reference architecture tailored for RooCode.  
* Patterns for integrating PostgreSQL and pgvector using RooCode's command execution capabilities and MCP.  
* Utilization of RooCode's built-in tools (file system, browser, terminal) and relevant MCP servers.  
* Design and implementation of a document processing pipeline feasible within RooCode's constraints.  
* Adaptation and integration of RooCode's Memory Bank feature for research context persistence.  
* Detailed configuration of RooCode files (.clinerules, .roomodes) to define the agent's behavior.  
* Essential security and optimization considerations for robust deployment.

**Core Challenge:** The central technical challenge lies in effectively integrating external systems—specifically a vector database and potentially complex document processing workflows—within the operational constraints and unique capabilities of the RooCode agent framework. Successfully navigating this requires proficient use of the Model Context Protocol (MCP) as the primary integration mechanism, ensuring secure communication, and optimizing interactions to maintain performance within the agent's execution environment.

## **2\. I. RooCode RAG Research Assistant: Reference Architecture**

Overview:  
Implementing a sophisticated RAG Research Assistant within RooCode necessitates a well-defined architecture that leverages RooCode's strengths while integrating external components seamlessly. The proposed architecture centers around the RooCode agent acting as an orchestrator, utilizing the Model Context Protocol (MCP) to communicate with specialized backend services and tools, including a PostgreSQL/pgvector database and document processing utilities.  
*(Conceptual Diagram Description: A diagram would show the User interacting with the RooCode Agent (Research Assistant Mode) within VS Code. The Agent communicates with an LLM (via RooCode's provider settings). The Agent also communicates via MCP with several components: a Web Search Tool (Browser/MCP), a custom PostgreSQL+pgvector Database MCP Server, and potentially a Filesystem/Shell MCP Server. The Database MCP Server interacts with the PostgreSQL+pgvector DB. The Filesystem/Shell MCP Server interacts with Document Processing CLI Tools and the local filesystem. The Agent also reads/writes to the RooCode Memory Bank stored within the project workspace.)*

**Component Breakdown:**

* **RooCode Agent (Research Assistant Mode):** This is the core component operating within the Visual Studio Code environment.1 It functions as an autonomous agent 4, interpreting natural language research queries, planning execution steps, invoking necessary tools via MCP or built-in commands, managing conversational and task context, and synthesizing final results for the user. Its specific behavior, persona, and capabilities are defined through custom entries in the .roomodes file and detailed operational logic in a corresponding .clinerules-research-assistant file.1  
* **Large Language Model (LLM):** The underlying intelligence engine (e.g., Google Gemini 2.5 Pro 3, Anthropic Claude 3.5 4). Integrated via RooCode's standard API provider settings 1, the LLM is responsible for understanding the nuances of research queries, potentially breaking down complex questions into sub-tasks (aligning with agentic RAG principles 9), generating precise search terms for web queries or structured queries for the vector database, and synthesizing coherent, cited answers from the retrieved contextual information.  
* **Model Context Protocol (MCP):** This protocol is the critical integration fabric connecting the RooCode agent to external functionalities.1 It standardizes communication between the agent and various "servers" or tools, such as the database connector, filesystem utilities, browser automation tools, or custom processing scripts. Configuration is managed globally or per-project via cline\_mcp\_settings.json or .roo/mcp.json files.1 The effective configuration and utilization of MCP are paramount to this architecture's success, acting as the central nervous system for external interactions. RooCode's ability to connect to diverse data sources and tools via MCP 4 is what enables the integration of the PostgreSQL database and external processing capabilities required for the RAG workflow. Without robust MCP integration, bridging the gap between RooCode's core coding assistance features and the demands of a data-intensive research assistant would be infeasible.  
* **PostgreSQL \+ pgvector Database:** This serves as the persistent, long-term knowledge repository.12 It stores processed research documents, their constituent chunks, and corresponding vector embeddings generated by an appropriate model. The pgvector extension 13 enables efficient vector similarity searches, allowing the agent to retrieve document chunks semantically relevant to a user's query. Access to this database is mediated exclusively through an MCP server to ensure controlled and secure interaction.  
* **Document Processing Tools (CLI):** A suite of external command-line utilities necessary for the ingestion pipeline. These tools handle tasks like text extraction from various file formats (PDF, EPUB, etc.).15 They are invoked by the RooCode agent, typically via its terminal execution capability 1 or through a dedicated Shell/Filesystem MCP server, allowing processing of local document files.  
* **Memory Bank (memory-bank/ directory):** This component provides project-specific, persistent context storage directly within the VS Code workspace, leveraging patterns established by community implementations like GreatScottyMac's Memory Bank.7 It utilizes structured Markdown files to store session state, recent user queries, refined search terms, intermediate findings, source metadata, and user preferences relevant to the ongoing research task. This differs from the vector database, which stores the core document knowledge.  
* **Web Search Tools (Browser/MCP):** Enables the agent to conduct online research for information not present in the local database or for accessing real-time data. This can be achieved using RooCode's built-in browser automation capabilities 1 for simpler tasks or by integrating more sophisticated browser control MCP servers 11 for complex interactions or accessing browser internals like console logs.11

Interaction Flow (Example Query):  
A typical research workflow might proceed as follows:

1. **User Query:** The user poses a research question within the RooCode chat interface, activating the Research Assistant mode.  
2. **RooCode Agent & LLM Analysis:** The agent, guided by .clinerules-research-assistant, passes the query and relevant context from the Memory Bank (e.g., activeContext.md, researchQueries.md) to the LLM.  
3. **Strategy Decision:** The LLM analyzes the query and context, deciding the best course of action: query the internal PostgreSQL database, search the web, or a combination. This decision is based on the nature of the query (e.g., factual lookup vs. recent event) and rules defined in .clinerules.  
4. **Tool Invocation (MCP):**  
   * *Database Query:* If querying the database, the agent formulates a semantic search query (embedding \+ SQL filters) and invokes the appropriate tool on the custom PostgreSQL MCP server.  
   * *Web Search:* If searching the web, the agent formulates search terms and uses the built-in browser tool or a dedicated Browser MCP server tool.  
5. **Data Retrieval:** The invoked tool executes the query/search and returns the relevant document chunks (from the database) or web page content/snippets.  
6. **LLM Synthesis:** The agent provides the retrieved information (database chunks, web results) along with the original query and necessary context to the LLM for synthesis. The LLM generates a coherent answer, ensuring proper citation of sources (database document IDs/source\_uri or web URLs).  
7. **Memory Bank Update:** The agent updates the Memory Bank (e.g., logs the query in researchQueries.md, stores synthesized findings in keyFindings.md, updates progress.md). This update logic is defined in .clinerules.  
8. **Response to User:** The agent presents the synthesized, cited answer to the user in the RooCode chat interface.

**Table 1: Core Research Assistant Components**

| Component | Description | Implementation Notes (RooCode Context) |
| :---- | :---- | :---- |
| LLM | Reasoning engine for query understanding, planning, synthesis. | Configured via RooCode API Provider settings.1 Choice impacts performance/cost. |
| RooCode Agent Framework | Core orchestrator within VS Code, managing workflow and tool interaction. | Utilizes custom .roomodes and .clinerules files for the "Research Assistant" mode.1 |
| Model Context Protocol (MCP) | Integration layer connecting RooCode to external tools/servers. | Central to architecture. Configured via cline\_mcp\_settings.json or .roo/mcp.json.1 Requires careful setup of relevant MCP servers (DB, Filesystem, Browser, Shell). |
| PostgreSQL+pgvector DB | Persistent storage for processed documents, chunks, and vector embeddings. | Accessed via a dedicated MCP server. Requires pgvector extension enabled.12 Schema needs vector type columns.13 |
| Document Processing Pipeline | Extracts text, chunks documents, generates embeddings for ingestion. | Implemented as external CLI tools/scripts 15 invoked via RooCode's terminal access or a Shell/Filesystem MCP server.1 Requires careful environment management.26 |
| Memory Bank (memory-bank/) | Workspace-local storage for session context, intermediate findings, query history using Markdown files. | Adapted from existing patterns.7 Structure defined for research tasks. Updates managed by .clinerules. Provides context for LLM prompts and DB queries. |
| Web Search Tool | Enables online research for external or real-time information. | Uses RooCode's built-in browser automation 1 or a dedicated Browser MCP server.11 |
| User Interface | RooCode chat panel within VS Code. | Standard RooCode interface for user interaction. |

A key design consideration emerging from this architecture is the **duality of memory systems**. The agent must manage both the RooCode Memory Bank and the PostgreSQL/pgvector database. The Memory Bank, implemented as Markdown files within the workspace 7, excels at storing conversational state, task progress, user preferences, and intermediate reasoning steps specific to the current project or research session. In contrast, the PostgreSQL/pgvector database serves as the scalable, long-term repository for the actual research knowledge—the indexed documents and their embeddings—optimized for semantic retrieval.12 A critical function of the agent's logic, defined within its .clinerules, will be to bridge these two systems effectively. Context from the Memory Bank (e.g., the user's stated goal in activeContext.md, previously explored topics in keyFindings.md) should inform and refine the queries sent to the vector database. Conversely, summaries or key insights derived from documents retrieved via the vector database should be persisted back into the Memory Bank (e.g., documentSummaries.md, keyFindings.md) to enrich the ongoing contextual understanding.

## **3\. II. Integrating PostgreSQL \+ pgvector with RooCode via MCP**

Integrating a local PostgreSQL database enhanced with the pgvector extension is fundamental to the RAG Research Assistant's ability to store and retrieve information from a private knowledge base. Given RooCode's architecture, the Model Context Protocol (MCP) provides the most structured and secure way to bridge the gap between the agent running in VS Code and the external database process.

**A. MCP Server Options for Database Interaction:**

Several approaches exist for enabling RooCode to interact with the PostgreSQL database via MCP:

1. **Existing Database MCP Servers:** Registries like Glama list various MCP servers designed for database interaction.25 One could potentially adapt a generic SQL or PostgreSQL server. However, specific support for pgvector operations (like vector similarity search operators) and the required security features might not be guaranteed or easily configurable. An MCP Memory Server using PostgreSQL/pgvector exists 28, demonstrating feasibility, though its specific toolset for general DB interaction might be limited if focused solely on memory functions. Examples like the SurrealDB MCP server show patterns for configuring credentials via environment variables 31, a crucial security practice.  
2. **Custom MCP Server:** Developing a dedicated MCP server (e.g., using Node.js or Python with libraries like psycopg2 32 and pgvector-python 34) offers the most flexibility and control. This allows tailoring MCP tools specifically for the RAG workflow: add\_document, batch\_insert\_chunks, query\_similar\_chunks, get\_document\_metadata, etc. The server can encapsulate database logic, handle pgvector specifics, implement efficient batching 35, and manage connections securely. RooCode itself can even assist in bootstrapping MCP server creation.36  
3. **Python Scripts via Terminal/Shell MCP:** RooCode can execute terminal commands 1, including running Python scripts that use libraries like psycopg2 to interact with the database. This can be done directly or via a generic Shell MCP server.24 While seemingly simpler initially, this approach introduces significant challenges in managing the Python execution environment (virtual environments, dependencies) reliably within the context that RooCode or the Shell MCP server provides.26 Ensuring the correct venv is activated and all necessary packages (psycopg2, pgvector, embedding model libraries) are available can be complex and prone to errors, especially across different user setups or operating systems.37

**Recommendation:** For a robust, maintainable, and secure RAG Research Assistant, developing a **Custom MCP Server (Option 2\)** is the recommended approach. It provides superior encapsulation of database logic, better control over the execution environment and dependencies, tailored RAG-specific functions, and a clearer path for implementing security best practices and performance optimizations like batching. While Option 3 might seem like a shortcut, the potential complexities of environment management within RooCode's execution model 26 can lead to significant integration friction.

**B. Schema Design for Research Documents and Embeddings:**

A well-designed database schema is crucial for efficiently storing documents, their chunks, embeddings, and metadata, enabling effective retrieval and proper citation.

**Proposed Schema:**

SQL

\-- Enable pgvector extension (run once per database)  
CREATE EXTENSION IF NOT EXISTS vector;

\-- Table to store document metadata  
CREATE TABLE documents (  
    doc\_id SERIAL PRIMARY KEY,                     \-- Unique document identifier  
    source\_uri TEXT UNIQUE NOT NULL,               \-- Original source (URL, file path)  
    title TEXT,                                    \-- Document title  
    authors TEXT,                                \-- List of authors  
    publication\_date DATE,                         \-- Publication date  
    extracted\_text\_hash VARCHAR(64),               \-- SHA-256 hash of extracted text (for change detection)  
    metadata\_jsonb JSONB,                          \-- Flexible storage for other metadata (abstract, journal, etc.)  
    last\_processed\_at TIMESTAMPTZ DEFAULT NOW()    \-- Timestamp of last ingestion/update  
);

\-- Table to store document chunks and their embeddings  
CREATE TABLE chunks (  
    chunk\_id SERIAL PRIMARY KEY,                   \-- Unique chunk identifier  
    document\_id INTEGER NOT NULL REFERENCES documents(doc\_id) ON DELETE CASCADE, \-- Foreign key to documents table  
    chunk\_text TEXT NOT NULL,                      \-- Text content of the chunk  
    chunk\_index INTEGER NOT NULL,                  \-- Order of the chunk within the document  
    embedding vector(1536)                         \-- Vector embedding (dimension depends on model, e.g., 1536 for text-embedding-ada-002)  
);

\-- Index on source\_uri for quick document existence checks  
CREATE INDEX idx\_documents\_source\_uri ON documents (source\_uri);

\-- Index on document\_id in chunks table for efficient retrieval of all chunks for a document  
CREATE INDEX idx\_chunks\_document\_id ON chunks (document\_id);

\-- HNSW index on embeddings for approximate nearest neighbor search (adjust parameters as needed)  
\-- Using cosine distance as it's common for semantic similarity  
CREATE INDEX idx\_chunks\_embedding\_cosine ON chunks USING hnsw (embedding vector\_cosine\_ops) WITH (m \= 16, ef\_construction \= 64);

\-- Optional: IVFFlat index (alternative to HNSW, may require tuning 'lists')  
\-- CREATE INDEX idx\_chunks\_embedding\_cosine\_ivf ON chunks USING ivfflat (embedding vector\_cosine\_ops) WITH (lists \= 100);

\-- Ensure unique chunk order within a document  
ALTER TABLE chunks ADD CONSTRAINT unique\_chunk\_order UNIQUE (document\_id, chunk\_index);

**Key Schema Elements:**

* **documents table:** Stores high-level information about each research paper or source. source\_uri acts as a key to prevent duplicate ingestion. extracted\_text\_hash helps in deciding whether a document needs reprocessing if its content changes. metadata\_jsonb offers flexibility for storing diverse metadata fields.  
* **chunks table:** Holds the segmented text pieces (chunk\_text) from each document, linked via document\_id. chunk\_index maintains the original order. The crucial embedding column stores the vector representation using the vector type from pgvector.14 The dimension (e.g., 1536\) must match the output dimension of the chosen embedding model.13  
* **Indexing:** Critically, an index must be created on the chunks.embedding column using a pgvector-supported method like HNSW (Hierarchical Navigable Small World) or IVFFlat (Inverted File with Flat Compression).13 HNSW generally offers better speed-recall trade-offs but uses more memory during indexing.14 The vector\_cosine\_ops parameter optimizes the index for cosine similarity searches, which is standard for comparing text embeddings.12 Indexes on documents.source\_uri and chunks.document\_id improve lookup performance.

**Table 2: PostgreSQL Schema for Research Documents**

| Table Name | Column Name | Data Type | Description | Indexing Notes |
| :---- | :---- | :---- | :---- | :---- |
| documents | doc\_id | SERIAL | Primary Key, Unique document ID | Primary Key Index (Automatic) |
|  | source\_uri | TEXT UNIQUE | Original source location (URL, file path) | Indexed (idx\_documents\_source\_uri) |
|  | title | TEXT | Document title | \- |
|  | authors | TEXT | Array of author names | Consider GIN index if searching authors often |
|  | publication\_date | DATE | Publication date | \- |
|  | extracted\_text\_hash | VARCHAR(64) | SHA-256 hash of extracted text | \- |
|  | metadata\_jsonb | JSONB | Other metadata (abstract, journal, keywords, etc.) | Consider GIN index for querying JSONB fields |
|  | last\_processed\_at | TIMESTAMPTZ | Timestamp of last processing | \- |
| chunks | chunk\_id | SERIAL | Primary Key, Unique chunk ID | Primary Key Index (Automatic) |
|  | document\_id | INTEGER | Foreign Key to documents.doc\_id | Indexed (idx\_chunks\_document\_id), Foreign Key |
|  | chunk\_text | TEXT | Text content of the chunk | \- |
|  | chunk\_index | INTEGER | Order of chunk within the document | Part of UNIQUE constraint (unique\_chunk\_order) |
|  | embedding | vector(DIMENSION) | Vector embedding for chunk\_text | Indexed (idx\_chunks\_embedding\_cosine, HNSW/IVFFlat) |

**C. Secure Database Command Execution in RooCode:**

Executing database commands initiated by an AI agent requires stringent security measures, particularly around credential management.40 Hardcoding secrets is unacceptable.40

* **MCP Server Approach (Recommended):**  
  * The custom MCP server should be designed to read database connection parameters (host, port, user, password, database name) from environment variables.31  
  * In RooCode's MCP configuration file (cline\_mcp\_settings.json or project-level .roo/mcp.json 1), define the MCP server entry. Use the env property within the server configuration to securely pass the necessary database credentials as environment variables to the server process when RooCode launches it.29 This avoids storing credentials directly in the configuration file itself or in the agent's code.  
  * Example structure in cline\_mcp\_settings.json:  
    JSON  
    {  
      "mcpServers": {  
        "research\_db": {  
          "command": "node", // Or python, etc.  
          "args": \["/path/to/your/custom/db\_mcp\_server.js"\],  
          "env": {  
            "PGHOST": "localhost",  
            "PGPORT": "5432",  
            "PGDATABASE": "research\_assistant\_db",  
            "PGUSER": "rag\_agent\_user",  
            "PGPASSWORD": "${env:DB\_PASSWORD}" // Example using VS Code env var substitution  
          }  
        }  
      }  
    }  
    *(Note: Securely managing DB\_PASSWORD itself, perhaps via system environment variables or a dedicated secrets manager accessible to VS Code, is crucial).*  
  * Ensure the database connection uses SSL/TLS if the PostgreSQL server is not running on localhost.  
* **Script Execution Approach (Less Secure):** If using direct script execution via terminal/Shell MCP, credentials must be sourced from the environment outside the script (e.g., .env file loaded by the script, system environment variables). However, ensuring the RooCode/MCP execution context correctly inherits these variables can be unreliable.26 There's also a higher risk of accidental logging or exposure.  
* **RooCode Permissions:** Regardless of the method, use .clinerules to define strict permissions, specifying which agent modes (only the Research Assistant mode) are allowed to invoke the database interaction tools/commands.5

The inherent risk of granting an AI agent database access necessitates prioritizing security. The custom MCP server approach provides better encapsulation, controlled credential injection via environment variables managed by RooCode's configuration 29, and a clearer separation of concerns compared to executing scripts directly, where environment variable inheritance and path resolution can be problematic.26

**D. Implementing Batch Database Operations via MCP:**

Processing documents often results in hundreds or thousands of text chunks that need to be inserted into the chunks table along with their embeddings. Inserting these one by one is highly inefficient. Batching significantly improves performance.35

* **Implementation (Custom MCP Server):**  
  * Define a specific MCP tool, for example, batch\_insert\_chunks.  
  * This tool should accept an array of chunk objects, where each object contains document\_id, chunk\_text, chunk\_index, and the embedding vector.  
  * The MCP server's backend logic (e.g., in Python) should use efficient database batch insertion methods. The psycopg2 library's extras.execute\_values function is highly recommended for this purpose, often providing substantial speedups over single inserts or even executemany.35  
  * The server should execute the batch insert within a single database transaction for atomicity.  
  * Robust error handling is needed to manage potential failures during the batch operation (e.g., constraint violations, connection issues) and report meaningful status back to the RooCode agent.  
* **Implementation (Script Execution):** If using the script execution approach, the Python script itself must implement the batching logic using methods like execute\_values.13 Data transfer from RooCode to the script needs to be efficient; for large numbers of chunks, passing data via standard input or temporary files might be necessary instead of command-line arguments.

## **4\. III. Leveraging RooCode Tools for Research Workflows**

The RooCode agent framework provides a set of built-in tools and integrates with external tools via MCP, which are essential for the Research Assistant's workflow, encompassing web data gathering, local file management, and execution of processing scripts.

**A. Web Data Extraction using Browser/MCP Tools:**

To supplement its internal knowledge base, the Research Assistant needs to access online information.

* **RooCode's Built-in Browser Automation:** RooCode includes capabilities to control a web browser programmatically.1 Commands like openBrowser("URL"), type("\#selector", "text"), click("\#selector"), assertTextContains(".selector", "text"), and closeBrowser() can be used within RooCode scripts (e.g., .roob files 10) or potentially directed by the agent's .clinerules. This is suitable for accessing specific URLs, filling simple forms, or scraping content from relatively static pages.  
  * *Example Snippet (Conceptual .clinerules action):*  
    YAML  
    \- tool: execute\_roob\_script  
      arguments:  
        script\_content: |  
          openBrowser("https://arxiv.org/abs/...")  
          // Add steps to extract abstract text based on page structure  
          const abstract \= //... logic to get text  
          closeBrowser()  
          // Return abstract

* **Browser MCP Servers:** For more complex web interactions, dedicated Browser MCP servers offer enhanced capabilities.11 These might provide features like accessing browser console logs 11, handling dynamic content more robustly, managing cookies/sessions, or taking screenshots.5 Configuration involves adding the server definition to cline\_mcp\_settings.json 22 and ensuring any necessary prerequisites (like browser drivers 10) are met. The specific tools exposed (e.g., launch\_browser, click, type, scroll, close\_browser 22) would then be available to the agent.  
* **Tool Selection:** The choice between the built-in browser and an MCP server depends on the complexity of the web interaction required. For simple page fetching or interaction with known, stable elements, the built-in tools may suffice. For dynamic applications, debugging web issues (using console logs), or advanced automation, a dedicated Browser MCP server is preferable.

**B. Local Document Management with RooCode File Tools:**

The agent needs to interact with local files, primarily to read source documents for the ingestion pipeline.

* **Reading Files:** The simplest way to bring local file content into the agent's context is using the @file mention (e.g., @/path/to/research\_paper.pdf) within the chat.5 Alternatively, a Filesystem MCP server can provide a dedicated read\_file tool.25 This is the primary mechanism for accessing the raw content of PDFs, EPUBs, Markdown files, etc., before they are processed.  
* **Listing Files:** To discover documents within a project directory, the agent can use tools provided by a Filesystem MCP server, such as list\_directory 42 or search\_files.42 This allows the agent to identify potential candidates for ingestion. RooCode might also have a built-in \<list\_files\> command, although MCP tools often offer more features like recursive listing or pattern matching.42  
* **Writing/Updating Files:** While RooCode offers \<insert\_content\> and \<apply\_diff\> tools \[User Query\], and Filesystem MCPs provide write\_file 42 or update\_file 43, these are less critical for the core *ingestion* workflow of the RAG assistant, which focuses on reading source documents and writing processed data to the database. These tools might be useful for saving generated reports, intermediate processing results, or potentially updating Memory Bank files directly if needed.  
* **Filesystem MCP Servers:** Using a dedicated Filesystem MCP server 25 is generally recommended for robust file operations. These servers often provide enhanced security features like restricting operations to specific allowed directories (FS\_BASE\_DIRECTORY 43 or args in config 42), path sanitization 43, and more granular tools (e.g., get\_file\_info 42, move\_file 42) compared to potentially simpler built-in commands. Configuration requires adding the server definition to the MCP settings file and specifying allowed paths for security.

**C. Executing Processing Scripts (Python) via Terminal/MCP:**

The document processing pipeline (text extraction, chunking, embedding) will likely involve executing external scripts, typically written in Python.

* **RooCode Terminal Access:** RooCode's built-in capability to run terminal commands 1 allows direct execution of Python scripts (e.g., python process\_document.py \--input paper.pdf \--output processed\_data.json). This provides a straightforward way to invoke the processing logic.  
* **Shell MCP Servers:** Alternatively, a Shell MCP server, such as the Super Shell MCP 24, can be used. This offers advantages like:  
  * Platform Abstraction: Handles differences between shells (bash, zsh, PowerShell, cmd).24  
  * Security: Enforces command whitelisting (Safe, Requires Approval, Forbidden levels).24  
  * Environment Control: Potentially offers better control over the execution environment, although challenges may remain. Configuration involves setting up the server in MCP settings and using its execute\_command tool.24  
* **Environment Management:** This is a critical and often challenging aspect. When RooCode or an MCP server executes a Python script, it must use the correct Python interpreter and have access to all required dependencies (e.g., pdftotext wrapper, tiktoken, openai, psycopg2, pgvector).  
  * **Recommendation:** Use Python virtual environments (venv). Ensure the execution command explicitly uses the Python executable from the *activated* virtual environment (e.g., /path/to/project/venv/bin/python your\_script.py on Linux/macOS 39, or the equivalent path on Windows). Relying on the system's default Python or assuming environment activation carries over from the user's terminal is unreliable.26  
  * Alternatively, tools like conda run \-n your\_env python your\_script.py can manage environment activation for Conda environments.38  
  * Be mindful of potential path resolution issues, especially on Windows, when commands are executed from within RooCode or an MCP server process.37 Using full, absolute paths to scripts and executables is often safer.  
* **Passing Data:** Determine how data (e.g., file paths, extracted text, configuration) is passed between the RooCode agent and the processing scripts. Options include command-line arguments, reading/writing temporary files (managed via Filesystem tools/MCP), or potentially standard input/output streams if supported by the execution method.

RooCode often provides multiple avenues to achieve a task (e.g., built-in file tools vs. Filesystem MCP, terminal vs. Shell MCP). The selection should be guided by the specific requirements for security, robustness, platform compatibility, and the complexity of the operation. For sensitive operations like database access or potentially destructive commands, or for complex file manipulations, leveraging specialized MCP servers with their inherent controls (allowed paths, whitelisting) is generally preferable to using the more open-ended built-in terminal access. Furthermore, the successful execution of external processing scripts, particularly Python scripts with dependencies, hinges critically on meticulous management of the execution environment. Failure to ensure the correct virtual environment activation and dependency availability within the context provided by RooCode or the MCP server is a common source of errors and instability.26 Explicit path specification and environment activation commands are often necessary.

**Table 3: MCP Tool Integration Summary**

| Task | RooCode Tool/MCP Server | Key Functions/Commands | Security/Configuration Notes |
| :---- | :---- | :---- | :---- |
| Web Search | Built-in Browser / Browser MCP | openBrowser, type, click / launch\_browser, search\_web (MCP specific) | Built-in has safety mechanisms.10 MCP server config in cline\_mcp\_settings.json. |
| Database Query (Chunks) | Custom DB MCP Server | query\_similar\_chunks(query\_embedding, top\_k, filter\_metadata) | Secure credential handling via env in MCP config.31 Use .clinerules permissions. |
| Database Insert (Chunks) | Custom DB MCP Server | batch\_insert\_chunks(chunk\_data\_list) | Use batching (execute\_values 35). Secure credentials. .clinerules permissions. |
| Document Reading (Local) | @file mention / Filesystem MCP | @/path/to/file / read\_file(path) | Filesystem MCP allows restricting access to allowed\_paths 42 or FS\_BASE\_DIRECTORY.43 |
| Document Writing (Local) | \<insert\_content\>, \<apply\_diff\> / Filesystem MCP | write\_file(path, content), update\_file(...) | Less critical for ingestion. Use with caution. Filesystem MCP security applies. |
| Script Execution (Python) | Built-in Terminal / Shell MCP | python script.py \[args\] / execute\_command(command, args) | **Critical:** Manage Python venv/conda environment activation explicitly.26 Shell MCP offers whitelisting.24 Path issues.37 |
| Text Extraction (via Script) | Built-in Terminal / Shell MCP | python extract.py \<infile\> / execute\_command(...) invoking python extract.py... | Requires text extraction tools (e.g., pdftotext) installed in the execution environment. Environment management is key. |

## **5\. IV. Document Processing Pipeline within RooCode Constraints**

A core component of the RAG system is the pipeline that ingests raw documents, processes them, and stores them in the vector database. This pipeline must operate within the constraints of the RooCode environment, meaning it primarily relies on executing external command-line tools and scripts via RooCode's terminal access or MCP servers.

**A. Text Extraction Tools and Techniques:**

The first step is extracting plain text from various document formats (PDF, EPUB, Markdown, Text). This requires cross-platform command-line tools that RooCode can invoke.

* **Tool Survey & Selection:**  
  * **PDF:** Several options exist. pdftotext (part of the Poppler or XPDF utilities) is a widely available open-source option, good for extracting text flow.17 mutool (from MuPDF, also open source) provides text extraction capabilities (mutool draw \-F txt).17 For scanned PDFs or images embedded in PDFs, OCR is necessary; Tesseract OCR is a powerful open-source engine callable from the command line.46 Commercial tools like Apryse PDF2Text 15 and VeryPDF PDF2Text 16 offer advanced features like layout preservation, robust Unicode handling 15, and potentially higher accuracy, but require licensing. The choice depends on the need for OCR, layout fidelity, handling of complex PDFs, and budget. For general text-based PDFs, pdftotext or mutool are strong starting points.  
  * **EPUB:** Calibre's ebook-convert command-line tool is very powerful and supports conversion to TXT 18, but Calibre itself is a large application with dependencies. Simpler, dedicated C-based tools like epub2txt 18 exist, designed for minimal dependencies, making them potentially easier to deploy in constrained environments. mutool can also convert EPUB to text.18 pandoc is a universal document converter capable of handling EPUB to plain text.50  
  * **Markdown/Text:** These formats are generally straightforward. Standard command-line utilities like cat (Linux/macOS) or type (Windows) can output the content, or RooCode can read them directly using @file or file tools. pandoc can be used to strip Markdown formatting if pure plain text is required.50  
* **Implementation Strategy:** A robust approach involves creating a dispatcher script (e.g., in Python). This script receives the input file path from the RooCode agent (via terminal/MCP command). It inspects the file extension (or uses a library to detect the MIME type) and then invokes the appropriate pre-installed command-line tool (pdftotext, ebook-convert, tesseract, mutool, etc.) using Python's subprocess module.51 The script captures the standard output (the extracted text) and returns it to the RooCode agent or writes it to a temporary file.  
  * *Example CLI Calls (Conceptual):*  
    * pdftotext input.pdf \- (Outputs text to stdout)  
    * ebook-convert input.epub output.txt \--txt-output-formatting=plain  
    * tesseract scanned\_page.png stdout \-l eng (Outputs OCR text to stdout)  
    * mutool convert \-o \- \-F txt input.epub (Outputs text to stdout)  
* **Table 4: Command-Line Text Extraction Tools Comparison**

| Tool Name | Supported Formats | Platform Compatibility | Key Features/Options | License | RooCode Integration Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| pdftotext | PDF | Win, Linux, macOS | Layout preservation (-layout), page range (-f, \-l), password (-opw, \-upw) 17 | GPL (Poppler) | pdftotext input.pdf \- (to stdout) |
| Apryse PDF2Text | PDF | Win, Linux, macOS | High quality, Unicode support, XML output, bounding boxes, commercial 15 | Commercial | ./pdf2text input.pdf \-o output.txt \--lic\_key... |
| VeryPDF PDF2Text | PDF | Win, Linux, macOS | OCR option, Unicode support, layout engine, commercial 16 | Commercial | pdf2txtocr.exe \-ocr \-infile input.pdf \-outfile output.txt |
| Tesseract OCR | Images (incl. in PDF) | Win, Linux, macOS | OCR engine, language support (-l), various output formats 46 | Apache 2.0 | Requires pre-processing PDF to images (e.g., using convert or mutool). tesseract image.png stdout \-l eng |
| mutool | PDF, EPUB, XPS, CBZ | Win, Linux, macOS | Text extraction (draw \-F txt), image conversion, rendering 17 | AGPLv3 | mutool draw \-o \- \-F txt input.pdf or mutool convert \-o \- \-F txt input.epub |
| Calibre ebook-convert | EPUB, MOBI, AZW, etc. | Win, Linux, macOS | Wide format support, extensive options, converts to TXT 18 | GPLv3 | ebook-convert input.epub output.txt. Requires Calibre installation. |
| pandoc | EPUB, Markdown, HTML, etc. | Win, Linux, macOS | Universal converter, many formats, converts to plain text 50 | GPLv2+ | pandoc input.epub \-t plain \-o output.txt or pandoc input.md \-t plain \-o output.txt |

**B. Document Chunking Strategies for RooCode:**

Once plain text is extracted, it needs to be split into smaller, manageable chunks for embedding and retrieval.

* **Rationale:** Chunking is necessary to respect the context window limitations of embedding models and LLMs 4, and to enable more targeted retrieval – finding the specific passage relevant to a query rather than an entire document.  
* **Methods:** Common strategies include:  
  * *Fixed-Size Chunking:* Splitting text every N characters or tokens, potentially with overlap. Simple but can break sentences or semantic units.  
  * *Recursive Character Splitting:* A common technique (used by libraries like LangChain) that tries to split based on paragraph breaks, then sentence breaks, then words, recursively, to maintain semantic coherence as much as possible while respecting size limits.  
  * *Semantic Chunking:* More advanced methods using NLP techniques or embedding models themselves to identify semantic boundaries, but potentially more complex to implement.  
* **Implementation:** Given the constraints, implementing chunking logic within the Python dispatcher script (called via terminal/MCP) is the most practical approach.  
  * For token-based splitting, the tiktoken library 13 can be used to count tokens accurately for models like OpenAI's.  
  * Recursive character splitting can be implemented with standard Python string manipulation, prioritizing splitting at \\n\\n, then \\n, then ., then spaces, while keeping track of chunk size (in characters or tokens).  
  * Using large external libraries like LangChain or LlamaIndex for chunking might be feasible if the Python environment can be reliably managed 26, but simpler, custom implementations might be more robust within the RooCode execution context.  
  * *Basic Python Example (Recursive Character Splitting Concept):*  
    Python  
    def chunk\_text(text, max\_chunk\_size, separators=\["\\n\\n", "\\n", ". ", " ", ""\]):  
        if len(text) \<= max\_chunk\_size:  
            return \[text\]  
        \# Try splitting by the first separator  
        best\_separator \= separators  
        parts \= text.split(best\_separator)  
        \#... (recursive logic to split parts further if they are too large,  
        \#      trying subsequent separators if splitting by the current one fails)...  
        \# Combine smaller parts back up to max\_chunk\_size  
        \#...  
        return chunks

**C. Embedding Generation Implementation:**

Each text chunk must be converted into a vector embedding.

* **Model Choice:** Select an appropriate embedding model. Options include OpenAI models (text-embedding-3-small, text-embedding-ada-002) accessible via API 13, or potentially open-source sentence-transformer models runnable locally (e.g., via Ollama 5 or a dedicated Python environment if resources permit). The chosen model determines the embedding dimension (e.g., 1536 for text-embedding-ada-002, 384 or 768 for many sentence-transformers).  
* **Implementation:** This logic should reside within the Python processing script.  
  * **API-based (e.g., OpenAI):** Use the official client library (e.g., openai Python package 13). API keys must be handled securely, preferably read from environment variables set by the MCP configuration or the script's execution environment.  
  * **Local Models:** If using a locally hosted model (e.g., Ollama running on localhost), the script needs to make HTTP requests to the model's API endpoint.  
* **Batching:** Processing potentially thousands of chunks requires batching requests to the embedding model/API for efficiency. Most APIs (like OpenAI's) support sending multiple texts in a single request. The Python script should group chunks into batches before sending them for embedding.  
  * *Python Example (OpenAI Batching Concept):*  
    Python  
    import openai  
    \# Assuming openai.api\_key is set via environment variable  
    openai\_client \= openai.OpenAI()

    def get\_embeddings\_batch(texts, model="text-embedding-3-small"):  
        texts \= \[text.replace("\\n", " ") for text in texts\] \# API recommendation  
        response \= openai\_client.embeddings.create(input\=texts, model=model)  
        return \[item.embedding for item in response.data\]

    \# Inside processing loop:  
    all\_chunks \= \[...\] \# List of text chunks  
    batch\_size \= 100 \# Adjust based on API limits and performance  
    all\_embeddings \=  
    for i in range(0, len(all\_chunks), batch\_size):  
        batch\_texts \= all\_chunks\[i:i \+ batch\_size\]  
        batch\_embeddings \= get\_embeddings\_batch(batch\_texts)  
        all\_embeddings.extend(batch\_embeddings)

**D. Populating the Vector Database:**

The final step of the pipeline is storing the processed data in PostgreSQL.

* **Workflow:** The overall ingestion process, orchestrated by the RooCode agent, looks like this:  
  1. Agent identifies a new document (e.g., user provides path, agent finds file).  
  2. Agent invokes the processing script/MCP tool, passing the document path.  
  3. Script/Tool:  
     * Extracts text using the appropriate CLI tool.  
     * Chunks the extracted text.  
     * Generates embeddings for each chunk (in batches).  
  4. Script/Tool (or Agent via DB MCP):  
     * Inserts document metadata into the documents table.  
     * Inserts all chunks and their corresponding embeddings into the chunks table using efficient batch insertion. This interaction happens via the custom Database MCP server or the database interaction script.  
* **Error Handling:** The pipeline needs robust error handling. Failures during text extraction (e.g., corrupted file, tool not found), embedding generation (e.g., API errors, invalid input), or database insertion (e.g., connection issues, constraint violations) should be caught, logged, and potentially reported back to the RooCode agent/user. Transaction management during batch insertion is important to ensure data consistency.

The entire document processing pipeline relies heavily on RooCode's ability to reliably execute external scripts and command-line tools. This execution context is paramount. Whether using the built-in terminal or a Shell/Filesystem MCP, ensuring the correct environment (Python version, activated venv/conda environment, installed dependencies, installed CLI tools, necessary environment variables like API keys) is consistently available is crucial for the pipeline's success.26 Furthermore, the selection of specific tools for text extraction must consider practical factors beyond mere functionality, such as their installation complexity, dependencies, cross-platform compatibility, and licensing implications 15, as these directly impact the feasibility of deploying and running the pipeline within the target execution environment controlled by RooCode.

## **6\. V. Implementing the Research Assistant Memory Bank**

While the PostgreSQL database serves as the long-term knowledge store, the RooCode Memory Bank provides crucial short-term and session-specific context. Adapting existing Memory Bank patterns 6 for the unique needs of a research assistant is key to enabling more intelligent and context-aware interactions.

**A. Designing the Memory Bank Structure for Research:**

The standard Memory Bank structure, typically using Markdown files within a memory-bank/ directory at the project root 20, provides a solid foundation.

* **Core Files (Adapted):**  
  * activeContext.md: Tracks the *current* research focus. This could include the main user query being addressed, specific sub-questions being investigated, or the document/topic currently under analysis. Updated frequently during a session.  
  * decisionLog.md: Records significant agent decisions during the research process. Examples include the rationale for choosing web search over database query, assessments of source reliability, or choices made during information synthesis.  
  * productContext.md: Defines the overall research project or goal. Contains high-level scope, objectives, and constraints provided by the user initially or refined over time. Changes less frequently.  
  * progress.md: Logs completed research steps, analyzed documents, and identifies remaining tasks or questions. Provides a history of the research trajectory within the session or project.  
* **Research-Specific Files (Proposed Additions):** To enhance research-specific context management, consider adding:  
  * researchQueries.md: A log of user queries and the corresponding refined search terms or database queries generated by the agent. Helps avoid redundant searches and track query evolution.  
  * documentSummaries.md: Stores concise, agent-generated summaries of key documents retrieved from the database or web, including source identifiers (e.g., doc\_id or URL). Provides quick access to salient points without re-reading full texts or re-querying.  
  * keyFindings.md: Accumulates synthesized insights, facts, or answers relevant to the activeContext.md. Each finding should be linked to its supporting evidence (citations from documentSummaries.md or source identifiers).  
  * sourceMetadataCache.md: Optionally cache metadata (title, authors, date) for frequently accessed doc\_ids to reduce repetitive lookups in the documents table, potentially speeding up citation generation.  
* **Rationale:** These files collectively provide a layered memory: productContext for the overall goal, activeContext for the immediate focus, progress and decisionLog for the process history, and the new files (researchQueries, documentSummaries, keyFindings) for accumulating research-specific artifacts (queries, summaries, synthesized knowledge). This structure helps the agent maintain focus, avoid repetition, synthesize information progressively, and provide better-contextualized responses.

**Table 5: Research Memory Bank File Structure**

| Filename (memory-bank/...) | Purpose | Key Content/Structure | Update Trigger/Mode |
| :---- | :---- | :---- | :---- |
| activeContext.md | Current research focus, active query, task state. | Current high-level query, sub-questions, document(s) under analysis, session goals. | Updated frequently by agent (via .clinerules) during query processing, synthesis. Read at start of interaction. |
| decisionLog.md | Rationale for agent's strategic choices. | Timestamped entries: Why DB vs. web search chosen, source reliability notes, synthesis strategy decisions. | Updated after significant decisions (strategy selection, source evaluation). |
| productContext.md | Overall research goal, scope, constraints. | User-defined research objective, scope limitations, required output format, long-term project context. | Updated infrequently, primarily based on initial setup or explicit user instruction to change scope. |
| progress.md | Log of completed work and upcoming tasks. | List of completed sub-queries, documents analyzed/ingested, identified gaps, next steps. | Updated after completing major steps (e.g., analyzing a document batch, answering a sub-query). |
| researchQueries.md (New) | Log of user queries and agent-generated search/database queries. | Timestamped entries: User query \-\> Agent's refined query (web search terms or DB query structure/embedding focus). | Updated after query analysis/refinement step. Checked before generating new queries. |
| documentSummaries.md (New) | Concise summaries of key retrieved documents. | Structured entries: Source ID (doc\_id/URL), Title, Agent-generated summary. | Updated after retrieving and analyzing significant documents from DB or web. |
| keyFindings.md (New) | Synthesized findings relevant to the active context. | Fact/statement, supporting citation(s) linking to documentSummaries.md or source IDs. Organized by topic/query. | Updated after information synthesis step. Read frequently to build upon existing knowledge. |

**B. Memory Bank Update Triggers and Maintenance Strategy:**

Maintaining the Memory Bank requires both automatic and potentially manual triggers.

* **Automatic Updates via .clinerules:** The primary mechanism for keeping the Memory Bank current is through rules defined in .clinerules-research-assistant. These rules should instruct the agent to update specific files after completing relevant tasks. For instance:  
  * After analyzing a user query, update activeContext.md and log the refined query in researchQueries.md.  
  * After retrieving and processing documents, update documentSummaries.md.  
  * After synthesizing information, update keyFindings.md and progress.md. The Memory Bank system aims for real-time synchronization 7, so these updates should reflect promptly in the files.  
* **Manual Updates (UMB Command):** The established "UMB" or "update memory bank" command 7 should be retained as a user-invoked fallback. This is useful for forcing a comprehensive synchronization before ending a session, after interruptions (like connection issues), or if the user suspects automatic updates might have missed something. The .clinerules should recognize this command and trigger a full review and update of all relevant Memory Bank files.  
* **Maintenance:** While the vector database holds the bulk knowledge, Memory Bank files can still grow. Periodically, the agent could be instructed (or rules defined) to summarize older sections of progress.md or decisionLog.md, or archive entries beyond a certain age or session count if performance becomes an issue. However, the primary focus should be on efficient retrieval rather than aggressive pruning.

**C. Persisting Findings and Metadata in Memory Bank:**

Storing information effectively requires a consistent format.

* **Format:** Use clear Markdown formatting. For keyFindings.md and documentSummaries.md, adopt a structured approach:  
  * *Summaries:* Use headings for each document (e.g., \#\# Summary: \[doc\_id\] \- Title), followed by the summary paragraph. Include the source\_uri.  
  * *Findings:* Use bullet points or numbered lists for individual findings. Each finding should clearly state the information and include inline citations referencing the source ID (e.g., \[doc\_id: 123, chunk\_id: 4\] or \`\`).  
* **Granularity:** The Memory Bank should store *synthesized* or *summarized* information, not raw retrieved chunks (which belong in the LLM's short-term context during synthesis). The goal is to capture the *essence* needed for ongoing context, reducing the need to constantly re-process raw data from the database.

**D. Efficient Memory Bank Retrieval Patterns:**

Loading the entire Memory Bank into every LLM prompt is inefficient.41 Retrieval must be targeted.

* **Context Loading:** The .clinerules must define which Memory Bank files are loaded by default when the Research Assistant mode starts or processes a new top-level query. Typically, this would include productContext.md, activeContext.md, and perhaps recent entries from keyFindings.md and researchQueries.md.20  
* **Targeted Reading:** Leverage RooCode's context mentions (@memory-bank/filename.md 5) within the .clinerules logic. Instruct the agent to specifically load only the files or sections relevant to the current sub-task. For example, before generating a database query, explicitly load @memory-bank/activeContext.md and @memory-bank/researchQueries.md.  
* **Summarization:** For potentially large files like progress.md or keyFindings.md, the .clinerules can implement a two-step process: first, instruct the LLM to read the relevant file and summarize the parts pertinent to the current query; second, use that summary, rather than the full file content, in the prompt for the main task (e.g., synthesis or query generation). This helps manage the context window size.41

A crucial function of this tailored Memory Bank is its role in **augmenting RAG queries**. The context stored—particularly in activeContext.md, researchQueries.md, and keyFindings.md—should be actively used by the agent when formulating queries for the PostgreSQL/pgvector database. Instead of just embedding the raw user query, the agent's .clinerules should instruct the LLM to construct a richer query embedding or add metadata filters based on this contextual memory. For example: "Considering the overall goal in productContext.md and the specific focus in activeContext.md, find document chunks related to '\[user query\]' that also mention concepts from keyFindings.md." This makes the retrieval step more targeted and relevant to the ongoing research narrative, moving beyond simple keyword or vector matching on the immediate query alone. However, this richer context comes at the cost of potentially larger Memory Bank files. It is vital to counteract the risk of **context bloat**.41 Loading multi-page Markdown files into every LLM interaction quickly exceeds context limits and increases costs. Therefore, the .clinerules must incorporate intelligent strategies for selective context loading and on-the-fly summarization of Memory Bank content, ensuring only the most relevant information is included in prompts for subsequent steps like database querying or final answer synthesis.

## **7\. VI. RooCode Configuration: .clinerules and .roomodes**

The behavior, persona, and operational logic of the custom Research Assistant mode are defined within RooCode's configuration files: .roomodes for the mode definition and .clinerules-research-assistant for the detailed rules and workflow.

**A. Crafting the .roomodes Entry for the Research Assistant:**

The .roomodes file, located in the project root 7, defines available agent modes. A new entry is required for the Research Assistant.

* **Structure and Content:**  
  * **name**: "Research Assistant" (User-facing name)  
  * **description**: "An AI assistant specialized in conducting research using a local knowledge base (PostgreSQL/pgvector) and online sources, synthesizing findings, and maintaining context via a Memory Bank."  
  * **baseMode**: Typically "code" or potentially "architect".5 The base mode provides default tool access, but this will be heavily customized by the mode-specific .clinerules. Choosing "code" might be a reasonable default.  
  * **roleDefinition**: A detailed prompt defining the agent's persona, capabilities, and core objective. This should be crafted carefully, drawing on best practices for agent instructions.56 Example excerpt: *"You are an expert AI Research Assistant operating within the RooCode framework. Your primary function is to assist users with research tasks by leveraging a persistent knowledge base stored in a PostgreSQL/pgvector database and accessing external web resources when necessary. You must understand complex queries, formulate effective search strategies (for both the database and the web), retrieve relevant information, critically evaluate sources, synthesize coherent and accurate answers with proper citations, and maintain research context using the project's Memory Bank (memory-bank/ directory). Adhere strictly to the operational rules defined in .clinerules-research-assistant."*  
  * **customInstructions**: This field can provide high-level, mode-wide instructions. However, for complex agents, it's often better to keep this minimal or empty 7 and define the detailed logic within the .clinerules file to avoid conflicting instructions. If used, it might outline the very top-level workflow steps.  
* **Example .roomodes Snippet (YAML format):**  
  YAML  
  modes:  
    \#... other modes...  
    \- name: Research Assistant  
      description: Conducts online and database research, synthesizes findings, manages a knowledge base.  
      baseMode: code  
      roleDefinition: |  
        You are an expert AI Research Assistant operating within the RooCode framework.  
        Your primary function is to assist users with research tasks by leveraging a  
        persistent knowledge base stored in a PostgreSQL/pgvector database and accessing  
        external web resources when necessary. You must understand complex queries,  
        formulate effective search strategies (for both the database and the web),  
        retrieve relevant information, critically evaluate sources, synthesize coherent  
        and accurate answers with proper citations, and maintain research context using  
        the project's Memory Bank (\`memory-bank/\` directory). Adhere strictly to the  
        operational rules defined in \`.clinerules-research-assistant\`.  
      customInstructions: "" \# Detailed logic in.clinerules

**B. Defining .clinerules-research-assistant Rules:**

This file, named .clinerules-research-assistant and placed in the project root 6, contains the core operational logic. It uses a YAML or similar structure to define rules that guide the agent's behavior step-by-step. These rules dictate workflow, tool usage, Memory Bank interactions, and decision-making.7

* **Key Rule Categories (Conceptual Examples):**  
  * **Initialization:**  
    * *Description:* Actions taken when the mode starts or receives the first query in a session.  
    * *Example Rule:* "On session start, read @memory-bank/productContext.md and @memory-bank/activeContext.md. If activeContext.md is empty or stale, prompt user for current research focus."  
  * **Query Analysis:**  
    * *Description:* Understanding the user's request and planning the approach.  
    * *Example Rule:* "Analyze user query. Identify keywords and entities. Check @memory-bank/researchQueries.md for similar past queries. Determine information type needed (e.g., definition, comparison, recent event, specific data point)."  
  * **Strategy Selection (RAG Trigger):**  
    * *Description:* Deciding whether to query the internal database, search the web, or use both.  
    * *Example Rule:* "IF query concerns recent events (e.g., past week) OR explicitly asks for online information OR analysis suggests information is unlikely to be in the ingested corpus, THEN prioritize web search. ELSE prioritize database query. Update @memory-bank/decisionLog.md with rationale."  
  * **Database Query Formulation:**  
    * *Description:* Constructing the semantic search query for PostgreSQL/pgvector.  
    * *Example Rule:* "Generate query embedding based on user query AND relevant context from @memory-bank/activeContext.md and @memory-bank/keyFindings.md. Construct SQL SELECT query using embedding \<=\> query\_embedding::vector ORDER BY distance LIMIT N. Include metadata filters if applicable. Invoke DB MCP tool query\_similar\_chunks with the SQL query."  
  * **Web Search Execution:**  
    * *Description:* Performing online searches.  
    * *Example Rule:* "Generate 3-5 concise search terms based on the query. Invoke Browser MCP tool search\_web with terms. Retrieve and parse text content from top 3-5 relevant results. Summarize each result briefly."  
  * **Information Synthesis:**  
    * *Description:* Combining retrieved information into a coherent answer.  
    * *Example Rule:* "Combine retrieved database chunks and web search summaries. Identify key points, resolve contradictions (prioritizing database sources if applicable, noting discrepancies). Generate a comprehensive answer addressing the user query. For every statement, include a citation marker linking to the source (e.g., or)."  
  * **Memory Bank Updates:**  
    * *Description:* Persisting context and findings after completing a step.  
    * *Example Rule:* "After synthesis, update @memory-bank/keyFindings.md with the main points and citations from the generated answer. Update @memory-bank/progress.md indicating query completion. Update @memory-bank/activeContext.md if the focus shifts."  
  * **Tool Permissions:**  
    * *Description:* Explicitly defining allowed tools for this mode.  
    * *Example Rule (Conceptual Structure):*  
      YAML  
      allowed\_tools:  
        \- db\_mcp\_server/query\_similar\_chunks  
        \- db\_mcp\_server/get\_document\_metadata  
        \- browser\_mcp/search\_web  
        \- browser\_mcp/fetch\_url\_content  
        \# Allow tools needed for ingestion if this mode handles it  
        \- filesystem\_mcp/read\_file  
        \- shell\_mcp/execute\_command \# For calling processing scripts  
        \# Disallow general file writing or dangerous commands

  * **Pre-Completion Verification:**  
    * *Description:* Performing checks before presenting the answer to the user.  
    * *Example Rule:* "Before displaying the final synthesized answer: Verify all citations are present and correctly formatted. Check for logical consistency within the answer. If confidence is low or ambiguity remains based on retrieved context, state this limitation to the user or ask for clarification."  
* **Table 6: .clinerules-research-assistant Key Rules**

| Rule Category | Description | Example Rule Snippet (Conceptual) |
| :---- | :---- | :---- |
| Initialization | Load initial context at session start. | On session\_start: read @memory-bank/productContext.md, @memory-bank/activeContext.md |
| Query Analysis | Understand query, check history. | Analyze query \-\> identify keywords, intent. Check @memory-bank/researchQueries.md. |
| RAG Trigger (DB vs Web) | Decide retrieval strategy based on query type. | IF query\_is\_recent\_event OR query\_needs\_online\_source THEN prioritize\_web\_search ELSE prioritize\_db\_query. Log decision in @memory-bank/decisionLog.md. |
| Database Query Formulation | Generate embedding \+ SQL, call DB MCP tool. | Generate embedding(query \+ context from @memory-bank/activeContext.md). Construct SQL for vector search. Call db\_mcp\_server/query\_similar\_chunks. |
| Web Search Execution | Generate search terms, call Browser MCP tool, parse results. | Generate search terms. Call browser\_mcp/search\_web. Parse top N results. |
| Information Synthesis | Combine DB/Web results, generate cited answer. | Synthesize answer from retrieved\_db\_chunks and parsed\_web\_results. Ensure all claims are cited or. |
| Memory Bank Update (Findings) | Store synthesized findings and update progress. | Update @memory-bank/keyFindings.md with synthesized points \+ citations. Update @memory-bank/progress.md. |
| Pre-Completion Verification | Check answer consistency, citation validity before output. | Verify citations in synthesized\_answer. Check for internal consistency. If low\_confidence, add disclaimer or ask\_clarification. |

**C. Memory Bank Initialization and Update Flow Configuration:**

The .clinerules file orchestrates the interaction with the Memory Bank throughout the agent's lifecycle.

* **Initialization:** The rules should include logic, similar to existing Memory Bank implementations 7, to check for the existence of the memory-bank/ directory and its core files when the Research Assistant mode is activated for the first time in a project. If missing, the rules should guide the agent (potentially switching temporarily to Code mode) to create the directory and initialize the essential files (activeContext.md, productContext.md, etc.).  
* **Update Flow:** The rules explicitly define *when* and *what* gets written to the Memory Bank files. As outlined in the rule examples above, specific steps in the RAG workflow (query analysis, retrieval, synthesis) trigger updates to corresponding files (researchQueries.md, documentSummaries.md, keyFindings.md, progress.md, activeContext.md). This ensures the Memory Bank reflects the current state and accumulated knowledge of the research process.

The .clinerules file serves as the **agent's operational "brain"**. While .roomodes sets the stage (persona, high-level goal), the .clinerules file encodes the intricate step-by-step logic, decision-making processes, RAG strategies, tool invocation conditions, and Memory Bank interaction protocols.20 The quality, detail, and robustness of these rules directly dictate the Research Assistant's effectiveness, reliability, and adherence to the intended workflow. Crafting these rules is a critical engineering task.

Furthermore, defining a perfect set of .clinerules from the outset is highly unlikely for a complex task like RAG-based research. The agent's behavior in response to diverse queries and information sources can be complex and sometimes unexpected.4 Therefore, the development process must anticipate **iterative refinement**. This involves defining an initial set of rules, rigorously testing the agent with various research scenarios, carefully observing its actions and outputs (especially its decisions and Memory Bank updates), identifying shortcomings or errors, and then refining the .clinerules accordingly. This feedback loop is essential for tuning the agent's performance and ensuring it behaves as intended.

## **8\. VII. Optimization and Security Considerations**

Deploying a capable RAG Research Assistant requires attention to both performance optimization (minimizing latency and cost) and security (protecting credentials and system integrity).

**A. Strategies for Minimizing API Calls and Latency:**

* **Efficient RAG Retrieval:** Optimize database queries. Combine vector similarity search (\<-\> or \<=\>) with traditional SQL WHERE clauses filtering on metadata stored in the documents or chunks tables (e.g., publication date range, specific authors, keywords in metadata\_jsonb). This retrieves fewer, more relevant chunks, reducing the amount of context passed to the LLM for synthesis.  
* **Memory Bank Caching:** Actively use the proposed Memory Bank files (documentSummaries.md, sourceMetadataCache.md) to cache frequently needed information. Storing summaries avoids re-synthesizing, and caching metadata avoids repeated database lookups for citation details. This reduces calls to both the LLM and the database.  
* **LLM Prompt Optimization:** Craft prompts for synthesis and analysis that are concise and clear. Avoid unnecessarily verbose instructions. Implement the Memory Bank summarization strategy to condense context from large Memory Bank files before including it in LLM prompts.41  
* **Batching:** Consistently apply batching for database insertions (execute\_values 35) and embedding generation API calls to improve throughput during document ingestion.  
* **MCP Tool Caching:** If using MCP servers whose tool lists are static, enable MCP's built-in caching mechanism (cache\_tools\_list=True in the MCP server configuration 58) to avoid redundant list\_tools() calls on each agent run, reducing latency, especially for remote MCP servers.

**B. Security Best Practices for Credentials and Command Execution:**

Integrating external databases, APIs, and command-line tools introduces security risks that must be mitigated.

* **Credential Management:**  
  * **NEVER** hardcode API keys (OpenAI, etc.) or database credentials in agent code, scripts, or configuration files.40  
  * **Use Environment Variables via MCP Config:** The recommended approach is to configure the custom MCP servers (Database, potentially others needing keys) to read credentials from environment variables.31 Pass these variables securely from RooCode's MCP settings (cline\_mcp\_settings.json or .roo/mcp.json) using the env property.29 Manage the actual secret values outside of version control (e.g., system environment variables, .env files ignored by git, dedicated secrets management tools like HashiCorp Vault or Infisical 40).  
* **Command Execution Security:**  
  * **Prefer MCP Servers:** Use dedicated, purpose-built MCP servers (Database, Shell, Filesystem) over direct, open-ended terminal access whenever possible. MCP provides better encapsulation and control.  
  * **Shell MCP Whitelisting:** If using a Shell MCP server, configure and strictly enforce command whitelisting.24 Classify commands as Safe, Requires Approval, or Forbidden. Minimize the number of commands requiring approval and forbid dangerous ones entirely.  
  * **Filesystem Access Control:** Configure Filesystem MCP servers to operate only within designated, non-sensitive directories using allowed\_paths 42 or FS\_BASE\_DIRECTORY 43 settings.  
  * **Limit Auto-Approval:** Avoid excessive use of RooCode's auto-approval setting 5 for agent actions, especially those involving file system modification, command execution, or database writes. Require explicit user confirmation for potentially risky operations.  
  * **Input Sanitization:** Ensure that any user input or data retrieved from external sources that might be used to construct file paths, shell commands, or SQL queries is rigorously sanitized to prevent injection attacks. Robust MCP servers should handle this internally.43  
  * **Containerization (Isolation):** Consider running the RooCode agent, its associated MCP servers, and processing scripts within a containerized environment (e.g., Docker via VS Code DevContainers 59). This isolates the agent and its potentially unpredictable actions 59 from the host operating system, significantly mitigating the risk of accidental damage (e.g., rm \-rf) or resource exhaustion.

It is important to recognize the inherent **trade-offs between performance and accuracy**. Techniques like caching information in the Memory Bank or using Approximate Nearest Neighbor (ANN) indexes (like HNSW or IVFFlat 14) in pgvector can significantly improve response times and reduce costs. However, caching introduces the risk of using stale data if the underlying source (database or web) has changed. ANN search, by definition, trades perfect recall for speed, meaning it might occasionally miss the absolute most relevant document chunk.14 The acceptable balance between speed and accuracy/freshness must be determined based on the specific requirements of the research tasks the agent is designed for.

Furthermore, **security must be approached holistically**. Protecting database credentials 31 is vital, but it's only one piece of the puzzle. A comprehensive security strategy must address all points of interaction: securing command execution via whitelisting and limited permissions 24, controlling file system access through restricted paths 42, managing API keys for LLMs and embedding services, and potentially isolating the entire agent environment using techniques like containerization.59 Applying defense-in-depth across all these areas is crucial for building a trustworthy and safe Research Assistant.

## **9\. Conclusion**

Summary of Implementation:  
This report has detailed a comprehensive approach for building an advanced RAG Research Assistant as a custom RooCode agent mode. The core strategy involves defining a dedicated research-assistant mode in .roomodes, encoding its operational logic within .clinerules-research-assistant, and leveraging the Model Context Protocol (MCP) as the central integration point. Key implementation steps include:

1. Setting up a local PostgreSQL database with the pgvector extension enabled.  
2. Designing an appropriate database schema (documents, chunks tables) for storing research data and embeddings.  
3. Developing or configuring a custom Database MCP server for secure and efficient interaction with PostgreSQL/pgvector, including batch insertion capabilities.  
4. Implementing a document processing pipeline using external command-line tools (for text extraction) and Python scripts (for chunking and embedding generation), invoked via RooCode's terminal/Shell MCP with careful environment management.  
5. Adapting the RooCode Memory Bank structure with research-specific files (researchQueries.md, documentSummaries.md, keyFindings.md) to maintain session context and augment retrieval.  
6. Crafting detailed .clinerules to orchestrate the RAG workflow: query analysis, strategy selection (DB vs. web), tool invocation, information synthesis with citation, and Memory Bank updates.  
7. Implementing security best practices for credential management and command/filesystem access, and applying optimization techniques to manage latency and API usage.

Capabilities Achieved:  
The resulting Research Assistant, operating within the RooCode VS Code extension, possesses significant capabilities:

* **Persistent Knowledge Base:** Maintains a searchable, private knowledge base of research documents within the local PostgreSQL/pgvector database.  
* **Hybrid Retrieval:** Intelligently queries both the internal database and external web sources based on the user's query.  
* **Contextual Understanding:** Utilizes the adapted Memory Bank to maintain context across multi-turn research sessions, informing queries and synthesis.  
* **Automated Processing:** Can ingest and process new documents (PDF, EPUB, etc.) into the knowledge base via the defined pipeline.  
* **Cited Synthesis:** Generates coherent answers based on retrieved evidence, providing citations back to the original sources.

Future Considerations:  
This architecture provides a strong foundation that can be extended further:

* **Agentic Planning:** Enhance the .clinerules or leverage frameworks like LangGraph 60 or AutoGen 61 (potentially via MCP integration) to implement more sophisticated, multi-step planning and self-correction capabilities, moving towards more autonomous agentic RAG.9  
* **Knowledge Graph Integration:** Augment the vector database with a knowledge graph (potentially using tools like txtai 62 or dedicated graph MCP servers 28) to represent and query relationships between entities found in the research documents.  
* **User Interface Enhancements:** Explore ways to present research results more effectively within the VS Code interface, potentially beyond simple chat messages (e.g., structured summaries, interactive citation links).  
* **Advanced Document Analysis:** Integrate more sophisticated NLP tools (via MCP or scripts) for tasks like entity recognition, relationship extraction, or automated summarization during the ingestion phase.

Final Thoughts:  
Building a specialized AI assistant like this RAG researcher demonstrates the power and flexibility of the RooCode framework, particularly its emphasis on extensibility through the Model Context Protocol and custom agent modes. While the integration of external databases and complex workflows presents challenges related to security and environment management, the patterns outlined in this report provide a viable path for creating highly capable, context-aware agents tailored to specific domain tasks directly within the developer's primary workspace. The key lies in careful architectural design, robust MCP implementation, and meticulous configuration of the agent's operational rules.

#### **Works cited**

1. Roo Code (prev. Roo Cline) gives you a whole dev team of AI agents in your code editor. \- GitHub, accessed April 15, 2025, [https://github.com/RooVetGit/Roo-Code](https://github.com/RooVetGit/Roo-Code)  
2. I want to get better at AI assisted development. Recommend me resources to learn from. : r/RooCode \- Reddit, accessed April 15, 2025, [https://www.reddit.com/r/RooCode/comments/1iuruxm/i\_want\_to\_get\_better\_at\_ai\_assisted\_development/](https://www.reddit.com/r/RooCode/comments/1iuruxm/i_want_to_get_better_at_ai_assisted_development/)  
3. How to Use RooCode Boomerang AI Agent for Free with Gemini 2.5 Pro API \- Apidog, accessed April 15, 2025, [https://apidog.com/blog/roocode-boomerang-ai-agent/](https://apidog.com/blog/roocode-boomerang-ai-agent/)  
4. Automating a Data Science Project with RooCode and GitHub Copilot: Step-by-Step Guide, accessed April 15, 2025, [https://www.tanyongsheng.com/blog/automating-a-data-science-project-with-roocode-and-github-copilot-step-by-step-guide/](https://www.tanyongsheng.com/blog/automating-a-data-science-project-with-roocode-and-github-copilot-step-by-step-guide/)  
5. Roo-Code/README.md at main · qpd-v/Roo-Code · GitHub, accessed April 15, 2025, [https://github.com/qpd-v/Roo-Code/blob/main/README.md](https://github.com/qpd-v/Roo-Code/blob/main/README.md)  
6. How I Effectively Use Roo Code for AI-Assisted Development \- Atomic Spin, accessed April 15, 2025, [https://spin.atomicobject.com/roo-code-ai-assisted-development/](https://spin.atomicobject.com/roo-code-ai-assisted-development/)  
7. roo-code-memory-bank/README.md at main · GreatScottyMac/roo ..., accessed April 15, 2025, [https://github.com/GreatScottyMac/roo-code-memory-bank/blob/main/README.md](https://github.com/GreatScottyMac/roo-code-memory-bank/blob/main/README.md)  
8. All-in-one default mode for basic roocode setup \- Reddit, accessed April 15, 2025, [https://www.reddit.com/r/RooCode/comments/1jrnal4/allinone\_default\_mode\_for\_basic\_roocode\_setup/](https://www.reddit.com/r/RooCode/comments/1jrnal4/allinone_default_mode_for_basic_roocode_setup/)  
9. ai-agents-for-beginners/05-agentic-rag/README.md at main \- GitHub, accessed April 15, 2025, [https://github.com/microsoft/ai-agents-for-beginners/blob/main/05-agentic-rag/README.md](https://github.com/microsoft/ai-agents-for-beginners/blob/main/05-agentic-rag/README.md)  
10. How to Use MCP Servers with Roo Code (within VSCode) \- Apidog, accessed April 15, 2025, [https://apidog.com/blog/mcp-server-roo-code/](https://apidog.com/blog/mcp-server-roo-code/)  
11. Browser Tools MCP with RooCode \- Reddit, accessed April 15, 2025, [https://www.reddit.com/r/RooCode/comments/1j9zant/browser\_tools\_mcp\_with\_roocode/](https://www.reddit.com/r/RooCode/comments/1j9zant/browser_tools_mcp_with_roocode/)  
12. RAG app with Postgres and pgvector \- EDB, accessed April 15, 2025, [https://www.enterprisedb.com/blog/rag-app-postgres-and-pgvector](https://www.enterprisedb.com/blog/rag-app-postgres-and-pgvector)  
13. PostgreSQL as a Vector Database: Create, Store, and Query OpenAI Embeddings With pgvector | Timescale, accessed April 15, 2025, [https://www.timescale.com/blog/postgresql-as-a-vector-database-create-store-and-query-openai-embeddings-with-pgvector](https://www.timescale.com/blog/postgresql-as-a-vector-database-create-store-and-query-openai-embeddings-with-pgvector)  
14. pgvector/pgvector: Open-source vector similarity search for Postgres \- GitHub, accessed April 15, 2025, [https://github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)  
15. PDF to Text Command Line: Windows, Linux, macOS | Apryse documentation, accessed April 15, 2025, [https://docs.apryse.com/cli/guides/pdf2text](https://docs.apryse.com/cli/guides/pdf2text)  
16. VeryPDF PDF to Text Command Line Extraction for Windows, Linux and Mac Developers Royalty Free, accessed April 15, 2025, [https://www.verypdf.com/wordpress/202407/verypdf-pdf-to-text-command-line-extraction-47938.html](https://www.verypdf.com/wordpress/202407/verypdf-pdf-to-text-command-line-extraction-47938.html)  
17. ghostscript \- PDF text extraction from given coordinates \- Stack Overflow, accessed April 15, 2025, [https://stackoverflow.com/questions/6187250/pdf-text-extraction-from-given-coordinates](https://stackoverflow.com/questions/6187250/pdf-text-extraction-from-given-coordinates)  
18. How can I convert .epub files to plain text? \- Ask Ubuntu, accessed April 15, 2025, [https://askubuntu.com/questions/102458/how-can-i-convert-epub-files-to-plain-text](https://askubuntu.com/questions/102458/how-can-i-convert-epub-files-to-plain-text)  
19. Community Projects | Roo Code Docs, accessed April 15, 2025, [https://docs.roocode.com/community/](https://docs.roocode.com/community/)  
20. roo-code-memory-bank/developer-primer.md at main \- GitHub, accessed April 15, 2025, [https://github.com/GreatScottyMac/roo-code-memory-bank/blob/main/developer-primer.md](https://github.com/GreatScottyMac/roo-code-memory-bank/blob/main/developer-primer.md)  
21. GreatScottyMac/roo-code-memory-bank \- GitHub, accessed April 15, 2025, [https://github.com/GreatScottyMac/roo-code-memory-bank](https://github.com/GreatScottyMac/roo-code-memory-bank)  
22. Browser Automation MCP Server \- Glama, accessed April 15, 2025, [https://glama.ai/mcp/servers/3o1j64rc1q](https://glama.ai/mcp/servers/3o1j64rc1q)  
23. Extracting plain text from EPUB \[closed\] \- Software Recommendations Stack Exchange, accessed April 15, 2025, [https://softwarerecs.stackexchange.com/questions/56103/extracting-plain-text-from-epub](https://softwarerecs.stackexchange.com/questions/56103/extracting-plain-text-from-epub)  
24. Super Shell MCP Server | Glama, accessed April 15, 2025, [https://glama.ai/mcp/servers/@cfdude/super-shell-mcp?](https://glama.ai/mcp/servers/@cfdude/super-shell-mcp)  
25. mcp-server-filesystem – MCP servers | Glama, accessed April 15, 2025, [https://glama.ai/mcp/servers?query=mcp-server-filesystem](https://glama.ai/mcp/servers?query=mcp-server-filesystem)  
26. Tell me how you do this \- struggling with python dependencies : r/RooCode \- Reddit, accessed April 15, 2025, [https://www.reddit.com/r/RooCode/comments/1jycs91/tell\_me\_how\_you\_do\_this\_struggling\_with\_python/](https://www.reddit.com/r/RooCode/comments/1jycs91/tell_me_how_you_do_this_struggling_with_python/)  
27. How can I run a python script using Anaconda from the command line?, accessed April 15, 2025, [https://unix.stackexchange.com/questions/300128/how-can-i-run-a-python-script-using-anaconda-from-the-command-line](https://unix.stackexchange.com/questions/300128/how-can-i-run-a-python-script-using-anaconda-from-the-command-line)  
28. Server Memory – MCP servers | Glama, accessed April 15, 2025, [https://glama.ai/mcp/servers?query=Server+Memory](https://glama.ai/mcp/servers?query=Server+Memory)  
29. Example Servers \- Model Context Protocol, accessed April 15, 2025, [https://modelcontextprotocol.io/examples](https://modelcontextprotocol.io/examples)  
30. sdimitrov/mcp-memory: MCP Memory Server with ... \- GitHub, accessed April 15, 2025, [https://github.com/sdimitrov/mcp-memory](https://github.com/sdimitrov/mcp-memory)  
31. SurrealDB MCP Server | Glama, accessed April 15, 2025, [https://glama.ai/mcp/servers/@nsxdavid/surrealdb-mcp-server?locale=en-US](https://glama.ai/mcp/servers/@nsxdavid/surrealdb-mcp-server?locale=en-US)  
32. pgvector Tutorial: Integrate Vector Search into PostgreSQL \- DataCamp, accessed April 15, 2025, [https://www.datacamp.com/tutorial/pgvector-tutorial](https://www.datacamp.com/tutorial/pgvector-tutorial)  
33. Using Pgvector With Python \- Timescale, accessed April 15, 2025, [https://www.timescale.com/learn/using-pgvector-with-python](https://www.timescale.com/learn/using-pgvector-with-python)  
34. pgvector support for Python \- GitHub, accessed April 15, 2025, [https://github.com/pgvector/pgvector-python](https://github.com/pgvector/pgvector-python)  
35. Psycopg2, Postgresql, Python: Fastest way to bulk-insert \- Stack Overflow, accessed April 15, 2025, [https://stackoverflow.com/questions/2271787/psycopg2-postgresql-python-fastest-way-to-bulk-insert](https://stackoverflow.com/questions/2271787/psycopg2-postgresql-python-fastest-way-to-bulk-insert)  
36. Move MCP creation from system prompt to agent/tool or MCP server · RooVetGit Roo-Code · Discussion \#558 \- GitHub, accessed April 15, 2025, [https://github.com/RooVetGit/Roo-Code/discussions/558](https://github.com/RooVetGit/Roo-Code/discussions/558)  
37. Trouble getting any MCP servers to work in Roo : r/RooCode \- Reddit, accessed April 15, 2025, [https://www.reddit.com/r/RooCode/comments/1juc3am/trouble\_getting\_any\_mcp\_servers\_to\_work\_in\_roo/](https://www.reddit.com/r/RooCode/comments/1juc3am/trouble_getting_any_mcp_servers_to_work_in_roo/)  
38. Provide a standard and fast way to execute a command inside an environment · Issue \#2379, accessed April 15, 2025, [https://github.com/conda/conda/issues/2379](https://github.com/conda/conda/issues/2379)  
39. how can i automatically run my python script in a virtualenv? \- Reddit, accessed April 15, 2025, [https://www.reddit.com/r/learnpython/comments/sfpwxr/how\_can\_i\_automatically\_run\_my\_python\_script\_in\_a/](https://www.reddit.com/r/learnpython/comments/sfpwxr/how_can_i_automatically_run_my_python_script_in_a/)  
40. Managing Secrets in MCP Servers \- Infisical, accessed April 15, 2025, [https://infisical.com/blog/managing-secrets-mcp-servers](https://infisical.com/blog/managing-secrets-mcp-servers)  
41. Working with Large Projects | Roo Code Docs, accessed April 15, 2025, [https://docs.roocode.com/advanced-usage/large-projects/](https://docs.roocode.com/advanced-usage/large-projects/)  
42. Go server implementing Model Context Protocol (MCP) for filesystem operations. \- GitHub, accessed April 15, 2025, [https://github.com/mark3labs/mcp-filesystem-server](https://github.com/mark3labs/mcp-filesystem-server)  
43. cyanheads/filesystem-mcp-server: A Model Context Protocol (MCP) server for platform-agnostic file capabilities, including advanced search/replace and directory tree traversal \- GitHub, accessed April 15, 2025, [https://github.com/cyanheads/filesystem-mcp-server](https://github.com/cyanheads/filesystem-mcp-server)  
44. bsmi021/mcp-filesystem-server: A Model Context Protocol server for accessing your file system. \- GitHub, accessed April 15, 2025, [https://github.com/bsmi021/mcp-filesystem-server](https://github.com/bsmi021/mcp-filesystem-server)  
45. Cross-platform, Command line utilities to convert PDF, DOC and DOCX to text \- Super User, accessed April 15, 2025, [https://superuser.com/questions/316157/cross-platform-command-line-utilities-to-convert-pdf-doc-and-docx-to-text](https://superuser.com/questions/316157/cross-platform-command-line-utilities-to-convert-pdf-doc-and-docx-to-text)  
46. Make existing PDF searchable ( OCR ) via command line / script \- Apple StackExchange, accessed April 15, 2025, [https://apple.stackexchange.com/questions/76471/make-existing-pdf-searchable-ocr-via-command-line-script](https://apple.stackexchange.com/questions/76471/make-existing-pdf-searchable-ocr-via-command-line-script)  
47. Top 7 Linux Optical Character Recognition (OCR) Tools in 2025 \- Wondershare EdrawMind, accessed April 15, 2025, [https://edrawmind.wondershare.com/productivity-improvement/7-best-ocr-tools-for-linux.html](https://edrawmind.wondershare.com/productivity-improvement/7-best-ocr-tools-for-linux.html)  
48. Download Windows Command-line PDF Tools \- Apryse documentation, accessed April 15, 2025, [https://docs.apryse.com/cli/guides/download](https://docs.apryse.com/cli/guides/download)  
49. kevinboone/epub2txt2: A simple command-line utility for Linux, for extracting text from EPUB documents. \- GitHub, accessed April 15, 2025, [https://github.com/kevinboone/epub2txt2](https://github.com/kevinboone/epub2txt2)  
50. Text processing on the Command Line \- sharing my tools, accessed April 15, 2025, [https://proycon.anaproy.nl/posts/my-cli-tools-for-text-processing/](https://proycon.anaproy.nl/posts/my-cli-tools-for-text-processing/)  
51. Python Script execute commands in Terminal \[duplicate\] \- Stack Overflow, accessed April 15, 2025, [https://stackoverflow.com/questions/3730964/python-script-execute-commands-in-terminal](https://stackoverflow.com/questions/3730964/python-script-execute-commands-in-terminal)  
52. PGVector \- ️ LangChain, accessed April 15, 2025, [https://python.langchain.com/docs/integrations/vectorstores/pgvector/](https://python.langchain.com/docs/integrations/vectorstores/pgvector/)  
53. Local AI Coding in VS Code: Installing Llama 3 with continue.dev & Ollama \- YouTube, accessed April 15, 2025, [https://www.youtube.com/watch?v=AV\_8czoF3PU](https://www.youtube.com/watch?v=AV_8czoF3PU)  
54. \[Poweruser Guide\] Level Up Your RooCode: Become a Roo Poweruser\! \[Memory Bank\] \- Reddit, accessed April 15, 2025, [https://www.reddit.com/r/RooCode/comments/1jfx9mk/poweruser\_guide\_level\_up\_your\_roocode\_become\_a/](https://www.reddit.com/r/RooCode/comments/1jfx9mk/poweruser_guide_level_up_your_roocode_become_a/)  
55. RooMode is here\! \- 3.3.20 Patch Notes for Roo Code : r/RooCode \- Reddit, accessed April 15, 2025, [https://www.reddit.com/r/RooCode/comments/1ips7uq/roomode\_is\_here\_3320\_patch\_notes\_for\_roo\_code/](https://www.reddit.com/r/RooCode/comments/1ips7uq/roomode_is_here_3320_patch_notes_for_roo_code/)  
56. Agent Crafter: An agent to help build other agents in CS Agent Builder : r/microsoft\_365\_copilot \- Reddit, accessed April 15, 2025, [https://www.reddit.com/r/microsoft\_365\_copilot/comments/1jwhn0o/agent\_crafter\_an\_agent\_to\_help\_build\_other\_agents/](https://www.reddit.com/r/microsoft_365_copilot/comments/1jwhn0o/agent_crafter_an_agent_to_help_build_other_agents/)  
57. How to Use Cursor Agent Mode \- Apidog, accessed April 15, 2025, [https://apidog.com/blog/how-to-use-cursor-agent-mode](https://apidog.com/blog/how-to-use-cursor-agent-mode)  
58. Model context protocol (MCP) \- OpenAI Agents SDK, accessed April 15, 2025, [https://openai.github.io/openai-agents-python/mcp/](https://openai.github.io/openai-agents-python/mcp/)  
59. Isolating AI Agents with DevContainer: A secure and scalable approach \- DEV Community, accessed April 15, 2025, [https://dev.to/siddhantkcode/isolating-ai-agents-with-devcontainer-a-secure-and-scalable-approach-4hi4](https://dev.to/siddhantkcode/isolating-ai-agents-with-devcontainer-a-secure-and-scalable-approach-4hi4)  
60. Roo Custom Modes : r/aiagents \- Reddit, accessed April 15, 2025, [https://www.reddit.com/r/aiagents/comments/1jwh770/roo\_custom\_modes/](https://www.reddit.com/r/aiagents/comments/1jwh770/roo_custom_modes/)  
61. Command Line Code Executor | AutoGen 0.2 \- Microsoft Open Source, accessed April 15, 2025, [https://microsoft.github.io/autogen/0.2/docs/topics/code-execution/cli-code-executor/](https://microsoft.github.io/autogen/0.2/docs/topics/code-execution/cli-code-executor/)  
62. Build a knowledge base into a tar.gz and give it to this MCP server, and it is ready to serve. \- GitHub, accessed April 15, 2025, [https://github.com/Geeksfino/kb-mcp-server](https://github.com/Geeksfino/kb-mcp-server)