import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer
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

# Placeholder for more PDF generation functions
# def create_pdf_multi_column(...):
#     pass

# def create_pdf_with_images(...):
#     pass