# Specifications for `synthetic_test_data` Python Package

## 1. Introduction

The `synthetic_test_data` Python package provides a configurable and extensible framework for generating various types of synthetic data files. These files are intended for testing applications that process documents, such as EPUB, PDF, and Markdown files. The package aims to be reusable across multiple projects, offering a default set of generated data out-of-the-box, while allowing users to customize generation parameters and extend its capabilities with new data types or variations.

This document outlines the API, configuration mechanism, extensibility points, default data sets, output structure, and dependencies for the package.

## 2. Package API

The primary interaction with the package will be through a main class or a set of high-level functions.

### 2.1. Main Entry Point

A central `DataGenerator` class or a primary function like `generate_data()` will serve as the main entry point.

**Option 1: Class-based API**

```python
class DataGenerator:
    def __init__(self, config_path=None, output_dir="generated_data"):
        """
        Initializes the generator with an optional configuration file path
        and an output directory.
        If config_path is None, loads default configuration.
        """
        # TDD_ANCHOR: test_datagenerator_init_default_config
        # TDD_ANCHOR: test_datagenerator_init_custom_config
        # TDD_ANCHOR: test_datagenerator_init_output_dir
        pass

    def generate(self, file_types=None, quantities=None, specific_variations=None):
        """
        Generates synthetic data.

        Args:
            file_types (list[str], optional): List of file types to generate (e.g., ["epub", "pdf"]).
                                            Defaults to all types specified in the config.
            quantities (dict[str, int], optional): Dictionary specifying quantity for each file type
                                                 (e.g., {"epub": 10, "pdf": 5}).
                                                 Overrides config quantities if provided.
            specific_variations (dict[str, list[str]], optional):
                                                 Dictionary specifying specific variations to generate
                                                 for each file type (e.g., {"epub": ["toc_complex", "basic_no_toc"]}).
                                                 If None, generates variations as per config.
        """
        # TDD_ANCHOR: test_generator_generate_all_types_default_quantities
        # TDD_ANCHOR: test_generator_generate_specific_types
        # TDD_ANCHOR: test_generator_generate_specific_quantities
        # TDD_ANCHOR: test_generator_generate_specific_variations
        # TDD_ANCHOR: test_generator_generate_no_config_uses_defaults
        pass

    def list_available_types(self):
        """Returns a list of supported file types."""
        # TDD_ANCHOR: test_generator_list_available_types
        pass

    def list_available_variations(self, file_type):
        """Returns a list of available variations for a given file type."""
        # TDD_ANCHOR: test_generator_list_available_variations_for_type
        pass
```

**Option 2: Function-based API**

```python
def generate_data(config_path=None, output_dir="generated_data", file_types=None, quantities=None, specific_variations=None):
    """
    Generates synthetic data based on configuration and specified parameters.
    (Docstring similar to DataGenerator.generate())
    """
    # TDD_ANCHOR: test_generate_data_func_default_config
    # TDD_ANCHOR: test_generate_data_func_custom_config
    # TDD_ANCHOR: test_generate_data_func_specific_types_quantities_variations
    pass

def list_available_types(config_path=None):
    # TDD_ANCHOR: test_list_available_types_func
    pass

def list_available_variations(file_type, config_path=None):
    # TDD_ANCHOR: test_list_available_variations_for_type_func
    pass
```
*(Decision: Class-based API is preferred for better state management if generation becomes more complex or involves multiple steps internally.)*

### 2.2. Specifying Data Types and Quantities

*   **File Types:** Users can specify a list of file types (e.g., `["epub", "pdf", "markdown"]`) to the `generate` method. If not provided, all types defined in the active configuration will be generated.
*   **Quantities:** A dictionary mapping file types to desired counts (e.g., `{"epub": 5, "pdf": 3}`). This allows overriding global or type-specific quantity settings in the configuration.
*   **Variations:** Users can request specific, named variations for each file type (e.g., for EPUBs: `["epub_with_toc", "epub_without_toc", "epub_complex_formatting"]`). If not specified, the package will generate a default set of variations or all configured variations for each type.

## 3. Configuration Mechanism

The package will support configuration through YAML files, with a fallback to default Python dictionary-based configurations if no file is provided. A CLI for the package itself could also use these configurations.

### 3.1. Configuration File Format (YAML)

A primary `config.yaml` (or user-specified file) will define generation parameters.

