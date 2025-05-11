# Synthetic Test Data Requirements for PhiloGraph Tier 0 MVP

## 1. Introduction

This document outlines the requirements for a suite of synthetic test data designed to comprehensively test the parsing, preprocessing, chunking, metadata extraction, and relationship extraction capabilities of the PhiloGraph Tier 0 MVP. The requirements are derived from the analysis of various EPUB, PDF, and Markdown formatting patterns detailed in the [`docs/reports/epub_formatting_analysis_report.md`](docs/reports/epub_formatting_analysis_report.md).

## 2. General Requirements for All File Types

*   **Content:** Should include philosophical text excerpts, ideally with identifiable authors, titles, and publication years to test metadata extraction.
*   **Language:** Primarily English, but include examples with non-ASCII characters (e.g., Greek, German, French) to test encoding and special character handling.
*   **Size Variations:**
    *   Small files (a few paragraphs).
    *   Medium files (several pages/sections).
    *   Large files (equivalent to a full book chapter or more) to test performance and memory handling.
    *   Empty files (0 bytes or containing only whitespace).
*   **Metadata:**
    *   Files with complete and accurate embedded metadata.
    *   Files with partial or missing metadata.
    *   Files with deliberately incorrect or conflicting metadata.
    *   Files with no embedded metadata.
*   **Structure:**
    *   Well-structured documents adhering to format specifications.
    *   Poorly structured documents with common errors (e.g., unclosed tags in HTML-based formats).
    *   Documents with minimal structure (e.g., plain text with no explicit headers).

## 3. Specific Requirements by File Type

### 3.1. EPUB Files

#### 3.1.1. Table of Contents (ToC)
*   **NCX ToC (`toc.ncx`):**
    *   Simple, flat NCX: `<navMap><navPoint id="np1" playOrder="1"><navLabel><text>Chapter 1</text></navLabel><content src="ch1.xhtml"/></navPoint></navMap>`
    *   Deeply nested NCX (3+ levels): (e.g., Kant, Taylor) `<navPoint id="p1"><navLabel><text>Part 1</text></navLabel><content src="p1.xhtml"/><navPoint id="p1c1"><navLabel><text>Chapter 1</text></navLabel><content src="p1c1.xhtml"/><navPoint id="p1c1s1"><navLabel><text>Section 1</text></navLabel><content src="p1c1s1.xhtml#anchor"/></navPoint></navPoint></navPoint>`
    *   NCX with links to anchors: `<content src="text/part0009_split_001.html#head1"/>` (Kant).
    *   NCX with links to separate content files.
    *   NCX with problematic entries: `<navLabel><text>A very long excerpt from the book instead of a title...</text></navLabel>` (Adorno).
    *   NCX with `pageList`: `<pageList><pageTarget type="normal" value="1" playOrder="1"><navLabel><text>1</text></navLabel><content src="ch1.xhtml#page_1"/></pageTarget></pageList>` (Zizek, Rorty, Heidegger - Basic Questions).
    *   Missing NCX (rely on HTML ToC or NavDoc).
    *   NCX with `dtb:depth` inconsistent with actual nesting (Marcuse - Reason and Revolution).
    *   NCX listing individual footnote files (Derrida - Of Grammatology).
*   **HTML ToC (as separate file):**
    *   Structured with `<p>` and classes: `<p class="toc">Part 1</p><p class="tocb">Chapter 1</p>` (Kant).
    *   Structured with `<ul>/<ol>` and `<li>`.
    *   Non-hyperlinked HTML ToC (Baudrillard, Deleuze).
    *   HTML ToC entries linking back to chapter content (e.g., chapter headings linking to ToC anchors in Derrida - Specters).
*   **EPUB 3 Navigation Document (`nav.xhtml`):**
    *   With `epub:type="toc"`: `<nav epub:type="toc" id="toc"><ol><li><a href="ch1.xhtml">Chapter 1</a></li></ol></nav>`
    *   With `epub:type="landmarks"`: `<nav epub:type="landmarks" hidden=""><ol><li><a epub:type="cover" href="cover.xhtml">Cover</a></li></ol></nav>`
    *   With `epub:type="page-list"`: `<nav epub:type="page-list" hidden=""><ol><li><a href="ch1.xhtml#page_1">1</a></li></ol></nav>`
    *   Minimal NavDoc.

#### 3.1.2. Headers and Titles
*   **Standard HTML Headers:**
    *   `<h1>` - `<h6>` (e.g., Pippin: `<h1 class="cn">Chapter Number</h1>`, `<h1 class="ct">Chapter Title</h1>`; Heidegger - Metaphysics: `<h1><span class="chapterNumber">Number</span><span class="chapterTitle">Title</span></h1>`, `<h2 class="h2a">Section Title</h2>`).
    *   Mixed content within headers: `<h2>Title <small>Subtitle</small></h2>` (Kant).
    *   Example: `<h1 class="chapter" id="c1">Chapter Title <span class="cn"><span class="bor">N</span></span></h1>` (Rosenzweig - Hegel and the State).
    *   Example: `<h3>ONE</h3>` (Chapter Number) and `<h2>Secrets of European Responsibility</h2>` (Chapter Title) (Derrida - Gift of Death).
