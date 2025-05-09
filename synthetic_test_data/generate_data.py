import os
from ebooklib import epub
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER

# Define output base directory relative to the script's location
BASE_OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

EPUB_DIR = os.path.join(BASE_OUTPUT_DIR, "epub")
PDF_DIR = os.path.join(BASE_OUTPUT_DIR, "pdf")
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

def _create_epub_book(identifier, title, author="Synthetic Data Generator", lang="en"):
    """Helper function to create a basic EpubBook object with common metadata."""
    book = epub.EpubBook()
    book.set_identifier(identifier)
    book.set_title(title)
    book.set_language(lang)
    book.add_author(author)
    book.add_metadata('DC', 'publisher', 'PhiloGraph Testing Inc.')
    book.add_metadata('DC', 'date', '2025-05-09', others={'event': 'publication'})
    return book

def _add_epub_chapters(book, chapter_details):
    """Helper to add chapters to the book and return chapter objects."""
    chapters = []
    for i, detail in enumerate(chapter_details):
        ch_title = detail.get("title", f"Chapter {i+1}")
        ch_filename = detail.get("filename", f"chap_{i+1:02}.xhtml")
        ch_content = detail.get("content", f"<h1>{ch_title}</h1><p>Content for {ch_title}.</p>")
        
        chapter = epub.EpubHtml(title=ch_title, file_name=ch_filename, lang=book.language)
        chapter.content = ch_content
        book.add_item(chapter)
        chapters.append(chapter)
    return chapters

def _write_epub_file(book, filepath):
    """Helper function to write the EPUB file."""
    try:
        epub.write_epub(filepath, book, {})
        print(f"Successfully created EPUB: {filepath}")
    except Exception as e:
        print(f"Error creating EPUB {filepath}: {e}")

def create_epub_ncx_simple(filename="ncx_simple.epub"):
    """
    Creates a simple EPUB file with a basic NCX Table of Contents.
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-ncx-simple-001", "Simple NCX EPUB")

    chapter_details = [
        {
            "title": "Introduction",
            "filename": "chap_01.xhtml",
            "content": """<h1>Chapter 1: Introduction</h1>
<p>This is the first chapter of a synthetically generated EPUB file.
Its purpose is to test basic NCX Table of Contents functionality.</p>
<p>Philosophical inquiry often begins with fundamental questions about existence, knowledge, values, reason, mind, and language.
This simple text serves as a placeholder for such profound discussions.</p>"""
        },
        {
            "title": "Further Thoughts",
            "filename": "chap_02.xhtml",
            "content": """<h1>Chapter 2: Further Thoughts</h1>
