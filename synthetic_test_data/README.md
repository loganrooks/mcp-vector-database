# Synthetic Test Data for PhiloGraph

This directory contains synthetic test data generated for testing the PhiloGraph application. The data includes EPUB, PDF (planned), and Markdown files designed to cover various formatting, content types, and edge cases as specified in [`../../docs/qa/synthetic_data_requirements.md`](../../docs/qa/synthetic_data_requirements.md).

## Generation

The files in this directory can be (re)generated using the `generate_all_data.py` script located in this directory.
The generation logic has been refactored into modular scripts:
*   `common.py`: Shared utilities and constants.
*   `epub_generators/` (package): Contains modularized EPUB generation functions (e.g., `toc.py`, `headers.py`, etc.). The old `generate_epubs.py` is now a placeholder.
*   `generate_pdfs.py`: PDF generation functions.
*   `generate_markdown.py`: Markdown generation functions.
*   `generate_all_data.py`: Main script to run all generation.

To run the main generation script:
```bash
python3 generate_all_data.py
```

Ensure you have the necessary dependencies installed, particularly `EbookLib` for EPUB generation and `reportlab` for PDF generation. You can install dependencies from the project's main `requirements.txt`:
```bash
pip3 install -r ../requirements.txt 
```
(Adjust path to `requirements.txt` if running from a different working directory).

## Structure

The data is organized by file type and then by the specific feature or edge case being tested. All generated files are output into the `generated/` subdirectory. Refer to [`../../docs/qa/synthetic_data_requirements.md`](../../docs/qa/synthetic_data_requirements.md) for the detailed proposed structure.

## Generated Files

The `generate_all_data.py` script creates the following synthetic files within the `generated/` directory:

### EPUB (`generated/epub/`)

**Table of Contents (`toc/`):**
*   `ncx_simple.epub`: Simple NCX ToC.
*   `ncx_nested.epub`: Nested NCX ToC.
*   `html_toc_linked.epub`: HTML Linked ToC.
*   `ncx_page_list.epub`: NCX with PageList.
*   `missing_ncx.epub`: Missing NCX (NavDoc only).
*   `navdoc_full.epub`: Full EPUB 3 NavDoc (ToC, Landmarks, PageList).
*   `ncx_links_to_anchors.epub`: NCX with navPoints linking to anchors within content files.
*   `ncx_problematic_entries.epub`: NCX with problematic entries (e.g., very long navLabel).
*   `ncx_inconsistent_depth.epub`: NCX with structurally inconsistent depth.
*   `ncx_lists_footnote_files.epub`: NCX listing individual footnote files.
*   `html_toc_p_tags.epub`: HTML ToC structured with `<p>` tags and classes.
*   `html_toc_non_linked.epub`: HTML ToC with non-hyperlinked entries.

**Headers (`headers/`):**
*   `p_tag_headers.epub`: Styled `<p>` Tag Headers.
*   `headers_edition_markers.epub`: Headers with Edition Markers.
*   `taylor_hegel_headers.epub`: Taylor/Hegel Style Headers.
*   `sennet_style_headers.epub`: Sennet-Style Headers.
*   `div_style_headers.epub`: Div-Style Headers.
*   `header_mixed_content.epub`: Headers with mixed content (e.g., `<h2>Title <small>Subtitle</small></h2>`).
*   `header_rosenzweig_hegel.epub`: Rosenzweig "Hegel and the State" style header.
*   `header_derrida_gift_death.epub`: Derrida "Gift of Death" style header.
*   `header_bch_p_strong.epub`: Byung-Chul Han style `<p>` with `<strong>` header.
*   `header_derrida_specters_p.epub`: Derrida "Specters of Marx" style `<p>` headers for number and title.
*   `header_kaplan_div.epub`: Kaplan style `<div>` based chapter number and title.
*   `header_descartes_dict_p.epub`: Descartes Dictionary style `<p>` headers for various levels.
*   `header_foucault_style.epub`: Foucault-style header with number, rule, and title in one `<h1>`.

**Notes (`notes/`):**
*   `same_page_footnotes.epub`: Same-Page Hyperlinked Footnotes.
*   `endnotes_separate_file.epub`: Endnotes in Separate File.
*   `kant_style_footnotes.epub`: Kant-Style Same-Page Footnotes.
*   `hegel_sol_footnotes.epub`: Hegel SoL-Style Same-Page Footnotes.
*   `dual_note_system.epub`: Dual Note System (Author Footnotes, Editor Endnotes).
*   `pippin_style_endnotes.epub`: Pippin-Style Endnotes.
*   `heidegger_ge_endnotes.epub`: Heidegger (German Existentialism) Style Endnotes.
*   `heidegger_metaphysics_footnotes.epub`: Heidegger (Metaphysics) Style Same-Page Footnotes.
*   `footnote_hegel_sol_ref.epub`: Hegel "Science of Logic" footnote reference style.
*   `footnote_hegel_por_author.epub`: Hegel "Philosophy of Right" author footnote style (dagger).
*   `footnote_marx_engels_reader.epub`: Marx & Engels Reader footnote reference style.
*   `footnote_marcuse_dual_style.epub`: Marcuse dual footnote style (asterisk and numbered).
*   `footnote_adorno_unlinked.epub`: Adorno unlinked footnote style.
*   `footnote_derrida_grammatology_dual.epub`: Derrida "Of Grammatology" dual footnote system.