```yaml
# config.yaml (example)
package_settings:
  output_directory: "synthetic_data_output" # Overridden by API if specified
  default_quantity_per_type: 1 # Default if not specified per type

file_types:
  epub:
    enabled: true
    quantity: 5 # Overrides package_settings.default_quantity_per_type
    output_subdir: "epubs" # Relative to package_settings.output_directory
    generators: # Defines specific variations and their configs
      - name: "ncx_simple"
        # TDD_ANCHOR: test_config_epub_ncx_simple_params
        # Based on synthetic_test_data/epub_generators/toc.py -> create_epub_ncx_simple
        # Parameters from docs/qa/synthetic_data_requirements.md and docs/reports/epub_formatting_analysis_report.md
        num_chapters: 3
        include_toc_page: true
        toc_depth: 1
        content_type: "prose_basic" # Link to content generation strategy
        # ... other specific params for ncx_simple
      - name: "navdoc_full"
        # TDD_ANCHOR: test_config_epub_navdoc_full_params
        # Based on synthetic_test_data/epub_generators/toc.py -> create_epub_navdoc_full
        num_chapters: 5
        include_nav_landmarks: true
        include_page_list: true
        # ... other specific params
      - name: "pippin_style_endnotes"
        # TDD_ANCHOR: test_config_epub_pippin_style_endnotes_params
        # Based on synthetic_test_data/epub_generators/notes.py -> create_epub_pippin_style_endnotes
        num_chapters: 2
        notes_per_chapter: 3
        # ... other specific params
    # ... other EPUB variations from synthetic_test_data/epub_generators/* and docs/qa/synthetic_data_requirements.md
    # e.g., citations.py, content_types.py, headers.py, multimedia.py, page_numbers.py, structure.py

  pdf:
    enabled: true
    quantity: 2
    output_subdir: "pdfs"
    generators:
      - name: "basic_text_pdf"
        # TDD_ANCHOR: test_config_pdf_basic_text_params
        num_pages: 10
        font_size: 12
        # ...
      - name: "pdf_with_images"
        # TDD_ANCHOR: test_config_pdf_with_images_params
        # ...
    # Parameters from docs/qa/synthetic_data_requirements.md

  markdown:
    enabled: true
    quantity: 3
    output_subdir: "markdown"
    generators:
      - name: "all_basic_elements"
        # TDD_ANCHOR: test_config_md_all_basic_elements_params
        # Based on synthetic_test_data/generate_markdown.py
        include_headers_levels: [1, 2, 3]
        include_lists: true
        include_tables: true
        # ...
    # Parameters from docs/qa/synthetic_data_requirements.md

# Global content generation strategies (can be referenced by file type generators)
content_strategies:
  prose_basic:
    type: "lorem_ipsum" # or "faker_text"
    paragraphs_per_chapter: 5
    sentences_per_paragraph: [3, 7]
  technical_mixed:
    # ...
```

### 3.2. Configurable Parameters

Parameters will be configurable at global, per-file-type, and per-variation levels.
Examples based on [`docs/qa/synthetic_data_requirements.md`](docs/qa/synthetic_data_requirements.md:1) and [`docs/reports/epub_formatting_analysis_report.md`](docs/reports/epub_formatting_analysis_report.md:1):

*   **EPUB:**
    *   `num_chapters`, `paragraphs_per_chapter`, `sentences_per_paragraph`
    *   `include_toc` (boolean), `toc_type` (NCX, NavDoc), `toc_depth`
    *   `include_cover_image` (boolean), `cover_image_path`
    *   `font_embedding` (boolean)
    *   `header_footer_style` (none, simple_page_num, chapter_title)
    *   `footnote_endnote_style` (inline, separate_page, per_chapter)
    *   `citation_style` (apa, mla, none)
    *   `image_inclusion` (none, single_per_chapter, multiple_inline)
    *   `table_complexity` (simple, complex_merged_cells)
    *   `math_content` (mathml, images)
    *   `custom_css_path`
    *   Specific landmark types for NavDoc (e.g., `bodymatter`, `toc`, `loi`, `lot`, `copyright-page`)
    *   Page-list generation in NavDoc
    *   Presence/absence of `guide` items in OPF
    *   EPUB version (2 or 3)
    *   Metadata fields (title, author, publisher, language, ISBN, publication_date, rights, description, subject)

*   **PDF:**
    *   `num_pages`
    *   `page_size` (A4, Letter), `orientation` (portrait, landscape)
    *   `font_name`, `font_size`, `line_spacing`
    *   `include_images` (boolean), `image_paths`
    *   `include_tables` (boolean)
    *   `header_footer_content` (text, page_numbers)
    *   `metadata` (title, author, subject, keywords)