*   **Styled `<p>` or `<div>` Tags as Headers:**
    *   `<p class="c9" id="..."><strong class="calibre3">TITLE</strong></p>` (Byung-Chul Han).
    *   `<p class="chapter-number_1"><a href="..."><b>1</b></a></p>` and `<p class="chapter-title_2"><a href="..."><b>TITLE</b></a></p>` (Derrida - Specters).
    *   `<div class="chapter-number">ONE</div>` and `<div class="chapter-title">TITLE</div>` (Kaplan).
    *   `<p class="ChapTitle"><a href="...">Title</a></p>`, `<p class="AHead"><strong>Title</strong></p>`, `<p class="BHead"><strong><em>Title</em></strong></p>` (Descartes Dictionary).
    *   `<p class="calibre_1"><span class="calibre3"><span class="bold">TITLE</span></span></p>` (Adorno).
    *   `<div><a id="anchor"></a>TITLE<br />...</div>` (Baudrillard - minimal).
    *   `<p class="chno">CHAPTER N</p>` and `<p class="chtitle">TITLE</p>` (Rorty).
    *   `<p class="cta">TITLE</p>` and `<p class="ctc">TITLE<br/>or<br/>SUBTITLE</p>` (Rosenzweig - Star).
    *   `<p class="fmt">TITLE</p>` (Gadamer - Intro).
*   **Headers with Embedded Edition Markers:**
    *   `[A 19/B 33]` directly in header text (Kant).
*   **Headers with Page/Section Markers:**
    *   `<span class="calibre40">21.27</span>` within header (Hegel - Science of Logic).
*   **Combined Chapter Number/Title Elements:**
    *   `<h3>` with class `h1` and nested `<span>` for number, separate `<h3>` with class `h3a` for title (Taylor - Hegel).
    *   `<h1>` with class `chapter` for number, separate `<h1>` with class `chapter_title` for title (Jameson).
    *   `<h1><a id="p23"/>1<br/>________________<br/>THE UNITIES OF DISCOURSE</h1>` (Foucault - Archaeology).

#### 3.1.3. Footnotes and Endnotes

