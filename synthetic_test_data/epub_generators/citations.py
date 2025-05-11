import os
from ebooklib import epub
from ..common import EPUB_DIR, _create_epub_book, _add_epub_chapters, _write_epub_file

def create_epub_citation_kant_intext(filename="citation_kant_intext.epub"):
    """
    Creates an EPUB with Kant-style in-text citations.
    e.g., (EX, p. 15; 23:21)
    """
    filepath = os.path.join(EPUB_DIR, "citations_bibliography", filename)
    book = _create_epub_book("synth-epub-cite-kant-001", "Kant In-Text Citation Style EPUB")

    css_content = """
    .kant-citation { font-style: italic; color: #444; }
    BODY { font-family: 'Garamond Premier Pro', serif; }
    """
    style_item = epub.EpubItem(uid="style_cite_kant", file_name="style/cite_kant.css", media_type="text/css", content=css_content)
    book.add_item(style_item)
    # This function seems incomplete, adding basic chapter and write for now.
    chapter_details = [
        {"title": "Kantian Citations", "filename": "c1_kant_cite.xhtml",
         "content": """<h1>On Kantian Citations</h1>
<p>Kant's works are often cited using academy pagination, like <span class="kant-citation">(KrV, A 73 / B 98)</span>.</p>
<p>Another example might be <span class="kant-citation">(GMS, 4:421)</span> for the Groundwork.</p>"""}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_kant_cite_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)


