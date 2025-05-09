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