*   **Markdown:**
    *   `elements_to_include` (list: headers, paragraphs, lists, tables, code_blocks, blockquotes, links, images)
    *   `header_levels` (e.g., 1-3)
    *   `list_types` (ordered, unordered, nested)
    *   `table_rows`, `table_columns`
    *   `code_block_languages`

### 3.3. Default Configuration

*   If no `config.yaml` is provided or found, the package will use a built-in default Python dictionary.
*   This default configuration will mirror the capabilities and output of the current scripts in `mcp-vector-database/synthetic_test_data/` (e.g., generating `ncx_simple.epub`, `navdoc_full.epub`, `pippin_style_endnotes.epub`, `all_basic_elements.md`, etc., as per their respective generator scripts).
*   The default output directory will be `./generated_data/` relative to where the script is run.
    *   **TDD_ANCHOR:** `test_load_default_config_generates_expected_files`
    *   **TDD_ANCHOR:** `test_default_config_epub_variations_match_current_scripts`
    *   **TDD_ANCHOR:** `test_default_config_pdf_variations_match_current_scripts`
    *   **TDD_ANCHOR:** `test_default_config_markdown_variations_match_current_scripts`

## 4. Extensibility Points

### 4.1. Adding New Data Generation Routines (Variations) for Existing Types

Users can add new variations by:
1.  **Convention:** Creating a new Python module (e.g., `my_custom_epub_generator.py`) within a designated `custom_generators/<file_type>/` directory. This module must contain a specific function, e.g., `create_my_variation(config_params, output_path)`.
    *   **TDD_ANCHOR:** `test_load_custom_generator_from_convention_dir`
2.  **Registration API (Alternative):**
    ```python
    generator_instance.register_variation_generator(
        file_type="epub",
        variation_name="my_cool_epub",
        generator_function=my_custom_epub_module.create_my_cool_epub
    )
    ```
    *   **TDD_ANCHOR:** `test_register_custom_variation_generator_api`
3.  The new variation and its specific parameters can then be referenced in the `config.yaml`.

### 4.2. Adding Support for Entirely New File Types

Users can add support for new file types by:
1.  **Convention:** Creating a new subdirectory under `custom_generators/` (e.g., `custom_generators/docx/`) and placing generator modules there.
2.  **Registration API:**
    ```python
    generator_instance.register_file_type_handler(
        file_type_name="docx",
        handler_class=MyCustomDocxHandler # A class that knows how to find/call docx variations
    )
    ```
    *   **TDD_ANCHOR:** `test_register_new_file_type_handler`
3.  The new file type and its configurations can then be added to `config.yaml`.
    A base `FileTypeHandler` class could be provided, which custom handlers would inherit from, defining methods for discovering and invoking variation generators.

## 5. Default Data Sets

The default configuration will generate a set of files based on the current capabilities demonstrated in `mcp-vector-database/synthetic_test_data/` and detailed in [`docs/qa/synthetic_data_requirements.md`](docs/qa/synthetic_data_requirements.md:1).

*   **EPUBs (examples, refer to `synthetic_test_data/epub_generators/` for full list):**
    *   `ncx_simple.epub`: Basic NCX ToC, few chapters.
        *   *Key Characteristics:* Simple navigation, standard prose.
    *   `navdoc_full.epub`: EPUB3 NavDoc with landmarks and page-list.
        *   *Key Characteristics:* Rich navigation features.
    *   `pippin_style_endnotes.epub`: Content with endnotes formatted in a specific style.
        *   *Key Characteristics:* Endnote presence and formatting.
    *   `citations_various.epub`: EPUB with different citation styles.
        *   *Key Characteristics:* APA, MLA, Chicago style citations.
    *   `multimedia_embedded.epub`: EPUB with embedded images and potentially audio/video placeholders.
        *   *Key Characteristics:* Embedded non-textual content.
    *   `complex_structure.epub`: EPUB with nested sections, blockquotes, etc.
        *   *Key Characteristics:* Deeply nested HTML structure.
    *   **TDD_ANCHOR:** `test_default_epub_set_generation_and_content_spot_check`

*   **PDFs (examples):**
    *   `basic_text_10pages.pdf`: Simple multi-page PDF with lorem ipsum.
        *   *Key Characteristics:* Basic text flow, multiple pages.
    *   `pdf_with_images_and_tables.pdf`: PDF including images and tables.
        *   *Key Characteristics:* Mixed content types.
    *   **TDD_ANCHOR:** `test_default_pdf_set_generation_and_content_spot_check`

*   **Markdown (examples):**
    *   `all_basic_elements.md`: Markdown file showcasing all standard elements (headers, lists, tables, code, etc.).
        *   *Key Characteristics:* Comprehensive coverage of Markdown syntax.
    *   `markdown_with_frontmatter.md`: Markdown with YAML frontmatter.
        *   *Key Characteristics:* Metadata block.
    *   **TDD_ANCHOR:** `test_default_markdown_set_generation_and_content_spot_check`

