import semchunk
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import ebooklib
import fitz # PyMuPDF
from ebooklib import epub

from .. import config
# Assuming http_client might be used for GROBID/AnyStyle API calls
from . import http_client

logger = logging.getLogger(__name__)

# --- Extraction Functions ---

def extract_epub_content(file_path: str | Path) -> Optional[Dict[str, Any]]:
    """
    Extracts content and metadata from an EPUB file.

    Returns:
        A dictionary containing:
        - 'text_by_section': Dict[str, str] mapping section titles to text.
        - 'metadata': Dict[str, Any] extracted metadata.
        - 'references_raw': None (EPUBs typically don't have structured refs like PDFs).
        Returns None if extraction fails.
    """
    # TDD: Test EPUB extraction returns text and metadata
    # TDD: Test handling of encrypted/DRM EPUBs (expect failure)
    # TDD: Test extraction of table of contents as sections
    try:
        logger.info(f"Extracting content from EPUB: {file_path}")
        book = epub.read_epub(file_path)
        metadata = {}
        text_by_section = {}
        references_raw = None # Not typically extracted from EPUB structure

        # Extract metadata
        try:
            metadata['title'] = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else None
            metadata['author'] = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else None
            metadata['language'] = book.get_metadata('DC', 'language')[0][0] if book.get_metadata('DC', 'language') else None
            metadata['identifier'] = book.get_metadata('DC', 'identifier')[0][0] if book.get_metadata('DC', 'identifier') else None
            # Add more metadata fields as needed (publisher, date, etc.)
        except Exception as meta_e:
            logger.warning(f"Could not extract some EPUB metadata from {file_path}: {meta_e}")

        # Extract text content section by section (using TOC)
        # Simple approach: iterate through items and try to map to TOC
        # More robust: Parse NCX or NavMap for structure
        section_sequence = 0
        current_section_title = "Introduction" # Default first section
        current_section_text = ""

        # Attempt to get TOC structure
        toc_items = []
        try:
            if book.toc:
                 # Flatten TOC for easier iteration
                 def flatten_toc(items):
                     flat = []
                     for item in items:
                         if isinstance(item, tuple): # Nested section
                             flat.append(item[0]) # Add the section itself
                             flat.extend(flatten_toc(item[1])) # Add its children
                         else:
                             flat.append(item) # Add the item
                     return flat
                 toc_items = flatten_toc(book.toc)
        except Exception as toc_e:
            logger.warning(f"Could not parse TOC for {file_path}: {toc_e}. Using item order.")


        # Iterate through EPUB items (HTML content)
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            # Try to find matching title in TOC
            item_title = None
            for toc_entry in toc_items:
                # Compare hrefs, removing anchors (#...)
                toc_href = toc_entry.href.split('#')[0]
                item_href = item.get_name().split('#')[0]
                if toc_href == item_href:
                    item_title = toc_entry.title
                    break

            # Basic HTML cleaning (replace with more robust parsing if needed)
            content = item.get_body_content().decode('utf-8', errors='ignore')
            text = re.sub('<[^<]+?>', ' ', content) # Simple tag removal
            text = re.sub(r'\s+', ' ', text).strip() # Normalize whitespace

            if text:
                if item_title and item_title != current_section_title:
                    # Store previous section if it had content
                    if current_section_text:
                         text_by_section[current_section_title] = current_section_text
                         section_sequence += 1
                    # Start new section
                    current_section_title = item_title
                    current_section_text = text
                else:
                    # Append to current section
                    current_section_text += "\n" + text

        # Add the last section
        if current_section_text:
            text_by_section[current_section_title] = current_section_text

        if not text_by_section:
             logger.warning(f"No text content extracted from EPUB: {file_path}")
             return None

        logger.info(f"Successfully extracted {len(text_by_section)} sections from EPUB: {file_path}")
        return {"text_by_section": text_by_section, "metadata": metadata, "references_raw": references_raw}

    except Exception as e:
        logger.error(f"Failed to extract EPUB content from {file_path}: {e}", exc_info=True)
        return None