<p>This second chapter continues the exploration, albeit in a very simple manner for testing purposes.</p>
<p>Consider the nature of synthetic data: it mimics reality to test systems, yet it is not real.
This paradox itself could be a subject of philosophical thought.</p>"""
        }
    ]
    chapters = _add_epub_chapters(book, chapter_details)
    
    # Define Table of Contents
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "intro"),
                epub.Link(chapters[1].file_name, chapters[1].title, "thoughts"))

    # Add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav()) # EPUB 3 NavDoc

    # Define CSS style
    style = 'BODY {color: black;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # Create spine
    book.spine = ['nav'] + chapters # 'nav' is the NavDoc

    _write_epub_file(book, filepath)


def create_epub_ncx_nested(filename="ncx_nested.epub"):
    """
    Creates an EPUB file with a nested NCX Table of Contents (3+ levels).
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-ncx-nested-001", "Nested NCX EPUB")

    chapter_details = [
        {
            "title": "Part I: Foundations", "filename": "part1_intro.xhtml",
            "content": "<h1>Part I: Foundations</h1><p>This part lays the groundwork.</p>"
        },
        {
            "title": "Chapter 1: Core Concepts", "filename": "chap_01.xhtml",
            "content": "<h1>Chapter 1: Core Concepts</h1><p>Discussing fundamental ideas.</p>"
        },
        {
            "title": "Section 1.1: First Concept", "filename": "sec_1_1.xhtml",
            "content": "<h2>Section 1.1: First Concept</h2><p>Detailing the first concept.</p>"
        },
        {
            "title": "Subsection 1.1.1: Sub-Detail", "filename": "sub_1_1_1.xhtml",
            "content": "<h3>Subsection 1.1.1: Sub-Detail</h3><p>A very specific detail.</p>"
        },
        {
            "title": "Section 1.2: Second Concept", "filename": "sec_1_2.xhtml",
            "content": "<h2>Section 1.2: Second Concept</h2><p>Exploring the second concept.</p>"
        },
        {
            "title": "Chapter 2: Advanced Topics", "filename": "chap_02.xhtml",
            "content": "<h1>Chapter 2: Advanced Topics</h1><p>Moving to more complex subjects.</p>"
        }
    ]
    chapters = _add_epub_chapters(book, chapter_details)

    # Define Table of Contents (Nested)
    # chapters[0] = Part I Intro HTML content
    # chapters[1] = Ch1 HTML content
    # chapters[2] = Sec 1.1 HTML content
    # chapters[3] = SubSec 1.1.1 HTML content
    # chapters[4] = Sec 1.2 HTML content
    # chapters[5] = Ch2 HTML content

    # Create individual Link items
    link_p1_intro = epub.Link(chapters[0].file_name, chapters[0].title, "p1intro_id")
    link_c1 = epub.Link(chapters[1].file_name, chapters[1].title, "c1_id")
    link_s1_1 = epub.Link(chapters[2].file_name, chapters[2].title, "s1_1_id")
    link_ss1_1_1 = epub.Link(chapters[3].file_name, chapters[3].title, "ss1_1_1_id")
    link_s1_2 = epub.Link(chapters[4].file_name, chapters[4].title, "s1_2_id")
    link_c2 = epub.Link(chapters[5].file_name, chapters[5].title, "c2_id")

    # Define TOC structure using tuples for nesting
    # Level 3 (Innermost)
    toc_ss1_1_1 = link_ss1_1_1  # This is a direct link, no children in this branch

    # Level 2
    # toc_s1_1 is a tuple: (Link object for Section 1.1, (tuple of its children))
    toc_s1_1 = (link_s1_1, (toc_ss1_1_1,))
    toc_s1_2 = link_s1_2  # This is a direct link, no children in this branch

    # Level 1
    # toc_c1 is a tuple: (Link object for Chapter 1, (tuple of its children))
    toc_c1 = (link_c1, (toc_s1_1, toc_s1_2))
    toc_c2 = link_c2  # This is a direct link, no children in this branch
    
    # Top Level
    # The "Part I: Foundations" entry itself links to the content of Part I (chapters[0])
    # and it contains Chapter 1 and Chapter 2 as its children in the TOC.
    book.toc = (
        (link_p1_intro, (toc_c1, toc_c2)),
    )

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    style = 'BODY {color: navy;}' # Different style for this book
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)


def create_epub_html_toc_linked(filename="html_toc_linked.epub"):
    """
    Creates an EPUB with a separate, linked HTML Table of Contents.
    NCX will be minimal or point to the HTML ToC.
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-html-toc-001", "HTML ToC EPUB")

    # Create HTML ToC page
    html_toc_content = """<h1>Table of Contents</h1>
<ul>
    <li><a href="chap_01.xhtml">Chapter 1: Beginnings</a></li>
    <li><a href="chap_02.xhtml">Chapter 2: Developments</a>
        <ul>
            <li><a href="chap_02.xhtml#sec2.1">Section 2.1: First Development</a></li>
        </ul>
    </li>
    <li><a href="chap_03.xhtml">Chapter 3: Conclusions</a></li>