*(This list will be expanded to match all generator scripts in `synthetic_test_data/epub_generators/` and other `generate_*.py` files, cross-referencing with `docs/qa/synthetic_data_requirements.md`)*

## 6. Output Structure

Generated files will be organized into subdirectories based on file type, within a main output directory.
The default structure, mirroring the refactored paths in `mcp-vector-database` (see `activeContext.md` [2025-05-10 16:41:29](memory-bank/activeContext.md:4)), will be:

```
<output_directory>/
├── epubs/
│   ├── ncx_simple_01.epub
│   ├── ncx_simple_02.epub
│   └── ...
├── pdfs/
│   ├── basic_text_10pages_01.pdf
│   └── ...
├── markdown/
│   ├── all_basic_elements_01.md
│   └── ...
└── <new_file_type>/
    └── ...
```

*   `<output_directory>`: Specified by the user or defaults to `generated_data`.
*   Subdirectory names (e.g., `epubs`, `pdfs`) are configurable via `output_subdir` in `config.yaml`.
*   Filenames will typically be `<variation_name>_<instance_number>.<extension>`.
    *   **TDD_ANCHOR:** `test_output_structure_creation`
    *   **TDD_ANCHOR:** `test_output_subdir_configuration`
    *   **TDD_ANCHOR:** `test_output_filename_format`

## 7. Dependencies

Initial anticipated Python dependencies:

*   `PyYAML`: For parsing YAML configuration files.
*   `EbookLib`: For EPUB generation (currently used in `synthetic_test_data/common.py`).
*   `ReportLab`: For PDF generation (currently used in `synthetic_test_data/generate_pdfs.py`).
*   `Faker`: For generating realistic fake data (names, addresses, text).
*   `python-markdown`: If Markdown generation involves converting from a structured format or for validation. (Or a simpler template-based approach might not need it).

    *   **TDD_ANCHOR:** `test_package_can_be_installed_with_listed_dependencies` (more of an integration test for the package itself later)

## 8. TDD Anchors (Summary)

This section summarizes TDD anchors mentioned throughout the document. These represent key test cases to be developed.

*   **DataGenerator Class & API:**
    *   `test_datagenerator_init_default_config`
    *   `test_datagenerator_init_custom_config`
    *   `test_datagenerator_init_output_dir`
    *   `test_generator_generate_all_types_default_quantities`
    *   `test_generator_generate_specific_types`
    *   `test_generator_generate_specific_quantities`
    *   `test_generator_generate_specific_variations`
    *   `test_generator_generate_no_config_uses_defaults`
    *   `test_generator_list_available_types`
    *   `test_generator_list_available_variations_for_type`
    *   (Similar tests if function-based API is chosen: `test_generate_data_func_*`, `test_list_available_types_func`, `test_list_available_variations_for_type_func`)

*   **Configuration:**
    *   `test_config_epub_ncx_simple_params`
    *   `test_config_epub_navdoc_full_params`
    *   `test_config_epub_pippin_style_endnotes_params`
    *   (Further tests for each EPUB variation's parameters from `docs/qa/synthetic_data_requirements.md`)
    *   `test_config_pdf_basic_text_params`
    *   `test_config_pdf_with_images_params`
    *   (Further tests for PDF parameters)
    *   `test_config_md_all_basic_elements_params`
    *   (Further tests for Markdown parameters)
    *   `test_load_default_config_generates_expected_files`
    *   `test_default_config_epub_variations_match_current_scripts`
    *   `test_default_config_pdf_variations_match_current_scripts`
    *   `test_default_config_markdown_variations_match_current_scripts`
    *   `test_config_override_default_quantity_per_type`
    *   `test_config_override_package_output_directory`

*   **Extensibility:**
    *   `test_load_custom_generator_from_convention_dir`
    *   `test_register_custom_variation_generator_api`
    *   `test_register_new_file_type_handler`
    *   `test_custom_generator_receives_correct_config_params`

*   **Default Data Sets & Output:**
    *   `test_default_epub_set_generation_and_content_spot_check`
    *   `test_default_pdf_set_generation_and_content_spot_check`
    *   `test_default_markdown_set_generation_and_content_spot_check`
    *   `test_output_structure_creation`
    *   `test_output_subdir_configuration`
    *   `test_output_filename_format`

*   **Package Level (Later Stage):**
    *   `test_package_can_be_installed_with_listed_dependencies`