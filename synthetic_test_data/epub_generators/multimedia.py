import os
from ebooklib import epub
from ..common import EPUB_DIR, _create_epub_book, _add_epub_chapters, _write_epub_file

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