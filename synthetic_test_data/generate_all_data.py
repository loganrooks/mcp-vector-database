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
    generate_epubs.create_epub_ncx_with_pagelist()
    generate_epubs.create_epub_missing_ncx()
    generate_epubs.create_epub_navdoc_full()
    generate_epubs.create_epub_ncx_links_to_anchors()
    generate_epubs.create_epub_ncx_problematic_entries()
    generate_epubs.create_epub_ncx_inconsistent_depth()
    generate_epubs.create_epub_ncx_lists_footnote_files()
    generate_epubs.create_epub_html_toc_p_tags()
    generate_epubs.create_epub_html_toc_non_linked()

    # EPUBs - Headers
    generate_epubs.create_epub_p_tag_headers()
    generate_epubs.create_epub_headers_with_edition_markers()
    generate_epubs.create_epub_taylor_hegel_headers()
    generate_epubs.create_epub_sennet_style_headers()
    generate_epubs.create_epub_div_style_headers()
    generate_epubs.create_epub_header_mixed_content()
    generate_epubs.create_epub_header_rosenzweig_hegel()
    generate_epubs.create_epub_header_derrida_gift_death()
    generate_epubs.create_epub_header_bch_p_strong()
    generate_epubs.create_epub_header_derrida_specters_p()
    generate_epubs.create_epub_header_kaplan_div()
    generate_epubs.create_epub_header_descartes_dict_p()
    generate_epubs.create_epub_header_foucault_style()

    # EPUBs - Notes
    generate_epubs.create_epub_same_page_footnotes()
    generate_epubs.create_epub_endnotes_separate_file()
    generate_epubs.create_epub_kant_style_footnotes()
    generate_epubs.create_epub_hegel_sol_style_footnotes()
    generate_epubs.create_epub_dual_note_system()
    generate_epubs.create_epub_pippin_style_endnotes()
    generate_epubs.create_epub_heidegger_ge_style_endnotes()
    generate_epubs.create_epub_heidegger_metaphysics_style_footnotes()
    generate_epubs.create_epub_footnote_hegel_sol_ref()
    generate_epubs.create_epub_footnote_hegel_por_author()
    generate_epubs.create_epub_footnote_marx_engels_reader()
    generate_epubs.create_epub_footnote_marcuse_dual_style()
    generate_epubs.create_epub_footnote_adorno_unlinked()
    generate_epubs.create_epub_footnote_derrida_grammatology_dual()

    # EPUBs - Citations & Bibliography
    generate_epubs.create_epub_citation_kant_intext()
    generate_epubs.create_epub_citation_taylor_intext_italic()
    generate_epubs.create_epub_citation_rosenzweig_biblioref()

    # EPUBs - Page Numbers & Edition Markers
    generate_epubs.create_epub_pagenum_semantic_pagebreak()
    generate_epubs.create_epub_pagenum_kant_anchor()
    generate_epubs.create_epub_pagenum_taylor_anchor()
    generate_epubs.create_epub_pagenum_deleuze_plain_text()
    
    # EPUBs - Images & Fonts
    generate_epubs.create_epub_image_as_special_text()
    generate_epubs.create_epub_font_obfuscated()

    # EPUBs - Structure & Metadata
    generate_epubs.create_epub_minimal_metadata()
    generate_epubs.create_epub2_with_guide()
    generate_epubs.create_epub_opf_specific_meta()
    generate_epubs.create_epub_spine_pagemap_ref()
    generate_epubs.create_epub_structure_split_files()
    generate_epubs.create_epub_structure_calibre_artifacts()
    generate_epubs.create_epub_structure_adobe_artifacts()
    generate_epubs.create_epub_accessibility_epub_type()
    
    # EPUBs - Content Types & Misc
    generate_epubs.create_epub_poetry()
    generate_epubs.create_epub_content_dialogue()
    generate_epubs.create_epub_content_epigraph()
    generate_epubs.create_epub_content_blockquote_styled()
    generate_epubs.create_epub_content_internal_cross_refs()
    generate_epubs.create_epub_content_forced_page_breaks()

    # PDFs
    generate_pdfs.create_pdf_text_single_column()
    generate_pdfs.create_pdf_text_multi_column()
    generate_pdfs.create_pdf_text_flow_around_image()
    generate_pdfs.create_pdf_simulated_ocr_high_quality()
    generate_pdfs.create_pdf_with_bookmarks()
    generate_pdfs.create_pdf_visual_toc_hyperlinked()
    generate_pdfs.create_pdf_running_headers_footers()
    generate_pdfs.create_pdf_bottom_page_footnotes()
    generate_pdfs.create_pdf_simple_table()

    # Markdown
    generate_markdown.create_md_basic_elements()
    generate_markdown.create_md_extended_elements()
    generate_markdown.create_md_json_frontmatter()
    generate_markdown.create_md_error_frontmatter()
    generate_markdown.create_md_no_frontmatter()
    generate_markdown.create_md_with_embedded_html()
    generate_markdown.create_md_with_latex()
    
    print("Synthetic data generation script finished.")

if __name__ == "__main__":
    main()