</ul>"""
    html_toc_page = epub.EpubHtml(title="Table of Contents", file_name="toc.xhtml", lang="en")
    html_toc_page.content = html_toc_content
    book.add_item(html_toc_page)

    chapter_details = [
        {"title": "Chapter 1: Beginnings", "filename": "chap_01.xhtml", "content": "<h1>Chapter 1: Beginnings</h1><p>Content for chapter 1.</p>"},
        {"title": "Chapter 2: Developments", "filename": "chap_02.xhtml", "content": "<h1>Chapter 2: Developments</h1><p>Content for chapter 2.</p><h2 id='sec2.1'>Section 2.1: First Development</h2><p>Details of section 2.1.</p>"},
        {"title": "Chapter 3: Conclusions", "filename": "chap_03.xhtml", "content": "<h1>Chapter 3: Conclusions</h1><p>Content for chapter 3.</p>"}
    ]
    chapters = _add_epub_chapters(book, chapter_details)

    book.toc = tuple(epub.Link(ch.file_name, ch.title, ch.file_name.split('.')[0]) for ch in chapters)
    
    book.add_item(epub.EpubNcx())
    
    nav_doc = epub.EpubNav()
    book.add_item(nav_doc)


    style = 'BODY {color: green;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    book.spine = ['nav', html_toc_page] + chapters
    
    _write_epub_file(book, filepath)

def create_pdf_text_single_column(filename="single_column.pdf"):
    """
    Creates a simple text-based PDF with a single column layout.
    """
    filepath = os.path.join(PDF_DIR, "text_based", filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    
    # Set metadata
    c.setTitle("Single Column Text PDF")
    c.setAuthor("Synthetic Data Generator")
    c.setSubject("Testing PDF text extraction")
    c.setKeywords(["pdf", "test", "text", "single column"])

    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleH1 = styles['h1']
    styleH2 = styles['h2']

    story = []

    # Title
    p_title = Paragraph("The Philosophy of Synthetic Documents", styleH1)
    story.append(p_title)
    story.append(Spacer(1, 0.2*inch))

    # Chapter 1
    p_ch1_title = Paragraph("Chapter 1: The Nature of the Artificial", styleH2)
    story.append(p_ch1_title)
    story.append(Spacer(1, 0.1*inch))

    text_ch1 = """This document, itself an artifact of synthetic generation, explores the philosophical implications of artificiality.
    When we create data that mimics reality, what does it tell us about the reality it seeks to emulate?
    This PDF is structured in a single column, a common format for textual documents, designed to test basic text extraction and layout parsing.
    The content herein is Lorem Ipsum with a philosophical bent, intended to provide sufficient textual matter for analysis without requiring deep semantic understanding for the purpose of format testing.
    We consider the works of Plato, who pondered the world of Forms, a realm of perfect archetypes that earthly objects merely imitate.
    Is synthetic data, then, an imitation of an imitation, twice removed from truth? Or does its deliberate construction for a specific purpose – testing – grant it a unique, albeit functional, essence?
    Further, the process of generating such data involves algorithms and predefined rules. Does this deterministic origin strip the data of any potential for emergent meaning, or is meaning solely a construct of the interpreting agent, whether human or machine?
    These questions, while tangential to the immediate technical goal of testing a data pipeline, serve to imbue the synthetic with a semblance of the thematic content it might one day process.
    """
    p_ch1_content = Paragraph(text_ch1.replace("\n", "<br/>"), styleN)
    story.append(p_ch1_content)
    story.append(Spacer(1, 0.2*inch))

    # Chapter 2
    p_ch2_title = Paragraph("Chapter 2: Implications for Knowledge Systems", styleH2)
    story.append(p_ch2_title)
    story.append(Spacer(1, 0.1*inch))

    text_ch2 = """If a knowledge system is trained or tested on synthetic data, how does this affect its understanding of genuine information?
    The verisimilitude of the synthetic becomes crucial. A poorly constructed synthetic dataset might lead to a skewed or brittle model.
    Conversely, a meticulously crafted dataset, covering a wide array of edge cases and complexities, can significantly enhance robustness.
    This particular PDF aims for simplicity in layout but richness in textual content to allow for straightforward extraction. Future synthetic PDFs will explore more complex layouts, including multiple columns, embedded images, and varied font usage.
    The challenge lies in creating synthetic data that is "real enough" for its purpose. For PhiloGraph, this means data that reflects the structural and semantic nuances of philosophical texts, including citations, footnotes, and complex argumentation, even if the arguments themselves are fabricated for the test.
    """
    p_ch2_content = Paragraph(text_ch2.replace("\n", "<br/>"), styleN)
    story.append(p_ch2_content)

    # Build the story on the canvas
    frame_width = letter[0] - 2*inch # Page width - 2x margin
    frame_height = letter[1] - 2*inch # Page height - 2x margin
    
    current_y = letter[1] - inch # Start 1 inch from top
    
    for item in story:
        item_height = item.wrapOn(c, frame_width, frame_height)[1] # Get height
        if current_y - item_height < inch: # If not enough space, new page
            c.showPage()
            c.setTitle("Single Column Text PDF") # Metadata for new page
            c.setAuthor("Synthetic Data Generator")
            current_y = letter[1] - inch
        
        item.drawOn(c, inch, current_y - item_height)
        current_y -= (item_height + 0.1*inch) # Add a little space after paragraph

    try:
        c.save()
        print(f"Successfully created PDF: {filepath}")
    except Exception as e:
        print(f"Error creating PDF {filepath}: {e}")


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
custom_field: SomeValue
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

def create_md_extended_elements(filename="extended_elements.md"):
    """
    Creates a Markdown file with tables, footnotes, task lists, and code blocks.
    Uses TOML frontmatter.
    """
    filepath = os.path.join(MD_DIR, "extended", filename)
    
    content = """+++
