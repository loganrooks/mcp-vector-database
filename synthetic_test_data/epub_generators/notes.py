import os
from ebooklib import epub
from ..common import EPUB_DIR, _create_epub_book, _add_epub_chapters, _write_epub_file

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

    endnotes_content = """<h1>Test Notes</h1><p id="fn1">This is a test note.</p>"""
    endnotes_page = epub.EpubHtml(title="Notes", file_name="notes_pippin.xhtml", lang="en")
    endnotes_page.content = endnotes_content
    endnotes_page.add_item(style_item)
    book.add_item(endnotes_page)

    chapter_details = [
        {
            "title": "Test Chapter Pippin",
            "filename": "chap_pippin_fn.xhtml",
            "content": """<h1>Test Chapter Content</h1><p>This is test chapter content with a note.<a class="fnref" href="notes_pippin.xhtml#fn1" id="fnref1">1</a></p>"""
        }
    ]
    chapters = _add_epub_chapters(book, chapter_details, default_style_item=style_item)
    book.toc = (
        epub.Link(chapters[0].file_name, chapters[0].title, "chap_pippin_toc"),
        epub.Link(endnotes_page.file_name, "Notes", "pippin_notes_toc_ncx") # Ensure unique ID for NCX
    )
    # Also ensure endnotes_page is part of the toc structure if not already handled by spine for linking
    book.add_item(epub.EpubNcx())
    
    # Replace custom NavDoc with default EpubNav to address manifest issues
    # This will generate a nav.xhtml based on book.toc
    # The custom landmarks from the original nav_doc_content will be lost.
    default_nav = epub.EpubNav()
    book.add_item(default_nav)
    default_nav.add_item(style_item) # Add style to the default nav

    # Spine uses 'nav' which refers to the item with 'nav' property (EpubNav sets this on itself)
    book.spine = [default_nav] + chapters + [endnotes_page]
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