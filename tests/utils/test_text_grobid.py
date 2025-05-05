# tests/utils/test_text_grobid.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import logging
from src.philograph.utils import http_client # Import needed for exception type
from src.philograph.utils import text_processing
from src.philograph import config

# --- Tests for call_grobid_extractor ---
@pytest.mark.asyncio
@patch('src.philograph.utils.text_processing.parse_grobid_tei')
@patch('src.philograph.utils.http_client.make_async_request')
@patch('src.philograph.config.GROBID_API_URL', 'http://dummy-grobid:8070') # Mock config value
async def test_call_grobid_extractor_api_success(mock_make_request, mock_parse_tei, tmp_path):
    """Tests successful PDF processing via GROBID API."""
    # Mock the response from http_client.make_async_request
    mock_response = AsyncMock()
    mock_response.text = "<TEI>dummy TEI content</TEI>"
    mock_response.raise_for_status = MagicMock() # Mock method to do nothing
    mock_make_request.return_value = mock_response

    # Mock the result from parse_grobid_tei
    expected_parsed_data = {
        "metadata": {"title": "Parsed Title"},
        "text_by_section": {"Abstract": "Parsed abstract."},
        "references_raw": ["Parsed ref 1"]
    }
    mock_parse_tei.return_value = expected_parsed_data

    # Create dummy PDF path
    pdf_path = tmp_path / "dummy.pdf"
    pdf_path.touch() # File needs to exist for 'open'

    result = await text_processing.call_grobid_extractor(pdf_path)

    # Assertions
    # Check that make_async_request was called correctly
    mock_make_request.assert_awaited_once()
    call_args, call_kwargs = mock_make_request.call_args
    assert call_args[0] == "POST"
    assert call_args[1] == "http://dummy-grobid:8070/api/processFulltextDocument"
    assert "files" in call_kwargs
    assert "input" in call_kwargs["files"]
    assert call_kwargs["files"]["input"][0] == "dummy.pdf"
    # Check that parse_grobid_tei was called with the response text
    mock_parse_tei.assert_called_once_with("<TEI>dummy TEI content</TEI>")
    # Check that the final result is the data returned by parse_grobid_tei
    assert result == expected_parsed_data


@pytest.mark.asyncio
@patch('src.philograph.utils.http_client.make_async_request', new_callable=AsyncMock) # Use AsyncMock directly
@patch('src.philograph.config.GROBID_API_URL', 'http://dummy-grobid:8070')
async def test_call_grobid_extractor_api_request_error(mock_make_request, tmp_path, caplog): # Removed mock_httpx
    """Tests handling of httpx.RequestError during GROBID API call."""
    # Configure make_async_request mock to raise RequestError when awaited
    error_message = "Simulated connection failed"
    # Use the real exception type from the imported http_client module
    mock_make_request.side_effect = http_client.httpx.RequestError(error_message)

    pdf_path = tmp_path / "error.pdf"
    pdf_path.touch()

    with caplog.at_level(logging.ERROR):
        result = await text_processing.call_grobid_extractor(pdf_path)

    # Assertions
    assert result is None # Should return None on request error
    mock_make_request.assert_awaited_once() # Check it was called

    # Check logs
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "ERROR"
    assert f"GROBID API request failed for {pdf_path}" in caplog.text
    assert error_message in caplog.text


@pytest.mark.asyncio
@patch('src.philograph.utils.http_client.make_async_request', new_callable=AsyncMock)
@patch('src.philograph.config.GROBID_API_URL', 'http://dummy-grobid:8070')
async def test_call_grobid_extractor_api_status_error(mock_make_request, tmp_path, caplog):
    """Tests handling of httpx.HTTPStatusError during GROBID API call."""
    # Configure make_async_request mock to raise HTTPStatusError
    error_message = "Simulated Server Error"
    mock_response = MagicMock() # Need a mock response object for the exception
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error Details"
    # Use the real exception type
    status_error = http_client.httpx.HTTPStatusError(
        message=error_message,
        request=MagicMock(), # Mock request object
        response=mock_response
    )
    mock_make_request.side_effect = status_error

    pdf_path = tmp_path / "status_error.pdf"
    pdf_path.touch()

    with caplog.at_level(logging.ERROR):
        result = await text_processing.call_grobid_extractor(pdf_path)

    # Assertions
    assert result is None # Should return None on status error
    mock_make_request.assert_awaited_once() # Check it was called

    # Check logs
    # Check logs for the specific error message format from the function
    assert len(caplog.records) == 1
    log_record = caplog.records[0]
    assert log_record.levelname == "ERROR"
    # Check the specific log message format used in text_processing.py
    expected_log_msg_start = f"GROBID API returned error for {pdf_path}: 500"
    assert expected_log_msg_start in log_record.message
    assert "Internal Server Error Details" in log_record.message