**Citations & Bibliography (`citations_bibliography/`):**
*   `citation_kant_intext.epub`: Kant-style in-text citations (e.g., `(KrV, A 84/B 116)`).
*   `citation_taylor_intext_italic.epub`: Taylor-style in-text citations (plain text with `<em>` for titles).
*   `citation_rosenzweig_biblioref.epub`: Rosenzweig style `epub:type="biblioref"` and bibliography.

**Page Numbers & Edition Markers (`page_numbers/`):**
*   `pagenum_semantic_pagebreak.epub`: EPUB 3 semantic pagebreaks (`<span epub:type="pagebreak">`).
*   `pagenum_kant_anchor.epub`: Kant-style anchor-based page markers (`<a id="page_XXX" class="calibre10">`).
*   `pagenum_taylor_anchor.epub`: Taylor-style anchor-based page markers (`<a id="page_X" class="calibre3">`).
*   `pagenum_deleuze_plain_text.epub`: Deleuze-style plain text page numbers embedded in content.

**Images & Fonts (`images_fonts/`):**
*   `image_as_special_text.epub`: Image used for special text/symbols.
*   `font_obfuscated.epub`: Simulates font obfuscation via `META-INF/encryption.xml` (structural indicator).

**Structure & Metadata (`structure_metadata/`):**
*   `minimal_metadata.epub`: Minimal/Missing Metadata.
*   `opf_specific_meta.epub`: Specific `<meta>` properties in OPF (title-type, calibre, Sigil, cover).
*   `spine_pagemap_ref.epub`: Spine referencing a (simulated) `page-map.xml`.
*   `split_file_chapter_main.epub`: Content split across multiple HTML files for a single logical chapter.
*   `calibre_artifacts.epub`: Simulates Calibre-specific metadata and `calibre_bookmarks.txt`.
*   `adobe_artifacts.epub`: Simulates Adobe converter artifacts (`.xpgt` reference, Adept meta tags).
*   `accessibility_epub_type.epub`: Demonstrates various `epub:type` semantic attributes.
*   `epub2_with_guide.epub`: EPUB 2.0 with a `<guide>` section in the OPF.

**Content Types & Misc. (`content_types/`):**
*   `poetry_formatting.epub`: Poetry Formatting.
*   `content_dialogue.epub`: Dialogue content.
*   `content_epigraph.epub`: Epigraphs.
*   `content_blockquote_styled.epub`: Styled blockquotes.
*   `content_internal_cross_refs.epub`: Internal cross-references.
*   `content_forced_page_breaks.epub`: Forced page breaks using CSS.

### PDF (`generated/pdf/`)

**Text Based (`text_based/`):**
*   `single_column.pdf`: Simple single-column text.
*   `multi_column.pdf`: Two-column layout.
*   `text_flow_around_image.pdf`: Simulated text flow around an image placeholder.

**Image Based OCR (`image_based_ocr/`):**
*   `simulated_ocr_hq.pdf`: Text simulating high-quality OCR output.

**Structure (`structure/`):**
*   `with_bookmarks.pdf`: Programmatically generated bookmark-based ToC.
*   `visual_toc_hyperlinked.pdf`: Visual, hyperlinked Table of Contents page.
*   `running_headers_footers.pdf`: Running headers and footers with page numbers.
*   `simple_table.pdf`: Simple table with clear borders.

**Notes (`notes/`):**
*   `bottom_page_footnotes.pdf`: Footnotes appearing at the bottom of the page (visual simulation).

### Markdown (`generated/markdown/`)

**Basic (`basic/`):**
*   `all_basic_elements.md`: Basic elements with YAML frontmatter.

**Extended (`extended/`):**
*   `extended_elements.md`: Tables, footnotes, task lists, code blocks with TOML frontmatter.

**Frontmatter (`frontmatter/`):**
*   `json_frontmatter.md`: JSON frontmatter.
*   `error_frontmatter.md`: Syntactically incorrect YAML frontmatter.
*   `no_frontmatter.md`: No frontmatter.

**General Edge Cases (`general_edge_cases/`):**
*   `embedded_html.md`: Embedded HTML (simple and complex/malformed).
*   `with_latex.md`: Embedded LaTeX expressions.

This list will be updated as more generation capabilities are added.