def extract_text_content(file_path: str | Path) -> Optional[Dict[str, Any]]:
    """
    Extracts content and potentially frontmatter metadata from TXT or MD files.
    """
    # TDD: Test TXT/MD extraction reads content correctly
    # TDD: Test MD extraction handles frontmatter metadata
    logger.info(f"Extracting content from Text/Markdown: {file_path}")
    metadata = {}
    text_content = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Rudimentary frontmatter detection (e.g., YAML between ---)
            lines = f.readlines()
            if len(lines) > 2 and lines[0].strip() == '---':
                try:
                    import yaml
                    fm_end_index = -1
                    for i, line in enumerate(lines[1:], start=1):
                        if line.strip() == '---':
                            fm_end_index = i
                            break
                    if fm_end_index > 0:
                        frontmatter = "".join(lines[1:fm_end_index])
                        metadata = yaml.safe_load(frontmatter) or {}
                        text_content = "".join(lines[fm_end_index+1:])
                        logger.debug(f"Extracted frontmatter metadata from {file_path}")
                    else: # No closing --- found
                        text_content = "".join(lines)
                except ImportError:
                    logger.warning("PyYAML not installed, cannot parse frontmatter. Treating as plain text.")
                    text_content = "".join(lines)
                except yaml.YAMLError as ye:
                     logger.warning(f"Error parsing YAML frontmatter in {file_path}: {ye}. Treating as plain text.")
                     text_content = "".join(lines) # Re-join all lines if parsing fails
            else:
                text_content = "".join(lines)

        # Basic metadata if none from frontmatter
        if not metadata.get('title'):
            metadata['title'] = Path(file_path).stem

        text_by_section = {"main": text_content.strip()}
        logger.info(f"Successfully extracted text content from: {file_path}")
        return {"text_by_section": text_by_section, "metadata": metadata, "references_raw": None}

    except Exception as e:
        logger.error(f"Failed to extract text content from {file_path}: {e}", exc_info=True)
        return None

async def call_grobid_extractor(pdf_path: str | Path) -> Optional[Dict[str, Any]]:
    """
    Calls GROBID (via API or local library) to extract structured data from a PDF.
    Placeholder implementation.
    """
    # TDD: Test GROBID PDF extraction returns text, metadata, refs
    # TDD: Test handling of GROBID API errors (if using API)
    # TDD: Test handling of complex PDF layouts
    logger.info(f"Calling GROBID extractor for: {pdf_path}")

    if config.GROBID_API_URL:
        # --- API Call Implementation ---
        logger.debug(f"Using GROBID API at: {config.GROBID_API_URL}")
        endpoint = f"{config.GROBID_API_URL}/api/processFulltextDocument"
        response = None
        tei_xml = None
        try:
            with open(pdf_path, 'rb') as f:
                files = {'input': (Path(pdf_path).name, f, 'application/pdf')}
                # Use the shared async client
                try:
                    response = await http_client.make_async_request(
                        "POST",
                        endpoint,
                        files=files,
                        # Increase timeout for potentially long processing
                        timeout=300.0 # 5 minutes, adjust as needed
                    )
                    response.raise_for_status() # Check for HTTP errors
                    tei_xml = response.text
                    logger.info(f"Received TEI XML from GROBID API for {pdf_path}")
                except http_client.httpx.RequestError as e:
                    logger.error(f"GROBID API request failed for {pdf_path}: {e}")
                    return None
                except http_client.httpx.HTTPStatusError as e:
                    logger.error(f"GROBID API returned error for {pdf_path}: {e.response.status_code} - {e.response.text}")
                    return None

            # If request was successful and we have XML, parse it
            if tei_xml:
                # TODO: Implement TEI XML parsing
                parsed_data = parse_grobid_tei(tei_xml)
                return parsed_data
            else:
                 # Should not happen if exceptions are caught correctly, but safety net
                 logger.error(f"GROBID API call for {pdf_path} completed but yielded no TEI XML.")
                 return None

        except Exception as e: # Catch other potential errors (e.g., file open, parse_grobid_tei)
            logger.error(f"Error during GROBID processing for {pdf_path}: {e}", exc_info=True)
            return None
            return None

    else:
        # --- Local Library Call Implementation (Placeholder) ---
        logger.warning("GROBID_API_URL not configured. Local GROBID library interaction not implemented.")
        # Example (if a library like 'grobid-client-python' was used):
        # try:
        #     from grobid_client.grobid_client import GrobidClient
        #     client = GrobidClient(config_path=...) # Configure client
        #     tei_xml = client.process("processFulltextDocument", str(pdf_path))
        #     parsed_data = parse_grobid_tei(tei_xml)
        #     return parsed_data
        # except ImportError:
        #     logger.error("grobid-client library not installed.")
        #     return None
        # except Exception as e:
        #     logger.error(f"Local GROBID processing failed for {pdf_path}: {e}", exc_info=True)
        #     return None
        return None # Return None if no API URL and no local library logic

import xml.etree.ElementTree as ET

