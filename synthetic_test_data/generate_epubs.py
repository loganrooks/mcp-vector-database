import os
from ebooklib import epub
from .common import EPUB_DIR, _create_epub_book, _add_epub_chapters, _write_epub_file

def create_epub_ncx_simple(filename="ncx_simple.epub"):
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-ncx-simple-001", "Simple NCX EPUB")
    chapter_details = [
        {"title": "Introduction", "filename": "chap_01.xhtml", 
         "content": """<h1>Chapter 1: Introduction</h1>
<p>This is the first chapter of a synthetically generated EPUB file. 
Its purpose is to test basic NCX Table of Contents functionality.</p>
<p>Philosophical inquiry often begins with fundamental questions about existence, knowledge, values, reason, mind, and language. 
This simple text serves as a placeholder for such profound discussions.</p>"""},
        {"title": "Further Thoughts", "filename": "chap_02.xhtml", 
         "content": """<h1>Chapter 2: Further Thoughts</h1>
<p>This second chapter continues the exploration, albeit in a very simple manner for testing purposes.</p>
<p>Consider the nature of synthetic data: it mimics reality to test systems, yet it is not real. 
This paradox itself could be a subject of philosophical thought.</p>"""}
    ]
    chapters = _add_epub_chapters(book, chapter_details)
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "intro"), epub.Link(chapters[1].file_name, chapters[1].title, "thoughts"))
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    style = 'BODY {color: black;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_ncx_nested(filename="ncx_nested.epub"):
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-ncx-nested-001", "Nested NCX EPUB")
    chapter_details = [
        {"title": "Part I: Foundations", "filename": "part1_intro.xhtml", "content": "<h1>Part I: Foundations</h1><p>This part lays the groundwork.</p>"},
        {"title": "Chapter 1: Core Concepts", "filename": "chap_01.xhtml", "content": "<h1>Chapter 1: Core Concepts</h1><p>Discussing fundamental ideas.</p>"},
        {"title": "Section 1.1: First Concept", "filename": "sec_1_1.xhtml", "content": "<h2>Section 1.1: First Concept</h2><p>Detailing the first concept.</p>"},
        {"title": "Subsection 1.1.1: Sub-Detail", "filename": "sub_1_1_1.xhtml", "content": "<h3>Subsection 1.1.1: Sub-Detail</h3><p>A very specific detail.</p>"},
        {"title": "Section 1.2: Second Concept", "filename": "sec_1_2.xhtml", "content": "<h2>Section 1.2: Second Concept</h2><p>Exploring the second concept.</p>"},
        {"title": "Chapter 2: Advanced Topics", "filename": "chap_02.xhtml", "content": "<h1>Chapter 2: Advanced Topics</h1><p>Moving to more complex subjects.</p>"}
    ]
    chapters = _add_epub_chapters(book, chapter_details)
    link_p1_intro = epub.Link(chapters[0].file_name, chapters[0].title, "p1intro_id")
    link_c1 = epub.Link(chapters[1].file_name, chapters[1].title, "c1_id")
    link_s1_1 = epub.Link(chapters[2].file_name, chapters[2].title, "s1_1_id")
    link_ss1_1_1 = epub.Link(chapters[3].file_name, chapters[3].title, "ss1_1_1_id")
    link_s1_2 = epub.Link(chapters[4].file_name, chapters[4].title, "s1_2_id")
    link_c2 = epub.Link(chapters[5].file_name, chapters[5].title, "c2_id")
    toc_ss1_1_1 = link_ss1_1_1
    toc_s1_1 = (link_s1_1, (toc_ss1_1_1,))
    toc_s1_2 = link_s1_2
    toc_c1 = (link_c1, (toc_s1_1, toc_s1_2))
    toc_c2 = link_c2
    book.toc = ((link_p1_intro, (toc_c1, toc_c2)),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    style = 'BODY {color: navy;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_html_toc_linked(filename="html_toc_linked.epub"):
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-html-toc-001", "HTML ToC EPUB")
    html_toc_content = """<h1>Table of Contents</h1>
<ul>
    <li><a href="chap_01.xhtml">Chapter 1: Beginnings</a></li>
    <li><a href="chap_02.xhtml">Chapter 2: Developments</a><ul><li><a href="chap_02.xhtml#sec2.1">Section 2.1: First Development</a></li></ul></li>
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
def create_epub_ncx_with_pagelist(filename="ncx_page_list.epub"):
    """
    Creates an EPUB with an NCX containing a pageList.
    Simulates structure found in Zizek, Rorty, Heidegger (Basic Questions) examples.
    Note: ebooklib does not directly support easy creation of <pageList> in NCX.
    This function will create the structure, but the pageList itself is illustrative
    and would require manual XML editing or a different library for full NCX validity.
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-ncx-pagelist-001", "NCX with PageList EPUB")
    book.epub_version = "2.0" # Common for NCX pageLists

    # Add chapters with page anchors
    c1_content = """<h1>Chapter 1: Print Pages</h1>
<p>This is page 1 content.<a id="page_1" /> Some more text here to make it look like a page.</p>
<p>Further text on page 1. Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
<p>This is page 2 content.<a id="page_2" /> Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>"""
    c1 = epub.EpubHtml(title="Chapter 1", file_name="chap_01_pl.xhtml", lang="en")
    c1.content = c1_content

    c2_content = """<h1>Chapter 2: More Print Pages</h1>
<p>This is page 3 content.<a id="page_3" /> Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
<p>Content for page 4.<a id="page_4" /> Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>"""
    c2 = epub.EpubHtml(title="Chapter 2", file_name="chap_02_pl.xhtml", lang="en")
    c2.content = c2_content
    
    book.add_item(c1)
    book.add_item(c2)
    chapters = [c1, c2]

    book.toc = (
        epub.Link(chapters[0].file_name, chapters[0].title, "chap1_pl_toc"),
        epub.Link(chapters[1].file_name, chapters[1].title, "chap2_pl_toc")
    )
    
    # Create NCX. ebooklib will generate the basic navMap.
    # The pageList needs to be manually constructed if we were to inject it.
    ncx_item = epub.EpubNcx()
    # To actually add a pageList, we would need to get ncx_item.content as bytes,
    # parse XML, insert the pageList XML string, then set ncx_item.content again.
    # This is beyond simple ebooklib usage.
    # For now, this EPUB will have a valid NCX but without the actual pageList data in it.
    # The presence of page_X anchors in content is the main testable feature here.
    book.add_item(ncx_item)
    
    # Add a NavDoc for EPUB3 compatibility, though pageList is typically NCX.
    nav_doc = epub.EpubNav()
    book.add_item(nav_doc)

    style = 'BODY {color: darkgoldenrod;}'
    nav_css = epub.EpubItem(uid="style_nav_pl", file_name="style/nav_pl.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    for ch in chapters:
        ch.add_item(nav_css)

    book.spine = ['nav'] + chapters # 'nav' refers to EpubNav here
    _write_epub_file(book, filepath)

def create_epub_missing_ncx(filename="missing_ncx.epub"):
    """
    Creates an EPUB 3 that intentionally lacks an NCX file, relying on NavDoc.
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-no-ncx-001", "Missing NCX EPUB (NavDoc Only)")
    book.epub_version = "3.0" 

    chapter_details = [
        {"title": "Chapter Alpha", "filename": "c_alpha.xhtml", "content": "<h1>Chapter Alpha</h1><p>Content relying on NavDoc.</p>"},
        {"title": "Chapter Beta", "filename": "c_beta.xhtml", "content": "<h1>Chapter Beta</h1><p>More content, NavDoc is key.</p>"}
    ]
    chapters = _add_epub_chapters(book, chapter_details)
    
    nav_html_content=u"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>Navigation</title>
  <meta charset="utf-8" />
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Table of Contents</h1>
    <ol>
      <li><a href="c_alpha.xhtml">Chapter Alpha</a></li>
      <li><a href="c_beta.xhtml">Chapter Beta</a></li>
    </ol>
  </nav>
  <nav epub:type="landmarks" hidden="">
    <h1>Landmarks</h1>
    <ol>
      <li><a epub:type="toc" href="#toc">Table of Contents</a></li>
      <li><a epub:type="bodymatter" href="c_alpha.xhtml">Start of Content</a></li>
    </ol>
  </nav>
</body>
</html>
"""
    nav_doc_item = epub.EpubHtml(title='Navigation', file_name='nav.xhtml', lang='en')
    nav_doc_item.content = nav_html_content
    nav_doc_item.properties.append('nav') # Crucial for EPUB3 NavDoc
    book.add_item(nav_doc_item)
    
    # DO NOT add epub.EpubNcx()
    
    style = 'BODY {color: steelblue;}'
    main_css = epub.EpubItem(uid="style_missing_ncx", file_name="style/main_missing_ncx.css", media_type="text/css", content=style)
    book.add_item(main_css)
    for ch in chapters:
        ch.add_item(main_css)
    nav_doc_item.add_item(main_css)

    book.spine = [nav_doc_item] + chapters # NavDoc should be in spine
    _write_epub_file(book, filepath)

def create_epub_navdoc_full(filename="navdoc_full.epub"):
    """
    Creates an EPUB 3 with a comprehensive NavDoc (ToC, Landmarks, PageList).
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-navdoc-full-001", "Full NavDoc EPUB")
    book.epub_version = "3.0"

    cover_page = epub.EpubHtml(title="Cover", file_name="cover.xhtml", lang="en")
    cover_page.content = "<h1>The Great Synthetic Novel</h1><p>by A. Coder</p><div id='coverimage_placeholder'>(Imagine a cover image here)</div>"
    book.add_item(cover_page)
    # book.set_cover("image/cover.jpg", open('dummy_cover.jpg', 'rb').read()) # If we had a dummy image

    ch1_content = """<h1>Chapter 1: The Beginning</h1>
<p>This is the first page of chapter 1.<span epub:type="pagebreak" id="page_1"/></p>
<p>This is the second page of chapter 1.<span epub:type="pagebreak" id="page_2"/></p>"""
    c1 = epub.EpubHtml(title="Chapter 1", file_name="ch1.xhtml", lang="en")
    c1.content = ch1_content

    ch2_content = """<h1>Chapter 2: The Middle</h1>
<p>Content for page 3.<span epub:type="pagebreak" id="page_3"/></p>"""
    c2 = epub.EpubHtml(title="Chapter 2", file_name="ch2.xhtml", lang="en")
    c2.content = ch2_content
    
    book.add_item(c1)
    book.add_item(c2)
    chapters = [c1, c2]

    nav_html_content=u"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>Navigation</title>
  <meta charset="utf-8" />
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Table of Contents</h1>
    <ol>
      <li><a href="ch1.xhtml">Chapter 1: The Beginning</a></li>
      <li><a href="ch2.xhtml">Chapter 2: The Middle</a></li>
    </ol>
  </nav>
  <nav epub:type="landmarks">
    <h1>Landmarks</h1>
    <ol>
      <li><a epub:type="cover" href="cover.xhtml">Cover Page</a></li>
      <li><a epub:type="toc" href="#toc">Table of Contents</a></li>
      <li><a epub:type="bodymatter" href="ch1.xhtml">Start of Content</a></li>
    </ol>
  </nav>
  <nav epub:type="page-list">
    <h1>Page List</h1>
    <ol>
      <li><a href="ch1.xhtml#page_1">1</a></li>
      <li><a href="ch1.xhtml#page_2">2</a></li>
      <li><a href="ch2.xhtml#page_3">3</a></li>
    </ol>
  </nav>
</body>
</html>
"""
    nav_doc_item = epub.EpubHtml(title='Navigation', file_name='nav.xhtml', lang='en')
    nav_doc_item.content = nav_html_content
    nav_doc_item.properties.append('nav')
    book.add_item(nav_doc_item)

    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_ncx_compat"),
                epub.Link(chapters[1].file_name, chapters[1].title, "c2_ncx_compat"))
    book.add_item(epub.EpubNcx()) # For backward compatibility

    style = 'BODY {color: darkslateblue;}'
    main_css = epub.EpubItem(uid="style_full_nav", file_name="style/main_full_nav.css", media_type="text/css", content=style)
    book.add_item(main_css)
    cover_page.add_item(main_css)
    for ch in chapters:
        ch.add_item(main_css)
    nav_doc_item.add_item(main_css)

    book.spine = [nav_doc_item, cover_page] + chapters 
    _write_epub_file(book, filepath)

def create_epub_ncx_with_pagelist(filename="ncx_page_list.epub"):
    """
    Creates an EPUB with an NCX containing a pageList.
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-ncx-pagelist-001", "NCX with PageList EPUB")

    # Add chapters with page anchors
    c1_content = """<h1>Chapter 1</h1>
<p>This is page 1 content.<a id="page_1" /></p>
<p>More content for page 1.</p>
<p>This is page 2 content.<a id="page_2" /></p>"""
    c1 = epub.EpubHtml(title="Chapter 1", file_name="chap_01.xhtml", lang="en")
    c1.content = c1_content

    c2_content = """<h1>Chapter 2</h1>
<p>This is page 3 content.<a id="page_3" /></p>
<p>Content for page 4.<a id="page_4" /></p>"""
    c2 = epub.EpubHtml(title="Chapter 2", file_name="chap_02.xhtml", lang="en")
    c2.content = c2_content
    
    book.add_item(c1)
    book.add_item(c2)
    chapters = [c1, c2]

    book.toc = (
        epub.Link(chapters[0].file_name, chapters[0].title, "chap1_toc"),
        epub.Link(chapters[1].file_name, chapters[1].title, "chap2_toc")
    )
    
    # Create NCX with pageList
    ncx = epub.EpubNcx()
    # ebooklib's EpubNcx doesn't directly support adding pageTargets to pageList easily.
    # We'd typically have to manipulate the XML string or use a more capable library for this.
    # For simulation, we'll note that a pageList *should* be here.
    # A real pageList would look like:
    # <pageList>
    #   <pageTarget type="normal" id="pt_1" value="1" playOrder="1">
    #     <navLabel><text>1</text></navLabel>
    #     <content src="chap_01.xhtml#page_1"/>
    #   </pageTarget>
    #   ...
    # </pageList>
    # We will add a custom property to the book object to signify this for now.
    book.custom_ncx_elements = """
  <pageList>
    <pageTarget type="normal" id="pt_1" value="1" playOrder="1">
      <navLabel><text>1</text></navLabel>
      <content src="chap_01.xhtml#page_1"/>
    </pageTarget>
    <pageTarget type="normal" id="pt_2" value="2" playOrder="2">
      <navLabel><text>2</text></navLabel>
      <content src="chap_01.xhtml#page_2"/>
    </pageTarget>
    <pageTarget type="normal" id="pt_3" value="3" playOrder="3">
      <navLabel><text>3</text></navLabel>
      <content src="chap_02.xhtml#page_3"/>
    </pageTarget>
    <pageTarget type="normal" id="pt_4" value="4" playOrder="4">
      <navLabel><text>4</text></navLabel>
      <content src="chap_02.xhtml#page_4"/>
    </pageTarget>
  </pageList>
"""
    # This custom_ncx_elements won't be automatically written by ebooklib.
    # It's a placeholder to indicate the intent.
    # A post-processing step or a different library would be needed to inject this into the NCX XML.

    book.add_item(ncx)
    book.add_item(epub.EpubNav())
    style = 'BODY {color: purple;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)
    # Note: The generated EPUB will have a standard NCX without the pageList via ebooklib.
    # Manual XML manipulation or a different tool would be needed for a true pageList.

def create_epub_missing_ncx(filename="missing_ncx.epub"):
    """
    Creates an EPUB that intentionally lacks an NCX file, relying on NavDoc.
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
def create_epub_taylor_hegel_headers(filename="taylor_hegel_headers.epub"):
    """
    Creates an EPUB with header styles like Charles Taylor's Hegel.
    - Chapter Number: h3 class="h1" with nested span class="small"
    - Chapter Title: h3 class="h3a" with nested em
    """
    filepath = os.path.join(EPUB_DIR, "headers", filename)
    book = _create_epub_book("synth-epub-taylor-headers-001", "Taylor/Hegel Style Headers")

    css_content = """
    h3.h1 { font-size: 1.4em; text-align: center; }
    h3.h1 span.small { font-size: 0.8em; font-weight: normal; display: block; }
    h3.h3a { font-size: 1.2em; text-align: center; margin-bottom: 1em;}
    h3.h3a em { font-style: italic; font-weight: bold;}
    """
    style_item = epub.EpubItem(uid="style_taylor_h", file_name="style/taylor_h.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_details = [
        {
            "title": "Chapter I Title", # This won't be used directly in content due to custom structure
            "filename": "chap_taylor_1.xhtml",
            "content": """
<h3 class="h1" id="ch1_num"><span class="small">CHAPTER I</span></h3>
<h3 class="h3a" id="ch1_title"><em>The Aim of the Enterprise</em></h3>
<p>This chapter emulates the header style found in Charles Taylor's "Hegel", where chapter numbers and titles might use h3 tags with specific classes and nested elements for styling.</p>
<h4 id="sec1">A Subsection with h4</h4>
<p>Some content here.</p>
"""
        },
        {
            "title": "Chapter II Title",
            "filename": "chap_taylor_2.xhtml",
            "content": """
<h3 class="h1" id="ch2_num"><span class="small">CHAPTER II</span></h3>
<h3 class="h3a" id="ch2_title"><em>Further Elaborations</em></h3>
<p>More content following a similar header pattern.</p>
<p class="center-num" id="subnum1">1</p>
<p>A numbered subsection introduced by a styled paragraph.</p>
"""
        }
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    book.toc = (
        epub.Link(chapters[0].file_name, "Chapter I: The Aim of the Enterprise", "ch1_taylor_toc"),
        epub.Link(chapters[1].file_name, "Chapter II: Further Elaborations", "ch2_taylor_toc")
    )
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav()) 
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_sennet_style_headers(filename="sennet_style_headers.epub"):
    """
    Creates an EPUB with header styles like Sennet's The Craftsman.
    - Part Title: h1 class="title"
    - Chapter Number (as title): h3 class="title5"
    - Chapter Sub-Title (actual title): h2 class="title6"
    """
    filepath = os.path.join(EPUB_DIR, "headers", filename)
    book = _create_epub_book("synth-epub-sennet-headers-001", "Sennet-Style Headers EPUB")

    css_content = """
    h1.title { font-size: 2em; text-align: center; text-transform: uppercase; }
    h1.title span.small { font-size: 0.7em; display: block; text-transform: none; }
    h3.title5 { font-size: 1.2em; text-align: center; font-weight: bold; margin-top: 2em; }
    h2.title6 { font-size: 1.5em; text-align: center; font-style: italic; margin-bottom: 1em; }
    h3.title3 { font-size: 1.1em; font-weight: bold; }
    h3.title4 span.em { font-style: italic; }
    """
    style_item = epub.EpubItem(uid="style_sennet_h", file_name="style/sennet_h.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_details = [
        {
            "title": "Part One: Craftsman", 
            "filename": "part_sennet_1.xhtml",
            "content": """
<h1 class="title" id="part1"><span class="small">PART ONE</span>Craftsman</h1>
<h3 class="title5" id="ch1_num_sennet">CHAPTER ONE</h3>
<h2 class="title6" id="ch1_title_sennet">The Troubled Craftsman</h2>
<p>This chapter emulates the header style from Sennet's "The Craftsman".</p>
<h3 class="title3" id="sec1_sennet">The Modern Hephaestus</h3>
<h3 class="title4" id="subsec1_sennet"><span class="em">Ancient Weavers and Linux Programmers</span></h3>
<p>Content for the first section.</p>
"""
        }
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    book.toc = (epub.Link(chapters[0].file_name, "Part One: The Troubled Craftsman", "part1_sennet_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav()) 
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_div_style_headers(filename="div_style_headers.epub"):
    """
    Creates an EPUB with header styles like Heidegger's German Existentialism.
    - Section Titles: div class="title-chapter" with span class="b"
    - Subtitles: div class="subtitle-chapter" with span class="i"
    """
    filepath = os.path.join(EPUB_DIR, "headers", filename)
    book = _create_epub_book("synth-epub-div-headers-001", "Div-Style Headers EPUB")

    css_content = """
    .title-chapter { font-size: 1.6em; margin-top: 1.5em; margin-bottom: 0.5em; text-align: center; }
    .title-chapter span.b { font-weight: bold; }
    .subtitle-chapter { font-size: 1.3em; margin-bottom: 1em; text-align: center; }
    .subtitle-chapter span.i { font-style: italic; }
    """
    style_item = epub.EpubItem(uid="style_div_h", file_name="style/div_h.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_details = [
        {
            "title": "Main Section Title", 
            "filename": "chap_div_h1.xhtml",
            "content": """
<div class="title-chapter" id="main_title_div"><span class="b">THE QUESTION OF BEING</span></div>
<div class="subtitle-chapter" id="sub_title_div"><span class="i">An Ontological Inquiry</span></div>
<p>This chapter uses div elements with specific classes to represent main titles and subtitles, 
as seen in some philosophical texts like Heidegger's "German Existentialism".</p>
<p>Further content follows...</p>
"""
        }
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    book.toc = (epub.Link(chapters[0].file_name, "The Question of Being", "div_h_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav()) 
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)
def create_epub_ncx_links_to_anchors(filename="ncx_links_to_anchors.epub"):
    """
    Creates an EPUB with an NCX ToC where navPoints link to anchors within content files.
    Simulates Kant example: <content src="text/part0009_split_001.html#head1"/>
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-ncx-anchors-001", "NCX Links to Anchors EPUB")

    chapter_details = [
        {"title": "Chapter One", "filename": "c1_anchors.xhtml",
         "content": """<h1 id="main_title">Chapter One: Anchors Away</h1>
<p>This is the first section.</p>
<h2 id="sec1_1">Section 1.1</h2>
<p>Content for section 1.1.</p>
<h2 id="sec1_2">Section 1.2</h2>
<p>Content for section 1.2.</p>"""},
        {"title": "Chapter Two", "filename": "c2_anchors.xhtml",
         "content": """<h1 id="chap2_title">Chapter Two: More Anchors</h1>
<p>This is the second chapter.</p>
<h2 id="sec2_1">Section 2.1</h2>
<p>Content for section 2.1 of chapter 2.</p>"""}
    ]
    chapters = _add_epub_chapters(book, chapter_details)

    # Create NCX links to anchors
    toc_c1_main = epub.Link(chapters[0].file_name + "#main_title", "Chapter One: Anchors Away", "c1_main_anchor")
    toc_c1_s1_1 = epub.Link(chapters[0].file_name + "#sec1_1", "Section 1.1", "c1_s1_1_anchor")
    toc_c1_s1_2 = epub.Link(chapters[0].file_name + "#sec1_2", "Section 1.2", "c1_s1_2_anchor")
    
    toc_c2_main = epub.Link(chapters[1].file_name + "#chap2_title", "Chapter Two: More Anchors", "c2_main_anchor")
    toc_c2_s2_1 = epub.Link(chapters[1].file_name + "#sec2_1", "Section 2.1", "c2_s2_1_anchor")

    book.toc = (
        (toc_c1_main, (toc_c1_s1_1, toc_c1_s1_2)),
        (toc_c2_main, (toc_c2_s2_1,))
    )
    
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    style = 'BODY {color: teal;}'
    nav_css = epub.EpubItem(uid="style_nav_anchor", file_name="style/nav_anchor.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    for ch in chapters:
        ch.add_item(nav_css)
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_ncx_problematic_entries(filename="ncx_problematic_entries.epub"):
    """
    Creates an EPUB with an NCX ToC containing problematic entries,
    e.g., very long text in navLabel (Adorno example).
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-ncx-problem-001", "NCX Problematic Entries EPUB")

    long_title = "This is an excessively long title for a chapter that really should have been summarized, but for the sake of testing problematic NCX entries, we are putting a whole paragraph, or at least a very long sentence, into the navLabel text to see how parsers and reading systems handle such an edge case. It might be truncated, or it might cause display issues, or it might be handled perfectly fine. The point is to test the boundaries and robustness of the system when faced with non-standard or poorly formed metadata within the NCX Table of Contents structure."
    
    chapter_details = [
        {"title": "Normal Chapter", "filename": "c1_problem.xhtml",
         "content": """<h1>A Normally Titled Chapter</h1><p>Some standard content.</p>"""},
        {"title": long_title, "filename": "c2_problem.xhtml",
         "content": """<h1>The Chapter with the Long Title</h1><p>Content for the chapter with the problematic NCX entry.</p>"""},
        {"title": "Another Chapter", "filename": "c3_problem.xhtml",
         "content": """<h1>Yet Another Chapter</h1><p>More content here.</p>"""}
    ]
    chapters = _add_epub_chapters(book, chapter_details)

    book.toc = (
        epub.Link(chapters[0].file_name, chapters[0].title, "c1_problem_toc"),
        epub.Link(chapters[1].file_name, chapters[1].title, "c2_problem_toc"), # This will use the long_title
        epub.Link(chapters[2].file_name, chapters[2].title, "c3_problem_toc")
    )
    
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    style = 'BODY {color: firebrick;}'
    nav_css = epub.EpubItem(uid="style_nav_problem", file_name="style/nav_problem.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    for ch in chapters:
        ch.add_item(nav_css)
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_ncx_inconsistent_depth(filename="ncx_inconsistent_depth.epub"):
    """
    Creates an EPUB with an NCX ToC where the dtb:depth attribute (if present,
    or implied depth) is inconsistent with actual navPoint nesting.
    Simulates Marcuse - Reason and Revolution example.
    ebooklib doesn't directly set dtb:depth, so this simulates the structural inconsistency.
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-ncx-depth-001", "NCX Inconsistent Depth EPUB")

    chapter_details = [
        {"title": "Part I", "filename": "p1_depth.xhtml", "content": "<h1>Part I</h1>"},
        {"title": "Chapter 1 (Under Part I)", "filename": "p1c1_depth.xhtml", "content": "<h2>Chapter 1</h2>"},
        {"title": "Standalone Chapter 2", "filename": "c2_depth.xhtml", "content": "<h1>Standalone Chapter 2</h1>"},
        {"title": "Section 2.1 (Under Chapter 2)", "filename": "c2s1_depth.xhtml", "content": "<h2>Section 2.1</h2>"},
        {"title": "Standalone Chapter 3", "filename": "c3_depth.xhtml", "content": "<h1>Standalone Chapter 3</h1>"}
    ]
    chapters = _add_epub_chapters(book, chapter_details)

    # Intentionally create a TOC structure that might imply certain depths,
    # but the actual content structure or a manually edited NCX could differ.
    # ebooklib generates depth based on tuple nesting.
    # We'll make a flat-looking structure in NCX for some nested content.
    
    link_p1 = epub.Link(chapters[0].file_name, chapters[0].title, "p1_d_id")
    link_p1c1 = epub.Link(chapters[1].file_name, chapters[1].title, "p1c1_d_id") # Should be under p1
    link_c2 = epub.Link(chapters[2].file_name, chapters[2].title, "c2_d_id")
    link_c2s1 = epub.Link(chapters[3].file_name, chapters[3].title, "c2s1_d_id") # Should be under c2
    link_c3 = epub.Link(chapters[4].file_name, chapters[4].title, "c3_d_id")

    # This structure is flat, but content implies nesting.
    # A real inconsistent depth would be if NCX had <navPoint dtb:depth="1"> containing another <navPoint dtb:depth="1">
def create_epub_ncx_lists_footnote_files(filename="ncx_lists_footnote_files.epub"):
    """
    Creates an EPUB with an NCX ToC that lists individual footnote files.
    Simulates Derrida - Of Grammatology example.
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-ncx-fnfiles-001", "NCX Lists Footnote Files EPUB")

    chapter_details = [
        {"title": "Main Text Chapter 1", "filename": "text_c1.xhtml",
         "content": """<h1>Chapter 1 with Footnotes</h1>
<p>Some text that refers to a footnote.<sup><a href="../footnotes/fn_c1_01.xhtml#fn1">1</a></sup></p>
<p>More text with another reference.<sup><a href="../footnotes/fn_c1_02.xhtml#fn2">2</a></sup></p>"""},
    ]
    chapters = _add_epub_chapters(book, chapter_details)

    # Create dummy footnote files (these would typically be in a separate dir)
    fn1_content = "<html><body><p id='fn1'>1. This is the first footnote, in its own file.</p></body></html>"
    fn1_page = epub.EpubHtml(title="Footnote 1-1", file_name="footnotes/fn_c1_01.xhtml", lang="en")
    fn1_page.content = fn1_content
    book.add_item(fn1_page)

    fn2_content = "<html><body><p id='fn2'>2. This is the second footnote, also in its own file.</p></body></html>"
    fn2_page = epub.EpubHtml(title="Footnote 1-2", file_name="footnotes/fn_c1_02.xhtml", lang="en")
    fn2_page.content = fn2_content
    book.add_item(fn2_page)

    # Create NCX links
    book.toc = (
        epub.Link(chapters[0].file_name, chapters[0].title, "text_c1_toc"),
        # NCX entries for footnote files
        epub.Link(fn1_page.file_name, "Footnote 1 (File)", "fn1_file_toc"),
        epub.Link(fn2_page.file_name, "Footnote 2 (File)", "fn2_file_toc")
    )
    
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav()) # Basic Nav for compatibility
    style = 'BODY {color: indigo;}'
    nav_css = epub.EpubItem(uid="style_nav_fnfiles", file_name="style/nav_fnfiles.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    for item in [chapters[0], fn1_page, fn2_page]:
        item.add_item(nav_css) # Apply style to all content docs
        
    # Spine order: main content, then footnote files (or as per typical structure)
    # For this test, putting them in spine might not be typical but tests NCX linking.
    book.spine = ['nav'] + chapters + [fn1_page, fn2_page] 
    _write_epub_file(book, filepath)

def create_epub_html_toc_p_tags(filename="html_toc_p_tags.epub"):
    """
    Creates an EPUB with an HTML ToC structured with <p> tags and classes.
    Simulates Kant example: <p class="toc">Part 1</p><p class="tocb">Chapter 1</p>
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-html-ptoc-001", "HTML ToC with P Tags EPUB")

    html_toc_content = """<h1>Table of Contents (Styled P</h1>
<p class="toc-part"><a href="part1.xhtml">Part I: The Groundwork</a></p>
<p class="toc-chapter"><a href="part1_chap1.xhtml">Chapter 1: First Principles</a></p>
<p class="toc-section"><a href="part1_chap1.xhtml#sec1">Section 1.1: Initial Thoughts</a></p>
<p class="toc-chapter"><a href="part1_chap2.xhtml">Chapter 2: Second Principles</a></p>
<p class="toc-part"><a href="part2.xhtml">Part II: The Structure</a></p>
<p class="toc-chapter"><a href="part2_chap1.xhtml">Chapter 3: Building Blocks</a></p>
"""
    html_toc_page = epub.EpubHtml(title="Table of Contents (P-Tag Style)", file_name="toc_p_style.xhtml", lang="en")
    html_toc_page.content = html_toc_content
    book.add_item(html_toc_page)

    # Dummy content files
    p1_content = "<h1 id='part1'>Part I: The Groundwork</h1><p>Content for part 1.</p>"
    p1_c1_content = "<h1 id='p1c1'>Chapter 1: First Principles</h1><p>Content.</p><h2 id='sec1'>Section 1.1</h2><p>More content.</p>"
    p1_c2_content = "<h1 id='p1c2'>Chapter 2: Second Principles</h1><p>Content.</p>"
    p2_content = "<h1 id='part2'>Part II: The Structure</h1><p>Content for part 2.</p>"
    p2_c1_content = "<h1 id='p2c1'>Chapter 3: Building Blocks</h1><p>Content.</p>"

    chapters_data = [
        {"title": "Part I", "filename": "part1.xhtml", "content": p1_content},
        {"title": "Part I - Ch1", "filename": "part1_chap1.xhtml", "content": p1_c1_content},
        {"title": "Part I - Ch2", "filename": "part1_chap2.xhtml", "content": p1_c2_content},
        {"title": "Part II", "filename": "part2.xhtml", "content": p2_content},
        {"title": "Part II - Ch1", "filename": "part2_chap1.xhtml", "content": p2_c1_content},
    ]
    chapters = _add_epub_chapters(book, chapters_data)
    
    # Basic NCX for fallback for create_epub_html_toc_p_tags
    # chapters_data for create_epub_html_toc_p_tags has 5 items.
    # chapters[0] = part1.xhtml
    # chapters[1] = part1_chap1.xhtml (has #sec1)
    # chapters[2] = part1_chap2.xhtml
    # chapters[3] = part2.xhtml
    # chapters[4] = part2_chap1.xhtml (Chapter 3)

    ncx_p1 = epub.Link(chapters[0].file_name, "Part I: The Groundwork", "ncx_p1_p_tag_corrected")
    ncx_p1_c1 = epub.Link(chapters[1].file_name, "Chapter 1: First Principles", "ncx_p1_c1_p_tag_corrected")
    ncx_p1_c1_s1 = epub.Link(chapters[1].file_name + "#sec1", "Section 1.1: Initial Thoughts", "ncx_p1_c1_s1_p_tag_corrected")
    ncx_p1_c2 = epub.Link(chapters[2].file_name, "Chapter 2: Second Principles", "ncx_p1_c2_p_tag_corrected")
    
    ncx_p2 = epub.Link(chapters[3].file_name, "Part II: The Structure", "ncx_p2_p_tag_corrected")
    ncx_p2_c1 = epub.Link(chapters[4].file_name, "Chapter 3: Building Blocks", "ncx_p2_c1_p_tag_corrected")

    book.toc = (
        (ncx_p1,
            (
                (ncx_p1_c1, (ncx_p1_c1_s1,)),
                ncx_p1_c2
            )
        ),
        (ncx_p2, (ncx_p2_c1,))
    )
def create_epub_html_toc_non_linked(filename="html_toc_non_linked.epub"):
    """
    Creates an EPUB with an HTML ToC that is not hyperlinked.
    Simulates Baudrillard, Deleuze examples.
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-html-nonlinked-toc-001", "Non-Linked HTML ToC EPUB")

    html_toc_content = """<h1>Table of Contents (Non-Linked)</h1>
<ul>
    <li>Chapter 1: The Unlinked Beginning</li>
    <li>Chapter 2: Further Unlinked Thoughts
        <ul><li>Section 2.1: A Detail</li></ul>
    </li>
    <li>Chapter 3: Final Unlinked Words</li>
</ul>"""
    html_toc_page = epub.EpubHtml(title="Table of Contents (Non-Linked)", file_name="toc_non_linked.xhtml", lang="en")
    html_toc_page.content = html_toc_content
    book.add_item(html_toc_page)

    chapter_details = [
        {"title": "Chapter 1: The Unlinked Beginning", "filename": "c1_nonlinked.xhtml", "content": "<h1>Chapter 1</h1><p>Content for chapter 1.</p>"},
        {"title": "Chapter 2: Further Unlinked Thoughts", "filename": "c2_nonlinked.xhtml", "content": "<h1>Chapter 2</h1><p>Content for chapter 2.</p><h2>Section 2.1</h2><p>Detail.</p>"},
        {"title": "Chapter 3: Final Unlinked Words", "filename": "c3_nonlinked.xhtml", "content": "<h1>Chapter 3</h1><p>Content for chapter 3.</p>"}
    ]
    chapters = _add_epub_chapters(book, chapter_details)
    
    # Basic NCX for fallback
    book.toc = tuple(epub.Link(ch.file_name, ch.title, ch.file_name.split('.')[0] + "_nl") for ch in chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav()) # Basic Nav

    style_content = "BODY {color: firebrick;} .toc-entry { margin-left: 1em; }"
    main_css = epub.EpubItem(uid="style_nonlinkedtoc", file_name="style/nonlinkedtoc.css", media_type="text/css", content=style_content)
    book.add_item(main_css)
    for ch in chapters:
        ch.add_item(main_css)
    html_toc_page.add_item(main_css)

    book.spine = [html_toc_page] + chapters # HTML ToC often first after cover (if any)
    _write_epub_file(book, filepath)
    
    ncx_p1 = epub.Link(chapters[0].file_name, "Part I: The Groundwork", "ncx_p1_p_tag")
    ncx_p1_c1 = epub.Link(chapters[1].file_name, "Chapter 1: First Principles", "ncx_p1_c1_p_tag")
    ncx_p1_c1_s1 = epub.Link(chapters[1].file_name + "#sec1", "Section 1.1: Initial Thoughts", "ncx_p1_c1_s1_p_tag")
    ncx_p1_c2 = epub.Link(chapters[2].file_name, "Chapter 2: Second Principles", "ncx_p1_c2_p_tag")
    
    ncx_p2 = epub.Link(chapters[3].file_name, "Part II: The Structure", "ncx_p2_p_tag")
    ncx_p2_c1 = epub.Link(chapters[4].file_name, "Chapter 3: Building Blocks", "ncx_p2_c1_p_tag")

    book.toc = (
        (ncx_p1,
            (
                (ncx_p1_c1, (ncx_p1_c1_s1,)),
                ncx_p1_c2
            )
        ),
        (ncx_p2, (ncx_p2_c1,))
    )

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav()) # Basic Nav
    style_content = """
    .toc-part { font-weight: bold; margin-left: 0em; margin-top: 1em; }
    .toc-chapter { margin-left: 1em; }
    .toc-section { margin-left: 2em; font-style: italic; }
    BODY {color: saddlebrown;}
    """
    main_css = epub.EpubItem(uid="style_ptoc", file_name="style/ptoc.css", media_type="text/css", content=style_content)
    book.add_item(main_css)
    html_toc_page.add_item(main_css) # Style for the ToC page itself
    for ch in chapters:
        ch.add_item(main_css)
        
    book.spine = ['nav', html_toc_page] + chapters
    _write_epub_file(book, filepath)

def create_epub_header_mixed_content(filename="header_mixed_content.epub"):
    """
    Creates an EPUB with headers (h1-h6) containing mixed content,
    e.g., <h2>Title <small>Subtitle</small></h2> (Kant example).
    """
    filepath = os.path.join(EPUB_DIR, "headers", filename)
    book = _create_epub_book("synth-epub-header-mixed-001", "Headers with Mixed Content EPUB")

    css_content = """
    h1 small { font-size: 0.7em; color: #555; font-style: italic; }
    h2 small { font-size: 0.8em; color: #666; font-weight: normal; }
    h3 span.marker { color: red; font-weight: bold; }
    BODY { font-family: sans-serif; }
    """
    style_item = epub.EpubItem(uid="style_header_mix", file_name="style/header_mix.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_details = [
        {"title": "Chapter One: Main Title with Subtitle", "filename": "c1_mixhead.xhtml",
         "content": """<h1 id="ch1">The Grand Philosophical Journey <small>An Introduction</small></h1>
<p>This chapter demonstrates a main title with a smaller subtitle within the H1 tag.</p>
<h2 id="sec1_1_mix">First Section <small>(Preliminary Remarks)</small></h2>
<p>Content for section 1.1, also featuring a subtitle in H2.</p>
<h3 id="sec1_2_mix">Second Section with a <span class="marker">Red Marker</span></h3>
<p>Content for section 1.2, with a styled span inside H3.</p>"""}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_mixhead_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_header_rosenzweig_hegel(filename="header_rosenzweig_hegel.epub"):
    """
    Creates an EPUB with header style like Rosenzweig's "Hegel and the State".
    e.g., <h1 class="chapter" id="c1">Chapter Title <span class="cn"><span class="bor">N</span></span></h1>
    """
    filepath = os.path.join(EPUB_DIR, "headers", filename)
    book = _create_epub_book("synth-epub-header-rosen-001", "Rosenzweig/Hegel Style Header EPUB")

    css_content = """
    h1.chapter { font-size: 1.5em; font-weight: bold; margin-bottom: 0.5em; border-bottom: 1px solid #ccc; padding-bottom: 0.2em;}
    h1.chapter span.cn { float: right; font-size: 0.9em; color: #333; }
    h1.chapter span.cn span.bor { border: 1px solid black; padding: 0.1em 0.3em; font-weight: normal; }
    BODY { font-family: 'Times New Roman', serif; }
    """
    style_item = epub.EpubItem(uid="style_header_rosen", file_name="style/header_rosen.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_details = [
        {"title": "The Dialectic of the State", "filename": "c1_rosen.xhtml",
         "content": """<h1 class="chapter" id="c1_rosen">The Dialectic of the State <span class="cn"><span class="bor">I</span></span></h1>
<p>This chapter uses a header style similar to that found in Rosenzweig's "Hegel and the State", 
featuring a chapter title with a styled chapter number floated to the right.</p>
<p>Further philosophical musings would go here, exploring the intricate relationship between the individual and the state, 
the nature of political obligation, and the historical development of state concepts.</p>"""},
        {"title": "Ethical Life and World History", "filename": "c2_rosen.xhtml",
         "content": """<h1 class="chapter" id="c2_rosen">Ethical Life and World History <span class="cn"><span class="bor">II</span></span></h1>
<p>The exploration continues into the realm of ethical life (Sittlichkeit) and its manifestation in world history.</p>"""}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (
        epub.Link(chapters[0].file_name, chapters[0].title, "c1_rosen_toc"),
        epub.Link(chapters[1].file_name, chapters[1].title, "c2_rosen_toc")
    )
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_header_derrida_gift_death(filename="header_derrida_gift_death.epub"):
    """
    Creates an EPUB with header style like Derrida's "Gift of Death".
    e.g., <h3>ONE</h3> (Chapter Number) and <h2>Secrets of European Responsibility</h2> (Chapter Title)
    """
    filepath = os.path.join(EPUB_DIR, "headers", filename)
    book = _create_epub_book("synth-epub-header-derrida-gd-001", "Derrida Gift of Death Style Header EPUB")

    css_content = """
    h3.chapnum-derrida-gd { font-size: 1.2em; font-weight: bold; text-align: center; margin-bottom: 0.1em; }
    h2.chaptitle-derrida-gd { font-size: 1.4em; font-style: italic; text-align: center; margin-bottom: 1.5em; }
    BODY { font-family: serif; }
    """
    style_item = epub.EpubItem(uid="style_header_derrida_gd", file_name="style/header_derrida_gd.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_details = [
        {"title": "ONE: Secrets of European Responsibility", "filename": "c1_derrida_gd.xhtml",
         "content": """<h3 class="chapnum-derrida-gd" id="c1_num_gd">ONE</h3>
<h2 class="chaptitle-derrida-gd" id="c1_title_gd">Secrets of European Responsibility</h2>
<p>This chapter emulates the header style from Derrida's "The Gift of Death", 
where a chapter number might be presented in an H3 tag, followed by the chapter title in an H2 tag.</p>
<p>The philosophical weight of such a title invites contemplation on ethics, responsibility, and the very foundations of European thought.</p>"""},
        {"title": "TWO: Whither the Political?", "filename": "c2_derrida_gd.xhtml",
         "content": """<h3 class="chapnum-derrida-gd" id="c2_num_gd">TWO</h3>
<h2 class="chaptitle-derrida-gd" id="c2_title_gd">Whither the Political?</h2>
<p>A subsequent chapter continuing the thematic exploration with a similar heading structure.</p>"""}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (
        epub.Link(chapters[0].file_name, chapters[0].title, "c1_derrida_gd_toc"),
        epub.Link(chapters[1].file_name, chapters[1].title, "c2_derrida_gd_toc")
    )
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_header_bch_p_strong(filename="header_bch_p_strong.epub"):
    """
    Creates an EPUB with styled <p> tag as header, like Byung-Chul Han.
    e.g., <p class="c9" id="..."><strong class="calibre3">TITLE</strong></p>
    """
    filepath = os.path.join(EPUB_DIR, "headers", filename)
    book = _create_epub_book("synth-epub-header-bch-001", "Byung-Chul Han Style P-Tag Header EPUB")

    css_content = """
    p.c9-bch { font-size: 1.3em; text-align: center; margin-top: 2em; margin-bottom: 1em; }
    p.c9-bch strong.calibre3-bch { font-weight: bold; letter-spacing: 0.05em; }
    BODY { font-family: Arial, sans-serif; }
    """
    style_item = epub.EpubItem(uid="style_header_bch", file_name="style/header_bch.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_details = [
        {"title": "THE BURNOUT SOCIETY", "filename": "c1_bch.xhtml",
         "content": """<p class="c9-bch" id="bch_title1"><strong class="calibre3-bch">THE BURNOUT SOCIETY</strong></p>
<p>This chapter uses a styled paragraph with a nested strong tag to represent a main title, 
a style observed in works by Byung-Chul Han.</p>
<p>The content would delve into critiques of late-modern capitalist society and its psychological impacts.</p>"""},
        {"title": "THE AGONY OF EROS", "filename": "c2_bch.xhtml",
         "content": """<p class="c9-bch" id="bch_title2"><strong class="calibre3-bch">THE AGONY OF EROS</strong></p>
<p>Another section employing the same paragraph-based header style.</p>"""}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (
        epub.Link(chapters[0].file_name, chapters[0].title, "c1_bch_toc"),
        epub.Link(chapters[1].file_name, chapters[1].title, "c2_bch_toc")
    )
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_header_derrida_specters_p(filename="header_derrida_specters_p.epub"):
    """
    Creates an EPUB with styled <p> tags for chapter number and title, like Derrida's "Specters of Marx".
    e.g., <p class="chapter-number_1"><a href="..."><b>1</b></a></p> 
           <p class="chapter-title_2"><a href="..."><b>TITLE</b></a></p>
    """
    filepath = os.path.join(EPUB_DIR, "headers", filename)
    book = _create_epub_book("synth-epub-header-derrida-sp-001", "Derrida Specters Style P-Tag Header EPUB")

    css_content = """
    p.chapter-number_1-sp { font-size: 1.1em; font-weight: bold; text-align: center; margin-bottom: 0.2em; }
    p.chapter-title_2-sp { font-size: 1.3em; font-style: italic; text-align: center; margin-bottom: 1.2em; }
    p.chapter-number_1-sp a, p.chapter-title_2-sp a { text-decoration: none; color: inherit; }
    BODY { font-family: 'Georgia', serif; }
    """
    style_item = epub.EpubItem(uid="style_header_derrida_sp", file_name="style/header_derrida_sp.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_details = [
        {"title": "Injunctions of Marx", "filename": "c1_derrida_sp.xhtml",
         "content": """<p class="chapter-number_1-sp" id="c1_num_sp"><a href="#c1_num_sp"><b>1</b></a></p>
<p class="chapter-title_2-sp" id="c1_title_sp"><a href="#c1_title_sp"><b>Injunctions of Marx</b></a></p>
<p>This chapter structure, with separate styled paragraphs for chapter number and title, 
is reminiscent of formatting found in Derrida's "Specters of Marx".</p>
<p>The text would explore themes of spectrality, inheritance, and the enduring legacy of Marxian thought.</p>"""},
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, "1. Injunctions of Marx", "c1_derrida_sp_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_footnote_hegel_sol_ref(filename="footnote_hegel_sol_ref.epub"):
    """
    Creates an EPUB with footnote reference style like Hegel's "Science of Logic".
    Ref: <span><a id="fileposXXXXX">...</a><a href="#fileposYYYYY"><sup class="calibre30">N</sup></a></span>
    Note text structure is already partially covered by create_epub_hegel_sol_style_footnotes,
    this focuses on the specific reference markup.
    """
    filepath = os.path.join(EPUB_DIR, "notes", filename)
    book = _create_epub_book("synth-epub-fn-hegel-sol-ref-001", "Hegel SoL Footnote Reference Style EPUB")

    css_content = """
    sup.calibre30-sol { vertical-align: super; font-size: 0.75em; }
    span.underline1-sol { text-decoration: underline; } /* For the empty span if needed */
    .fn-body-sol { margin-top: 1em; padding: 0.5em; border-top: 1px solid #eee; }
    .fn-body-sol sup.calibre30-sol { font-weight: bold; }
    BODY { font-family: 'Times New Roman', serif; }
    """
    style_item = epub.EpubItem(uid="style_fn_hegel_sol_ref", file_name="style/fn_hegel_sol_ref.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_content = """<h1>The Doctrine of Being</h1>
<p>In the progression of thought, the initial immediacy of Being <span><a id="textpos001"></a><a href="#fnpos001"><sup class="calibre30-sol">1</sup></a></span> reveals itself as insufficient. 
This leads to further determinations.</p>
<p>The concept of Nothing, often misunderstood <span><a id="textpos002"><span class="underline1-sol"></span></a><a href="#fnpos002"><sup class="calibre30-sol">2</sup></a></span>, plays a crucial role in this dialectic.</p>
<hr/>
<div class="fn-body-sol" id="fnpos001">
  <p><a href="#textpos001"><sup class="calibre30-sol">1</sup></a> Hegel's discussion of Being (Sein) is foundational. See Greater Logic, Book I, Section I, Chapter 1.</p>
</div>
<div class="fn-body-sol" id="fnpos002">
  <p><a href="#textpos002"><sup class="calibre30-sol">2</sup></a> The dialectical interplay between Being and Nothing gives rise to Becoming (Werden).</p>
</div>
"""
    chapter_details = [
        {"title": "Doctrine of Being (SoL Footnote Refs)", "filename": "c1_hegel_sol_fnref.xhtml", "content": chapter_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_hegel_sol_fnref_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)
def create_epub_header_kaplan_div(filename="header_kaplan_div.epub"):
    """
    Creates an EPUB with div-based chapter number and title, like Kaplan's "Beyond Post-Zionism".
    e.g., <div class="chapter-number">ONE</div> 
           <div class="chapter-title">TITLE</div>
    """
    filepath = os.path.join(EPUB_DIR, "headers", filename)
    book = _create_epub_book("synth-epub-header-kaplan-001", "Kaplan Style Div Header EPUB")

    css_content = """
    div.chapter-number-kaplan { font-size: 1em; font-weight: bold; text-align: center; margin-bottom: 0.1em; text-transform: uppercase; }
    div.chapter-title-kaplan { font-size: 1.5em; font-style: italic; text-align: center; margin-bottom: 1.5em; }
    BODY { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    """
    style_item = epub.EpubItem(uid="style_header_kaplan", file_name="style/header_kaplan.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_details = [
        {"title": "The End of Oslow", "filename": "c1_kaplan.xhtml",
         "content": """<div class="chapter-number-kaplan" id="c1_num_kaplan">ONE</div>
<div class="chapter-title-kaplan" id="c1_title_kaplan">The End of Oslow</div>
<p>This chapter uses div elements for chapter numbering and titles, a style seen in works like Kaplan's "Beyond Post-Zionism".</p>
<p>The content would typically analyze political and social shifts in relevant contexts.</p>"""},
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, "ONE: The End of Oslow", "c1_kaplan_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)
def create_epub_header_foucault_style(filename="header_foucault_style.epub"):
    """
    Creates an EPUB with a Foucault-style header.
    <h1><a id="p23"/>1<br/>________________<br/>THE UNITIES OF DISCOURSE</h1>
    """
    filepath = os.path.join(EPUB_DIR, "headers", filename)
    book = _create_epub_book("synth-epub-foucault-header-001", "Foucault Style Header EPUB")

    css_content = """
    h1.foucault-header { 
        text-align: center; 
        font-family: serif; 
        margin-bottom: 2em;
    }
    h1.foucault-header a { 
        text-decoration: none; 
        color: inherit; 
    }
    """
    style_item = epub.EpubItem(uid="style_foucault_h", file_name="style/foucault_h.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_content = """
<h1 class="foucault-header"><a id="p23"/>1<br/>________________<br/>THE UNITIES OF DISCOURSE</h1>
<p>This chapter simulates a header style found in some editions of Foucault's work, 
featuring a number, a horizontal rule (simulated with underscores), and the title, all within a single h1 tag.</p>
<p>The archaeological method, as Foucault describes, seeks to unearth the epistemic foundations of discourse...</p>
"""
    chapter_details = [
        {
            "title": "The Unities of Discourse", 
            "filename": "chap_foucault_1.xhtml",
            "content": chapter_content
        }
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (
        epub.Link(chapters[0].file_name + "#p23", "1. The Unities of Discourse", "foucault_ch1_toc"),
    )
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav()) 
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_header_descartes_dict_p(filename="header_descartes_dict_p.epub"):
    """
    Creates an EPUB with styled <p> tags for various heading levels, like "A Descartes Dictionary".
    e.g., <p class="ChapTitle">, <p class="AHead">, <p class="BHead">
    """
    filepath = os.path.join(EPUB_DIR, "headers", filename)
    book = _create_epub_book("synth-epub-header-descartes-dict-001", "Descartes Dictionary Style P-Tag Headers EPUB")

    css_content = """
    p.ChapTitle-dd { font-size: 1.6em; font-weight: bold; text-align: center; margin-top: 1.5em; margin-bottom: 0.8em; }
    p.AHead-dd { font-size: 1.3em; font-weight: bold; margin-top: 1em; margin-bottom: 0.4em; }
    p.BHead-dd { font-size: 1.1em; font-style: italic; font-weight: bold; margin-top: 0.8em; margin-bottom: 0.3em; }
    BODY { font-family: 'Garamond', serif; }
    """
    style_item = epub.EpubItem(uid="style_header_descartes_dict", file_name="style/header_descartes_dict.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_details = [
        {"title": "MIND (Mens)", "filename": "entry_mind_dd.xhtml",
         "content": """<p class="ChapTitle-dd" id="title_mind"><a href="#title_mind">MIND (Mens)</a></p>
<p>This entry simulates the heading structure of "A Descartes Dictionary", using styled paragraphs for different levels of headings.</p>
<p class="AHead-dd" id="ahead_substance"><strong>Mind as Substance</strong></p>
<p>Descartes famously argued for the mind as a distinct substance...</p>
<p class="BHead-dd" id="bhead_thinking"><strong><em>The Nature of Thinking</em></strong></p>
<p>Thinking, for Descartes, encompasses doubting, understanding, affirming, denying, willing, refusing, imagining, and sensing...</p>"""},
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, "MIND (Mens)", "entry_mind_dd_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_footnote_hegel_por_author(filename="footnote_hegel_por_author.epub"):
    """
    Creates an EPUB with Hegel's Philosophy of Right author footnote style (dagger).
    Ref: <sup class="calibre11"><a id="ifnX" href="part0011.html#fnX"><em class="calibre3">†</em></a></sup>
    This complements create_epub_dual_note_system which handles editor/translator notes.
    """
    filepath = os.path.join(EPUB_DIR, "notes", filename)
    book = _create_epub_book("synth-epub-fn-hegel-por-author-001", "Hegel PoR Author Footnote EPUB")

    css_content = """
    sup.calibre11-hpor { vertical-align: super; font-size: 0.75em; }
    sup.calibre11-hpor em.calibre3-hpor { font-style: normal; /* Dagger is already distinct */ }
    .fn-author-hpor { margin-top: 0.5em; padding-left: 1em; font-size: 0.9em; }
    .fn-author-hpor em.calibre3-hpor { font-style: normal; }
    BODY { font-family: 'Times New Roman', serif; }
    """
    style_item = epub.EpubItem(uid="style_fn_hegel_por_author", file_name="style/fn_hegel_por_author.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_content = """<h1>The Concept of Right</h1>
<p>The abstract concept of Right, in its initial phase, is purely formal.<sup class="calibre11-hpor"><a id="ifn1" href="#fn1-author"><em class="calibre3-hpor">†</em></a></sup> 
Its realization requires further development through property, contract, and wrong.</p>
<p>This formal Right is the sphere of abstract personality.<sup class="calibre11-hpor"><a id="ifn2" href="#fn2-author"><em class="calibre3-hpor">‡</em></a></sup></p>
<hr/>
<div class="fn-author-hpor" id="fn1-author">
  <p><em class="calibre3-hpor">†</em> This is an author's own note, typically marked with a dagger or similar symbol in Hegel's PoR editions.</p>
</div>
<div class="fn-author-hpor" id="fn2-author">
  <p><em class="calibre3-hpor">‡</em> Another authorial clarification or aside.</p>
</div>
"""
    chapter_details = [
        {"title": "Concept of Right (Author Notes)", "filename": "c1_hegel_por_author_fn.xhtml", "content": chapter_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_hegel_por_author_fn_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_footnote_marx_engels_reader(filename="footnote_marx_engels_reader.epub"):
    """
    Creates an EPUB with footnote reference style like "Marx & Engels Reader".
    Ref: <a id="footnote-refXX" href="part0057.html#footnoteXX" class="calibre8"><span><sup class="calibre9">N</sup></span></a>
    """
    filepath = os.path.join(EPUB_DIR, "notes", filename)
    book = _create_epub_book("synth-epub-fn-marx-engels-001", "Marx & Engels Reader Footnote Style EPUB")

    css_content = """
    a.calibre8-mer { text-decoration: none; }
    sup.calibre9-mer { vertical-align: super; font-size: 0.75em; }
    .endnote-section-mer { margin-top: 2em; border-top: 1px dashed #999; padding-top: 1em; }
    .endnote-item-mer { margin-bottom: 0.5em; font-size: 0.9em; }
    .endnote-item-mer sup.calibre9-mer { font-weight: bold; }
    BODY { font-family: sans-serif; }
    """
    style_item = epub.EpubItem(uid="style_fn_marx_engels", file_name="style/fn_marx_engels.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    main_content_xhtml = """<h1>Critique of the Gotha Program</h1>
<p>In a higher phase of communist society, after the enslaving subordination of the individual to the division of labor, and therewith also the antithesis between mental and physical labor, has vanished; after labor has become not only a means of life but life's prime want; <a id="footnote-ref01" href="notes_mer.xhtml#footnote01" class="calibre8-mer"><span><sup class="calibre9-mer">1</sup></span></a> after the productive forces have also increased with the all-around development of the individual, and all the springs of co-operative wealth flow more abundantly<a id="footnote-ref02" href="notes_mer.xhtml#footnote02" class="calibre8-mer"><span><sup class="calibre9-mer">2</sup></span></a> – only then can the narrow horizon of bourgeois right be crossed in its entirety and society inscribe on its banners: From each according to his ability, to each according to his needs!</p>
"""
    notes_content_xhtml = """<h2>Notes</h2>
<div class="endnote-section-mer">
  <div class="endnote-item-mer" id="footnote01">
    <p><a href="main_mer.xhtml#footnote-ref01" class="calibre8-mer"><span><sup class="calibre9-mer">1</sup></span></a> This refers to the utopian socialists' views on labor.</p>
  </div>
  <div class="endnote-item-mer" id="footnote02">
    <p><a href="main_mer.xhtml#footnote-ref02" class="calibre8-mer"><span><sup class="calibre9-mer">2</sup></span></a> Marx's vision of abundance in a communist society.</p>
  </div>
</div>
"""

    main_chap = epub.EpubHtml(title="Critique of Gotha Program", file_name="main_mer.xhtml", lang="en")
    main_chap.content = main_content_xhtml
    main_chap.add_item(style_item)
    book.add_item(main_chap)

    notes_page = epub.EpubHtml(title="Notes", file_name="notes_mer.xhtml", lang="en")
    notes_page.content = notes_content_xhtml
    notes_page.add_item(style_item)
    book.add_item(notes_page)
    
    book.toc = (
        epub.Link(main_chap.file_name, "Critique of Gotha Program", "main_mer_toc"),
        epub.Link(notes_page.file_name, "Notes", "notes_mer_toc")
    )
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav', main_chap, notes_page]
    _write_epub_file(book, filepath)
def create_epub_footnote_marcuse_dual_style(filename="footnote_marcuse_dual_style.epub"):
    """
    Creates an EPUB with Marcuse's dual footnote style (asterisk and numbered).
    Ref: Asterisk: <a href="#fn-fnref1_1" id="fn1_1">*</a>
         Numbered: <a href="#fn-fnref1_5" id="fn1_5"><sup>1</sup></a>
    """
    filepath = os.path.join(EPUB_DIR, "notes", filename)
    book = _create_epub_book("synth-epub-fn-marcuse-dual-001", "Marcuse Dual Footnote Style EPUB")

    css_content = """
    a.fn-marcuse-ast { text-decoration: none; font-weight: bold; }
    a.fn-marcuse-num sup { vertical-align: super; font-size: 0.75em; }
    .footnote-section-marcuse { margin-top: 1.5em; border-top: 1px solid #ccc; padding-top: 0.8em; }
    p.fn-marcuse { margin-left: 1em; margin-bottom: 0.3em; font-size: 0.9em; }
    p.fn-marcuse a { font-weight: normal; }
    BODY { font-family: 'Arial Narrow', sans-serif; }
    """
    style_item = epub.EpubItem(uid="style_fn_marcuse_dual", file_name="style/fn_marcuse_dual.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_content = """<h1>One-Dimensional Man Revisited</h1>
<p>The critique of advanced industrial society remains pertinent.<a href="#fn-fnref_ast1" id="fn_ast1" class="fn-marcuse-ast">*</a> 
Its mechanisms of control are subtle yet pervasive.</p>
<p>Consider the role of technology in shaping consciousness.<a href="#fn-fnref_num1" id="fn_num1" class="fn-marcuse-num"><sup>1</sup></a> 
This is a key aspect of the analysis.</p>
<p>Further points expand on these themes.<a href="#fn-fnref_ast2" id="fn_ast2" class="fn-marcuse-ast">†</a> 
And more numbered insights.<a href="#fn-fnref_num2" id="fn_num2" class="fn-marcuse-num"><sup>2</sup></a></p>
<hr/>
<div class="footnote-section-marcuse">
  <p class="fn-marcuse"><a id="fn-fnref_ast1" href="#fn_ast1">*</a> Marcuse's original thesis on the flattening of culture.</p>
  <p class="fn-marcuse"><a id="fn-fnref_num1" href="#fn_num1">1.</a> See discussion on technological rationality.</p>
  <p class="fn-marcuse"><a id="fn-fnref_ast2" href="#fn_ast2">†</a> A secondary symbolic note.</p>
  <p class="fn-marcuse"><a id="fn-fnref_num2" href="#fn_num2">2.</a> Further elaboration on the previous point.</p>
</div>
"""
    chapter_details = [
        {"title": "Marcuse Dual Notes", "filename": "c1_marcuse_dual_fn.xhtml", "content": chapter_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_marcuse_dual_fn_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_footnote_adorno_unlinked(filename="footnote_adorno_unlinked.epub"):
    """
    Creates an EPUB with Adorno's unlinked footnote style.
    Ref: <sup class="calibre5"><small class="calibre6"><span class="calibre7">N</span></small></sup>
    """
    filepath = os.path.join(EPUB_DIR, "notes", filename)
    book = _create_epub_book("synth-epub-fn-adorno-unlinked-001", "Adorno Unlinked Footnote Style EPUB")

    css_content = """
    sup.calibre5-adorno { vertical-align: super; font-size: 0.7em; }
    small.calibre6-adorno { font-size: 0.9em; } /* May not be strictly necessary if sup is small enough */
    span.calibre7-adorno { /* No specific style, just for structure */ }
    .footnote-text-adorno { margin-top: 1em; font-size: 0.85em; padding-left: 1.5em; text-indent: -1.5em; }
    BODY { font-family: 'Minion Pro', serif; }
    """
    style_item = epub.EpubItem(uid="style_fn_adorno_unlinked", file_name="style/fn_adorno_unlinked.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_content = """<h1>Negative Dialectics Fragment</h1>
<p>The constellation of concepts is crucial.<sup class="calibre5-adorno"><small class="calibre6-adorno"><span class="calibre7-adorno">1</span></small></sup> 
Identity thinking must be resisted.</p>
<p>Auschwitz has rendered all culture, including the critical theory that arises from it, suspect.<sup class="calibre5-adorno"><small class="calibre6-adorno"><span class="calibre7-adorno">2</span></small></sup></p>
<hr/>
<div class="footnotes-section-adorno">
  <p class="footnote-text-adorno">1. This refers to Adorno's methodological approach.</p>
  <p class="footnote-text-adorno">2. A central tenet of Adorno's later philosophy.</p>
</div>
"""
    chapter_details = [
        {"title": "Adorno Unlinked Notes", "filename": "c1_adorno_unlinked_fn.xhtml", "content": chapter_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_adorno_unlinked_fn_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_footnote_derrida_grammatology_dual(filename="footnote_derrida_grammatology_dual.epub"):
    """
    Creates an EPUB with Derrida's "Of Grammatology" dual footnote system.
    Symbol-marked to separate small files: <a class="nounder" href="../Text/chXX_fnYY.html#footZZZ">*</a>
    Numbered to consolidated file: <sup><a class="nounder" href="../Text/ch08_notes.html#chXXenYYa">N</a></sup>
    """
    filepath = os.path.join(EPUB_DIR, "notes", filename)
    book = _create_epub_book("synth-epub-fn-derrida-gram-001", "Derrida Grammatology Dual Footnote EPUB")

    css_content = """
    a.nounder-derrida { text-decoration: none; }
    sup a.nounder-derrida { vertical-align: super; font-size: 0.75em; }
    .footnote-sep-file { font-size: 0.9em; margin-top: 0.5em; }
    .endnotes-consolidated-file { font-size: 0.9em; margin-top: 1em; border-top: 1px solid #aaa; padding-top: 0.5em; }
    BODY { font-family: 'Palatino Linotype', 'Book Antiqua', Palatino, serif; }
    """
    style_item = epub.EpubItem(uid="style_fn_derrida_gram", file_name="style/fn_derrida_gram.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    # Main content file
    main_chap_content = """<h1>The End of the Book and the Beginning of Writing</h1>
<p>The concept of the "trace" is fundamental to this deconstruction.<a class="nounder-derrida" href="../Text/fn_gram_c1_01.xhtml#fn_trace">*</a> 
It precedes presence.</p>
<p>Logocentrism has dominated Western metaphysics.<sup><a class="nounder-derrida" href="../Text/notes_gram_consolidated.xhtml#en_logo">1</a></sup> 
This critique aims to unsettle that dominance.</p>
<p>Another point requiring a separate note.<a class="nounder-derrida" href="../Text/fn_gram_c1_02.xhtml#fn_diff">†</a></p>
<p>And a further consolidated endnote.<sup><a class="nounder-derrida" href="../Text/notes_gram_consolidated.xhtml#en_supp">2</a></sup></p>
"""
    main_chap = epub.EpubHtml(title="The End of the Book", file_name="Text/c1_grammatology.xhtml", lang="en")
    main_chap.content = main_chap_content
    main_chap.add_item(style_item)
    book.add_item(main_chap)

    # Separate footnote file 1
    fn1_content = "<html><body><p class='footnote-sep-file' id='fn_trace'>* On the concept of the trace and its implications for signification.</p></body></html>"
    fn1_page = epub.EpubHtml(title="Footnote Trace", file_name="Text/fn_gram_c1_01.xhtml", lang="en")
    fn1_page.content = fn1_content
    fn1_page.add_item(style_item)
    book.add_item(fn1_page)

    # Separate footnote file 2
    fn2_content = "<html><body><p class='footnote-sep-file' id='fn_diff'>† This relates to différance, a key neologism.</p></body></html>"
    fn2_page = epub.EpubHtml(title="Footnote Différance", file_name="Text/fn_gram_c1_02.xhtml", lang="en")
    fn2_page.content = fn2_content
    fn2_page.add_item(style_item)
    book.add_item(fn2_page)

    # Consolidated endnotes file
    endnotes_content = """<h2>Endnotes</h2>
<div class="endnotes-consolidated-file">
  <p id="en_logo">1. For an extended discussion of logocentrism, see Part I.</p>
  <p id="en_supp">2. The logic of the supplement is explored throughout the text.</p>
</div>
"""
    endnotes_page = epub.EpubHtml(title="Consolidated Endnotes", file_name="Text/notes_gram_consolidated.xhtml", lang="en")
    endnotes_page.content = endnotes_content
    endnotes_page.add_item(style_item)
    book.add_item(endnotes_page)
    
    book.toc = (
        epub.Link(main_chap.file_name, "The End of the Book", "c1_gram_toc"),
        # Optionally list note files in NCX as per Derrida example in requirements
        epub.Link(fn1_page.file_name, "Note: Trace", "fn1_gram_toc"),
        epub.Link(fn2_page.file_name, "Note: Différance", "fn2_gram_toc"),
        epub.Link(endnotes_page.file_name, "Endnotes (Consolidated)", "endnotes_gram_toc")
    )
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav', main_chap, fn1_page, fn2_page, endnotes_page] # Order might vary
    _write_epub_file(book, filepath)

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

def create_epub_image_as_special_text(filename="image_as_special_text.epub"):
    """
    Creates an EPUB that uses an image for special text/symbols, like Hegel SoL.
    Ref: <img alt="" src="images/00003.jpg" class="calibre18"/>
    Requires a dummy image file.
    """
    filepath = os.path.join(EPUB_DIR, "images_fonts", filename)
    book = _create_epub_book("synth-epub-img-special-text-001", "Image for Special Text EPUB")

    css_content = """
    img.calibre18-hegel-img { height: 1.2em; vertical-align: middle; border: 1px solid lightgray; }
    BODY { font-family: 'Georgia', serif; }
    """
    style_item = epub.EpubItem(uid="style_img_special_text", file_name="style/img_special_text.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    # Create a dummy image file (e.g., a small black square)
    dummy_image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x05\x00\x00\x00\x05\x08\x02\x00\x00\x00\x02\x08\x17\x9f\x00\x00\x00\x0cIDATx\x9cc`\x00\x00\x00\x04\x00\x01\xf1\x0f\x8e\x0e\x00\x00\x00\x00IEND\xaeB`\x82' # 5x5 black PNG
    image_item = epub.EpubItem(uid="img_special_char", file_name="images/special_char_placeholder.png", media_type="image/png", content=dummy_image_content)
    book.add_item(image_item)
    
    # Add cover image to manifest if it's a common pattern with such images
    # book.set_cover("images/cover_placeholder.png", dummy_image_content) # Example

    chapter_content = """<h1>Logic and Its Symbols</h1>
<p>In some philosophical texts, particularly older editions or complex logical treatises, 
special symbols might be rendered as images. For example, a specific logical operator 
<img alt="[special operator]" src="../images/special_char_placeholder.png" class="calibre18-hegel-img"/> 
could be used throughout the text.</p>
<p>This tests the handling of such embedded images that represent textual or symbolic content, 
rather than purely illustrative figures. Another instance: <img alt="[another symbol]" src="../images/special_char_placeholder.png" class="calibre18-hegel-img"/>.</p>
"""
    chapter_details = [
        {"title": "Image as Special Text", "filename": "c1_img_special_text.xhtml", "content": chapter_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_img_special_text_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_font_obfuscated(filename="font_obfuscated.epub"):
    """
    Creates an EPUB structure that indicates font obfuscation via META-INF/encryption.xml.
    The actual font files and encryption are not performed, only the structural indicator.
    """
    filepath = os.path.join(EPUB_DIR, "images_fonts", filename)
    book = _create_epub_book("synth-epub-font-obfuscated-001", "Obfuscated Font Structure EPUB")
    book.epub_version = "2.0" # Often seen with older DRM/obfuscation

    css_content = """
    @font-face {
        font-family: 'ObfuscatedSans';
        src: url('../fonts/obfuscated_font.ttf'); /* Path relative to CSS file */
    }
    body { font-family: 'ObfuscatedSans', sans-serif; color: #333; }
    h1 { font-weight: normal; }
    """
    style_item = epub.EpubItem(uid="style_font_obf", file_name="style/font_obf.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    # Dummy font file (content doesn't matter for this test, only its manifest entry)
    dummy_font_content = b'This is not a real font file.'
    font_item = epub.EpubItem(uid="font_obf_sans", file_name="fonts/obfuscated_font.ttf", media_type="application/x-font-truetype", content=dummy_font_content)
    book.add_item(font_item)

    chapter_content = """<h1>Text with Obfuscated Font</h1>
<p>This EPUB is structured to suggest that its fonts might be obfuscated or encrypted. 
The key indicator for a system would be the presence of an <code>encryption.xml</code> file 
in the <code>META-INF</code> directory, referencing font files.</p>
<p>The actual text rendering would depend on the reading system's ability to handle such obfuscation.</p>
"""
    chapter_details = [
        {"title": "Obfuscated Font Test", "filename": "c1_font_obf.xhtml", "content": chapter_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    # Create a dummy encryption.xml content
    # This is a simplified example. Real encryption.xml can be more complex.
    encryption_xml_content = u"""<?xml version="1.0" encoding="UTF-8"?>
<encryption xmlns="urn:oasis:names:tc:opendocument:xmlns:container" xmlns:enc="http://www.w3.org/2001/04/xmlenc#">
  <enc:EncryptedData>
    <enc:EncryptionMethod Algorithm="http://www.idpf.org/2008/embedding" />
    <enc:CipherData>
      <enc:CipherReference URI="OEBPS/fonts/obfuscated_font.ttf" /> 
      โซ่<!-- This is just a placeholder for where encrypted key might be or other data -->
    </enc:CipherData>
  </enc:EncryptedData>
</encryption>
"""
    # Add encryption.xml to META-INF. ebooklib doesn't have a direct way, so we add it as a generic item.
    # The path needs to be correct for EPUB structure.
    # ebooklib will place items added via book.add_item() into the OEBPS folder by default if path is not specified.
    # To put it in META-INF, we might need to adjust how _write_epub_file works or handle it manually.
    # For now, we'll add it and note that its location is key.
    # A more robust solution would involve manipulating the EPUB ZIP archive post-creation.
    # Let's assume for this test, its presence in manifest with a META-INF path is indicative.
    # However, ebooklib doesn't allow specifying paths outside OEBPS for add_item.
    # So, this test will primarily rely on the *concept* and the OPF potentially referencing it if a tool did it.
    # The most direct way to test this is to check for encryption.xml after generation.
    # We will add a custom attribute to the book to signify this for test validation.
    if not hasattr(book, 'custom_files_to_add'):
        book.custom_files_to_add = {}
    book.custom_files_to_add["META-INF/encryption.xml"] = encryption_xml_content.encode('utf-8')

    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_font_obf_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath) # _write_epub_file would need modification to handle custom_files_to_add

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
    # Actual generation of the <guide> section in OPF is handled by ebooklib based on this.

    book.toc = (
        epub.Link(chapters[0].file_name, chapters[0].title, "c1_epub2_toc"),
        epub.Link(chapters[1].file_name, chapters[1].title, "c2_epub2_toc")
    )
    book.add_item(epub.EpubNcx())
    # No EPUB3 NavDoc for a pure EPUB2 example usually, NCX is primary.
    
    # Typical EPUB2 spine order
    # book.spine = [cover_page, toc_page] + chapters # Original
    book.spine = chapters # Simplified for debugging
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
    book.add_metadata(None, 'meta', '', {'property': 'title-type', 'refines': '#' + book.uid + '_title_alt', '_text': 'subtitle'}) # Requires another dc:title for subtitle
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

def create_epub_content_dialogue(filename="content_dialogue.epub"):
    """
    Creates an EPUB with dialogue content.
    """
    filepath = os.path.join(EPUB_DIR, "content_types", filename)
    book = _create_epub_book("synth-epub-content-dialogue-001", "Dialogue Content EPUB")

    css_content = """
    p.speaker { font-weight: bold; margin-bottom: 0.2em; }
    p.dialogue { margin-left: 2em; margin-bottom: 0.8em; }
    div.scene-description { font-style: italic; color: #555; margin-bottom: 1em; text-align: center; }
    BODY { font-family: 'Verdana', sans-serif; }
    """
    style_item = epub.EpubItem(uid="style_dialogue", file_name="style/dialogue.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_content = """<h1>A Philosophical Debate</h1>
<div class="scene-description">Two philosophers, Alex and Ben, are seated in a study.</div>
<p class="speaker">Alex:</p>
<p class="dialogue">The nature of consciousness, it seems to me, remains the most profound mystery.</p>
<p class="speaker">Ben:</p>
<p class="dialogue">Indeed. But do you believe it is a mystery that can be unraveled by empirical means alone? Or does it require a different mode of inquiry altogether?</p>
<p class="speaker">Alex:</p>
<p class="dialogue">That is precisely the question. If we limit ourselves to third-person observation, we risk missing the essence of subjective experience.</p>
<p class="speaker">Ben:</p>
<p class="dialogue">Yet, without empirical grounding, are we not merely speculating? Where is the line between philosophical insight and untestable assertion?</p>
"""
    chapter_details = [
        {"title": "Dialogue on Consciousness", "filename": "c1_dialogue.xhtml", "content": chapter_content}
    ]
def create_epub_content_epigraph(filename="content_epigraph.epub"):
    """
    Creates an EPUB with an epigraph.
    Ref: Pippin example <div class="epigraph"><p class="epf">Epigraph text.</p></div>
    """
    filepath = os.path.join(EPUB_DIR, "content_types", filename)
    book = _create_epub_book("synth-epub-content-epigraph-001", "Epigraph Content EPUB")

    css_content = """
    div.epigraph-pippin { 
        margin-top: 1em; margin-bottom: 2em; 
        margin-left: 15%; margin-right: 5%; 
        font-style: italic; 
    }
    p.epf-pippin { text-align: right; color: #555; }
    p.epf-source-pippin { text-align: right; color: #777; font-size: 0.9em; }
    BODY { font-family: 'Garamond', serif; }
    """
    style_item = epub.EpubItem(uid="style_epigraph", file_name="style/epigraph.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_content = """<h1>Chapter One: Beginnings</h1>
<div class="epigraph-pippin">
  <p class="epf-pippin">"The owl of Minerva spreads its wings only with the falling of the dusk."</p>
  <p class="epf-source-pippin">— G.W.F. Hegel, <em>Philosophy of Right</em></p>
</div>
<p>This chapter begins after an epigraph, a common feature in philosophical texts. 
The epigraph sets a tone or introduces a key theme for the ensuing discussion.</p>
<p>The main body of the chapter would then proceed to elaborate on its central arguments.</p>
"""
    chapter_details = [
        {"title": "Chapter with Epigraph", "filename": "c1_epigraph.xhtml", "content": chapter_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_epigraph_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_content_blockquote_styled(filename="content_blockquote_styled.epub"):
    """
    Creates an EPUB with styled blockquotes.
    Ref: Hegel SoL: <blockquote class="calibre14">
    """
    filepath = os.path.join(EPUB_DIR, "content_types", filename)
    book = _create_epub_book("synth-epub-content-blockquote-001", "Styled Blockquote EPUB")

    css_content = """
    blockquote.calibre14-hegelsol { 
        font-family: 'Times New Roman', Times, serif;
        font-size: 0.95em; 
        margin-left: 2em; margin-right: 1em; 
        padding: 0.5em 0.8em; 
        border-left: 3px solid #888; 
        background-color: #f9f9f9;
    }
    blockquote.calibre14-hegelsol p { margin-top: 0.3em; margin-bottom: 0.3em; }
    BODY { font-family: 'Arial', sans-serif; }
    """
    style_item = epub.EpubItem(uid="style_blockquote", file_name="style/blockquote.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_content = """<h1>Quoting Authorities</h1>
<p>Philosophical arguments often involve quoting other thinkers. For example, one might cite Kant:</p>
<blockquote class="calibre14-hegelsol">
  <p>"Two things fill the mind with ever new and increasing admiration and awe, the more often and steadily we reflect upon them: 
  the starry heavens above me and the moral law within me."</p>
  <p>— Immanuel Kant, <em>Critique of Practical Reason</em></p>
</blockquote>
<p>This synthetic EPUB demonstrates a styled blockquote, similar to formatting found in some editions of Hegel or other scholarly works, 
where quotes are visually set apart from the main text using specific classes and CSS.</p>
"""
    chapter_details = [
        {"title": "Styled Blockquotes", "filename": "c1_blockquote.xhtml", "content": chapter_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_blockquote_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
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
def create_epub_content_internal_cross_refs(filename="content_internal_cross_refs.epub"):
    """
    Creates an EPUB with internal cross-references.
    Ref: Pippin example <a class="xref" href="...">Cross-ref text</a>
    """
    filepath = os.path.join(EPUB_DIR, "content_types", filename)
    book = _create_epub_book("synth-epub-content-xref-001", "Internal Cross-References EPUB")

    css_content = """
    a.xref-pippin { color: #2a6496; text-decoration: underline; }
    h2#target_section { background-color: #f0f0f0; padding: 0.2em; }
    BODY { font-family: 'Lucida Grande', sans-serif; }
    """
    style_item = epub.EpubItem(uid="style_xref", file_name="style/xref.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter1_content = """<h1>Chapter One: Introducing Concepts</h1>
<p>In this chapter, we lay out the foundational ideas. 
Later, in <a class="xref-pippin" href="c2_xref.xhtml#target_section">our discussion of applications</a>, 
we will see how these concepts play out in practice.</p>
<p id="intro_point">This specific point will be referenced from Chapter 2.</p>
"""
    chapter2_content = """<h1>Chapter Two: Applications and Further Details</h1>
<p>As mentioned in <a class="xref-pippin" href="c1_xref.xhtml#intro_point">the introductory chapter</a>, 
the practical applications are numerous.</p>
<h2 id="target_section">Detailed Applications</h2>
<p>This section is the target of a cross-reference from the first chapter. 
It demonstrates how internal links can connect different parts of the text, 
enhancing navigation and coherence in scholarly or complex works.</p>
"""
    chapter_details = [
        {"title": "Chapter 1 (XRef Source)", "filename": "c1_xref.xhtml", "content": chapter1_content},
        {"title": "Chapter 2 (XRef Target)", "filename": "c2_xref.xhtml", "content": chapter2_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (
        epub.Link(chapters[0].file_name, chapters[0].title, "c1_xref_toc"),
        epub.Link(chapters[1].file_name, chapters[1].title, "c2_xref_toc")
    )
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_content_forced_page_breaks(filename="content_forced_page_breaks.epub"):
    """
    Creates an EPUB with forced page breaks using div style.
    Ref: Derrida example <div style="page-break-before: always;" />
    """
    filepath = os.path.join(EPUB_DIR, "content_types", filename)
    book = _create_epub_book("synth-epub-content-forcebreak-001", "Forced Page Breaks EPUB")

    # No specific CSS needed for the break itself, but general styling is good.
    css_content = "BODY { font-family: 'Arial', sans-serif; line-height: 1.4; }"
    style_item = epub.EpubItem(uid="style_forcebreak", file_name="style/forcebreak.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_content = """<h1>Chapter with Forced Breaks</h1>
<p>This paragraph represents the content on what would be the first page or section.</p>
<p>It discusses introductory concepts before a significant shift in topic or presentation that warrants a forced break.</p>
<div style="page-break-before: always;"></div>
<h2>A New Section After Break</h2>
<p>This content appears after a forced page break. Such breaks are sometimes used in EPUBs, 
often converted from print layouts, to try and mimic the print pagination, 
or to ensure a new major section starts on a new "page" in the reading system.</p>
<div style="page-break-before: always;"></div>
<p>Another paragraph, appearing on yet another "page" due to a forced break. 
This tests the reading system's handling of such CSS-driven pagination control.</p>
"""
    chapter_details = [
        {"title": "Forced Page Breaks Example", "filename": "c1_forcebreak.xhtml", "content": chapter_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_forcebreak_toc"),)
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
    xpgt_item = epub.EpubItem(uid="adobe_page_template", 
                              file_name="META-INF/template.xpgt", # Desired path
                              media_type="application/vnd.adobe-page-template+xml", 
                              content=dummy_xpgt_content)
    # book.add_item(xpgt_item) # This would place it in OEBPS.
    # The manifest_extra_items will add this to the book items.
    # The custom_files_to_add logic in _write_epub_file also adds it as a book item, causing duplication.
    # Relying on manifest_extra_items to create the item.
    # if not hasattr(book, 'custom_files_to_add'):
    #     book.custom_files_to_add = {}
    # book.custom_files_to_add["META-INF/template.xpgt"] = dummy_xpgt_content # This causes duplication with manifest_extra_items
    
    book.manifest_extra_items = [
        {'id': 'adobe_page_template', 'href': 'META-INF/template.xpgt', 'media_type': 'application/vnd.adobe-page-template+xml'}
    ]


    chapter_details = [
        {"title": "Chapter with Adobe Artifacts", "filename": "c1_adobe.xhtml", 
         "content": "<h1>Adobe Processed Content</h1><p>This EPUB simulates characteristics of a file processed by Adobe software, "
                    "which might include specific meta tags in the OPF and references to Adobe Page Template (.xpgt) files.</p>"}
    ]
    chapters = _add_epub_chapters(book, chapter_details)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_adobe_toc"),)
    book.add_item(epub.EpubNcx())
    # No NavDoc for this EPUB2 example
    book.spine = ['nav'] + chapters # 'nav' here refers to NCX if no EpubNav is primary
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
    # A separate metadata.opf is also typical of Calibre's working directory, but inside the EPUB,
    # it's usually merged into the main content.opf. We are testing the content.opf metadata here.

    chapter_details = [
        {"title": "Chapter Processed by Calibre", "filename": "c1_calibre.xhtml", 
         "content": "<h1>Calibre Processed Content</h1><p>This chapter simulates content that might have been processed or managed by Calibre, leading to specific metadata entries in the OPF file.</p>"}
    ]
    chapters = _add_epub_chapters(book, chapter_details)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_calibre_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_dialogue_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)
    # The path needs to be correct for EPUB structure.
    # ebooklib will place items added via book.add_item() into the OEBPS folder by default if path is not specified.
    # To put it in META-INF, we might need to adjust how _write_epub_file works or handle it manually.
    # For now, we'll add it and note that its location is key.
    # A more robust solution would involve manipulating the EPUB ZIP archive post-creation.
    # Let's assume for this test, its presence in manifest with a META-INF path is indicative.
    # However, ebooklib doesn't allow specifying paths outside OEBPS for add_item.
    # So, this test will primarily rely on the *concept* and the OPF potentially referencing it if a tool did it.
    # The most direct way to test this is to check for encryption.xml after generation.
    # We will add a custom attribute to the book to signify this for test validation.
    book.custom_files_to_add = {
        # "META-INF/encryption.xml": encryption_xml_content.encode('utf-8') # Erroneous line removed
    }

    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_font_obf_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath) # _write_epub_file would need modification to handle custom_files_to_add

    css_content = """
    a.calibre10-kantpage { /* Usually invisible, but we can style for testing */
        display: inline-block; width: 1px; height: 1px; 
        /* background-color: red; opacity: 0.5; */ /* For visual debugging */
    }
    BODY { font-family: 'Times New Roman', serif; line-height: 1.6; }
    """
    style_item = epub.EpubItem(uid="style_pgnum_kant_anchor", file_name="style/pgnum_kant_anchor.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_content = """<h1>Prolegomena to Any Future Metaphysics</h1>
<p>The first part of the Prolegomena begins here.<a id="page_A19" class="calibre10-kantpage"></a> This text simulates the placement of 
page anchors as found in some editions of Kant's works, often derived from Calibre or similar converters.</p>
<p>These anchors, like <code><a id="page_B33" class="calibre10-kantpage"></a></code>, 
are typically empty and used by reading systems or conversion tools to map print page numbers.</p>
<p>Here is another marker for a new page.<a id="page_A20" class="calibre10-kantpage"></a> The philosophical argument continues, 
addressing the possibility of synthetic a priori judgments.</p>
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
    book.add_item(style_item)

    chapter_content = """<h1>Critique of Pure Reason: A Synthetic Overview</h1>
<p>The transcendental deduction of the categories is a cornerstone of Kant's critical project 
<span class="kant-citation">(KrV, A 84/B 116 – A 130/B 169)</span>. 
It seeks to demonstrate the objective validity of the pure concepts of the understanding.</p>
<p>Kant distinguishes between analytic and synthetic judgments <span class="kant-citation">(Prolegomena, §2; 4:266-268)</span>, 
a distinction crucial for understanding his approach to metaphysics.</p>
<p>The antinomies of pure reason reveal the limits of speculative thought when it ventures beyond the bounds of possible experience 
<span class="kant-citation">(KrV, A 405/B 432 – A 567/B 595)</span>.</p>
"""
    chapter_details = [
        {"title": "Kant In-Text Citations", "filename": "c1_kant_cite.xhtml", "content": chapter_content}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_kant_cite_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)
    # Orphaned code block causing NameError fully removed.
    book = _create_epub_book("synth-epub-no-ncx-001", "Missing NCX EPUB")
    book.epub_version = "3.0" # Ensure it's EPUB 3

    chapter_details = [
        {"title": "Chapter One", "filename": "c1.xhtml", "content": "<h1>Chapter One</h1><p>Content here.</p>"},
        {"title": "Chapter Two", "filename": "c2.xhtml", "content": "<h1>Chapter Two</h1><p>More content.</p>"}
    ]
    chapters = _add_epub_chapters(book, chapter_details)
    
    # Create a NavDoc that will serve as the primary ToC
    nav_html = epub.EpubHtml(title='Navigation', file_name='nav.xhtml', lang='en')
    nav_html.content=u"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>Navigation</title>
  <meta charset="utf-8" />
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Table of Contents</h1>
    <ol>
      <li><a href="c1.xhtml">Chapter One</a></li>
      <li><a href="c2.xhtml">Chapter Two</a></li>
    </ol>
  </nav>
  <nav epub:type="landmarks" hidden="">
    <h1>Landmarks</h1>
    <ol>
      <li><a epub:type="toc" href="nav.xhtml#toc">Table of Contents</a></li>
      <li><a epub:type="bodymatter" href="c1.xhtml">Start of Content</a></li>
    </ol>
  </nav>
</body>
</html>
"""
    book.add_item(nav_html)
    book.spine = [nav_html] + chapters # Nav HTML should be in spine and marked as 'nav'
    
    # Add nav_html to guide for EPUB2 readers (though we are aiming for EPUB3 here)
    # book.guide.append({'type': 'toc', 'title': 'Table of Contents', 'href': 'nav.xhtml'})
    
    # DO NOT add epub.EpubNcx()
    
    style = 'BODY {color: darkcyan;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css) # Add to book items
    for ch in chapters: # Link to chapters
        ch.add_item(nav_css)
    nav_html.add_item(nav_css) # Link to nav doc as well

    _write_epub_file(book, filepath)

def create_epub_navdoc_full(filename="navdoc_full.epub"):
    """
    Creates an EPUB 3 with a comprehensive NavDoc (ToC, Landmarks, PageList).
    """
    filepath = os.path.join(EPUB_DIR, "toc", filename)
    book = _create_epub_book("synth-epub-navdoc-full-001", "Full NavDoc EPUB")
    book.epub_version = "3.0"

    # Create content files with page anchors
    ch1_content = """<h1>Chapter 1: The Beginning</h1>
<p>This is the first page of chapter 1.<span epub:type="pagebreak" id="page_1" title="1"/></p>
<p>This is the second page of chapter 1.<span epub:type="pagebreak" id="page_2" title="2"/></p>"""
    c1 = epub.EpubHtml(title="Chapter 1", file_name="ch1.xhtml", lang="en")
    c1.content = ch1_content

    ch2_content = """<h1>Chapter 2: The Middle</h1>
<p>Content for page 3.<span epub:type="pagebreak" id="page_3" title="3"/></p>"""
    c2 = epub.EpubHtml(title="Chapter 2", file_name="ch2.xhtml", lang="en")
    c2.content = ch2_content
    
    cover_page = epub.EpubHtml(title="Cover", file_name="cover.xhtml", lang="en")
    cover_page.content = "<h1>The Great Synthetic Novel</h1><p>by A. Coder</p>"
    # For a real cover, you'd add an image and set book.set_cover(...)

    book.add_item(cover_page)
    book.add_item(c1)
    book.add_item(c2)
    chapters = [c1, c2]

    # Create NavDoc
    nav_html_content = u"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>Navigation</title>
  <meta charset="utf-8" />
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Table of Contents</h1>
    <ol>
      <li><a href="ch1.xhtml">Chapter 1: The Beginning</a></li>
      <li><a href="ch2.xhtml">Chapter 2: The Middle</a></li>
    </ol>
  </nav>
  <nav epub:type="landmarks" hidden="">
    <h1>Landmarks</h1>
    <ol>
      <li><a epub:type="cover" href="cover.xhtml">Cover Page</a></li>
      <li><a epub:type="toc" href="#toc">Table of Contents</a></li>
      <li><a epub:type="bodymatter" href="ch1.xhtml">Start of Content</a></li>
    </ol>
  </nav>
  <nav epub:type="page-list" hidden="">
    <h1>Page List</h1>
    <ol>
      <li><a href="ch1.xhtml#page_1">1</a></li>
      <li><a href="ch1.xhtml#page_2">2</a></li>
      <li><a href="ch2.xhtml#page_3">3</a></li>
    </ol>
  </nav>
</body>
</html>
"""
    nav_html = epub.EpubHtml(title='Navigation', file_name='nav.xhtml', lang='en')
    nav_html.content = nav_html_content
    nav_html.properties.append('nav') # Mark this as the NavDoc in OPF properties
    book.add_item(nav_html)

    # NCX for backward compatibility (optional for pure EPUB3, but good practice)
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_ncx"),
                epub.Link(chapters[1].file_name, chapters[1].title, "c2_ncx"))
    book.add_item(epub.EpubNcx())

    style = 'BODY {color: darkslateblue;}'
    main_css = epub.EpubItem(uid="style_main", file_name="style/main.css", media_type="text/css", content=style)
    book.add_item(main_css)
    cover_page.add_item(main_css)
    for ch in chapters:
        ch.add_item(main_css)
    nav_html.add_item(main_css)


    book.spine = ['nav', cover_page] + chapters # NavDoc should be first in spine if it's the primary nav
    _write_epub_file(book, filepath)


def create_epub_p_tag_headers(filename="p_tag_headers.epub"):
    filepath = os.path.join(EPUB_DIR, "headers", filename)
    book = _create_epub_book("synth-epub-p-headers-001", "P Tag Headers EPUB")
    css_content = """
    body { font-family: sans-serif; }
    p.h1-style { font-size: 2em; font-weight: bold; margin-top: 1em; margin-bottom: 0.5em; }
    p.h2-style { font-size: 1.5em; font-weight: bold; margin-top: 0.8em; margin-bottom: 0.4em; }
    p.h3-style { font-size: 1.2em; font-weight: bold; margin-top: 0.6em; margin-bottom: 0.3em; }
    """
    style_item = epub.EpubItem(uid="style_main", file_name="style/main.css", media_type="text/css", content=css_content)
    book.add_item(style_item)
    chapter_details = [
        {"title": "Chapter 1 with P-Tag Headers", "filename": "chap_01_p_headers.xhtml", "content": """
<p class="h1-style">Chapter 1: The Illusion of Structure</p>
<p>This chapter uses paragraph tags styled as headers. This tests the system's ability to identify headers based on styling or contextual cues rather than just standard h1-h6 tags.</p>
<p class="h2-style">Section 1.1: Semantic Ambiguity</p>
<p>When is a paragraph not just a paragraph? When it's a header in disguise. Philosophical texts sometimes employ such stylistic choices, either by design or as artifacts of conversion.</p>
<p class="h3-style">Subsection 1.1.1: The Baudrillard Effect</p>
<p>Consider texts where the visual hierarchy is paramount, and HTML semantics are secondary. This subsection delves into that concept.</p>
<p>Some normal paragraph text to follow.</p>
"""},
        {"title": "Chapter 2: More P-Styled Fun", "filename": "chap_02_p_headers.xhtml", "content": """
<p class="h1-style">Chapter 2: Deconstructing Norms</p>
<p>Continuing the theme of non-standard headers.</p>
<p class="h2-style">Section 2.1: The Heideggerian Question Mark</p>
<p>Heidegger's "Basic Questions of Philosophy" sometimes uses styled paragraphs for thematic divisions. This section emulates that.</p>
<p>Another paragraph of standard text.</p>
"""}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    book.toc = tuple(epub.Link(ch.file_name, ch.title, ch.file_name.split('.')[0]) for ch in chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_headers_with_edition_markers(filename="headers_edition_markers.epub"):
    filepath = os.path.join(EPUB_DIR, "headers", filename)
    book = _create_epub_book("synth-epub-edition-markers-001", "Headers with Edition Markers")
    chapter_details = [
        {"title": "Critique of Pure Reason [A]", "filename": "kant_a_section.xhtml", "content": """
<h1 id="a1">The Transcendental Aesthetic [A 19 / B 33]</h1>
<p>This section begins the first part of the Critique, following the A edition pagination. The markers [A 19 / B 33] are embedded directly in the header.</p>
<h2 id="a1_sec1">Section I: Of Space [A 22 / B 37]</h2>
<p>Here we discuss space. Note the edition markers.</p>
<p>Some text about space... [A 23 / B 38]</p>
<p>More text... [A 24 / B 39]</p>
"""},
        {"title": "Critique of Pure Reason [B]", "filename": "kant_b_section.xhtml", "content": """
<h1 id="b1">The Transcendental Aesthetic [B 33 / A 19] - Revised</h1>
<p>This section follows the B edition pagination, with cross-reference to A. The markers are again in the header.</p>
<h2 id="b1_sec1">Section I: Of Space (Revised) [B 37 / A 22]</h2>
<p>The discussion of space, revised for the B edition.</p>
<p>Some B edition text about space... [B 38 / A 23]</p>
<p>More B edition text... [B 39 / A 24]</p>
"""}
    ]
    chapters = _add_epub_chapters(book, chapter_details)
    book.toc = (epub.Link(chapters[0].file_name, "Critique A Section", "kant_a"), epub.Link(chapters[1].file_name, "Critique B Section", "kant_b"))
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    style = 'BODY {color: darkred;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)
def create_epub_pippin_style_endnotes(filename="pippin_style_endnotes.epub"):
    """
    Creates an EPUB with Pippin-style endnotes.
    Ref: <a class="fnref" href="target_notes_file.xhtml#fnX" id="fnXr">N</a>
    """
    filepath = os.path.join(EPUB_DIR, "notes", filename)
    book = _create_epub_book("synth-epub-pippin-fn-001", "Pippin-Style Endnotes EPUB")
    book.epub_version = "3.0" # Often seen with EPUB3 structures

    css_content = """
    body { font-family: 'Times New Roman', Times, serif; }
    a.fnref { text-decoration: none; color: #A52A2A; vertical-align: super; font-size: 0.75em;}
    .endnote-pippin { margin-left: 1em; text-indent: -1em; margin-bottom: 0.3em;}
    """
    style_item = epub.EpubItem(uid="style_pippin_notes", file_name="style/pippin_notes.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    endnotes_content = """<h1>Notes</h1>
<p class="endnote-pippin" id="fn1">1. This is the first Pippin-style endnote, typically found in a dedicated notes file.</p>
<p class="endnote-pippin" id="fn2">2. Another endnote, demonstrating the collection of notes.</p>
"""
    endnotes_page = epub.EpubHtml(title="Notes", file_name="notes_pippin.xhtml", lang="en")
    endnotes_page.content = endnotes_content
    endnotes_page.add_item(style_item)
    book.add_item(endnotes_page)

    chapter_details = [
        {
            "title": "Chapter with Pippin-Style Notes", 
            "filename": "chap_pippin_fn.xhtml",
            "content": """
<h1>Chapter Alpha: The Dialectic of Recognition</h1>
<p>Pippin's work on Hegel often explores the theme of recognition.<a class="fnref" href="notes_pippin.xhtml#fn1" id="fnref1">1</a> 
This concept is crucial for understanding intersubjectivity.</p>
<p>The struggle for recognition, as Hegel outlines, is a dynamic process.<a class="fnref" href="notes_pippin.xhtml#fn2" id="fnref2">2</a></p>
"""
        }
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    book.toc = (
        epub.Link(chapters[0].file_name, chapters[0].title, "chap_pippin_toc"),
        epub.Link(endnotes_page.file_name, "Notes", "pippin_notes_toc_ncx") # Ensure unique ID for NCX
    )
    # Also ensure endnotes_page is part of the toc structure if not already handled by spine for linking
    book.add_item(epub.EpubNcx())
    # Add landmarks to NavDoc
    nav_doc_content = u"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Navigation</title></head>
<body>
  <nav epub:type="toc" id="toc"><h1>Contents</h1><ol>
    <li><a href="chap_pippin_fn.xhtml">Chapter Alpha</a></li>
    <li><a href="notes_pippin.xhtml">Notes</a></li>
  </ol></nav>
  <nav epub:type="landmarks"><h1>Landmarks</h1><ol>
    <li><a epub:type="bodymatter" href="chap_pippin_fn.xhtml">Start of Content</a></li>
    <li><a epub:type="notes" href="notes_pippin.xhtml">Notes</a></li>
  </ol></nav>
</body></html>"""
    nav_doc_item = epub.EpubHtml(title='Navigation', file_name='nav_pippin.xhtml', lang='en')
    nav_doc_item.content = nav_doc_content
    nav_doc_item.properties.append('nav')
    nav_doc_item.add_item(style_item) # Add style to nav doc
    book.add_item(nav_doc_item)
    book.spine = [nav_doc_item] + chapters + [endnotes_page] # Restored original spine
    _write_epub_file(book, filepath)

def create_epub_heidegger_ge_style_endnotes(filename="heidegger_ge_endnotes.epub"):
    """
    Creates an EPUB with Heidegger (German Existentialism) style endnotes.
    Ref: <sup><a href="notes.html#ftn_fnX" id="ref_ftn_fnX"><span><span class="footnote_number">N</span></span></a></sup>
    """
    filepath = os.path.join(EPUB_DIR, "notes", filename)
    book = _create_epub_book("synth-epub-heidegger-ge-fn-001", "Heidegger GE-Style Endnotes")

    css_content = """
    body { font-family: 'Arial', sans-serif; }
    sup a { text-decoration: none; }
    .footnote_number { font-size: 0.7em; vertical-align: super; color: #3333AA; }
    .endnote-heidegger-ge { margin-left: 1.5em; text-indent: -1.5em; margin-bottom: 0.4em;}
    """
    style_item = epub.EpubItem(uid="style_heidegger_ge_notes", file_name="style/heidegger_ge.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    endnotes_content = """<h1>Notes</h1>
<p class="endnote-heidegger-ge" id="ftn_fn1"><a href="chap_heidegger_ge.xhtml#ref_ftn_fn1"><span><span class="footnote_number">1</span></span></a>. This is the first note, in the style of Heidegger's German Existentialism EPUBs.</p>
<p class="endnote-heidegger-ge" id="ftn_fn2"><a href="chap_heidegger_ge.xhtml#ref_ftn_fn2"><span><span class="footnote_number">2</span></span></a>. Another note, following the same complex reference and text structure.</p>
"""
    endnotes_page = epub.EpubHtml(title="Notes", file_name="notes_heidegger_ge.xhtml", lang="en")
    endnotes_page.content = endnotes_content
    endnotes_page.add_item(style_item)
    book.add_item(endnotes_page)

    chapter_details = [
        {
            "title": "Chapter with Heidegger GE-Style Notes", 
            "filename": "chap_heidegger_ge.xhtml",
            "content": """
<div class="title-chapter"><span class="b">The Essence of Truth</span></div>
<div class="p-indent"><span>Heidegger's inquiry into truth involves a departure from traditional correspondence theories.<sup><a href="notes_heidegger_ge.xhtml#ftn_fn1" id="ref_ftn_fn1"><span><span class="footnote_number">1</span></span></a></sup> 
Aletheia, or unhiddenness, becomes a key concept.</span></div>
<div class="p-indent"><span>This unhiddenness is not a static property but an event of disclosure.<sup><a href="notes_heidegger_ge.xhtml#ftn_fn2" id="ref_ftn_fn2"><span><span class="footnote_number">2</span></span></a></sup></span></div>
"""
        }
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    book.toc = (
        epub.Link(chapters[0].file_name, "The Essence of Truth", "chap_hge_toc"),
        epub.Link(endnotes_page.file_name, "Notes", "hge_notes_toc")
    )
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav()) 
    book.spine = ['nav'] + chapters + [endnotes_page]
    _write_epub_file(book, filepath)

def create_epub_heidegger_metaphysics_style_footnotes(filename="heidegger_metaphysics_footnotes.epub"):
    """
    Creates an EPUB with Heidegger (Metaphysics) style same-page footnotes.
    Ref: <sup><a aria-describedby="fnX" epub:type="noteref" href="#fnX" id="ftX">N</a></sup>
    Note text: <section class="notesSet" role="doc-endnotes"><ol class="notesList"><li class="noteEntry" role="doc-endnote">...</li></ol></section>
    """
    filepath = os.path.join(EPUB_DIR, "notes", filename)
    book = _create_epub_book("synth-epub-heidegger-meta-fn-001", "Heidegger Metaphysics-Style Footnotes")
    book.epub_version = "3.0"

    css_content = """
    body { font-family: 'Palatino Linotype', 'Book Antiqua', Palatino, serif; }
    sup a { text-decoration: none; color: #4B0082; } /* Indigo */
    section.notesSet { margin-top: 2em; padding-top: 1em; border-top: 1px solid #ccc; }
    ol.notesList { list-style-type: none; padding-left: 0; }
    li.noteEntry { margin-bottom: 0.5em; font-size: 0.9em;}
    li.noteEntry p { margin: 0; }
    """
    style_item = epub.EpubItem(uid="style_heidegger_meta_notes", file_name="style/heidegger_meta.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_details = [
        {
            "title": "Chapter with Heidegger Metaphysics-Style Notes", 
            "filename": "chap_heidegger_meta_fn.xhtml",
            "content": """
<h1><span class="chapterNumber">1</span> <span class="chapterTitle">The Question of Being Revisited</span></h1>
<p>The fundamental question of metaphysics, for Heidegger, is the question of Being.<sup><a aria-describedby="fn1_meta" epub:type="noteref" href="#fn1_meta" id="ft1_meta">1</a></sup> 
This is not a question about beings, but Being itself.</p>
<p>He distinguishes this from ontical inquiries which focus on entities.<sup><a aria-describedby="fn2_meta" epub:type="noteref" href="#fn2_meta" id="ft2_meta">2</a></sup></p>

<section class="notesSet" role="doc-endnotes" epub:type="footnotes">
  <h2 class="notes_title_hidden">Footnotes</h2> <!-- Often hidden by CSS -->
  <ol class="notesList">
    <li class="noteEntry" id="fn1_meta" role="doc-footnote" epub:type="footnote"><p><a epub:type="backlink" href="#ft1_meta" role="doc-backlink">1.</a> As elaborated in *Being and Time*. {TN: Translator's note - this is a simplification.}</p></li>
    <li class="noteEntry" id="fn2_meta" role="doc-footnote" epub:type="footnote"><p><a epub:type="backlink" href="#ft2_meta" role="doc-backlink">2.</a> The ontic-ontological difference is key.</p></li>
  </ol>
</section>
"""
        }
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    book.toc = (epub.Link(chapters[0].file_name, "Chapter 1", "chap_hm_toc"),)
    
    nav_doc_item = epub.EpubNav() # Basic NavDoc
    book.add_item(nav_doc_item)
    book.add_item(epub.EpubNcx()) # For backward compatibility
    
    book.spine = ['nav'] + chapters # 'nav' refers to EpubNav
    _write_epub_file(book, filepath)

def create_epub_same_page_footnotes(filename="same_page_footnotes.epub"):
    filepath = os.path.join(EPUB_DIR, "notes", filename)
    book = _create_epub_book("synth-epub-same-page-fn-001", "Same-Page Footnotes EPUB")
    css_content = """
    body { font-family: serif; }
    .footnote { font-size: 0.8em; margin-top: 1em; border-top: 1px solid #ccc; padding-top: 0.5em; }
    sup a { text-decoration: none; color: blue; }"""
    style_item = epub.EpubItem(uid="style_notes", file_name="style/notes.css", media_type="text/css", content=css_content)
    book.add_item(style_item)
    chapter_details = [{"title": "Chapter with Footnotes", "filename": "chap_footnotes.xhtml", "content": """
<h1>Chapter 1: The Burden of Proof</h1>
<p>In philosophical discourse, the burden of proof often shifts. Consider the assertion that synthetic data can fully replicate the nuances of human-generated text.<sup id="fnref1"><a href="#fn1">1</a></sup> This is a strong claim.</p>
<p>One might argue that the very act of synthesis, being a programmed endeavor, inherently limits the scope of what can be produced. It lacks the serendipity of human thought.<sup id="fnref2"><a href="#fn2">2</a></sup></p>
<hr class="footnote-separator" />
<div class="footnotes">
<p id="fn1" class="footnote"><a href="#fnref1">1.</a> This claim is often debated in AI ethics circles, particularly concerning generative models.</p>
<p id="fn2" class="footnote"><a href="#fnref2">2.</a> See Turing's arguments on "Lady Lovelace's Objection" regarding machine originality.</p>
</div>"""}]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "chap_fn"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_endnotes_separate_file(filename="endnotes_separate_file.epub"):
    filepath = os.path.join(EPUB_DIR, "notes", filename)
    book = _create_epub_book("synth-epub-endnotes-sep-001", "Separate Endnotes EPUB")
    css_content = """
    body { font-family: serif; }
    sup a { text-decoration: none; color: green; }
    .endnote-item { margin-bottom: 0.5em; }"""
    style_item = epub.EpubItem(uid="style_endnotes", file_name="style/endnotes.css", media_type="text/css", content=css_content)
    book.add_item(style_item)
    endnotes_content = """<h1>Endnotes</h1>
<div id="en1" class="endnote-item"><p><a href="chap_main.xhtml#enref1">1.</a> The concept of "Dasein" is central to Heidegger's Being and Time.</p></div>
<div id="en2" class="endnote-item"><p><a href="chap_main.xhtml#enref2">2.</a> This refers to the Socratic paradox, "I know that I know nothing."</p></div>
<div id="en3" class="endnote-item"><p><a href="chap_main_page2.xhtml#enref3">3.</a> Foucault's analysis of power structures is detailed in "Discipline and Punish".</p></div>"""
    endnotes_page = epub.EpubHtml(title="Endnotes", file_name="endnotes.xhtml", lang="en")
    endnotes_page.content = endnotes_content
    endnotes_page.add_item(style_item)
    book.add_item(endnotes_page)
    chapter_details = [
        {"title": "Main Content - Page 1", "filename": "chap_main.xhtml", "content": """
<h1>Chapter 1: Existential Inquiries</h1>
<p>Heidegger's notion of being-in-the-world presents a complex phenomenological account.<sup id="enref1"><a href="endnotes.xhtml#en1">1</a></sup> It challenges traditional subject-object dichotomies.</p>
<p>The pursuit of wisdom often begins with acknowledging ignorance.<sup id="enref2"><a href="endnotes.xhtml#en2">2</a></sup> This is a recurring theme in ancient philosophy.</p>"""},
        {"title": "Main Content - Page 2", "filename": "chap_main_page2.xhtml", "content": """
<h1>Chapter 2: Power and Knowledge</h1>
<p>Foucault explored the intricate relationship between power and knowledge systems.<sup id="enref3"><a href="endnotes.xhtml#en3">3</a></sup> His work has been influential in various disciplines.</p>"""}
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    book.toc = (epub.Link(chapters[0].file_name, "Chapter 1", "chap1_end"), epub.Link(chapters[1].file_name, "Chapter 2", "chap2_end"), epub.Link(endnotes_page.file_name, "Endnotes", "endnotes_toc_link"))
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters + [endnotes_page]
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

def create_epub_poetry(filename="poetry_formatting.epub"):
    filepath = os.path.join(EPUB_DIR, "content_types", filename)
    book = _create_epub_book("synth-epub-poetry-001", "Verses of Synthesis")
    css_content = """
    body { font-family: 'Times New Roman', Times, serif; }
    .poem { margin-left: 2em; margin-bottom: 1em; }
    .poem-title { font-style: italic; text-align: center; margin-bottom: 0.5em; }
    .stanza { margin-bottom: 1em; }
    .poemline { display: block; text-indent: -1em; margin-left: 1em; } /* Basic hanging indent */
    p.poemline.indent1 { margin-left: 2em; text-indent: -1em; }
    p.poemline.indent2 { margin-left: 3em; text-indent: -1em; }
    """
    style_item = epub.EpubItem(uid="style_poetry", file_name="style/poetry.css", media_type="text/css", content=css_content)
    book.add_item(style_item)
    chapter_details = [{"title": "Ode to a Synthetic Text", "filename": "ode_synthetic.xhtml", "content": """
<h1>Ode to a Synthetic Text</h1>
<div class="poem">
  <p class="poem-title">Ode to a Synthetic Text</p>
  <div class="stanza">
    <p class="poemline">Born of code, not feathered quill,</p>
    <p class="poemline">Your purpose clear, your content still.</p>
    <p class="poemline">You test the logic, sharp and keen,</p>
    <p class="poemline">A silent actor on the digital scene.</p>
  </div>
  <div class="stanza">
    <p class="poemline">No muse's fire, no poet's ache,</p>
    <p class="poemline indent1">Just algorithms, for goodness sake!</p>
    <p class="poemline">Yet in your structure, we might find,</p>
    <p class="poemline indent1">A mimicry of heart and mind.</p>
  </div>
</div>
<p>This section tests poetry formatting, including stanzas and line indentations.</p>
"""}]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "ode_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_kant_style_footnotes(filename="kant_style_footnotes.epub"):
    """
    Creates an EPUB with Kant-style same-page footnotes.
    Ref: <sup><em class="calibreX"><a>...</a></em></sup> and <p class="footnotes">
    """
    filepath = os.path.join(EPUB_DIR, "notes", filename)
    book = _create_epub_book("synth-epub-kant-fn-001", "Kant-Style Footnotes EPUB")

    css_content = """
    body { font-family: 'Georgia', serif; }
    .calibre1 { font-style: italic; }
    .calibre9 { text-decoration: none; color: #0000FF; } /* Example blue link */
    .calibre18 {} /* Example sup container class */
    p.footnotes { font-size: 0.75em; margin-top: 1.5em; border-top: 1px dashed #999; padding-top: 0.75em; }
    """
    style_item = epub.EpubItem(uid="style_kant_notes", file_name="style/kant_notes.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_details = [
        {
            "title": "Chapter with Kantian Footnotes", 
            "filename": "chap_kant_fn.xhtml",
            "content": """
<h1>Chapter 1: The Synthetic A Priori</h1>
<p>Kant's exploration of synthetic a priori judgments revolutionized philosophy.<sup class="calibre18"><em class="calibre1"><a id="Fkantfn1" href="#Fkantfr1" class="calibre9">1</a></em></sup> 
This concept is foundational to his transcendental idealism.</p>
<p>He argues that concepts without intuitions are empty, while intuitions without concepts are blind.<sup class="calibre18"><em class="calibre1"><a id="Fkantfn2" href="#Fkantfr2" class="calibre9">2</a></em></sup></p>
<hr />
<div>
  <p id="Fkantfr1" class="footnotes"><sup class="calibre18"><em class="calibre1"><a href="#Fkantfn1" class="calibre9">1.</a></em></sup> See Critique of Pure Reason, B19.</p>
  <p id="Fkantfr2" class="footnotes"><sup class="calibre18"><em class="calibre1"><a href="#Fkantfn2" class="calibre9">2.</a></em></sup> Ibid., A51/B75. This highlights the interplay between sensibility and understanding.</p>
</div>
"""
        }
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "chap_kant_fn_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav()) 
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_hegel_sol_style_footnotes(filename="hegel_sol_footnotes.epub"):
    """
    Creates an EPUB with Hegel's Science of Logic style footnotes.
    Ref: <span><a><sup ...></a></span> and complex div/blockquote for note text.
    """
    filepath = os.path.join(EPUB_DIR, "notes", filename)
    book = _create_epub_book("synth-epub-hegel-sol-fn-001", "Hegel SoL-Style Footnotes")

    css_content = """
    body { font-family: 'Minion Pro', serif; }
    .calibre30 { font-size: 0.75em; vertical-align: super; } /* For sup in ref */
    .calibre32 { margin-top: 1em; border-top: 1px solid black; padding-top: 0.5em; } /* div container for note */
    .calibre33 {} /* inner div */
    .calibre14 { margin: 0; padding: 0; font-size: 0.9em; } /* blockquote for note text */
    a { text-decoration: none; color: #550000; } /* Dark red link */
    """
    style_item = epub.EpubItem(uid="style_hegel_sol_notes", file_name="style/hegel_sol.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    chapter_details = [
        {
            "title": "Chapter with Hegelian Footnotes", 
            "filename": "chap_hegel_sol_fn.xhtml",
            "content": """
<h1>Chapter 1: Being, Nothing, Becoming</h1>
<p>The dialectical movement from Being through Nothing to Becoming is a cornerstone of Hegelian logic.<span><a id="hegelFNref1"></a><a href="#hegelFN1"><sup class="calibre30">1</sup></a></span> 
This initial triad sets the stage for the entire system.</p>
<p>Pure Being, devoid of all determination, is indistinguishable from Pure Nothing.<span><a id="hegelFNref2"></a><a href="#hegelFN2"><sup class="calibre30">2</sup></a></span></p>

<div class="calibre32" id="hegelFN1">
  <div class="calibre33">
    <blockquote class="calibre14">
      <span><a href="#hegelFNref1"><sup class="calibre30">1</sup></a></span> 
      This is discussed extensively in the opening sections of the Science of Logic. The transition is not merely a juxtaposition but an immanent development.
    </blockquote>
  </div>
</div>
<div class="calibre32" id="hegelFN2">
  <div class="calibre33">
    <blockquote class="calibre14">
      <span><a href="#hegelFNref2"><sup class="calibre30">2</sup></a></span> 
      Hegel, G.W.F. *Science of Logic*, Miller translation, p. 82. "Being, pure being, without any further determination..."
    </blockquote>
  </div>
</div>
"""
        }
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "chap_hegel_sol_fn_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav()) 
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

def create_epub_dual_note_system(filename="dual_note_system.epub"):
    """
    Creates an EPUB with a dual note system (e.g., Hegel's Philosophy of Right).
    Numbered endnotes (editor) and symbol-based same-page footnotes (author).
    """
    filepath = os.path.join(EPUB_DIR, "notes", filename)
    book = _create_epub_book("synth-epub-dual-notes-001", "Dual Note System EPUB")

    css_content = """
    body { font-family: 'Garamond', serif; }
    .footnote-author { font-size: 0.8em; margin-top: 0.5em; padding-top: 0.2em; border-top: 1px dotted #666; }
    .endnote-editor-ref sup a { color: #006400; } /* Dark green for editor notes */
    .footnote-author-ref sup a { color: #800000; } /* Maroon for author notes */
    .endnote-item { margin-bottom: 0.5em; }
    """
    style_item = epub.EpubItem(uid="style_dual_notes", file_name="style/dual_notes.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    # Editor's Endnotes HTML file
    editor_endnotes_content = """
<h1>Editor's Endnotes</h1>
<div id="editorEN1" class="endnote-item">
  <p><a href="chap_dual.xhtml#editorENref1">1.</a> This passage refers to the political climate of early 19th century Prussia.</p>
</div>
<div id="editorEN2" class="endnote-item">
  <p><a href="chap_dual.xhtml#editorENref2">2.</a> The term "Sittlichkeit" (ethical life) is crucial here.</p>
</div>
"""
    editor_endnotes_page = epub.EpubHtml(title="Editor's Endnotes", file_name="editor_endnotes.xhtml", lang="en")
    editor_endnotes_page.content = editor_endnotes_content
    editor_endnotes_page.add_item(style_item)
    book.add_item(editor_endnotes_page)

    chapter_details = [
        {
            "title": "Chapter with Dual Notes", 
            "filename": "chap_dual.xhtml",
            "content": """
<h1>The State and Ethical Life</h1>
<p>The realization of freedom in the objective spirit is the state.<sup class="footnote-author-ref"><a id="authorFNrefStar" href="#authorFNStar">*</a></sup> 
This is not merely an aggregation of individuals but an organic whole.<sup class="endnote-editor-ref"><a id="editorENref1" href="editor_endnotes.xhtml#editorEN1">1</a></sup></p>
<p>Ethical life (Sittlichkeit) finds its actuality in the institutions of family, civil society, and the state.<sup class="endnote-editor-ref"><a id="editorENref2" href="editor_endnotes.xhtml#editorEN2">2</a></sup> 
The individual achieves true self-consciousness through participation in these universal forms.<sup class="footnote-author-ref"><a id="authorFNrefDagger" href="#authorFNDagger">†</a></sup></p>
<hr />
<div class="footnotes-author">
  <p id="authorFNStar" class="footnote-author"><a href="#authorFNrefStar">*</a> Author's own clarification: This refers to the rational state, not any empirical instantiation.</p>
  <p id="authorFNDagger" class="footnote-author"><a href="#authorFNrefDagger">†</a> Author's note: Compare with ancient Greek polis.</p>
</div>
"""
        }
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (
        epub.Link(chapters[0].file_name, "Chapter Dual Notes", "chap_dual_toc"),
        epub.Link(editor_endnotes_page.file_name, "Editor's Endnotes", "editor_notes_toc")
    )
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav()) 
    book.spine = ['nav'] + chapters + [editor_endnotes_page]
    _write_epub_file(book, filepath)