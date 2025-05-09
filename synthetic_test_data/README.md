# Synthetic Test Data for PhiloGraph

This directory contains synthetic test data generated for testing the PhiloGraph application. The data includes EPUB, PDF (planned), and Markdown files designed to cover various formatting, content types, and edge cases as specified in [`../../docs/qa/synthetic_data_requirements.md`](../../docs/qa/synthetic_data_requirements.md).

## Generation

The files in this directory can be (re)generated using the `generate_data.py` script located in this directory.

To run the script:
```bash
python3 generate_data.py
```

Ensure you have the necessary dependencies installed, particularly `EbookLib` for EPUB generation and `reportlab` for PDF generation. You can install dependencies from the project's main `requirements.txt`:
```bash
pip3 install -r ../requirements.txt 
```
(Adjust path to `requirements.txt` if running from a different working directory).

## Structure

The data is organized by file type and then by the specific feature or edge case being tested. Refer to [`../../docs/qa/synthetic_data_requirements.md`](../../docs/qa/synthetic_data_requirements.md) for the detailed proposed structure.

## Current Status

The `generate_data.py` script has been expanded and currently creates:
*   EPUB files:
    *   Simple NCX ToC (`epub/toc/ncx_simple.epub`)
    *   Nested NCX ToC (`epub/toc/ncx_nested.epub`)
    *   HTML Linked ToC (`epub/toc/html_toc_linked.epub`)
*   PDF files:
    *   Simple single-column text PDF (`pdf/text_based/single_column.pdf`)
*   Markdown files:
    *   Basic elements with YAML frontmatter (`markdown/basic/all_basic_elements.md`)
    *   Extended elements (tables, footnotes, task lists, code blocks) with TOML frontmatter (`markdown/extended/extended_elements.md`)

The script will be further expanded to generate a more comprehensive suite of test files according to the requirements.