import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, Table, TableStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from .common import PDF_DIR

def create_pdf_text_single_column(filename="single_column.pdf"):
    """
    Creates a simple text-based PDF with a single column layout.
    """
    filepath = os.path.join(PDF_DIR, "text_based", filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    
    # Set metadata
    c.setTitle("Single Column Text PDF")
    c.setAuthor("Synthetic Data Generator")
    c.setSubject("Testing PDF text extraction")
    c.setKeywords(["pdf", "test", "text", "single column"])

    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleH1 = styles['h1']
    styleH2 = styles['h2']

    story = []

    # Title
    p_title = Paragraph("The Philosophy of Synthetic Documents", styleH1)
    story.append(p_title)
    story.append(Spacer(1, 0.2*inch))

    # Chapter 1
    p_ch1_title = Paragraph("Chapter 1: The Nature of the Artificial", styleH2)
    story.append(p_ch1_title)
    story.append(Spacer(1, 0.1*inch))

    text_ch1 = """This document, itself an artifact of synthetic generation, explores the philosophical implications of artificiality. 
    When we create data that mimics reality, what does it tell us about the reality it seeks to emulate? 
    This PDF is structured in a single column, a common format for textual documents, designed to test basic text extraction and layout parsing. 
    The content herein is Lorem Ipsum with a philosophical bent, intended to provide sufficient textual matter for analysis without requiring deep semantic understanding for the purpose of format testing.
    We consider the works of Plato, who pondered the world of Forms, a realm of perfect archetypes that earthly objects merely imitate. 
    Is synthetic data, then, an imitation of an imitation, twice removed from truth? Or does its deliberate construction for a specific purpose – testing – grant it a unique, albeit functional, essence?
    Further, the process of generating such data involves algorithms and predefined rules. Does this deterministic origin strip the data of any potential for emergent meaning, or is meaning solely a construct of the interpreting agent, whether human or machine?
    These questions, while tangential to the immediate technical goal of testing a data pipeline, serve to imbue the synthetic with a semblance of the thematic content it might one day process.
    """
    p_ch1_content = Paragraph(text_ch1.replace("\n", "<br/>"), styleN)
    story.append(p_ch1_content)
    story.append(Spacer(1, 0.2*inch))

    # Chapter 2
    p_ch2_title = Paragraph("Chapter 2: Implications for Knowledge Systems", styleH2)
    story.append(p_ch2_title)
    story.append(Spacer(1, 0.1*inch))

    text_ch2 = """If a knowledge system is trained or tested on synthetic data, how does this affect its understanding of genuine information? 
    The verisimilitude of the synthetic becomes crucial. A poorly constructed synthetic dataset might lead to a skewed or brittle model. 
    Conversely, a meticulously crafted dataset, covering a wide array of edge cases and complexities, can significantly enhance robustness.
    This particular PDF aims for simplicity in layout but richness in textual content to allow for straightforward extraction. Future synthetic PDFs will explore more complex layouts, including multiple columns, embedded images, and varied font usage.
    The challenge lies in creating synthetic data that is "real enough" for its purpose. For PhiloGraph, this means data that reflects the structural and semantic nuances of philosophical texts, including citations, footnotes, and complex argumentation, even if the arguments themselves are fabricated for the test.
    """
    p_ch2_content = Paragraph(text_ch2.replace("\n", "<br/>"), styleN)
    story.append(p_ch2_content)

    # Build the story on the canvas
    frame_width = letter[0] - 2*inch # Page width - 2x margin
    frame_height = letter[1] - 2*inch # Page height - 2x margin
    
    current_y = letter[1] - inch # Start 1 inch from top
    
    for item in story:
        item_height = item.wrapOn(c, frame_width, frame_height)[1] # Get height
        if current_y - item_height < inch: # If not enough space, new page
            c.showPage()
            c.setTitle("Single Column Text PDF") # Metadata for new page
            c.setAuthor("Synthetic Data Generator")
            current_y = letter[1] - inch
        
        item.drawOn(c, inch, current_y - item_height)
        current_y -= (item_height + 0.1*inch) # Add a little space after paragraph

    try:
        c.save()
        print(f"Successfully created PDF: {filepath}")
    except Exception as e:
        print(f"Error creating PDF {filepath}: {e}")

def create_pdf_text_multi_column(filename="multi_column.pdf"):
    """
    Creates a text-based PDF with a two-column layout.
    """
    filepath = os.path.join(PDF_DIR, "text_based", filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    c.setTitle("Multi-Column Text PDF")
    c.setAuthor("Synthetic Data Generator")

    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleH1 = styles['h1']
    
    col_width = (letter[0] - 1.5*inch) / 2 # 0.5 inch gutter, 0.5 inch margins
    col_gutter = 0.5 * inch
    frame_height = letter[1] - 2*inch

    # Column 1
    story_col1 = []
    story_col1.append(Paragraph("The Dialectic of Columns: Part I", styleH1))
    story_col1.append(Spacer(1, 0.1*inch))
    text_col1 = """This is the first column of a two-column layout. Philosophical texts, especially in journal formats or older books, frequently utilize multi-column layouts. 
    Testing extraction from such layouts is crucial. The challenge lies in correctly associating text flows and maintaining reading order. 
    This column contains introductory remarks on the nature of spatial arrangement in textual presentation. How does the division of space affect the reception of ideas?
    Does a column constrain thought, or does it provide a focused channel for its articulation? These are meta-textual considerations."""
    story_col1.append(Paragraph(text_col1.replace("\n", " "), styleN))

    # Column 2
    story_col2 = []
    story_col2.append(Paragraph("The Dialectic of Columns: Part II", styleH1))
    story_col2.append(Spacer(1, 0.1*inch))
    text_col2 = """This second column continues the discourse. It might explore counterarguments or provide further examples. 
    The parser must distinguish this text as belonging to the second column and not as a continuation of the first column's bottom onto a new page's top.
    Consider the aesthetic impact: a multi-column layout can feel denser, more 'academic', or simply more efficient in terms of paper usage.
    The synthetic generation of such layouts helps ensure that downstream processing tools are robust to these common formatting variations found in scholarly articles and books."""
    story_col2.append(Paragraph(text_col2.replace("\n", " "), styleN))

    current_y = letter[1] - inch
    for item in story_col1:
        item_height = item.wrapOn(c, col_width, frame_height)[1]
        if current_y - item_height < inch: 
            break 
        item.drawOn(c, 0.5*inch, current_y - item_height)
        current_y -= (item_height + 0.05*inch)

    current_y = letter[1] - inch 
    for item in story_col2:
        item_height = item.wrapOn(c, col_width, frame_height)[1]
        if current_y - item_height < inch:
            break
        item.drawOn(c, 0.5*inch + col_width + col_gutter, current_y - item_height)
        current_y -= (item_height + 0.05*inch)
        
    try:
        c.save()
        print(f"Successfully created PDF: {filepath}")
    except Exception as e:
        print(f"Error creating PDF {filepath}: {e}")

def create_pdf_text_flow_around_image(filename="text_flow_around_image.pdf"):
    """
    Creates a PDF with text flowing around a simple image placeholder.
    Actual text flow is complex with reportlab; this is a simplified simulation.
    """
    filepath = os.path.join(PDF_DIR, "text_based", filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    c.setTitle("Text Flow Around Image PDF")
    c.setAuthor("Synthetic Data Generator")

    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleH1 = styles['h1']

    img_x, img_y, img_w, img_h = 2*inch, 5*inch, 1.5*inch, 2*inch
    c.rect(img_x, img_y, img_w, img_h, stroke=1, fill=0)
    c.drawString(img_x + 0.1*inch, img_y + img_h/2, "[Image Placeholder]")

    story = []
    story.append(Paragraph("The Interplay of Text and Image", styleH1))
    story.append(Spacer(1, 0.2*inch))

    text_content = """Philosophical discourse sometimes incorporates visual elements, though less frequently than other disciplines. 
    This paragraph begins before the image area. The challenge for text extraction is to correctly segment text that might be broken 
    by such an image. This text should appear to the left or above the image. We continue writing to demonstrate flow. 
    The ideal parser would recognize the image block and continue text extraction from the appropriate point after or beside the image.
    This particular sentence is intended to be long enough to potentially wrap around or be interrupted by the image placeholder drawn on the canvas.
    The subsequent text should appear after the image area. This tests the parser's ability to handle non-linear text blocks.
    ReportLab's basic drawing commands make true text reflow complex; this is a visual simulation. 
    A more sophisticated approach would use Platypus Frames or other advanced layout tools.
    This final part of the text should clearly be below the image area, demonstrating a jump in the reading order if the image were truly inline.
    """
    
    p_above = Paragraph(text_content.split("The subsequent text")[0], styleN)
    p_above.wrapOn(c, letter[0] - 2*inch, 3*inch) 
    p_above.drawOn(c, inch, letter[1] - inch - p_above.height)

    p_below_text = "The subsequent text" + text_content.split("The subsequent text")[1]
    p_below = Paragraph(p_below_text, styleN)
    p_below.wrapOn(c, letter[0] - 2*inch, img_y - inch - 0.2*inch) 
    p_below.drawOn(c, inch, inch ) 

    try:
        c.save()
        print(f"Successfully created PDF: {filepath}")
    except Exception as e:
        print(f"Error creating PDF {filepath}: {e}")

def create_pdf_simulated_ocr_high_quality(filename="simulated_ocr_hq.pdf"):
    """
    Creates a PDF with text that simulates high-quality OCR output (minimal common errors).
    """
    filepath = os.path.join(PDF_DIR, "image_based_ocr", filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    c.setTitle("Simulated High-Quality OCR PDF")
    c.setAuthor("Synthetic Data Generator")

    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontName = 'Courier' 
    styleN.leading = 14
    styleH1 = styles['h1']
    styleH1.fontName = 'Courier-Bold'

    story = []
    story.append(Paragraph("Fragment from a Scanned Text (High Quality OCR)", styleH1))
    story.append(Spacer(1, 0.2*inch))

    ocr_text = """The problern of universals has a long history in philosophy. 
    It concerns the question of whether properties that can be predicated of many individuals (e.g., "redness," "humanity") 
    exist in some way independently of those individuals. Plato's theory of Forms is a classic exampIe of realism regarding universals. 
    Nominalists, on the other hand, argue that only particulars exist, and universals are mere names or concepts.
    This text simulates a fairly clean OCR capture. There might be an occasional misrecognized character, like 'I' for 'l' or 'rn' for 'm', 
    but overall, the text is highly legible and structurally intact. For examp1e, the word 'example' might appear as 'exampIe'.
    Punctuation should be mostly correct . However , some spacing issues might occur.The goal is to test robustness to these minor imperfections.
    A good OCR engine would produce text of this quality from a clear, well-printed source document.
    """
    p_ocr_content = Paragraph(ocr_text.replace("\n", "<br/>"), styleN)
    story.append(p_ocr_content)

    frame_width = letter[0] - 2*inch
    frame_height = letter[1] - 2*inch
    current_y = letter[1] - inch
    
    for item in story:
        item_height = item.wrapOn(c, frame_width, frame_height)[1]
        if current_y - item_height < inch:
            c.showPage()
            c.setTitle("Simulated High-Quality OCR PDF")
            c.setAuthor("Synthetic Data Generator")
            current_y = letter[1] - inch
        item.drawOn(c, inch, current_y - item_height)
        current_y -= (item_height + 0.1*inch)
        
    try:
        c.save()
        print(f"Successfully created PDF: {filepath}")
    except Exception as e:
        print(f"Error creating PDF {filepath}: {e}")

def create_pdf_with_bookmarks(filename="with_bookmarks.pdf"):
    """
    Creates a PDF with a programmatically generated bookmark-based ToC.
    Simplified for debugging.
    """
    filepath = os.path.join(PDF_DIR, "structure", filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    c.setTitle("PDF with Bookmarks (ToC)")
    c.setAuthor("Synthetic Data Generator")

    # Page 1
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, letter[1] - inch, "Main Title: The Structure of Knowledge")
    c.bookmarkPage("main_title_key_debug") 
    c.addOutlineEntry("Main Title", "main_title_key_debug", level=0) 

    c.setFont("Helvetica-Bold", 14)
    c.drawString(inch, letter[1] - 1.5*inch, "Chapter 1: Foundational Concepts")
    c.bookmarkPage("chapter1_key_debug")
    c.addOutlineEntry("Chapter 1: Foundational Concepts", "chapter1_key_debug", level=1)
    
    c.setFont("Helvetica", 12)
    text_c1 = c.beginText(inch, letter[1] - 2*inch)
    text_c1.textLine("This is the content of the first chapter for debugging bookmarks.")
    c.drawText(text_c1)
    
    try:
        c.save()
        print(f"Successfully created PDF: {filepath}")
    except Exception as e:
        print(f"Error creating PDF {filepath}: {e}")

def create_pdf_visual_toc_hyperlinked(filename="visual_toc_hyperlinked.pdf"):
    """
    Creates a PDF with a visual, hyperlinked Table of Contents page.
    """
    filepath = os.path.join(PDF_DIR, "structure", filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    c.setTitle("PDF with Visual Hyperlinked ToC")
    c.setAuthor("Synthetic Data Generator")

    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleH1 = styles['h1']
    styleH2 = styles['h2']
    
    # ToC Page
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(letter[0]/2, letter[1] - inch, "Table of Contents")
    
    toc_items = [
        ("Chapter 1: The Beginning", "ch1_target"),
        ("Chapter 2: The Middle", "ch2_target"),
        ("  Section 2.1: A Detail", "sec21_target"),
        ("Chapter 3: The End", "ch3_target")
    ]
    
    y_pos = letter[1] - 1.5*inch
    for i, (text, target) in enumerate(toc_items):
        c.setFont("Helvetica", 12)
        c.drawString(inch, y_pos, text)
        c.linkURL(f"#{target}", (inch, y_pos - 0.1*inch, 4*inch, y_pos + 0.1*inch), relative=1)
        y_pos -= 0.3*inch
        if y_pos < inch: 
            c.showPage()
            c.setTitle("PDF with Visual Hyperlinked ToC")
            c.setAuthor("Synthetic Data Generator")
            y_pos = letter[1] - inch

    # Content Pages
    c.showPage()
    c.setTitle("PDF with Visual Hyperlinked ToC")
    c.setAuthor("Synthetic Data Generator")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, letter[1] - inch, "Chapter 1: The Beginning")
    c.bookmarkPage("ch1_target") 
    c.setFont("Helvetica", 12)
    c.drawString(inch, letter[1] - 1.5*inch, "Content for the first chapter.")

    c.showPage()
    c.setTitle("PDF with Visual Hyperlinked ToC")
    c.setAuthor("Synthetic Data Generator")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, letter[1] - inch, "Chapter 2: The Middle")
    c.bookmarkPage("ch2_target")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(inch, letter[1] - 1.5*inch, "Section 2.1: A Detail")
    c.bookmarkPage("sec21_target")
    c.setFont("Helvetica", 12)
    c.drawString(inch, letter[1] - 2.0*inch, "Content for section 2.1.")

    c.showPage()
    c.setTitle("PDF with Visual Hyperlinked ToC")
    c.setAuthor("Synthetic Data Generator")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, letter[1] - inch, "Chapter 3: The End")
    c.bookmarkPage("ch3_target")
    c.setFont("Helvetica", 12)
    c.drawString(inch, letter[1] - 1.5*inch, "Content for the final chapter.")

    try:
        c.save()
        print(f"Successfully created PDF: {filepath}")
    except Exception as e:
        print(f"Error creating PDF {filepath}: {e}")

def create_pdf_running_headers_footers(filename="running_headers_footers.pdf"):
    """
    Creates a PDF with running headers (e.g., chapter title) and footers (e.g., page numbers).
    """
    filepath = os.path.join(PDF_DIR, "structure", filename)
    
    def draw_header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawString(inch, 0.75 * inch, f"Page {doc.page}")
        canvas.setFont('Helvetica-Oblique', 9)
        canvas.drawString(inch, letter[1] - 0.75 * inch, "Synthetic Philosophical Treatise")
        canvas.restoreState()

    doc = SimpleDocTemplate(filepath, pagesize=letter)
    
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleH1 = styles['h1']
    story = []

    story.append(Paragraph("Chapter 1: Epistemological Considerations", styleH1))
    for i in range(15): 
        story.append(Paragraph(f"This is paragraph {i+1} of the first chapter. We are discussing the limits of knowledge and the nature of belief. "
                               "The running header should display the document title, and the footer should show the current page number. "
                               "This tests the extraction process's ability to ignore or correctly identify such repeating elements.", styleN))
        story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("Chapter 2: Metaphysical Debates", styleH1))
    for i in range(15):
        story.append(Paragraph(f"Paragraph {i+1} in the second chapter. Here, the focus shifts to the fundamental nature of reality. "
                               "Running headers and footers should persist across these pages. It is important that these elements are not "
                               "mistakenly included as part of the main textual content during parsing and chunking.", styleN))
        story.append(Spacer(1, 0.1*inch))

    try:
        doc.build(story, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
        print(f"Successfully created PDF: {filepath}")
    except Exception as e:
        print(f"Error creating PDF {filepath}: {e}")

def create_pdf_bottom_page_footnotes(filename="bottom_page_footnotes.pdf"):
    """
    Creates a PDF with footnotes appearing at the bottom of the page.
    This is a simplified visual simulation using absolute positioning.
    """
    filepath = os.path.join(PDF_DIR, "notes", filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    c.setTitle("PDF with Bottom Page Footnotes")
    c.setAuthor("Synthetic Data Generator")

    c.setFont("Helvetica", 12)
    text_y = letter[1] - inch
    
    line1 = "This is the main text of the document. It contains a reference to a footnote here.<sup>1</sup>"
    c.drawString(inch, text_y, line1)
    text_y -= 0.3*inch
    
    line2 = "The text continues, discussing various philosophical points. Another footnote reference appears here.<sup>2</sup>"
    c.drawString(inch, text_y, line2)
    text_y -= 0.3*inch

    line3 = "This ensures that the footnote text is clearly separated from the main body content."
    c.drawString(inch, text_y, line3)

    c.line(inch, inch + 0.5*inch + 0.3*inch*2, letter[0] - inch, inch + 0.5*inch + 0.3*inch*2)

    c.setFont("Helvetica", 9)
    fn_y = inch + 0.5*inch 
    fn1_text = "<sup>1</sup> This is the first footnote, appearing at the bottom of the page."
    c.drawString(inch, fn_y + 0.3*inch, fn1_text) 
    
    fn2_text = "<sup>2</sup> This is the second footnote, providing additional commentary."
    c.drawString(inch, fn_y, fn2_text)

    try:
        c.save()
        print(f"Successfully created PDF: {filepath}")
    except Exception as e:
        print(f"Error creating PDF {filepath}: {e}")

def create_pdf_simple_table(filename="simple_table.pdf"):
    """
    Creates a PDF with a simple table with clear borders.
    """
    filepath = os.path.join(PDF_DIR, "structure", filename)
    # Canvas setup is not needed if using SimpleDocTemplate primarily
    # c = canvas.Canvas(filepath, pagesize=letter) 
    # c.setTitle("PDF with Simple Table")
    # c.setAuthor("Synthetic Data Generator")

    from reportlab.lib import colors # Already imported via TableStyle but good practice if used directly

    styles = getSampleStyleSheet()
    styleH1 = styles['h1']
    
    story = []
    story.append(Paragraph("Philosophical Concepts: A Comparative Table", styleH1))
    story.append(Spacer(1, 0.3*inch))

    data = [
        ["Concept", "Originator", "Key Idea"],
        ["Forms", "Plato", "Perfect archetypes existing in a separate realm."],
        ["Categorical Imperative", "Kant", "Act only according to that maxim whereby you can at the same time will that it should become a universal law."],
        ["Tabula Rasa", "Locke", "The mind is a blank slate at birth."],
        ["Übermensch", "Nietzsche", "The 'overman' or 'superman' who has overcome traditional morality."]
    ]
    
    table = Table(data)
    table_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    table.setStyle(table_style)
    story.append(table)

    doc = SimpleDocTemplate(filepath, pagesize=letter,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    # Set metadata on the doc object for SimpleDocTemplate
    doc.title = "PDF with Simple Table"
    doc.author = "Synthetic Data Generator"
    doc.subject = "Testing PDF table generation"
    doc.keywords = ["pdf", "test", "table", "reportlab"]
    
    try:
        doc.build(story)
        print(f"Successfully created PDF: {filepath}")
    except Exception as e:
        print(f"Error creating PDF {filepath}: {e}")

# Placeholder for more PDF generation functions
# def create_pdf_multi_column(...):
#     pass

# def create_pdf_with_images(...):
#     pass