def create_epub_citation_taylor_intext_italic(filename="citation_taylor_intext_italic.epub"):
    """
    Creates an EPUB with Taylor-style in-text citations (plain text with italics for titles).
    e.g., See Kant’s <em class="calibre8">Critique of Pure Reason</em>, A70/B95.
    """
    filepath = os.path.join(EPUB_DIR, "citations_bibliography", filename)
    book = _create_epub_book("synth-epub-cite-taylor-001", "Taylor In-Text Citation Style EPUB")

    css_content = """
    em.calibre8-taylor { font-style: italic; }
    .taylor-citation-ref { /* No specific style, just for semantic grouping if needed */ }
    BODY { font-family: 'Georgia', serif; }
    """
    style_item = epub.EpubItem(uid="style_cite_taylor", file_name="style/cite_taylor.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_content = """<h1>Hegel and Modern Society: A Synthetic Fragment</h1>
<p>Charles Taylor's analysis of Hegel often refers to primary texts directly within his prose. 
For instance, one might read: See Hegel’s <em class="calibre8-taylor">Phenomenology of Spirit</em>, ¶73-79, for his discussion of Lordship and Bondage. 
This approach integrates citations seamlessly.</p>
<p>Further, Taylor might reference Kant, such as: 
This contrasts with Kant’s position in the <em class="calibre8-taylor">Critique of Practical Reason</em> <span class="taylor-citation-ref">(Ak. V, 30)</span>.</p>
"""
    chapter_details = [
        {"title": "Taylor In-Text Citations", "filename": "c1_taylor_cite.xhtml", "content": chapter_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_taylor_cite_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_citation_rosenzweig_biblioref(filename="citation_rosenzweig_biblioref.epub"):
    """
    Creates an EPUB with Rosenzweig "Hegel and the State" style bibliorefs and bibliography.
    Ref: <a epub:type="biblioref" href="bibliography.xhtml#r0_X" id="r0_Xb" role="doc-biblioref">Author Year</a>
         <li epub:type="biblioentry" id="r0_X">...<a epub:type="backlink" href="#r0_Xb">↩</a></li>
    """
    filepath = os.path.join(EPUB_DIR, "citations_bibliography", filename)
    book = _create_epub_book("synth-epub-cite-rosen-bibref-001", "Rosenzweig Biblioref Style EPUB")
    book.epub_version = "3.0" # epub:type is EPUB3

    css_content = """
    a[epub|type="biblioref"] { text-decoration: none; color: #0056b3; }
    section[epub|type="bibliography"] { margin-top: 2em; padding-top: 1em; border-top: 1px solid #ccc; }
    section[epub|type="bibliography"] h2 { font-size: 1.4em; }
    section[epub|type="bibliography"] li { margin-bottom: 0.5em; }
    a[epub|type="backlink"] { text-decoration: none; color: #777; margin-left: 0.5em; }
    BODY { font-family: 'Times New Roman', Times, serif; }
    """
    style_item = epub.EpubItem(uid="style_cite_rosen_bibref", file_name="style/cite_rosen_bibref.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    # Main content file
    main_chap_content = """<h1>Hegel's Early Political Writings</h1>
<p>Rosenzweig's analysis meticulously traces Hegel's development. He often refers to specific editions and works, 
for example, <a epub:type="biblioref" href="bibliography_rosen.xhtml#hegel1802" id="ref_hegel1802" role="doc-biblioref">Hegel 1802</a>.</p>
<p>Further discussion might involve other key texts, such as those by <a epub:type="biblioref" href="bibliography_rosen.xhtml#haym1857" id="ref_haym1857" role="doc-biblioref">Haym 1857</a> or 
<a epub:type="biblioref" href="bibliography_rosen.xhtml#dilthey1905" id="ref_dilthey1905" role="doc-biblioref">Dilthey 1905</a>.</p>
"""
    main_chap = epub.EpubHtml(title="Hegel's Early Writings", file_name="c1_rosen_bibref.xhtml", lang="en")
    main_chap.content = main_chap_content
    main_chap.add_item(style_item)
    book.add_item(main_chap)

    # Bibliography file
    bib_content = """<html xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Bibliography</title>
<link rel="stylesheet" type="text/css" href="style/cite_rosen_bibref.css"/>
</head>
<body>
  <section epub:type="bibliography" role="doc-bibliography" id="biblio_section">
    <h2>Bibliography</h2>
    <ul>
      <li epub:type="biblioentry" id="hegel1802" role="doc-biblioentry">Hegel, G.W.F. (1802). <em>Die Verfassung Deutschlands</em> (The German Constitution). 
        <a epub:type="backlink" href="c1_rosen_bibref.xhtml#ref_hegel1802" role="doc-backlink">↩</a></li>
      <li epub:type="biblioentry" id="haym1857" role="doc-biblioentry">Haym, R. (1857). <em>Hegel und seine Zeit</em>. 
        <a epub:type="backlink" href="c1_rosen_bibref.xhtml#ref_haym1857" role="doc-backlink">↩</a></li>
      <li epub:type="biblioentry" id="dilthey1905" role="doc-biblioentry">Dilthey, W. (1905). <em>Die Jugendgeschichte Hegels</em>.
        <a epub:type="backlink" href="c1_rosen_bibref.xhtml#ref_dilthey1905" role="doc-backlink">↩</a></li>
    </ul>
  </section>
</body></html>
"""
    bib_page = epub.EpubHtml(title="Bibliography", file_name="bibliography_rosen.xhtml", lang="en")
    bib_page.content = bib_content
    # bib_page.add_item(style_item) # Already linked in HTML
    book.add_item(bib_page)
    
    book.toc = (
        epub.Link(main_chap.file_name, "Hegel's Early Writings", "c1_rosen_bibref_toc"),
        epub.Link(bib_page.file_name, "Bibliography", "bib_rosen_bibref_toc")
    )
    book.add_item(epub.EpubNcx())
    nav_doc = epub.EpubNav() # Basic NavDoc
    nav_doc.html_content = u"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Nav</title></head>
<body>
  <nav epub:type="toc" id="toc"><ol>
    <li><a href="c1_rosen_bibref.xhtml">Hegel's Early Writings</a></li>
    <li><a href="bibliography_rosen.xhtml">Bibliography</a></li>
  </ol></nav>
  <nav epub:type="landmarks" hidden=""><ol>
    <li><a epub:type="bodymatter" href="c1_rosen_bibref.xhtml">Start Reading</a></li>
    <li><a epub:type="bibliography" href="bibliography_rosen.xhtml">Bibliography</a></li>
  </ol></nav>
</body></html>"""
    nav_doc.properties.append('nav')
    book.add_item(nav_doc)
    
    book.spine = [nav_doc, main_chap, bib_page]
    _write_epub_file(book, filepath)