# Synthetic Test Data for PhiloGraph

This directory contains synthetic test data generated for testing the PhiloGraph application. The data includes EPUB, PDF (planned), and Markdown files designed to cover various formatting, content types, and edge cases as specified in [`../../docs/qa/synthetic_data_requirements.md`](../../docs/qa/synthetic_data_requirements.md).

## Generation

The files in this directory can be (re)generated using the `generate_data.py` script located in this directory.

To run the script:
```bash
python3 generate_data.py
```

Ensure you have the necessary dependencies installed, particularly `EbookLib` for EPUB generation. You can install dependencies from the project's main `requirements.txt`:
```bash
pip3 install -r ../requirements.txt 
```
(Adjust path to `requirements.txt` if running from a different working directory).

## Structure

The data is organized by file type and then by the specific feature or edge case being tested. Refer to [`../../docs/qa/synthetic_data_requirements.md`](../../docs/qa/synthetic_data_requirements.md) for the detailed proposed structure.

## Current Status

This is an initial set of generated data. The `generate_data.py` script currently creates:
*   A simple EPUB file with a basic NCX ToC (`epub/toc/ncx_simple.epub`).
*   A Markdown file showcasing basic elements (`markdown/basic/all_basic_elements.md`).

The script can be expanded to generate a more comprehensive suite of test files according to the requirements.