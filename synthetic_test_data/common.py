import os
from ebooklib import epub

# Define output base directory relative to the script's location
BASE_OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

EPUB_DIR = os.path.join(BASE_OUTPUT_DIR, "epub")
PDF_DIR = os.path.join(BASE_OUTPUT_DIR, "pdf")
MD_DIR = os.path.join(BASE_OUTPUT_DIR, "markdown")

def ensure_output_directories():
    """Ensures all necessary output directories exist."""
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

def _create_epub_book(identifier, title, author="Synthetic Data Generator", lang="en", custom_metadata=None, add_default_metadata=True):
    """Helper function to create a basic EpubBook object with common metadata."""
    book = epub.EpubBook()
    if add_default_metadata:
        if identifier: book.set_identifier(identifier)
        if title: book.set_title(title)
        if lang: book.set_language(lang)
        if author: book.add_author(author)
        book.add_metadata('DC', 'publisher', 'PhiloGraph Testing Inc.')
        book.add_metadata('DC', 'date', '2025-05-09', others={'event': 'publication'})
    
    if custom_metadata: # For adding specific or overriding metadata
        for prefix, name, value, others_dict in custom_metadata: 
            book.add_metadata(prefix, name, value, others=others_dict)
    return book

def _add_epub_chapters(book, chapter_details, default_style_item=None):
    """Helper to add chapters to the book and return chapter objects.
       Can link a default style item to all chapters."""
    chapters = []
    for i, detail in enumerate(chapter_details):
        ch_title = detail.get("title", f"Chapter {i+1}")
        ch_filename = detail.get("filename", f"chap_{i+1:02}.xhtml")
        ch_content = detail.get("content", f"<h1>{ch_title}</h1><p>Content for {ch_title}.</p>")
        
        chapter = epub.EpubHtml(title=ch_title, file_name=ch_filename, lang=book.language)
        chapter.content = ch_content
        if default_style_item:
            chapter.add_item(default_style_item)
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

# Call this once if common.py is imported, or ensure main runner calls it.
# For now, let's assume the main runner will call ensure_output_directories().