def parse_grobid_tei(tei_xml: str) -> Optional[Dict[str, Any]]:
    """
    Parses TEI XML output from GROBID using xml.etree.ElementTree.
    Minimal implementation to pass basic test.
    """
    # TDD: Test parsing of GROBID TEI XML for structure, text, metadata, biblio
    logger.debug("Parsing GROBID TEI XML")
    try:
        # Define the TEI namespace
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        root = ET.fromstring(tei_xml)

        metadata = {}
        text_by_section = {}
        references_raw = []

        # --- Extract Metadata ---
        title_elem = root.find('.//tei:titleStmt/tei:title[@type="main"]', ns)
        metadata['title'] = title_elem.text if title_elem is not None else None

        # Simple author extraction (adjust if multiple authors or complex names)
        author_elem = root.find('.//tei:analytic/tei:author/tei:persName', ns)
        if author_elem is not None:
            forename = author_elem.findtext('tei:forename', '', ns)
            surname = author_elem.findtext('tei:surname', '', ns)
            metadata['author'] = f"{forename} {surname}".strip()
        else:
            metadata['author'] = None

        # --- Extract Text by Section ---
        # Abstract
        abstract_div = root.find('.//tei:body/tei:div[@type="abstract"]', ns)
        if abstract_div is not None:
            # Concatenate text from all <p> tags within the abstract div
            abstract_text = ' '.join(p.text for p in abstract_div.findall('tei:p', ns) if p.text)
            text_by_section['Abstract'] = abstract_text.strip()

        # Other sections (Introduction, Section 1, etc.)
        for div in root.findall('.//tei:body/tei:div', ns):
            div_type = div.get('type')
            if div_type != 'abstract': # Skip abstract as it's handled separately
                head_elem = div.find('tei:head', ns)
                section_title = head_elem.text if head_elem is not None else f"Section_{div_type or 'unknown'}"
                section_text = ' '.join(p.text for p in div.findall('tei:p', ns) if p.text).strip()
                if section_text:
                    text_by_section[section_title] = section_text

        # --- Extract References ---
        ref_list = root.find('.//tei:back/tei:div[@type="references"]/tei:listBibl', ns)
        if ref_list is not None:
            for bibl in ref_list.findall('tei:bibl', ns):
                if bibl.text:
                    references_raw.append(bibl.text.strip())

        return {"text_by_section": text_by_section, "metadata": metadata, "references_raw": references_raw}

    except ET.ParseError as pe:
        logger.error(f"Failed to parse TEI XML (ParseError): {pe}", exc_info=False) # Less verbose for common parse errors
        return None
    except Exception as e:
        logger.error(f"Failed to parse TEI XML (General Error): {e}", exc_info=True) # Keep full traceback for unexpected errors
        return None

# --- Chunking ---

def chunk_text_semantically(text: str, chunk_size: int) -> List[str]:
    """
    Chunks text using a semantic chunking strategy.
    Placeholder implementation - requires a 'semchunk' library or implementation.
    """
    # TDD: Test chunking produces expected chunk sizes and overlap
    # TDD: Test handling of very short texts
    # TDD: Test handling of texts with no clear sentence boundaries
    logger.debug(f"Chunking text semantically using semchunk, target size: {chunk_size}")
    try:
        # Assuming semchunk.chunk is the primary function based on library name
        # The library might have different functions or parameters, adjust if tests fail.
        chunks = semchunk.chunk(text, chunk_size)
        logger.debug(f"Successfully chunked text into {len(chunks)} chunks.")
        return chunks
    except Exception as e:
        logger.error(f"Error during semantic chunking with semchunk: {e}", exc_info=True)
        # Fallback or re-raise depending on desired behavior
        # Raising exception might be better to signal failure clearly
        raise ValueError(f"Semantic chunking failed: {e}") from e


# --- Reference Parsing ---

async def parse_references(raw_references: List[str]) -> List[Dict[str, Any]]:
    """
    Parses raw reference strings into structured data.
    Uses AnyStyle via API if configured, otherwise falls back to basic parsing.
    """
    # TDD: Test parsing various citation string formats
    # TDD: Test using AnyStyle if available and configured
    # TDD: Test extraction of key fields (author, title, year)
    parsed_details_list = []
    logger.info(f"Parsing {len(raw_references)} raw references...")

    if config.ANYSTYLE_API_URL:
        logger.debug(f"Using AnyStyle API at: {config.ANYSTYLE_API_URL}")
        # TODO: Implement batching if AnyStyle API supports it
        for ref_string in raw_references:
            try:
                parsed = await call_anystyle_parser(ref_string)
                if parsed:
                    parsed_details_list.append(parsed)
            except Exception as e:
                 logger.warning(f"AnyStyle parsing failed for reference: '{ref_string[:50]}...': {e}")
                 # Optionally fallback to basic parser here
                 parsed = basic_reference_parser(ref_string)
                 if parsed:
                     parsed_details_list.append(parsed)
    else:
        logger.debug("Using basic reference parser.")
        for ref_string in raw_references:
            parsed = basic_reference_parser(ref_string)
            if parsed:
                parsed_details_list.append(parsed)

    logger.info(f"Successfully parsed {len(parsed_details_list)} references.")
    return parsed_details_list

