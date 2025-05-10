import os
from ebooklib import epub

# Define output base directory relative to the script's location
BASE_OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

EPUB_DIR = os.path.join(BASE_OUTPUT_DIR, "generated", "epub")
PDF_DIR = os.path.join(BASE_OUTPUT_DIR, "generated", "pdf")
MD_DIR = os.path.join(BASE_OUTPUT_DIR, "generated", "markdown")

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
    """Helper function to write the EPUB file, with basic custom file handling."""
    
    # Attempt to handle custom files that need to be added to the archive
    # Note: ebooklib places items in OEBPS by default. For META-INF or root files,
    # this approach is a simulation; true placement would require ZIP manipulation.
    if hasattr(book, 'custom_files_to_add'):
        for rel_path, content_bytes in book.custom_files_to_add.items():
            # Determine uid and media_type based on common cases or make them generic
            uid = os.path.splitext(os.path.basename(rel_path))[0].replace('.', '_') + "_custom"
            media_type = "application/xml" # Default, adjust if more types needed
            if rel_path.endswith(".txt"):
                media_type = "text/plain"
            
            # Create an EpubItem. file_name here will be relative to OEBPS or root of content items.
            # This won't correctly place META-INF/encryption.xml at META-INF/encryption.xml
            # It will likely be OEBPS/META-INF/encryption.xml or similar.
            # This is a known limitation for this synthetic data generator using only ebooklib.
            custom_item = epub.EpubItem(uid=uid, file_name=rel_path, media_type=media_type, content=content_bytes)
            book.add_item(custom_item)
            print(f"Note: Added custom file '{rel_path}' as item '{custom_item.file_name}' (actual EPUB path may vary due to ebooklib structure).")

    # Add extra manifest items if specified (e.g., for .xpgt files not directly handled as content)
    if hasattr(book, 'manifest_extra_items'):
        for item_attrs in book.manifest_extra_items:
            # These items are primarily for manifest inclusion. Content might be dummy or not added to zip by ebooklib if href is unusual.
            # This is a simulation of manifest entries.
            uid = item_attrs.get('id', os.path.splitext(os.path.basename(item_attrs['href']))[0] + "_manifest_extra")
            # Create a minimal EpubItem to get it into the manifest.
            # Content is not strictly necessary if it's just a manifest reference to an externally placed file (like META-INF).
            # However, ebooklib requires content for EpubItem.
            extra_item = epub.EpubItem(uid=uid,
                                       file_name=item_attrs['href'], # This path will be relative to OEBPS
                                       media_type=item_attrs['media_type'],
                                       content=b'<!-- Placeholder for manifest-only item -->')
            book.add_item(extra_item)
            print(f"Note: Added manifest extra item for '{item_attrs['href']}'.")

    # ebooklib should handle book.guide for EPUB 2 if set.
    # No special handling needed here for book.guide beyond ensuring it's set on the book object
    # in the calling function (e.g., create_epub2_with_guide).

    try:
        epub.write_epub(filepath, book, {})
        print(f"Successfully created EPUB: {filepath}")
    except Exception as e:
        print(f"Error creating EPUB {filepath}: {e}")

# Call this once if common.py is imported, or ensure main runner calls it.
# For now, let's assume the main runner will call ensure_output_directories().