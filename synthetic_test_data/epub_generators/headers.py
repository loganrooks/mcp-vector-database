import os
from ebooklib import epub
from ..common import EPUB_DIR, _create_epub_book, _add_epub_chapters, _write_epub_file

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