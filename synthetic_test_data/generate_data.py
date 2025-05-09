import os
from ebooklib import epub

# Define output base directory relative to the script's location
BASE_OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

EPUB_DIR = os.path.join(BASE_OUTPUT_DIR, "epub")
PDF_DIR = os.path.join(BASE_OUTPUT_DIR, "pdf") # Placeholder for future PDF generation
MD_DIR = os.path.join(BASE_OUTPUT_DIR, "markdown")

# Ensure all specific output subdirectories exist
# (These should have been created by the previous mkdir -p command,
# but including them here makes the script more robust if run standalone)
os.makedirs(os.path.join(EPUB_DIR, "toc"), exist_ok=True)
os.makedirs(os.path.join(EPUB_DIR, "headers"), exist_ok=True)
os.makedirs(os.path.join(EPUB_DIR, "notes"), exist_ok=True)
os.makedirs(os.path.join(EPUB_DIR, "citations_bibliography"), exist_ok=True)
os.makedirs(os.path.join(EPUB_DIR, "images_fonts"), exist_ok=True)
os.makedirs(os.path.join(EPUB_DIR, "structure_metadata"), exist_ok=True)
os.makedirs(os.path.join(EPUB_DIR, "content_types"), exist_ok=True)
os.makedirs(os.path.join(EPUB_DIR, "general_edge_cases"), exist_ok=True)

os.makedirs(os.path.join(PDF_DIR, "text_based"), exist_ok=True)
os.makedirs(os.path.join(PDF_DIR, "image_based_ocr"), exist_ok=True)
os.makedirs(os.path.join(PDF_DIR, "structure"), exist_ok=True)
os.makedirs(os.path.join(PDF_DIR, "notes"), exist_ok=True)
os.makedirs(os.path.join(PDF_DIR, "general_edge_cases"), exist_ok=True)

os.makedirs(os.path.join(MD_DIR, "basic"), exist_ok=True)
os.makedirs(os.path.join(MD_DIR, "extended"), exist_ok=True)
os.makedirs(os.path.join(MD_DIR, "frontmatter"), exist_ok=True)
os.makedirs(os.path.join(MD_DIR, "general_edge_cases"), exist_ok=True)

def create_epub_ncx_simple(filename="ncx_simple.epub"):
    """
    Creates a simple EPUB file with a basic NCX Table of Contents.
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    
    book = epub.EpubBook()

    # Set metadata
    book.set_identifier("synth-epub-ncx-simple-001")
    book.set_title("Simple NCX EPUB")
    book.set_language("en")
    book.add_author("Synthetic Data Generator")
    book.add_metadata('DC', 'publisher', 'PhiloGraph Testing Inc.')
    book.add_metadata('DC', 'date', '2025-05-09', others={'event': 'publication'})


    # Create chapters
    c1_content = """<h1>Chapter 1: Introduction</h1>
<p>This is the first chapter of a synthetically generated EPUB file. 
Its purpose is to test basic NCX Table of Contents functionality.</p>
<p>Philosophical inquiry often begins with fundamental questions about existence, knowledge, values, reason, mind, and language. 
This simple text serves as a placeholder for such profound discussions.</p>"""
    c1 = epub.EpubHtml(title="Introduction", file_name="chap_01.xhtml", lang="en")
    c1.content = c1_content

    c2_content = """<h1>Chapter 2: Further Thoughts</h1>
<p>This second chapter continues the exploration, albeit in a very simple manner for testing purposes.</p>
<p>Consider the nature of synthetic data: it mimics reality to test systems, yet it is not real. 
This paradox itself could be a subject of philosophical thought.</p>"""
    c2 = epub.EpubHtml(title="Further Thoughts", file_name="chap_02.xhtml", lang="en")
    c2.content = c2_content
    
    # Add chapters to the book
    book.add_item(c1)
    book.add_item(c2)

    # Define Table of Contents
    book.toc = (epub.Link("chap_01.xhtml", "Introduction", "intro"),
                epub.Link("chap_02.xhtml", "Further Thoughts", "thoughts"))

    # Add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav()) # EPUB 3 NavDoc

    # Define CSS style
    style = 'BODY {color: black;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # Create spine
    book.spine = ['nav', c1, c2] # 'nav' is the NavDoc

    # Write to the file
    try:
        epub.write_epub(filepath, book, {})
        print(f"Successfully created EPUB: {filepath}")
    except Exception as e:
        print(f"Error creating EPUB {filepath}: {e}")

def create_md_basic_elements(filename="all_basic_elements.md"):
    """
    Creates a Markdown file showcasing basic formatting elements.
    """
    filepath = os.path.join(MD_DIR, "basic", filename)
    
    content = """---
title: Basic Markdown Elements
author: Synthetic Data Generator
date: 2025-05-09
tags: [markdown, test, basic]
---

# Header 1: The Nature of Synthesis

This document serves as a basic test for Markdown parsing.

## Header 2: Elements of Style

We explore *italicized text* for emphasis, and **bold text** for strong importance. 
Sometimes, we might use `inline code` for technical terms or snippets.

### Header 3: Lists and Organization

An unordered list:
- Item Alpha: The first principle.
- Item Beta: The second consideration.
  - Nested Item Beta.1: A sub-point.
  - Nested Item Beta.2: Another sub-point.
- Item Gamma: The final thought in this list.

An ordered list:
1. First step: Define requirements.
2. Second step: Generate synthetic data.
   1. Sub-step 2.1: Create EPUBs.
   2. Sub-step 2.2: Create PDFs.
   3. Sub-step 2.3: Create Markdown files.
3. Third step: Test the system.

### Header 3: Links and Images

A link to a [philosophical resource](https://plato.stanford.edu/).

An image placeholder (actual image file not generated by this script):
![Placeholder image of a classical bust](images/placeholder_bust.jpg)

---
> "The only true wisdom is in knowing you know nothing." 
> - Socrates (attributed)

This is a blockquote, often used for quotations or highlighted text.
"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully created Markdown: {filepath}")
    except Exception as e:
        print(f"Error creating Markdown {filepath}: {e}")

if __name__ == "__main__":
    print("Starting synthetic data generation...")
    
    create_epub_ncx_simple()
    create_md_basic_elements()
    
    # Future: Add calls to generate other EPUB files
    # e.g., create_epub_ncx_nested(), create_epub_html_toc_linked()
    
    # Future: Add calls to generate PDF files
    # e.g., create_pdf_single_column_text()
    
    # Future: Add calls to generate other Markdown files
    # e.g., create_md_tables_footnotes()

    print("Synthetic data generation script finished.")