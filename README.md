# Scrivener to Obsidian Converter

A simple web app that converts Scrivener projects to Obsidian vaults.

## For Writers, Not Techies

No command line. No complicated options. Just:

1. Click "Select .scriv" - native file picker opens
2. Click "Select folder" - choose where to save
3. Click "Convert"

That's it. Your files stay on your computer. Nothing is uploaded anywhere.

## What Gets Converted

| Scrivener | Obsidian |
|-----------|----------|
| Binder folders | Folders |
| Documents (RTF) | Markdown files (.md) |
| Document title | Filename + frontmatter |
| Synopsis | YAML frontmatter field |
| Notes | Callout block at end of file |
| Labels | Tags (label/your-label) |
| Status | Tags (status/your-status) |
| Include in Compile | Frontmatter field |

### Example Output

A Scrivener document becomes:

```markdown
---
title: "Chapter 1 - The Beginning"
synopsis: "John arrives at the lighthouse."
tags:
  - label/first-draft
  - status/to-do
include_in_compile: true
---

The rain had been falling for three days...

> [!note] Author Notes
> Remember to add more sensory details here.
```

## Installation

### macOS

```bash
git clone https://github.com/zaphodsdad/obsidian-converter.git
cd obsidian-converter
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Running

```bash
cd obsidian-converter
source .venv/bin/activate
uvicorn app.main:app --port 8000
```

Then open http://127.0.0.1:8000 in your browser.

## Requirements

- macOS (Windows/Linux support planned)
- Python 3.10+
- Scrivener 3 project (.scriv)

## Tech Stack

- **Backend:** Python, FastAPI
- **Frontend:** Vanilla HTML/CSS/JS
- **RTF Parsing:** striprtf library
- **File Dialogs:** Native macOS via osascript

## License

MIT
