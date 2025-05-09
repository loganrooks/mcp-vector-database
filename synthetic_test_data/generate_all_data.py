import os
from .common import ensure_output_directories
from . import generate_epubs
from . import generate_pdfs
from . import generate_markdown

def main():
    print("Starting synthetic data generation...")
    
    # Ensure all output directories exist
    ensure_output_directories()

    # EPUBs - TOC
    generate_epubs.create_epub_ncx_simple()
    generate_epubs.create_epub_ncx_nested()
    generate_epubs.create_epub_html_toc_linked()

    # EPUBs - Headers
    generate_epubs.create_epub_p_tag_headers()
    generate_epubs.create_epub_headers_with_edition_markers()

    # EPUBs - Notes
    generate_epubs.create_epub_same_page_footnotes()
    generate_epubs.create_epub_endnotes_separate_file()
    generate_epubs.create_epub_kant_style_footnotes()
    generate_epubs.create_epub_hegel_sol_style_footnotes()
    generate_epubs.create_epub_dual_note_system()

    # EPUBs - Metadata & Content Types
    generate_epubs.create_epub_minimal_metadata()
    generate_epubs.create_epub_poetry()

    # PDFs
    generate_pdfs.create_pdf_text_single_column()

    # Markdown
    generate_markdown.create_md_basic_elements()
    generate_markdown.create_md_extended_elements()
    
    # Future EPUBs to implement from generate_epubs.py:
    # generate_epubs.create_epub_ncx_page_list()
    # generate_epubs.create_epub_missing_ncx()
    # generate_epubs.create_epub_epub3_navdoc_full()
    # generate_epubs.create_epub_with_page_map()
    # generate_epubs.create_epub_with_embedded_image()
    # generate_epubs.create_epub_with_embedded_font()
    # generate_epubs.create_epub_calibre_style()
    # generate_epubs.create_epub_error_opf()


    # Future PDFs to implement from generate_pdfs.py:
    # generate_pdfs.create_pdf_multi_column_text()
    # generate_pdfs.create_pdf_with_images_tables()
    # generate_pdfs.create_pdf_scanned_simulated() # If feasible
    # generate_pdfs.create_pdf_ligatures()
    # generate_pdfs.create_pdf_corrupted_simulated()


    # Future Markdown to implement from generate_markdown.py:
    # generate_markdown.create_md_json_frontmatter()
    # generate_markdown.create_md_no_frontmatter()
    # generate_markdown.create_md_with_html()
    # generate_markdown.create_md_with_latex()

    print("Synthetic data generation script finished.")

if __name__ == "__main__":
    main()