*   **A. Reference Markup in Main Text (Specific Examples):**
    *   **Kant (Critique):**
        *   Same-file: `<sup class="calibre18"><em class="calibre1"><a id="Fpart1fn1" href="part0023.html#Fpart1fr1" class="calibre9">1</a></em></sup>`
        *   Different-file: `<sup class="calibre18"><a id="ghi1" href="part0060.html#ihg1" class="calibre9">1</a></sup>`
    *   **Taylor (Hegel):** `<sup class="calibre20"><a id="pX-fnY" href="partZZZZ.html#pXfnY">Y</a></sup>`
    *   **Hegel (Science of Logic):** `<span><a id="fileposXXXXX">...</a><a href="#fileposYYYYY"><sup class="calibre30">N</sup></a></span>` (first `<a>` often empty `<span>` with underline class: `<span class="underline1"></span>`)
    *   **Hegel (Philosophy of Right - Dual System):**
        *   Endnotes (Editor/Translator): `<sup class="calibre11"><a id="ipreenX" href="part0029.html#preenX"><em class="calibre3">N</em></a></sup>`
        *   Footnotes (Author): `<sup class="calibre11"><a id="ifnX" href="part0011.html#fnX"><em class="calibre3">†</em></a></sup>`
    *   **Pippin (Realm of Shadows - EPUB 3):** `<a class="fnref" href="target_notes_file.xhtml#fnX" id="fnXr">N</a>`
    *   **Heidegger (German Existentialism):** `<sup><a href="e9780806536255_ftn01.html#ftn_fnX" id="ref_ftn_fnX"><span><span class="footnote_number">N</span></span></a></sup>`
    *   **Heidegger (Metaphysics - EPUB 3):** `<sup><a aria-describedby="fnX" epub:type="noteref" href="#fnX" id="ftX">N</a></sup>`
    *   **Marx & Engels Reader:** `<a id="footnote-refXX" href="part0057.html#footnoteXX" class="calibre8"><span><sup class="calibre9">N</sup></span></a>`
    *   **Marcuse (Marxism, Revolution, Utopia - Dual Style):**
        *   Asterisk: `<a href="#fn-fnref1_1" id="fn1_1">*</a>`
        *   Numbered: `<a href="#fn-fnref1_5" id="fn1_5"><sup>1</sup></a>`
    *   **Adorno (Negative Dialectics - Unlinked):** `<sup class="calibre5"><small class="calibre6"><span class="calibre7">N</span></small></sup>`
    *   **Derrida (Of Grammatology - Dual System):**
        *   Symbol-marked (to separate small files): `<a class="nounder" href="../Text/chXX_fnYY.html#footZZZ">*</a>`
        *   Numbered (to consolidated file): `<sup><a class="nounder" href="../Text/ch08_notes.html#chXXenYYa">N</a></sup>`
    *   **Zizek et al. (Reading Hegel):** `<a href="partXXXX.xhtml#anchorY" class="class_s1gu">N</a>`
    *   **Marcuse (Reason and Revolution):** `<sup><a href="#foot_X" id="foot-X">N</a></sup>`
    *   **Rosenzweig (Hegel and the State - Biblioref):** `<a epub:type="biblioref" href="A_006_foreword1.xhtml#r0_X" id="r0_Xb" role="doc-biblioref">Author Year</a>`
    *   **Byung-Chul Han (Burnout Society):** `<sup class="calibre7"><a class="calibre4" href="part0011.html#id_146" id="id_145">1</a></sup>`
    *   **Allison (Kant's TI):** `<sup><a id="ftn_refnum_chapter_X_N" href="#ftn_chapter_X_N">[N]</a></sup>`
    *   **Baudrillard (Simulacra - Unlinked):** Plain text `*1`, `*2` (not wrapped in `<sup>` or `<a>`).
    *   **Buber (On Judaism):** `<a class="hlink" id="c01-nts1a" href="Bube_9780307834089_epub_nts_r1.htm#c01-nts1"><sup class="frac">N</sup></a>`
    *   **Heidegger (Ponderings - Segment Endnotes):** `<a id="rpg1fn1"/><sup><a href="chapter1b.xhtml#pg1fn1">1</a></sup>` (empty anchor followed by linked sup)
    *   **Kaplan (Beyond Post-Zionism):** `<sup class="item2"><a id="ch01fn_1" href="14_notes.xhtml#ch01fn1">N</a></sup>`
    *   **Levinas (Totality and Infinity - Dual, Split Files):**
        *   To other split: `<span><a href="part0009_split_005.html#ftn1" class="calibre12">*</a></span>`
        *   Same-page (Preface): `<span><a href="part0007.html#ftn2" class="calibre12">*</a></span>` or `<sup class="calibre15"><span><a href="part0007.html#ftn3" class="calibre12">1</a></span></sup>`
    *   **Rorty (Mirror of Nature):** `<sup><a href="#rfnX_Y" id="fnX_Y">N</a></sup>`
    *   **Rosenzweig (Star of Redemption - Unlinked):** `<sup>1</sup>` (plain superscript, no link)
    *   **Sartre (Being and Nothingness - EPUB 3):** `<sup class="sup"><a href="footnotes.xhtml#fn_id" id="fn_ref_id">N</a></sup>`
    *   **Sennet (Craftsman):** `<a id="ch001fn1a"></a><a href="part0018.html#ch001fn1" class="hlink"><sup class="small3">1</sup></a>` (empty anchor followed by linked sup)
    *   **Gadamer (Truth and Method):** `<a href="ch1a.html#fn1-ref" id="fn1"><sup>1</sup></a>`

*   **B. Note Text Location & Structure (Specific Examples):**
    *   **Same-page footnotes:**
        *   Kant: `<p class="footnotes" id="Fpart1fr1">Note text...</p>`
        *   Taylor: `<p class="footnote"> <sup class="calibre22"><a id="pXfnY" href="...">Y</a></sup> Note text...</p>`
        *   Hegel (Science of Logic): `<div class="calibre32" id="fileposYYYYY"><div class="calibre33"><blockquote class="calibre14"><span><a href="#fileposXXXXX"><sup class="calibre30">N</sup></a></span> ...note text... </blockquote></div></div>`
        *   Heidegger (Metaphysics - EPUB 3): `<section class="notesSet" role="doc-endnotes"><ol class="notesList"><li class="noteEntry" role="doc-endnote" id="fnX"><p>Note text... <a epub:type="backlink" href="#ftX" role="doc-backlink">↩</a></p></li></ol></section>`
        *   Marcuse (Marxism, Revolution, Utopia - Dual Style):
            *   Asterisk: `<p class="fn1"><a id="fn-fnref1_1" href="...">*</a> Note text...</p>`
            *   Numbered: `<p class="fn"><span class="label"><a id="fn1_5_ref" href="...">N</a></span> Note text...</p>`
        *   Allison (Kant's TI): After `<hr class="sigil_split_marker"/>`, `<p class="calibre1">Notes</p>`, then `<p class="calibre1"><sup><a id="ftn_chapter_1_1" href="...">[1]</a></sup>&nbsp;Note text...&nbsp;<a href="#ftn_refnum_chapter_1_1">Go back</a></p>`
        *   Foucault (Archaeology): `<p class="fn"><span class="spanlabel"><a href="#ch1-fn1" id="ch1-fnref1">1</a></span><span class="spanbody">...note text...</span></p>`
        *   Jameson (Hegel Variations - EPUB 3): After ornamental image, `<div class="footnote"><p class="footnote" id="c01-ftn1"><a class="hlink" href="...#c01-ftn1a"><sup class="frac">1</sup></a> Note text...</p></div>`
        *   Levinas (Preface): `<div class="footnotesection">...<div class="footnote" id="ftn2"><span class="footnotenumber">*</span><div class="calibre3"><div class="para2">Note text...</div></div></div>...</div>`
        *   Rorty: `<p class="foott"><sup><a href="#fn1_1" id="rfn1_1">1</a></sup> Note text...</p>` or `<p class="foot">...</p>`
        *   Rosenzweig (Star - Unlinked): `<p class="ntnlf"><sup>1</sup> Note text...</p>` or `<p class="ntnl">...</p>`
        *   Husserl Dictionary (Intro): `<p class="note"> <a id="int1_1" href="...">1</a> Note text...</p>` or `<p class="note1">...</p>`
    *   **Endnotes (collected in a separate file, e.g., `notes.xhtml`):**
        *   Structure within `notes.xhtml` varies:
            *   Simple list of `<p id="note_anchor">N. Note text</p>`.
            *   More complex structures with back-links.
            *   Example (Derrida - Specters): `<div class="endnote-item"><a id="pg-246-148" href="12_chapter-title-1.html#pg-24-117">1.</a> <p class="endnote-text">Note text...</p></div>`
    *   **Chapter-end notes (collected at end of chapter's HTML file):**
        *   Zizek et al.: Within a `<div class="class_s5w">`, each note in `<div id="anchorY" class="class_s5b">N. Note text...</div>`.
    *   **Segment-end notes (collected at end of a multi-file logical section):**
        *   Heidegger (Ponderings): Notes for `chapter1.xhtml` in `chapter1b.xhtml` (or later segment), structure similar to other endnote files.
        *   Levinas (Totality and Infinity - Main Content): Notes for `part0009_split_001.html` in `part0009_split_005.html` (structure not detailed).
        *   Gadamer (Truth and Method): Notes for `ch1.html` in `ch1a.html` (structure not detailed).
    *   **Granular Footnote Files (one note per file, or few):**
        *   Derrida (Of Grammatology - Symbol-marked): e.g., `ch01_fn01.html` containing `<p class="footnote" id="foot001">* Note text</p>`.
*   **C. General Note Characteristics:**
    *   **Dual Systems:** Mix of footnote/endnote styles (e.g., Hegel - Phil. of Right; Derrida - Grammatology; Marcuse - Marxism, Rev, Utopia; Levinas - Totality).
    *   **Unlinked References:** Plain superscript or text markers with no `<a>` tag (Adorno, Baudrillard, Hardt & Negri, Derrida - Gift of Death, Rosenzweig - Star).
    *   Notes containing citations (e.g., Kant: `(EX, p. 15; 23:21)` within footnote text; Taylor: `<em class="calibre8">Book Title</em>` within footnote).
    *   Translator's notes explicitly marked: e.g., `{TN: ...}` (Heidegger - Metaphysics), or "Translator’s addition." (Rosenzweig - Star).

#### 3.1.4. Citations and Bibliographies
*   **In-text citations (within main body or note text):**
    *   Parenthetical: `(EX, p. 15; 23:21)` (Kant).
    *   Plain text with italics for titles: `See Kant’s <em class="calibre8">Critique of Pure Reason</em>, A70/B95.` (Taylor).
    *   Bibliographic references linking to a bibliography section in the same file: `<a epub:type="biblioref" href="A_006_foreword1.xhtml#r0_X" id="r0_Xb" role="doc-biblioref">Author Year</a>` (Rosenzweig - Hegel and the State).
    *   Cross-references to other dictionary entries: `<strong class="calibre2"><em>Distinction</em></strong>` (Descartes Dictionary), `<strong class="calibre2">consciousness</strong>` (Husserl Dictionary).
*   **Bibliography Section:**
    *   Dedicated HTML file (e.g., Taylor: `text/part0035.html`; Hegel - Phil. of Right: `text/part0032.html`; Pippin: `chi-pippin-hegels-0018.xhtml`; Marcuse - Reason & Rev: `xhtml/23_biblio.xhtml`; Descartes Dictionary: `html/9781472514691_Bib.html#bib1`; Sartre: `bibliography.xhtml`; Allison: `OEBPS/Text/biblio.xhtml`).
    *   Section within a content file (e.g., Rosenzweig - Hegel and the State: `<section epub:type="bibliography" role="doc-bibliography">` in `A_006_foreword1.xhtml`).
    *   Formatted using lists (`<ul>`, `<ol>`) or paragraphs.
    *   Entries with `<cite>` tags: (Rosenzweig - Hegel and the State).
    *   Entries with `epub:type="biblioentry"` and `epub:type="backlink"`: (Rosenzweig - Hegel and the State: `<li epub:type="biblioentry" id="r0_X">...<a epub:type="backlink" href="#r0_Xb" role="doc-backlink">↩</a></li>`).
    *   Bibliography with navigable sub-sections in NCX (Husserl Dictionary).
    *   "Bibliographic Note" linked in NCX (Marx & Engels Reader).

#### 3.1.5. Page Numbers and Edition Markers
*   **EPUB 3 Semantic Pagebreaks:**
    *   `<span aria-label="X" epub:type="pagebreak" id="Page_X" role="doc-pagebreak"/>` (Heidegger - Metaphysics, Sartre).
    *   `<span epub:type="pagebreak" id="pgX" title="X"/>` within an `<a>` tag: `<a id="page1"><span epub:type="pagebreak" id="pg1" title="1"/></a>` (Jameson).
*   **Anchor-based Page Markers (EPUB 2 / Calibre / Other):**
    *   `<a id="page_XXX" class="calibre10"></a>` (Kant).
    *   `<a id="page_X" class="calibre3"></a>` (Taylor).
    *   `<a id="page_X"/>` (Marcuse - Reason & Rev, Rosenzweig - Star, Rorty, Heidegger - Basic Questions, Heidegger - Ponderings, Kaplan, Baudrillard, Buber, Husserl Dictionary, Gadamer).
    *   `<a id="page_X" class="calibreX"></a>` (Byung-Chul Han, Heidegger - Intro to Metaphysics).
    *   `<a class="page" id="pX"/>` or `<a class="page" data-locator="pX"/>` (Pippin).
    *   `<a id="pl-XX-Y"/>` (Derrida - Specters - internal layout markers).
*   **Plain text page numbers embedded in content:**
    *   From PDF conversions, often interrupting text flow (Deleuze - Anti-Oedipus: `"xl"`, `"xli"`).
*   **Edition Markers:**
    *   `[A 19/B 33]` as plain text near/in headers (Kant).
*   **Page/Section Markers in Text/Headers:**
    *   `<span class="calibre40">21.27</span>` in header (Hegel - Science of Logic).
    *   `<span class="calibre37">21.28</span>` in text (Hegel - Science of Logic).
    *   Print page ranges in sub-topic headers: `"On the Possibility of Philosophy 15-16"` (Adorno).
*   **NCX `pageList`:**
    *   Present and mapping to anchors (Zizek, Rorty, Heidegger - Basic Questions, Heidegger - Ponderings, Marcuse - Reason & Rev, Rosenzweig - Star, Jameson).

#### 3.1.6. Images and Fonts
*   **Images:**
    *   Standard formats: `.jpeg`, `.png`, `.gif`.
    *   Used for special text/symbols: `<img alt="" src="images/00003.jpg" class="calibre18"/>` (Hegel - Science of Logic).
    *   `.unknown` extension, `application/octet-stream` media type (Kant).
    *   Chapter decorations, figures, tables (Marcuse - Reason & Rev: `chapimage.jpg`, `figX-XX.jpg`).
    *   Full-page images (`pgX.jpg`) (Rosenzweig - Star).
    *   Ornamental images as separators (Jameson).
*   **Fonts:**
    *   Embedded `.ttf` / `.otf` fonts (Hegel - Phil. of Right, Marcuse - Marxism Rev Utopia, Derrida - Specters, Derrida - Grammatology, Buber, Sartre, Jameson, Rosenzweig - Star, Foucault - Archaeology).
        *   Media types: `application/x-font-truetype`, `application/vnd.ms-opentype`, `application/octet-stream` (Marcuse - Reason & Rev).
    *   Obfuscated/encrypted fonts (presence of `META-INF/encryption.xml`) (Hegel - Phil. of Right, Sennet).
    *   No embedded fonts (Pippin, Heidegger - German Existentialism, Heidegger - Metaphysics, Adorno, Heidegger - Basic Questions, Heidegger - Ponderings, Kaplan, Heidegger - Intro to Metaphysics, Gadamer, Deleuze, Hardt & Negri, Baudrillard, Allison).

#### 3.1.7. Structure and Metadata
*   **EPUB Version:** EPUB 2 vs. EPUB 3.
*   **Manifest (`content.opf`):**
    *   Standard item declarations: `<item id="..." href="..." media-type="..."/>`.
    *   Metadata: `<dc:title>`, `<dc:creator>`, `<dc:language>`, `<dc:identifier id="pub-id" opf:scheme="ISBN">...</dc:identifier>`, `<dc:publisher>`, `<dc:date opf:event="publication">YYYY-MM-DD</dc:date>`.
    *   `<meta property="title-type">main</meta>`, `<meta property="title-type">subtitle</meta>` (Pippin).
    *   `<meta name="calibre:series" ...>`, `<meta name="calibre:timestamp" ...>`.
    *   `<meta name="Sigil version" ...>`.
    *   `<meta name="cover" content="cover-image-item-id" />`.
*   **Spine:**
    *   Order of content files: `<itemref idref="item_id_cover" linear="no"/> <itemref idref="item_id_ch1"/>`.
    *   `page-map.xml` reference: `<itemref idref="page-map" linear="no"/>` (Zizek, Marcuse - Reason & Rev).
*   **Guide (OPF - EPUB 2):**
    *   `<reference type="toc" title="Table of Contents" href="toc.xhtml"/>`
    *   `<reference type="cover" title="Cover" href="cover.xhtml"/>`
    *   `<reference type="text" title="Start Reading" href="chapter1.xhtml"/>`
    *   References to notes, bibliography, index files.
    *   Empty guide section (Deleuze).
*   **File/Directory Structure:**
    *   Content in root vs. `OEBPS/`, `OPS/`, `text/` subdirectories.
    *   Split files: `_split_YYY.html` (Kant, Hegel - Science of Logic, Marx & Engels, Adorno, Deleuze, Levinas, Sennet, Husserl Dictionary).
    *   Segmented chapter files: `chapter1.xhtml`, `chapter1a.xhtml` (notes), `chapter1b.xhtml` (Heidegger - Ponderings, Gadamer).
*   **Publisher/Converter Artifacts:**
    *   Calibre metadata/structure (`calibre_bookmarks.txt`, `metadata.opf` separate from `content.opf`).
    *   Sigil metadata.
    *   Adobe page templates (`.xpgt`, `Adept.expected.resource` / `Adept.resource` meta tags) (Derrida - Specters, Heidegger - German Existentialism, Heidegger - Basic Questions, Heidegger - Ponderings, Buber, Foucault - Archaeology, Derrida - Gift of Death, Byung-Chul Han).
    *   "ScribdMpubToEpubConverter" metadata (Derrida - Gift of Death).
    *   "ePub Bud" publisher (Baudrillard).
    *   "pdftohtml 0.36" generator (Deleuze).
*   **Accessibility Metadata:**
    *   Detailed in OPF (Heidegger - Metaphysics, Sartre).
    *   `epub:type` attributes for semantic roles (`doc-introduction`, `doc-chapter`, `doc-footnote`, `doc-endnote`, `doc-pagebreak`, `noteref`, `biblioref`, `biblioentry`, `backlink`, `credit`, `toc`, `landmarks`, `page-list`).

#### 3.1.8. Content Types & Misc.
*   **Standard Prose Paragraphs:**
    *   `<p>Text</p>`
    *   `<p class="indent">Text</p>`, `<p class="noindent">Text</p>`
    *   `<div class="p-indent"><span>Text</span></div>` (Heidegger - German Existentialism).
*   **Poetry Formatting:**
    *   `<div class="poem"><p class="poemline">Line 1</p><p class="poemline">Line 2</p></div>` (Hegel - Phil. of Right).
    *   Multiple `<p class="tocc">` with nested `<span>` (Taylor - Hegel).
    *   `<p class="s20">`, `<p class="s25">` (Marx & Engels).
*   **Dialogue.**
*   **Epigraphs:**
    *   `<div class="epigraph"><p class="epf">Epigraph text.</p></div>` (Pippin).
    *   Simple `<p class="calibre1">` (Hardt & Negri).
*   **Blockquotes:** Standard `<blockquote>` or styled divs/paragraphs (e.g. Hegel - Science of Logic: `<blockquote class="calibre14">`).
*   **Index Term Markers:** `<span id="indx-termXXXX"/>` (Rosenzweig - Hegel and the State).
*   **Internal Cross-References:** `<a class="xref" href="...">Cross-ref text</a>` (Pippin).
*   **Forced Page Breaks:** `<div style="page-break-before: always;" />` (Derrida - Gift of Death).
*   **Ornamental Images/Lines:** Used as separators or decorations (e.g., between chapter number and title in Derrida - Specters; separating main text from footnotes in Jameson).
*   **Unusual CSS Class Usage:** `<span class="underline">` for italics (Adorno).
*   **Bracketed numbers as centered paragraphs:** `{1}` in `<p class="c14">` (Heidegger - Intro to Metaphysics).
*   **DOI Link:** `<p class="doi">DOI: <a ...>...</a></p>` (Rosenzweig - Hegel and the State).
*   **Credit Span:** `<span epub:type="credit" role="doc-credit">` (Rosenzweig - Hegel and the State).

### 3.2. PDF Files

*   **Text Extraction Challenges:**
    *   **Selectable Text:**
        *   Single column, clean layout.
        *   Multi-column layout (e.g., academic papers).
        *   Text flow around images or figures.
        *   Text with unusual spacing or character kerning.
        *   Text with embedded (non-standard) fonts that might hinder copy-pasting.
    *   **OCRed Text (from image-based PDFs):**
        *   High-quality OCR (minimal errors).
        *   Medium-quality OCR (some errors, noise).
        *   Low-quality OCR (significant errors, skewed text, background noise).
        *   Scanned documents with handwritten annotations mixed with typed text.
    *   **Ligatures:** Common ligatures (fi, fl, etc.) and less common ones.
    *   **Mathematical Formulas & Special Symbols:** As selectable text vs. embedded images.
*   **Structural Element Variations:**
    *   **Table of Contents:**
        *   PDFs with bookmark-based ToC (programmatically accessible).
        *   PDFs with a visual ToC page (hyperlinked text).
        *   PDFs with a visual ToC page (non-hyperlinked text).
        *   ToC entries spanning multiple lines.
    *   **Headers/Footers:**
        *   Running headers/footers containing page numbers, chapter titles, author names. Test correct exclusion from main content.
        *   Headers/footers with inconsistent formatting.
    *   **Headings:**
        *   Visually distinct headings (font size, weight) but no explicit PDF tags.
        *   PDFs with tagged headings (H1, H2, etc.).
    *   **Paragraphs & Line Breaks:**
        *   Standard paragraph breaks.
        *   Hard line breaks within paragraphs.
        *   Justified text leading to large inter-word spaces.
*   **Footnotes/Endnotes:**
    *   Footnotes at the bottom of the page, clearly separated.
    *   Footnotes in a two-column layout at the bottom.
    *   Footnotes that span across pages.
    *   Endnotes at the end of chapters or the entire document.
    *   Superscript numbers for references (linked or unlinked if PDF supports it).
    *   Symbol-based references (*, †, etc.).
*   **Tables and Figures:**
    *   Simple tables with clear borders.
    *   Complex tables (merged cells, multi-line cells, no clear borders).
    *   Tables spanning multiple pages.
    *   Embedded images/diagrams with captions above, below, or side-by-side.
    *   Figures that are full-page scans.
*   **Metadata (Document Properties):**
    *   Complete and accurate: Title, Author, Subject, Keywords, Creator, Producer, CreationDate, ModDate.
    *   Partial or missing properties.
    *   Incorrectly encoded metadata (e.g., non-UTF-8 characters).
*   **Special Cases & Edge Cases:**
    *   Rotated pages.
    *   Mixed page sizes/orientations within a single PDF.
    *   Password-protected PDFs (for reading, not editing - test graceful failure if access denied).
    *   Corrupted or partially downloaded PDFs (test graceful failure).
    *   PDFs with layers (test extraction of visible layers).
    *   PDFs with form fields (test extraction of field content vs. static text).
    *   Very large PDFs (hundreds of pages) to test performance.

### 3.3. Markdown Files

*   **Basic Formatting:**
    *   Headers: All levels (`# H1` to `###### H6`).
    *   Emphasis: `*italic*`, `_italic_`, `**bold**`, `__bold__`, `***bold-italic***`, `~~strikethrough~~`.
    *   Lists:
        *   Unordered: `*`, `-`, `+` markers.
        *   Ordered: `1.`, `2.`, etc.
        *   Nested lists (mixed ordered/unordered, multiple levels).
    *   Links: `[text](url)`, `[text](url "title")`, reference-style links `[text][id]` and `[id]: url`.
    *   Images: `![alt text](image_url)`, `![alt text](image_url "title")`.
    *   Blockquotes: `>`, `>>` nested.
    *   Horizontal Rules: `---`, `***`, `___`.
*   **Advanced/Extended Markdown (GFM - GitHub Flavored Markdown & others):**
    *   **Tables:**
        *   Simple: `| H1 | H2 |\n|---|---|\n| C1 | C2 |`
        *   With alignment: `|:---|:---:|---:|`
        *   Tables with inline markdown (bold, italics, links in cells).
    *   **Footnotes:**
        *   Standard: `Here is a footnote reference,[^1] and another.[^longnote]`
          `[^1]: Here is the footnote.`
          `[^longnote]: Here's one with multiple blocks.`
            `Subsequent paragraphs are indented to show that they`
            `belong to the previous footnote.`
    *   **Task lists:** `- [x] Completed task`, `- [ ] Incomplete task`.
    *   **Code Blocks:**
        *   Indented: `    code`
        *   Fenced: ````python\nprint("hello")\n```` (with and without language specifier).
*   **Front Matter:**
    *   YAML: `--- \ntitle: Test\nauthor: AI\n---`
    *   TOML: `+++ \ntitle = "Test"\nauthor = "AI"\n+++`
    *   JSON: `{ "title": "Test", "author": "AI" }` (less common, but for completeness).
    *   Front matter with various data types: strings, numbers, booleans, lists, nested objects.
    *   Front matter with syntax errors.
    *   No front matter.
*   **Structure & Edge Cases:**
    *   Single long Markdown file with many sections.
    *   Multiple linked Markdown files (conceptual links, e.g., `[link to other doc](./other.md)`).
    *   Markdown with embedded HTML:
        *   Simple HTML tags: `<b>bold</b>`, `<div>...</div>`.
        *   Complex or malformed embedded HTML.
    *   Markdown with LaTeX expressions: `$inline math$`, `$$display math$$`.
    *   Files with mixed line endings (CRLF, LF).
    *   Files with unusual characters or encoding issues (if not UTF-8).
    *   Very deeply nested structures (e.g., lists within blockquotes within lists).

## 4. Desired Output/Structure for Synthetic Files

Each synthetic file should be designed to test specific parsing and extraction capabilities. The content should allow for:

*   **Metadata Extraction:** Clear author, title, publication date (if applicable), and other relevant metadata should be extractable, either from embedded metadata or inferred from content.
*   **Structural Element Identification:**
    *   Correct identification of book titles, chapter titles, section headings (and their hierarchy).
    *   Accurate parsing of ToC entries and their corresponding targets.
*   **Note Extraction:**
    *   Correct identification of footnote/endnote references in the main text.
    *   Correct extraction of note content.
    *   Accurate association of references to their note text, regardless of location (same-page, end-of-chapter, end-of-book, separate files).
*   **Citation/Bibliography Extraction:**
    *   Identification of in-text citations.
    *   Extraction of full bibliographic entries from a bibliography section.
*   **Content Chunking:**
    *   Text should be structured to test various chunking strategies (e.g., by paragraph, by section, by semantic meaning).
    *   Files should include elements that might challenge chunking (e.g., short paragraphs, long paragraphs, lists, tables, poetry).
*   **Relationship Extraction (Conceptual):**
    *   Content should ideally contain text from which simple relationships can be inferred (e.g., "Author X discusses Concept Y in Book Z," "Philosopher A influenced Philosopher B"). This is more about the *content* than the *formatting*, but the formatting should not hinder this.
    *   Presence of clear definitions or discussions of philosophical terms.

## 5. Proposed Directory Structure for Synthetic Test Data

A clear, hierarchical directory structure is proposed to organize the synthetic test files:

```
./synthetic_test_data/
├── epub/
│   ├── toc/
│   │   ├── ncx_simple.epub
│   │   ├── ncx_nested.epub
│   │   ├── ncx_page_list.epub
│   │   ├── html_toc_linked.epub
│   │   ├── navdoc_full.epub
│   │   └── ... (other ToC variations)
│   ├── headers/
│   │   ├── standard_headings.epub
│   │   ├── p_tag_headings.epub
│   │   └── ... (other header variations)
│   ├── notes/
│   │   ├── same_page_footnotes_linked.epub
│   │   ├── endnotes_separate_file_linked.epub
│   │   ├── endnotes_unlinked_references.epub
│   │   ├── dual_note_system.epub
│   │   ├── granular_footnote_files.epub
│   │   └── ... (other note variations)
│   ├── citations_bibliography/
│   │   ├── intext_citations_biblio_section.epub
│   │   └── ...
│   ├── images_fonts/
│   │   ├── embedded_fonts_obfuscated.epub
│   │   ├── images_as_text.epub
│   │   └── ...
│   ├── structure_metadata/
│   │   ├── epub2_calibre_split.epub
│   │   ├── epub3_professional.epub
│   │   ├── minimal_metadata.epub
│   │   └── ...
│   ├── content_types/
│   │   ├── poetry_formatting.epub
│   │   └── ...
│   └── general_edge_cases/
│       ├── empty_file.epub
│       ├── very_large_file.epub
│       ├── file_with_only_images.epub
│       └── ...
├── pdf/
│   ├── text_based/
│   │   ├── single_column.pdf
│   │   ├── multi_column.pdf
│   │   └── ...
│   ├── image_based_ocr/
│   │   ├── high_quality_scan.pdf
│   │   ├── low_quality_scan.pdf
│   │   └── ...
│   ├── structure/
│   │   ├── embedded_toc_metadata.pdf
│   │   ├── visual_toc_only.pdf
│   │   └── ...
│   ├── notes/
│   │   ├── bottom_page_footnotes.pdf
│   │   └── ...
│   └── general_edge_cases/
│       ├── pdf_with_ligatures.pdf
│       ├── corrupted.pdf
│       └── ...
└── markdown/
    ├── basic/
    │   ├── all_basic_elements.md
    │   └── ...
    ├── extended/
    │   ├── tables_and_footnotes.md
    │   └── ...
    ├── frontmatter/
    │   ├── yaml_frontmatter.md
    │   ├── no_frontmatter.md
    │   └── ...
    └── general_edge_cases/
        ├── markdown_with_html.md
        ├── empty_markdown.md
        └── ...
```

This structure categorizes files by format and then by the primary feature or edge case they are designed to test.

## 6. Testing Focus

These synthetic files will help test:
*   **Parsing Robustness:** Handling various valid and slightly malformed structures.
*   **Preprocessing Logic:** Correctly identifying and isolating relevant content sections.
*   **Chunking Strategies:** Effectiveness of chunking across different content layouts and structures.
*   **Metadata Extraction Accuracy:** Pulling correct metadata from diverse sources (OPF, NCX, NavDoc, PDF properties, Markdown front matter).
*   **Relationship Extraction Foundation:** Ensuring that the textual content, once correctly parsed and chunked, is suitable for downstream relationship extraction models (though the synthetic data itself won't contain pre-defined relationships).

This suite aims to provide a solid foundation for ensuring the PhiloGraph ingestion pipeline is robust and reliable across a wide spectrum of input document formats and complexities.