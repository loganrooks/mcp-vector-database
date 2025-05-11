import os
from ebooklib import epub
from ..common import EPUB_DIR, _create_epub_book, _add_epub_chapters, _write_epub_file

def create_epub2_with_guide(filename="epub2_with_guide.epub"):
    """
    Creates an EPUB 2.0 file with a typical Guide section in the OPF.
    """
    filepath = os.path.join(EPUB_DIR, "structure_metadata", filename)
    book = _create_epub_book("synth-epub2-guide-001", "EPUB 2.0 with Guide")
    book.epub_version = "2.0"

    css_content = "BODY { font-family: 'Liberation Serif', serif; color: #111; }"
    style_item = epub.EpubItem(uid="style_epub2_guide", file_name="style/epub2_guide.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    # Cover page (dummy)
    cover_html_content = "<html><head><title>Cover</title></head><body><h1>My EPUB2 Book</h1><p>(Cover Image Placeholder)</p></body></html>"
    cover_page = epub.EpubHtml(title="Cover", file_name="cover.xhtml", lang="en")
    cover_page.content = cover_html_content
    cover_page.add_item(style_item)
    book.add_item(cover_page)
    # book.add_metadata('OPF', 'cover', 'cover-image') # Commenting out as no actual image item is defined

    # ToC page (HTML)
    toc_html_content = """<h1>Table of Contents</h1>
<ul>
  <li><a href="chapter1_epub2.xhtml">Chapter 1: The Old Ways</a></li>
  <li><a href="chapter2_epub2.xhtml">Chapter 2: New Perspectives</a></li>
</ul>"""
    toc_page = epub.EpubHtml(title="Table of Contents", file_name="toc_epub2.xhtml", lang="en")
    toc_page.content = toc_html_content
    toc_page.add_item(style_item)
    book.add_item(toc_page)

    chapter_details = [
        {"title": "Chapter 1: The Old Ways", "filename": "chapter1_epub2.xhtml", "content": "<h1>Chapter 1</h1><p>Content for an EPUB2 chapter.</p>"},
        {"title": "Chapter 2: New Perspectives", "filename": "chapter2_epub2.xhtml", "content": "<h1>Chapter 2</h1><p>More content here.</p>"}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    # Define Guide items
    # ebooklib doesn't directly create the <guide> section in OPF in a straightforward way.
    # It's usually inferred or would require OPF template manipulation.
    # We'll add custom metadata to signify the intent for the guide.
    # Define Guide items
    # Define Guide items
    # ebooklib expects book.guide to be a list of dictionaries.
    # Set to empty list if not defining specific guide items to avoid NoneType iteration.
    book.guide = [] 
    # Example of how guide items might be structured for ebooklib if it supported more direct creation:
    # book.guide.append({'type': 'cover', 'title': 'Cover Page', 'href': 'cover.xhtml'})
    # book.guide.append({'type': 'toc', 'title': 'Table of Contents', 'href': 'toc_epub2.xhtml'})
    # book.guide.append({'type': 'text', 'title': 'Start Reading', 'href': 'chapter1_epub2.xhtml'})
    # Actual generation of the <guide> section in OPF is handled by ebooklib based on this.

    book.toc = (
        epub.Link(chapters[0].file_name, chapters[0].title, "c1_epub2_toc"),
        epub.Link(chapters[1].file_name, chapters[1].title, "c2_epub2_toc")
    )
    book.add_item(epub.EpubNcx())
    # No EPUB3 NavDoc for a pure EPUB2 example usually, NCX is primary.
    
    # Typical EPUB2 spine order
    book.spine = [cover_page, toc_page] + chapters # Restored original spine based on feedback log
    _write_epub_file(book, filepath)

def create_epub_opf_specific_meta(filename="opf_specific_meta.epub"):
    """
    Creates an EPUB with specific <meta> properties in content.opf.
    e.g., title-type, calibre, Sigil, cover.
    """
    filepath = os.path.join(EPUB_DIR, "structure_metadata", filename)
    book = _create_epub_book("synth-epub-opf-meta-001", "OPF Specific Metadata EPUB")
    book.epub_version = "3.0" # Can be EPUB2 or 3

    # Standard DC metadata
    book.add_author("A. Synthesizer")
    book.set_language("fr") # Example of non-English
    book.set_identifier("urn:uuid:fakedcidentifier001") # scheme is part of set_identifier in some libs, or done via add_metadata for more control
    # To be more precise with scheme for DC identifier:
    # book.add_metadata('DC', 'identifier', 'urn:uuid:fakedcidentifier001', others={'id': 'pub-id', 'opf:scheme': 'URN'})
    # For simplicity with ebooklib's direct method, we'll use set_identifier.
    # If scheme is critical, the add_metadata approach is better.
    # Let's stick to set_identifier for now as it's simpler and likely what was intended.
    
    # Specific <meta> properties
    # ebooklib handles 'cover' via set_cover or by finding item with id 'cover' or properties 'cover-image'.
    # For other meta tags, we use add_metadata with namespace 'OPF' (ebooklib default for opf meta) or None.
    book.add_metadata(None, 'meta', '', {'property': 'title-type', 'refines': '#' + book.uid + '_title', '_text': 'main'})
    # book.add_metadata(None, 'meta', '', {'property': 'title-type', 'refines': '#' + book.uid + '_title_alt', '_text': 'subtitle'}) # Requires another dc:title for subtitle
    book.add_metadata('OPF', 'meta', 'calibre:series', {'name': 'calibre:series', 'content': 'Synthetic Philosophy'})
    book.add_metadata('OPF', 'meta', 'calibre:series_index', {'name': 'calibre:series_index', 'content': '1.0'})
    book.add_metadata('OPF', 'meta', 'Sigil version', {'name': 'Sigil version', 'content': '1.9.30'})
    
    # Add a dummy cover image and set it to test the <meta name="cover" ...>
    dummy_cover_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\xfa\x0f\x00\x01\x05\x01\xfe\xa8\xcd\xf6\x00\x00\x00\x00IEND\xaeB`\x82' # 1x1 white PNG
    book.set_cover("cover_image.png", dummy_cover_content) # This should generate the <meta name="cover" content="cover">

    chapter_details = [
        {"title": "Chapter with Rich OPF Meta", "filename": "c1_opf_meta.xhtml", 
         "content": "<h1>Metadata Matters</h1><p>This EPUB focuses on testing the generation and parsing of specific OPF metadata fields.</p>"}
    ]
    chapters = _add_epub_chapters(book, chapter_details)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_opf_meta_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav', 'cover'] + chapters # 'cover' is the conventional ID for the cover image item
    _write_epub_file(book, filepath)

def create_epub_spine_pagemap_ref(filename="spine_pagemap_ref.epub"):
    """
    Creates an EPUB where the spine references a page-map.xml.
    Simulates Zizek, Marcuse examples.
    """
    filepath = os.path.join(EPUB_DIR, "structure_metadata", filename)
    book = _create_epub_book("synth-epub-spine-pagemap-001", "Spine with Page-Map Ref EPUB")

    # Dummy page-map.xml content
    page_map_xml_content = u"""<?xml version="1.0" encoding="UTF-8"?>
<page-map xmlns="http://www.idpf.org/2007/opf">
  <page name="1" href="content/chapter1_pm.xhtml#page_1"/>
  <page name="2" href="content/chapter1_pm.xhtml#page_2"/>
  <page name="3" href="content/chapter2_pm.xhtml#page_3"/>
</page-map>
"""
    # Add page-map.xml to the book items.
    # ebooklib places items in OEBPS by default. Path needs to be relative to OPF.
    page_map_item = epub.EpubItem(uid="page_map_xml", file_name="page-map.xml", media_type="application/oebps-page-map+xml", content=page_map_xml_content.encode('utf-8'))
    book.add_item(page_map_item)

    chapter_details = [
        {"title": "Chapter One (Page Mapped)", "filename": "content/chapter1_pm.xhtml", 
         "content": "<h1>Chapter 1</h1><p>Page 1 content.<a id='page_1'/></p><p>Page 2 content.<a id='page_2'/></p>"},
        {"title": "Chapter Two (Page Mapped)", "filename": "content/chapter2_pm.xhtml", 
         "content": "<h1>Chapter 2</h1><p>Page 3 content.<a id='page_3'/></p>"}
    ]
    chapters = _add_epub_chapters(book, chapter_details)
    
    book.toc = (
        epub.Link(chapters[0].file_name, chapters[0].title, "c1_pm_toc"),
        epub.Link(chapters[1].file_name, chapters[1].title, "c2_pm_toc")
    )
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Add page_map_item to spine with linear="no"
    # ebooklib spine items are typically EpubHtml or similar content docs.
    # To add a non-linear item like page-map.xml to the spine, it's usually done by
    # ensuring it's in the manifest and then the OPF generator might handle it.
    # ebooklib's spine is primarily for linear reading order.
    # We will ensure it's in the manifest. The test is to see if `page-map.xml` is present
    # and if an OPF generator *could* reference it in the spine.
    # For simulation, we'll add its id to book.spine_extra_nonlinear_ids if we modify _write_epub_file
    book.custom_opf_fields = {
        "spine_nonlinear_ids": [page_map_item.id]
    }
    # This custom_opf_fields would need to be handled by _write_epub_file to modify the OPF output.

    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_structure_split_files(filename_pattern="split_file_chapter_{}.epub", num_splits=3):
    """
    Creates an EPUB with content split across multiple HTML files for a single logical chapter.
    Simulates Kant, Hegel SoL _split_YYY.html structure.
    Generates one EPUB for the entire "chapter".
    """
    main_filename = filename_pattern.format("main")
    filepath = os.path.join(EPUB_DIR, "structure_metadata", main_filename)
    
    book_title = "Split File Chapter EPUB"
    book_id = f"synth-epub-struct-split-{os.path.splitext(main_filename)[0]}"
    book = _create_epub_book(book_id, book_title)

    css_content = "BODY { font-family: 'Verdana', sans-serif; color: #2c3e50; }"
    style_item = epub.EpubItem(uid="style_split_file", file_name="style/split_file.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    split_chapters = []
    toc_links = []

    base_xhtml_name = "chapter1_split_{:03d}.xhtml"
    
    # Part 1
    ch1_part1_content = """<h1>The Grand Argument (Part 1)</h1>
<p>This is the beginning of a chapter that is split into multiple files. 
This first part introduces the main thesis.</p>
<p>Philosophical arguments often require extensive elaboration, necessitating such splits in digital formats for manageability or due to conversion artifacts.</p>
<p><em>Continuation in next part...</em></p>"""
    ch1_part1_fn = base_xhtml_name.format(1)
    ch1_part1 = epub.EpubHtml(title="The Grand Argument - Part 1", file_name=ch1_part1_fn, lang="en")
    ch1_part1.content = ch1_part1_content
    ch1_part1.add_item(style_item)
    book.add_item(ch1_part1)
    split_chapters.append(ch1_part1)
    toc_links.append(epub.Link(ch1_part1.file_name, "Chapter 1, Part 1", "c1p1_split_toc"))

    # Part 2
    ch1_part2_content = """<h2>The Grand Argument (Part 2)</h2>
<p>This is the second part of the split chapter, continuing the argument from the previous file.</p>
<p>Here, we delve into supporting evidence and counter-arguments.</p>
<p><em>Further details in the final part...</em></p>"""
    ch1_part2_fn = base_xhtml_name.format(2)
    ch1_part2 = epub.EpubHtml(title="The Grand Argument - Part 2", file_name=ch1_part2_fn, lang="en")
    ch1_part2.content = ch1_part2_content
    ch1_part2.add_item(style_item)
    book.add_item(ch1_part2)
    split_chapters.append(ch1_part2)
    toc_links.append(epub.Link(ch1_part2.file_name, "Chapter 1, Part 2", "c1p2_split_toc"))
    
    # Part 3 (Final)
    ch1_part3_content = """<h2>The Grand Argument (Part 3 - Conclusion)</h2>
<p>The final part of this split chapter, bringing the argument to a close.</p>
<p>This structure tests how well systems can reassemble or navigate content spread across multiple physical files but representing a single logical unit.</p>"""
    ch1_part3_fn = base_xhtml_name.format(3)
    ch1_part3 = epub.EpubHtml(title="The Grand Argument - Part 3", file_name=ch1_part3_fn, lang="en")
    ch1_part3.content = ch1_part3_content
    ch1_part3.add_item(style_item)
    book.add_item(ch1_part3)
    split_chapters.append(ch1_part3)
    toc_links.append(epub.Link(ch1_part3.file_name, "Chapter 1, Part 3", "c1p3_split_toc"))
    
    book.toc = tuple(toc_links)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + split_chapters
    _write_epub_file(book, filepath)

def create_epub_structure_calibre_artifacts(filename="calibre_artifacts.epub"):
    """
    Creates an EPUB that simulates Calibre-specific artifacts.
    e.g., calibre_bookmarks.txt, separate metadata.opf (though ebooklib merges into one content.opf).
    Focuses on adding Calibre-specific metadata to the main OPF.
    """
    filepath = os.path.join(EPUB_DIR, "structure_metadata", filename)
    book = _create_epub_book("synth-epub-calibre-artifacts-001", "Calibre Artifacts EPUB")

    # Add Calibre-specific metadata
    book.add_metadata('OPF', 'meta', 'calibre:timestamp', {'name': 'calibre:timestamp', 'content': '2024-01-15T10:30:00+00:00'})
    book.add_metadata('OPF', 'meta', 'calibre:series', {'name': 'calibre:series', 'content': 'Calibre Test Series'})
    book.add_metadata('OPF', 'meta', 'calibre:series_index', {'name': 'calibre:series_index', 'content': '3'})
    book.add_metadata('OPF', 'meta', 'calibre:author_link_map', {'name': 'calibre:author_link_map', 'content': '{"A. Calibre User": ""}'})
    book.add_author("A. Calibre User") # Ensure author matches link map for consistency

    # Simulate calibre_bookmarks.txt by adding it as a non-linear item.
    # Its actual content and format are complex, so we'll use placeholder text.
    bookmarks_content = """
[
    {
        "format": "EPUB",
        "title": "Calibre Artifacts EPUB",
        "bookmarks": [
            {
                "type": "last-read",
                "pos": "epubcfi(/6/2[chapter_1]!/4/2/1:0)" 
            }
        ]
    }
]
"""
    # ebooklib doesn't have a direct way to add files like calibre_bookmarks.txt outside OEBPS
    # or to ensure they are not in the spine.
    # We'll add a custom attribute to signify this, for potential handling in _write_epub_file.
    book.custom_files_to_add = {
        "calibre_bookmarks.txt": bookmarks_content.encode('utf-8') # Placed at root of EPUB
    }
    # This function is incomplete. Adding basic chapter, ToC, and write for now.
    chapter_details = [
        {"title": "Calibre Artifacts Chapter", "filename": "c1_calibre_artifact.xhtml", 
         "content": "<h1>Calibre Processed</h1><p>This chapter is in a book with Calibre-specific metadata and simulated artifact files.</p>"}
    ]
    chapters = _add_epub_chapters(book, chapter_details)
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_calibre_artifact_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)


def create_epub_structure_adobe_artifacts(filename="adobe_artifacts.epub"):
    """
    Creates an EPUB simulating Adobe converter artifacts like .xpgt references
    and Adept meta tags in the OPF.
    """
    filepath = os.path.join(EPUB_DIR, "structure_metadata", filename)
    book = _create_epub_book("synth-epub-adobe-artifacts-001", "Adobe Artifacts EPUB")
    book.epub_version = "2.0" # Often seen with older Adobe-processed files

    # Add Adobe-specific meta tags to OPF
    # These are typically related to Adobe Digital Editions DRM or layout.
    book.add_metadata('OPF', 'meta', 'adept_expected_resource', 
                      {'name': 'Adept.expected.resource', 
                       'content': 'urn:uuid:adept-document-id-placeholder'})
    book.add_metadata('OPF', 'meta', 'adept_resource',
                      {'name': 'Adept.resource', 
                       'content': 'urn:uuid:adept-document-id-placeholder'}) 
                       # In real files, this might point to an encryption.xml or rights file.

    # Simulate reference to an .xpgt (Adobe Page Template) file in manifest
    # The .xpgt file itself is complex XML; we'll just add a manifest item.
    # ebooklib doesn't directly support adding items with arbitrary paths like META-INF for encryption.xml
    # or specific handling for .xpgt files beyond being a generic item.
    # We'll add a dummy item to the manifest.
    dummy_xpgt_content = "<?xml version='1.0' encoding='UTF-8'?><ade:template xmlns:ade='http://ns.adobe.com/digitaleditions/ २०७८/page-template'></ade:template>".encode('utf-8')
    # xpgt_item = epub.EpubItem(uid="adobe_page_template", 
    #                           file_name="META-INF/template.xpgt", # Desired path
    #                           media_type="application/vnd.adobe-page-template+xml", 
    #                           content=dummy_xpgt_content)
    # book.add_item(xpgt_item) # This would place it in OEBPS.
    # The manifest_extra_items will add this to the book items.
    # The custom_files_to_add logic in _write_epub_file also adds it as a book item, causing duplication.
    # Relying on manifest_extra_items to create the item.
    # if not hasattr(book, 'custom_files_to_add'):
    #     book.custom_files_to_add = {}
    # book.custom_files_to_add["META-INF/template.xpgt"] = dummy_xpgt_content # This was noted as causing duplication
    
    # Relying on custom_files_to_add (and its handling in _write_epub_file) to add META-INF/template.xpgt
    # Removing manifest_extra_items for this entry to avoid duplication.
    # Also ensure _write_epub_file can handle adding this file if not just a manifest entry.
    if not hasattr(book, 'custom_files_to_add'):
        book.custom_files_to_add = {}
    book.custom_files_to_add["META-INF/template.xpgt"] = dummy_xpgt_content


    chapter_details = [
        {"title": "Chapter with Adobe Artifacts", "filename": "c1_adobe.xhtml", 
         "content": "<h1>Adobe Processed Content</h1><p>This EPUB simulates characteristics of a file processed by Adobe software, "
                    "which might include specific meta tags in the OPF and references to Adobe Page Template (.xpgt) files.</p>"}
    ]
    chapters = _add_epub_chapters(book, chapter_details)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_adobe_toc"),)
    book.add_item(epub.EpubNcx())
    # No NavDoc for this EPUB2 example
    # For EPUB 2, NCX is primary navigation, referenced in OPF, not typically in spine like EPUB3 NavDoc.
    book.spine = chapters
    _write_epub_file(book, filepath)

def create_epub_accessibility_epub_type(filename="accessibility_epub_type.epub"):
    """
    Creates an EPUB 3 demonstrating various epub:type semantic attributes for accessibility.
    """
    filepath = os.path.join(EPUB_DIR, "structure_metadata", filename)
    book = _create_epub_book("synth-epub-a11y-types-001", "EPUB Accessibility Types")
    book.epub_version = "3.0"

    css_content = """
    body { font-family: sans-serif; }
    section[epub|type~="doc-chapter"] { border-left: 3px solid blue; padding-left: 10px; margin-bottom: 15px; }
    h1[epub|type~="title"] { color: blue; }
    aside[epub|type~="footnote"] { font-size: 0.9em; border: 1px solid #ccc; padding: 5px; margin-top: 5px; background: #f9f9f9;}
    p[epub|type~="credit"] { font-style: italic; text-align: center; font-size:0.8em; }
    """
    style_item = epub.EpubItem(uid="style_a11y", file_name="style/a11y.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    intro_content = """<section epub:type="doc-introduction" id="intro">
  <h1 epub:type="title">Introduction to Semantic EPUB</h1>
  <p>This document demonstrates the use of <code>epub:type</code> attributes to enhance accessibility and semantic understanding of EPUB content.</p>
</section>"""
    intro_page = epub.EpubHtml(title="Introduction", file_name="intro_a11y.xhtml", lang="en")
    intro_page.content = intro_content
    intro_page.add_item(style_item)
    book.add_item(intro_page)

    chapter1_content = """<section epub:type="doc-chapter" id="ch1">
  <h1 epub:type="title">Chapter 1: Core Concepts</h1>
  <p>This chapter explores core concepts related to semantic markup. We will discuss the importance of landmarks, notes, and other structural elements.</p>
  <p>Here is a reference to a note.<sup><a epub:type="noteref" href="#fn1">1</a></sup></p>
  <aside epub:type="footnote" id="fn1" role="doc-footnote">
    <p>1. This is a footnote, semantically marked up using <code>epub:type="footnote"</code>. 
    It could also be an <code>doc-endnote</code>. <a epub:type="backlink" href="#ch1">↩</a></p>
  </aside>
  <p epub:type="credit">Chapter illustration by A. Artist.</p>
</section>"""
    chapter1_page = epub.EpubHtml(title="Chapter 1", file_name="ch1_a11y.xhtml", lang="en")
    chapter1_page.content = chapter1_content
    chapter1_page.add_item(style_item)
    book.add_item(chapter1_page)

    # NavDoc with semantic types
    nav_html_content=u"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Navigation</title></head>
<body>
  <nav epub:type="toc" id="toc"><h1>Contents</h1><ol>
    <li><a href="intro_a11y.xhtml">Introduction</a></li>
    <li><a href="ch1_a11y.xhtml">Chapter 1: Core Concepts</a></li>
  </ol></nav>
  <nav epub:type="landmarks" hidden=""><h1>Landmarks</h1><ol>
    <li><a epub:type="doc-introduction" href="intro_a11y.xhtml#intro">Introduction</a></li>
    <li><a epub:type="bodymatter" href="ch1_a11y.xhtml#ch1">Start of Main Content</a></li>
  </ol></nav>
</body></html>"""
    nav_doc_item = epub.EpubHtml(title='Navigation', file_name='nav_a11y.xhtml', lang='en')
    nav_doc_item.content = nav_html_content
    nav_doc_item.properties.append('nav')
    book.add_item(nav_doc_item)
    
    book.toc = ( # Fallback NCX
        epub.Link(intro_page.file_name, "Introduction", "intro_a11y_ncx"),
        epub.Link(chapter1_page.file_name, "Chapter 1", "ch1_a11y_ncx")
    )
    book.add_item(epub.EpubNcx())
    book.spine = [nav_doc_item, intro_page, chapter1_page]
    _write_epub_file(book, filepath)

def create_epub_minimal_metadata(filename="minimal_metadata.epub"):
    filepath = os.path.join(EPUB_DIR, "structure_metadata", filename)
    book = _create_epub_book(identifier=None, title=None, author=None, lang=None, add_default_metadata=False)
    book.set_identifier("synth-epub-min-meta-001")
    book.set_title("Minimal Metadata Book")
    book.set_language("en")
    chapter_details = [{"title": "Vague Chapter", "filename": "chap_vague.xhtml", "content": """<h1>A Vague Chapter</h1><p>This chapter exists in a book with very little identifying information. 
            The purpose is to test how the system handles missing or sparse metadata fields.</p>
            <p>What can be inferred? What defaults are assumed?</p>"""}]
    chapters = _add_epub_chapters(book, chapter_details)
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "vague_chap_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    style = 'BODY {color: gray;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)