title = "Extended Markdown Showcase"
author = "Synthetic Data Generator"
date = "2025-05-09"
category = "synthetic"
draft = false
description = "A test file for advanced Markdown features."
+++

# Extended Markdown Features

This document demonstrates more complex Markdown elements.

## Tables

A simple table:

| Philosopher | Key Idea             | Era      |
|-------------|----------------------|----------|
| Plato       | Theory of Forms      | Ancient  |
| Kant        | Categorical Imperative | Modern   |
| Nietzsche   | Will to Power        | Modern   |

A table with different alignments:

| Left Align  | Center Align | Right Align |
|:------------|:------------:|------------:|
| Col 3 is    | some wordy   |        $1600 |
| Col 2 is    | centered     |          $12 |
| zebra stripes | are neat   |           $1 |

## Footnotes

Here is some text with a footnote.[^1] And another one.[^2]

[^1]: This is the first footnote. It can contain **bold** and *italic* text.
[^2]: This is the second footnote. It might link to [another resource](https://example.com).

## Task Lists

- [x] Define requirements for synthetic data
- [ ] Generate EPUB files
  - [ ] Simple NCX
  - [ ] Nested NCX
- [ ] Generate PDF files
- [ ] Generate Markdown files
  - [x] Basic elements
  - [ ] Extended elements (this one!)

## Code Blocks

Python code block:
```python
def greet(name):
    print(f"Hello, {name}!")

greet("Philosopher")
```

JSON code block:
```json
{
  "concept": "Synthetic Data",
  "purpose": "Testing",
  "formats": ["EPUB", "PDF", "Markdown"]
}
```

Indented code block:

    // This is an indented code block
    // Often used for simpler snippets.
    function example() {
        return true;
    }

## Horizontal Rules

---

***

___

These are different ways to create horizontal rules.
"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully created Markdown: {filepath}")
    except Exception as e:
        print(f"Error creating Markdown {filepath}: {e}")


if __name__ == "__main__":
    print("Starting synthetic data generation...")
    
    # EPUBs
    create_epub_ncx_simple()
    create_epub_ncx_nested()
    create_epub_html_toc_linked()

    # PDFs
    create_pdf_text_single_column()

    # Markdown
    create_md_basic_elements()
    create_md_extended_elements()
    
    # Future: Add calls to generate other EPUB files
    # e.g., create_epub_ncx_page_list(), create_epub_p_tag_headings()
    
    # Future: Add calls to generate PDF files
    # e.g., create_pdf_multi_column_text(), create_pdf_with_images_tables()
    
    # Future: Add calls to generate other Markdown files
    # e.g., create_md_yaml_frontmatter_variations()

    print("Synthetic data generation script finished.")