async def call_anystyle_parser(reference_string: str) -> Optional[Dict[str, Any]]:
    """Calls the AnyStyle API to parse a reference string."""
    logger.debug(f"Calling AnyStyle parser for: '{reference_string[:50]}...'")
    if not config.ANYSTYLE_API_URL:
        logger.warning("ANYSTYLE_API_URL not configured, cannot call AnyStyle.")
        return None

    endpoint = config.ANYSTYLE_API_URL # Assuming endpoint takes POST with JSON
    payload = {"references": [reference_string]}

    try:
        response = await http_client.make_async_request("POST", endpoint, json_data=payload, timeout=30.0)
        await response.raise_for_status()
        parsed_list = await response.json()
        if parsed_list and isinstance(parsed_list, list):
            # TODO: Verify and refine normalization against the actual AnyStyle API response schema.
            # The current implementation assumes a list containing a dict with 'title', 'author' (list of dicts with 'family'), and 'date' keys.
            parsed_data = parsed_list[0]

            # Safer normalization using .get() with defaults
            title = parsed_data.get("title")
            authors_list = parsed_data.get("author", [])
            date = parsed_data.get("date")

            structured_ref = {
                "title": title[0] if isinstance(title, list) and title else title if isinstance(title, str) else None,
                "author": " and ".join(
                    author.get("family", "")
                    for author in authors_list if isinstance(author, dict) and author.get("family")
                ).strip() or None,
                "year": date[0] if isinstance(date, list) and date else date if isinstance(date, str) else None,
                "raw": reference_string, # Keep original
                "source": "anystyle",
                "full_parsed": parsed_data # Store original parsed data for potential future use
            }
            return structured_ref
        else:
            logger.warning(f"Unexpected response format from AnyStyle for '{reference_string[:50]}...': {parsed_list}")
            return None
    except http_client.httpx.RequestError as e:
        logger.error(f"AnyStyle API request failed: {e}")
        raise # Re-raise to potentially trigger fallback in parse_references
    except http_client.httpx.HTTPStatusError as e:
        logger.error(f"AnyStyle API returned error: {e.response.status_code} - {e.response.text}")
        raise # Re-raise
    except Exception as e:
        logger.error(f"Error during AnyStyle API call: {e}", exc_info=True)
        raise # Re-raise

def basic_reference_parser(reference_string: str) -> Optional[Dict[str, Any]]:
    """Performs very basic reference parsing using heuristics as a fallback."""
    logger.debug(f"Using basic heuristic parser for: '{reference_string[:50]}...'")

    # Attempt to find a year in parentheses, allowing for spaces
    year_match = re.search(r'\(\s*(\d{4})\s*\)', reference_string)
    year = year_match.group(1) if year_match else None

    if not year:
        logger.warning(f"Basic parser could not extract year using regex from: '{reference_string[:50]}...'")
        return None # Return None if year extraction failed

    # Split based on the found year pattern
    year_pattern = year_match.group(0) # e.g., "( 2023 )"
    parts = reference_string.split(year_pattern, 1) # Split only once

    # Extract potential author and title parts based on split
    author_part = parts[0].strip() if len(parts) > 0 else "" # Strip whitespace only
    title_part = parts[1].strip().lstrip('.,;: ') if len(parts) > 1 else "" # Strip whitespace and leading punctuation

    # Assign None if the stripped part is empty, otherwise use the stripped part
    author = author_part if author_part else None
    title = title_part if title_part else None

    # Require a non-empty author string for a successful parse
    if not author:
        logger.warning(f"Basic parser found year ({year}) but failed to extract plausible author from: '{reference_string[:50]}...'")
        return None

    logger.debug(f"Basic parse result - Author: {author}, Year: {year}, Title: {title}")
    return {
        "title": title,
        "author": author,
        "year": year,
        "raw": reference_string,
        "source": "basic_heuristic", # Ensure correct source string
        "full_parsed": None
    }