import json
import logging
import sys
from typing import Optional, List, Dict, Any

import httpx
import typer
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax

from .. import config # Assuming config is accessible

# --- CLI Setup ---
app = typer.Typer(help="PhiloGraph Command Line Interface")
console = Console()
error_console = Console(stderr=True, style="bold red")

logger = logging.getLogger(__name__)
# Configure basic logging for CLI (can be enhanced)
logging.basicConfig(level=config.LOG_LEVEL, format='%(asctime)s - CLI - %(levelname)s - %(message)s')

# --- Helper Functions ---

def make_api_request(method: str, endpoint: str, json_data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Any:
    """Makes a synchronous HTTP request to the backend API."""
    # TDD: Test successful GET request
    # TDD: Test successful POST request with JSON data
    # TDD: Test handling of API connection errors
    # TDD: Test handling of non-2xx HTTP status codes from API
    # TDD: Test handling of JSON decoding errors from API response
    url = f"{config.API_URL}{endpoint}"
    logger.debug(f"Making API request: {method} {url}")
    try:
        # Use synchronous httpx client for CLI simplicity
        with httpx.Client(timeout=60.0) as client: # Longer timeout for potentially long ops like ingest
            response = client.request(method, url, json=json_data, params=params)
            response.raise_for_status() # Raise exception for 4xx/5xx errors
            try:
                return response.json()
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON response from {url}. Status: {response.status_code}. Response text: {response.text[:500]}...")
                error_console.print(f"Error: Invalid response format received from server (Status: {response.status_code}).")
                raise typer.Exit(code=1)
    except httpx.ConnectError as e:
        logger.error(f"Connection error calling API endpoint {url}: {e}")
        error_console.print(f"Error: Could not connect to the PhiloGraph backend at {config.API_URL}.")
        error_console.print("Please ensure the backend service is running.")
        raise typer.Exit(code=1)
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling API endpoint {url}: {e.response.status_code} - {e.response.text[:500]}...")
        try:
            error_detail = e.response.json().get('detail', e.response.text)
        except json.JSONDecodeError:
            error_detail = e.response.text
        error_console.print(f"Error from server ({e.response.status_code}): {error_detail}")
        raise typer.Exit(code=1)
    except Exception as e:
        # Avoid logging/printing generic message if it's a planned exit
        if not isinstance(e, typer.Exit):
            logger.exception(f"Unexpected error calling API endpoint {url}", exc_info=e)
            error_console.print(f"An unexpected error occurred: {e}")
            raise typer.Exit(code=1) # Re-raise typer.Exit for unexpected errors
        else:
            raise # Re-raise the original typer.Exit if it was planned (e.g., from JSONDecodeError)

def display_results(data: Any):
    """Formats and prints data nicely for the console using Rich."""
    # TDD: Test display of search results list
    # TDD: Test display of single document details
    # TDD: Test display of collection items
    # TDD: Test display of simple messages
    # TDD: Test display of directory ingestion summary
    if isinstance(data, dict) and "results" in data and isinstance(data["results"], list):
        # Handle Search Results
        table = Table(title="Search Results", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Text Snippet")
        table.add_column("Source", style="cyan")
        table.add_column("Dist.", style="yellow", justify="right")

        for item in data["results"]:
            snippet = item.get("text", "")[:150] + "..." if len(item.get("text", "")) > 150 else item.get("text", "")
            source_doc = item.get("source_document", {})
            source_info = f"{source_doc.get('title', 'N/A')} ({source_doc.get('author', 'N/A')}, {source_doc.get('year', 'N/A')}) [DocID: {source_doc.get('doc_id')}]"
            distance = f"{item.get('distance', float('inf')):.4f}"
            table.add_row(str(item.get("chunk_id")), snippet, source_info, distance)
        console.print(table)

    elif isinstance(data, dict) and "document_id" in data and "status" in data and data["status"] != "Directory Processed":
        # Handle single document ingestion/retrieval/creation confirmation
        console.print(f"[bold green]Success:[/bold green] {data.get('message', 'Operation successful.')}")
        if data.get("document_id"):
            console.print(f"Document ID: {data['document_id']}")
        # Print other details if needed

    elif isinstance(data, dict) and "status" in data and data["status"] == "Directory Processed":
         # Handle directory ingestion summary
         console.print(f"[bold blue]Info:[/bold blue] {data.get('message', 'Directory processing summary:')}")
         if data.get("details"):
             # Optionally print details for each file
             pass # Keep summary concise for now

    elif isinstance(data, dict) and "collection_id" in data and "items" in data:
         # Handle Get Collection Items
         table = Table(title=f"Items in Collection {data['collection_id']}", show_header=True, header_style="bold magenta")
         table.add_column("Item Type", style="cyan")
         table.add_column("Item ID", style="dim")
         for item in data["items"]:
             table.add_row(item.get("item_type"), str(item.get("item_id")))
         console.print(table)

    elif isinstance(data, dict) and "message" in data:
         # Handle simple status messages (e.g., add to collection)
         console.print(f"[bold green]Success:[/bold green] {data['message']}")
         if data.get("collection_id"):
             console.print(f"Collection ID: {data['collection_id']}")

    elif isinstance(data, list):
         # Generic list display
         console.print(data) # Rich handles basic list printing well

    elif isinstance(data, dict):
         # Generic dictionary display (pretty print JSON)
         syntax = Syntax(json.dumps(data, indent=2), "json", theme="default", line_numbers=False)
         console.print(syntax)
    else:
        # Fallback for other types
        console.print(data)


# --- CLI Commands ---

@app.command()
def ingest(
    path: str = typer.Argument(..., help="Path to the file or directory (relative to configured source directory).")
):
    """
    Ingest a document or directory into PhiloGraph.
    """
    # TDD: Test calling API /ingest endpoint with correct path
    # TDD: Test displaying success message from API
    # TDD: Test displaying error message from API
    logger.info(f"CLI: Initiating ingestion for path: {path}")
    console.print(f"Requesting ingestion for: {path}...")
    response_data = make_api_request("POST", "/ingest", json_data={"path": path})
    display_results(response_data)

@app.command()
def search(
    query: str = typer.Argument(..., help="The search query text."),
    author: Optional[str] = typer.Option(None, "--author", "-a", help="Filter results by author (case-insensitive)."),
    year: Optional[int] = typer.Option(None, "--year", "-y", help="Filter results by publication year."),
    doc_id: Optional[int] = typer.Option(None, "--doc-id", "-d", help="Filter results by source document ID."),
    limit: int = typer.Option(config.SEARCH_TOP_K, "--limit", "-l", help="Maximum number of results to return.")
):
    """
    Search for text chunks in PhiloGraph.
    """
    # TDD: Test calling API /search with query only
    # TDD: Test calling API /search with query and author filter
    # TDD: Test calling API /search with query and year filter
    # TDD: Test calling API /search with query and doc_id filter
    # TDD: Test calling API /search with limit parameter
    # TDD: Test displaying formatted search results
    logger.info(f"CLI: Searching for query: '{query[:50]}...' with filters...")
    filters = {}
    if author: filters['author'] = author
    if year: filters['year'] = year
    if doc_id: filters['doc_id'] = doc_id

    # Prepare parameters for GET request
    # Prepare JSON payload for POST request
    payload = {"query": query, "limit": limit}
    if filters:
        payload['filters'] = filters # Send filters as a dictionary object

    console.print(f"Searching for '{query}'...")
    # Use POST request with JSON payload
    response_data = make_api_request("POST", "/search", json_data=payload)
    # The API is expected to return a dict with a 'results' key containing a list
    if isinstance(response_data, dict) and "results" in response_data and isinstance(response_data["results"], list):
        results = response_data["results"]
        if not results:
            console.print("No results found.")
        else:
            # Pass the list of results to display_results
            display_results({"results": results}) # Wrap in dict for display_results
    elif response_data is None: # Handle case where make_api_request returns None due to error handled internally
        # Error already printed by make_api_request, just exit
        pass # typer.Exit already raised in make_api_request
    else:
        # Log the unexpected response type
        logger.warning(f"Received unexpected response type from search API: {type(response_data)}")
        error_console.print(f"Error: Received unexpected response format from search API.")


@app.command()
def show(
    item_type: str = typer.Argument(..., help="Type of item (e.g., 'document')."),
    item_id: str = typer.Argument(..., help="The ID of the item.") # Use string initially for flexibility
):
    """
    Show details for a specific item (e.g., document).
    """
    # TDD: Test showing a document calls /documents/<id>
    # TDD: Test showing an invalid item_type prints error
    # TDD: Test showing non-existent item_id displays API error
    logger.info(f"CLI: Showing details for {item_type} {item_id}")
    item_type_lower = item_type.lower()

    if item_type_lower == 'document':
        try:
            doc_id_int = int(item_id)
            endpoint = f"/documents/{doc_id_int}"
            response_data = make_api_request("GET", endpoint)
            display_results(response_data)
        except ValueError:
            error_console.print(f"Error: Invalid Document ID '{item_id}'. Must be an integer.")
            raise typer.Exit(code=1)
    elif item_type_lower == 'chunk':
        # Assuming chunk IDs are strings, no conversion needed for now
        endpoint = f"/chunks/{item_id}" # Assuming this endpoint exists
        response_data = make_api_request("GET", endpoint)
        display_results(response_data)
    else:
        error_console.print(f"Error: Invalid item type '{item_type}'. Must be 'document' or 'chunk'.")
        raise typer.Exit(code=1)

# Define command groups for better organization
collection_app = typer.Typer(name="collection", help="Manage collections.")
app.add_typer(collection_app)

@collection_app.command("create")
def collection_create(
    name: str = typer.Argument(..., help="Name for the new collection.")
):
    """Creates a new collection."""
    logger.info(f"CLI: Creating collection '{name}'")
    response_data = make_api_request("POST", "/collections", json_data={"name": name})
    display_results(response_data)

@collection_app.command("add")
def collection_add_item(
    collection_id: str = typer.Argument(..., help="ID of the collection."), # Changed from int
    item_type: str = typer.Argument(..., help="Type of item ('document' or 'chunk')."),
    item_id: str = typer.Argument(..., help="ID of the item to add.") # Changed from int
):
    """Adds an item (document or chunk) to a collection."""
    logger.info(f"CLI: Adding {item_type} {item_id} to collection {collection_id}")
    endpoint = f"/collections/{collection_id}/items"
    payload = {"item_type": item_type.lower(), "item_id": item_id}
    response_data = make_api_request("POST", endpoint, json_data=payload)
    display_results(response_data)

@collection_app.command("list")
def collection_list_items(
    collection_id: str = typer.Argument(..., help="ID of the collection.") # Changed from int
):
    """Lists items within a specific collection."""
    logger.info(f"CLI: Listing items in collection {collection_id}")
    endpoint = f"/collections/{collection_id}"
    response_data = make_api_request("GET", endpoint)
    display_results(response_data) # display_results handles collection item lists


def _display_confirmation_options(options: List[Dict[str, Any]]):
    """Displays the book options in a formatted table."""
    if not options:
        console.print("[yellow]No options found.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Title")
    table.add_column("Author", style="cyan")
    table.add_column("Year", style="green")
    table.add_column("Format", style="yellow")
    table.add_column("Size", style="blue")

    for i, book in enumerate(options):
        table.add_row(
            str(i+1),
            book.get('title', 'N/A'),
            book.get('author', 'N/A'),
            str(book.get('year', 'N/A')),
            book.get('extension', 'N/A'),
            book.get('size', 'N/A')
        )
    console.print(table)


def _handle_acquire_confirmation(response: Dict[str, Any], yes_flag: bool):
    """Handles the confirmation flow for acquiring a text."""
    acquisition_id = response.get('acquisition_id')
    options = response.get('options', [])

# Basic validation: Ensure we have options and an ID to proceed.
    if not options or not acquisition_id:
        error_console.print("Error: API returned confirmation status but no options or ID.")
        raise typer.Exit(code=1)

    selected_book = None
    if yes_flag:
# Handle the --yes flag for automatic confirmation.
# If exactly one option is found, auto-select it.
        if isinstance(options, list) and len(options) == 1:
            selected_book = options[0]
            console.print(f"Found 1 match. Auto-confirming acquisition for: '{selected_book.get('title')}' (--yes used).")
# If multiple options are found, --yes is invalid; raise an error.
        elif isinstance(options, list) and len(options) > 1:
            error_console.print("Error: Multiple options found. Cannot auto-confirm with --yes.")
            _display_confirmation_options(options) # Show options for clarity
            raise typer.Exit(code=1)
        else: # len(options) == 0 or not isinstance(options, list)
# If no valid options (empty list or not a list), --yes cannot proceed.
            error_console.print("Error: No valid options found for auto-confirmation.")
            raise typer.Exit(code=1)
    else: # Manual selection
# Prompt the user for manual selection if --yes is not used.
        console.print("\n[bold yellow]Potential matches found. Select a book to acquire (enter number) or 0 to cancel:[/bold yellow]")
        _display_confirmation_options(options)
        try:
            selection = typer.prompt("Enter selection number (or 0 to cancel)", type=int, default=0)
# Handle user cancellation (input 0).
            if selection == 0:
                console.print("Acquisition cancelled.")
                return # Exit confirmation flow gracefully
# Handle valid user selection (within the range of options).
            elif 0 < selection <= len(options):
                selected_book = options[selection - 1]
                console.print(f"Confirming acquisition for: '{selected_book.get('title')}'...")
# Handle invalid selection number (out of range).
            else:
                error_console.print("Error: Invalid selection number.")
                raise typer.Exit(code=1)
# Handle non-numeric input (caught by typer.prompt type validation).
        except ValueError: # Should not happen with typer.prompt(type=int)
            error_console.print("Invalid input. Please enter a number.")
            raise typer.Exit(code=1)
# If a book was successfully selected (either automatically or manually).

    # If a book was selected (either auto or manual)
    if selected_book:
        confirm_payload = {
            "acquisition_id": acquisition_id,
            "selected_book_details": selected_book
# Call the /acquire/confirm API endpoint with the selected details.
        }
        confirm_response = make_api_request("POST", "/acquire/confirm", json_data=confirm_payload)
        display_results(confirm_response)
@app.command()
def acquire(
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Title of the text to acquire (use with --author)."),
    author: Optional[str] = typer.Option(None, "--author", "-a", help="Author of the text to acquire (use with --title)."),
    find_missing_threshold: Optional[int] = typer.Option(None, "--find-missing-threshold", "--threshold", help="Minimum citation count to find missing texts (use instead of --title/--author)."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Automatically confirm acquisition if only one option is found."),
):
    """
    Attempt to acquire and ingest a text via zlibrary-mcp.

    Use EITHER --title/--author OR --find-missing-threshold.
    """
    # TDD: Test calling API /acquire endpoint (initial search trigger - threshold)
    # TDD: Test calling API /acquire endpoint (initial search trigger - title/author)
    # TDD: Test handling API response requiring confirmation
    # TDD: Test prompting user for confirmation
    # TDD: Test calling API /acquire/confirm after user confirmation
    # TDD: Test handling API errors during acquisition process
    logger.info(f"CLI: Starting acquisition process...")

    # Argument validation
    search_by_details = bool(title or author)
    search_by_threshold = find_missing_threshold is not None

    if search_by_details and search_by_threshold:
        error_console.print("Error: Cannot use --title/--author and --find-missing-threshold together.")
        raise typer.Exit(code=1)
    if not search_by_details and not search_by_threshold:
        error_console.print("Error: Must provide either --title/--author or --find-missing-threshold.")
        raise typer.Exit(code=1)

    # Prepare payload based on mode
    if search_by_details:
        text_details = {"title": title, "author": author}
        payload = {"text_details": text_details}
        console.print(f"Searching for text: Title='{title}', Author='{author}'...")
    else: # search_by_threshold
        payload = {"find_missing_threshold": find_missing_threshold}
        console.print(f"Identifying potentially missing texts (threshold: {find_missing_threshold})...")

    initial_response = make_api_request("POST", "/acquire", json_data=payload)

    # --- Confirmation Flow (Common Logic) ---
    # --- Confirmation Flow or Direct Result ---
    if initial_response.get('status') == 'needs_confirmation':
        _handle_acquire_confirmation(initial_response, yes)

    else: # Handle initial errors or non-confirmation status
        display_results(initial_response) # Display the direct result/error


# --- Main Execution ---
if __name__ == "__main__":
    app()
@app.command()
def status(
    acquisition_id: str = typer.Argument(..., help="The ID of the acquisition task to check.")
):
    """
    Check the status of a specific acquisition task.
    """
    logger.info(f"CLI: Checking status for acquisition ID: {acquisition_id}")
    endpoint = f"/acquire/status/{acquisition_id}"
    response_data = make_api_request("GET", endpoint)
    display_results(response_data)