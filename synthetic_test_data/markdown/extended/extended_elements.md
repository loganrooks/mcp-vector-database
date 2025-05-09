+++
title = "Extended Markdown Showcase"
author = "Synthetic Data Generator"
date = "2025-05-09"
category = "synthetic"
draft = false
description = "A test file for advanced Markdown features."
+++
# Extended Markdown Features
This document demonstrates more complex Markdown elements.
## Tables
A simple table:
| Philosopher | Key Idea             | Era      |
|-------------|----------------------|----------|
| Plato       | Theory of Forms      | Ancient  |
| Kant        | Categorical Imperative | Modern   |
| Nietzsche   | Will to Power        | Modern   |
A table with different alignments:
| Left Align  | Center Align | Right Align |
|:------------|:------------:|------------:|
| Col 3 is    | some wordy   |        $1600 |
| Col 2 is    | centered     |          $12 |
| zebra stripes | are neat   |           $1 |
## Footnotes
Here is some text with a footnote.[^1] And another one.[^2]
[^1]: This is the first footnote. It can contain **bold** and *italic* text.
[^2]: This is the second footnote. It might link to [another resource](https://example.com).
## Task Lists
- [x] Define requirements for synthetic data
- [ ] Generate EPUB files
  - [ ] Simple NCX
  - [ ] Nested NCX
- [ ] Generate PDF files
- [ ] Generate Markdown files
  - [x] Basic elements
  - [ ] Extended elements (this one!)
## Code Blocks
Python code block:
```python
def greet(name):
    print(f"Hello, {name}!")
greet("Philosopher")
```
JSON code block:
```json
{
  "concept": "Synthetic Data",
  "purpose": "Testing",
  "formats": ["EPUB", "PDF", "Markdown"]
}
```
Indented code block:

    // This is an indented code block
    // Often used for simpler snippets.
    function example() {
        return true;
    }
## Horizontal Rules
---
***
___
These are different ways to create horizontal rules.
