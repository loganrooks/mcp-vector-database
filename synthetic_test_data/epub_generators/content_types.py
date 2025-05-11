import os
from ebooklib import epub
from ..common import EPUB_DIR, _create_epub_book, _add_epub_chapters, _write_epub_file

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
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    
    book.toc = (epub.Link(chapters[0].file_name, chapters[0].title, "c1_dialogue_toc"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    _write_epub_file(book, filepath)

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