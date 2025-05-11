import os
from ebooklib import epub
from ..common import EPUB_DIR, _create_epub_book, _add_epub_chapters, _write_epub_file

def create_epub_pagenum_semantic_pagebreak(filename="pagenum_semantic_pagebreak.epub"):
    """
    Creates an EPUB with EPUB 3 semantic pagebreaks.
    Ref: <span aria-label="X" epub:type="pagebreak" id="Page_X" role="doc-pagebreak"/>
    (Heidegger - Metaphysics, Sartre example)
    """
    filepath = os.path.join(EPUB_DIR, "page_numbers", filename)
    book = _create_epub_book("synth-epub-pgnum-semantic-001", "EPUB3 Semantic Pagebreaks")
    book.epub_version = "3.0"

    css_content = """
    span[epub|type="pagebreak"] { display: block; text-align: center; margin: 0.5em 0; color: #999; font-size: 0.8em; }
    span[epub|type="pagebreak"]:before { content: "[Page " attr(aria-label) "]"; }
    BODY { font-family: 'Calibri', sans-serif; }
    """
    style_item = epub.EpubItem(uid="style_pgnum_semantic", file_name="style/pgnum_semantic.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_content = """<h1>Being and Time: A New Beginning</h1>
<p>The question of the meaning of Being must be posed anew. 
This is the introductory part of our inquiry.</p>
<span aria-label="12" epub:type="pagebreak" id="Page_12" role="doc-pagebreak"></span>
<p>We now turn to the existential analytic of Dasein. 
This marks page 12 of the original print edition.</p>
<p>Further elaborations on Dasein's being-in-the-world follow.</p>
<span aria-label="13" epub:type="pagebreak" id="Page_13" role="doc-pagebreak"></span>
<p>This content would correspond to page 13.</p>
"""
    chapter_details = [
        {"title": "Semantic Pagebreaks", "filename": "c1_pgnum_semantic.xhtml", "content": chapter_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_pgnum_semantic_toc"),)
    book.add_item(epub.EpubNcx())
    # Create a NavDoc with page-list
    nav_html_content=u"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Nav</title></head>
<body>
  <nav epub:type="toc" id="toc"><ol><li><a href="c1_pgnum_semantic.xhtml">Semantic Pagebreaks</a></li></ol></nav>
  <nav epub:type="page-list" hidden=""><ol>
    <li><a href="c1_pgnum_semantic.xhtml#Page_12">12</a></li>
    <li><a href="c1_pgnum_semantic.xhtml#Page_13">13</a></li>
  </ol></nav>
</body></html>"""
    nav_doc_item = epub.EpubHtml(title='Navigation', file_name='nav_pgnum.xhtml', lang='en')
    nav_doc_item.content = nav_html_content
    nav_doc_item.properties.append('nav')
    book.add_item(nav_doc_item)
    
    book.spine = [nav_doc_item] + chapters
    _write_epub_file(book, filepath)

def create_epub_pagenum_kant_anchor(filename="pagenum_kant_anchor.epub"):
    """
    Creates an EPUB with anchor-based page markers like Kant.
    Ref: <a id="page_XXX" class="calibre10"></a>
    """
    filepath = os.path.join(EPUB_DIR, "page_numbers", filename)
    book = _create_epub_book("synth-epub-pgnum-kant-anchor-001", "Kant Anchor Page Markers EPUB")
    # This function was incomplete, adding basic structure to make it runnable
    css_content = """
    a.calibre10-kantpage { /* Usually invisible, might have specific styling for debug */ }
    BODY { font-family: 'Times New Roman', serif; }
    """
    style_item = epub.EpubItem(uid="style_pgnum_kant_anchor", file_name="style/pgnum_kant_anchor.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_content = """<h1>Critique of Pure Reason - Page Markers</h1>
<p>This text simulates Kant-style page markers using anchors.<a id="page_A25" class="calibre10-kantpage"></a> 
The content here would correspond to page A25 of the first edition.</p>
<p>Further discussion continues, and here we mark page B40.<a id="page_B40" class="calibre10-kantpage"></a></p>
"""
    chapter_details = [
        {"title": "Kant Anchor Page Markers", "filename": "c1_kant_pgnum_anchor.xhtml", "content": chapter_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_kant_pgnum_anchor_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_pagenum_taylor_anchor(filename="pagenum_taylor_anchor.epub"):
    """
    Creates an EPUB with anchor-based page markers like Taylor's "Hegel".
    Ref: <a id="page_X" class="calibre3"></a>
    """
    filepath = os.path.join(EPUB_DIR, "page_numbers", filename)
    book = _create_epub_book("synth-epub-pgnum-taylor-anchor-001", "Taylor Anchor Page Markers EPUB")

    css_content = """
    a.calibre3-taylorpage { /* Usually invisible */ }
    BODY { font-family: 'Georgia', serif; line-height: 1.5; }
    """
    style_item = epub.EpubItem(uid="style_pgnum_taylor_anchor", file_name="style/pgnum_taylor_anchor.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_content = """<h1>The Structure of Self-Consciousness</h1>
<p>Taylor's exploration of Hegelian self-consciousness often spans multiple print pages.<a id="page_123" class="calibre3-taylorpage"></a> 
This synthetic text includes page markers similar to those found in such EPUBs.</p>
<p>The transition from consciousness to self-consciousness is a pivotal moment.<a id="page_124" class="calibre3-taylorpage"></a> 
These markers, like <code><a id="page_125" class="calibre3-taylorpage"></a></code>, help align digital and print versions.</p>
"""
    chapter_details = [
        {"title": "Taylor Anchor Page Markers", "filename": "c1_taylor_pgnum_anchor.xhtml", "content": chapter_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_taylor_pgnum_anchor_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_pagenum_deleuze_plain_text(filename="pagenum_deleuze_plain_text.epub"):
    """
    Creates an EPUB with plain text page numbers embedded in content, like Deleuze's "Anti-Oedipus".
    e.g., "xl", "xli" interrupting text flow.
    """
    filepath = os.path.join(EPUB_DIR, "page_numbers", filename)
    book = _create_epub_book("synth-epub-pgnum-deleuze-plain-001", "Deleuze Plain Text Page Numbers EPUB")

    # No specific CSS needed for this feature, but a general one is good.
    css_content = "BODY { font-family: 'Courier New', monospace; color: #222; }"
    style_item = epub.EpubItem(uid="style_pgnum_deleuze_plain", file_name="style/pgnum_deleuze_plain.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_content = """<h1>Desiring-Machines</h1>
<p>The concept of desiring-production is central. It operates by breaks and flows. 
This is detailed further as the argument unfolds. xl The schizoanalytic project aims to dismantle Oedipal structures. 
It is a process of decoding and deterritorialization.</p>
<p>Consider the body without organs (BwO) as a surface for these processes. xli 
It is not a pre-existing entity but a limit that is continually approached and repelled. 
The flows of desire traverse this surface, creating temporary assemblages.</p>
<p>This text simulates page numbers like "xlii" or "45" appearing directly in the text flow, 
often a result of OCR or specific conversion processes from PDFs where page numbers were part of the main text block.</p>
"""
    chapter_details = [
        {"title": "Deleuze Plain Text Page Numbers", "filename": "c1_deleuze_pgnum_plain.xhtml", "content": chapter_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_deleuze_pgnum_plain_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)