@pytest.mark.asyncio
@patch('src.philograph.utils.text_processing.logger') # Use logger mock via patch
@patch('src.philograph.config.GROBID_API_URL', None) # Mock config value to None
async def test_call_grobid_extractor_no_api_url(mock_logger, tmp_path):
    """Tests behavior when GROBID_API_URL is not configured."""
    pdf_path = tmp_path / "no_api.pdf"
    pdf_path.touch()

    result = await text_processing.call_grobid_extractor(pdf_path)

    # Assertions
    assert result is None # Should return None if API URL is not set

    # Check logs - Use mock_logger directly
    mock_logger.warning.assert_called_once_with(
        "GROBID_API_URL not configured. Local GROBID library interaction not implemented."
    )

# --- Tests for parse_grobid_tei ---

def test_parse_grobid_tei_basic():
    """Tests basic parsing of a minimal GROBID TEI XML structure."""
    # Minimal TEI XML example (replace with more realistic sample if needed)
    tei_xml = """
    <TEI xmlns="http://www.tei-c.org/ns/1.0">
        <teiHeader>
            <fileDesc>
                <titleStmt>
                    <title level="a" type="main">Sample Title</title>
                </titleStmt>
                <publicationStmt>
                    <publisher>Publisher</publisher>
                </publicationStmt>
                <sourceDesc>
                    <biblStruct>
                        <analytic>
                            <author><persName><forename>Test</forename><surname>Author</surname></persName></author>
                        </analytic>
                        <monogr>
                            <title level="j">Journal Name</title>
                            <imprint>
                                <date when="2023">2023</date>
                            </imprint>
                        </monogr>
                    </biblStruct>
                </sourceDesc>
            </fileDesc>
        </teiHeader>
        <text>
            <body>
                <div type="abstract"><p>This is the abstract.</p></div>
                <div type="introduction"><head>Introduction</head><p>Introductory text.</p></div>
                <div type="section"><head>Section 1</head><p>Section 1 text.</p></div>
            </body>
            <back>
                <div type="references">
                    <listBibl>
                        <bibl>Reference 1 string.</bibl>
                        <bibl>Reference 2 string.</bibl>
                    </listBibl>
                </div>
            </back>
        </text>
    </TEI>
    """
    # Since the function is a placeholder, this test will currently fail
    # as it expects real parsing, not the placeholder data.
    # We expect failure in the Red phase.
    expected_metadata = {"title": "Sample Title", "author": "Test Author"} # Simplified expectation
    expected_sections = {
        "Abstract": "This is the abstract.",
        "Introduction": "Introductory text.",
        "Section 1": "Section 1 text.",
        # Placeholder doesn't extract refs section text separately
    }
    expected_refs = ["Reference 1 string.", "Reference 2 string."]

    # This call will return the placeholder data, not the parsed data
    result = text_processing.parse_grobid_tei(tei_xml)

    assert result is not None
    # Assert against the expected parsed data, not the old placeholder data
    assert result["metadata"]["title"] == expected_metadata["title"]
    assert result["metadata"]["author"] == expected_metadata["author"]
    # Check a subset of sections for brevity, assuming the parsing logic is correct
    assert result["text_by_section"]["Abstract"] == expected_sections["Abstract"]
    assert result["text_by_section"]["Introduction"] == expected_sections["Introduction"]
    assert result["text_by_section"]["Section 1"] == expected_sections["Section 1"]
    assert result["references_raw"] == expected_refs


def test_parse_grobid_tei_parse_error(caplog):
    """Tests handling of invalid XML input."""
    invalid_xml = "<TEI><unclosedTag>"

    with caplog.at_level(logging.ERROR):
        result = text_processing.parse_grobid_tei(invalid_xml)

    assert result is None
    assert "Failed to parse TEI XML (ParseError)" in caplog.text