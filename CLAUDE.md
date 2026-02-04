# Scrivener to Obsidian Converter

A simple web app that converts Scrivener projects to Obsidian vaults.

## Target User

**Non-technical writers.** Think: someone who knows Scrivener well, wants to try Obsidian, but doesn't know command lines or technical stuff. The UI must be dead simple.

## UI Design

```
┌─────────────────────────────────────────┐
│  Scrivener → Obsidian                   │
├─────────────────────────────────────────┤
│                                         │
│  📁 Scrivener Project:                  │
│  [Select .scriv file...]                │
│  /Users/jane/My Novel.scriv             │
│                                         │
│  📂 Output Folder:                      │
│  [Select folder...]                     │
│  /Users/jane/My Novel Vault             │
│                                         │
│  [    Convert    ]                      │
│                                         │
│  ✓ Converted 47 documents to markdown   │
│                                         │
└─────────────────────────────────────────┘
```

**That's it.** Two folder pickers, one button. No options, no settings.

## Conversion Mapping

```
Scrivener                    →    Obsidian
─────────────────────────────────────────────────
Binder folders               →    Folders
Documents (RTF)              →    Markdown files (.md)
Document title               →    Filename
Synopsis                     →    YAML frontmatter (synopsis field)
Notes                        →    Callout block at end of file
Labels                       →    Tags in frontmatter
Status                       →    Tags in frontmatter
Include in Compile           →    Frontmatter field
```

### Example Output

For a Scrivener document "Chapter 1 - The Beginning":

```markdown
---
title: "Chapter 1 - The Beginning"
synopsis: "John arrives at the lighthouse and discovers the hidden door."
tags:
  - label/first-draft
  - status/to-do
include_in_compile: true
---

The rain had been falling for three days when John finally saw the lighthouse...

[content continues...]

> [!note] Author Notes
> Remember to add more sensory details here. Check timeline against Chapter 3.
```

## Scrivener File Format

A `.scriv` file is a folder containing:
```
MyNovel.scriv/
├── Files/
│   └── Data/
│       ├── {UUID}/
│       │   ├── content.rtf    # Document text
│       │   ├── synopsis.txt   # Synopsis (plain text)
│       │   └── notes.rtf      # Document notes
│       └── ...
└── project.scrivx             # XML binder structure
```

### Key Technical Details

1. **Binder structure** is in `project.scrivx` (XML)
2. **Document content** is RTF at `Files/Data/{UUID}/content.rtf`
3. **Synopsis** is plain text at `Files/Data/{UUID}/synopsis.txt`
4. **Notes** are RTF at `Files/Data/{UUID}/notes.rtf`
5. **Labels/Status** are in the `.scrivx` XML metadata

## Tech Stack

- **Backend:** Python + FastAPI
- **Frontend:** Vanilla HTML/CSS/JS (keep it simple)
- **RTF parsing:** `striprtf` library
- **XML parsing:** Built-in `xml.etree.ElementTree`

## Project Structure

```
obsidian-converter/
├── app/
│   ├── main.py              # FastAPI app
│   ├── converter.py         # Conversion logic
│   └── static/
│       ├── index.html
│       ├── style.css
│       └── app.js
├── pyproject.toml
├── README.md
└── CLAUDE.md
```

## Implementation Steps

1. **Set up FastAPI app** with static file serving
2. **Build simple UI** - two folder inputs, convert button
3. **Implement conversion logic:**
   - Parse `.scrivx` to get binder structure
   - Walk the binder tree
   - For each document:
     - Read RTF content → convert to plain text
     - Read synopsis if exists
     - Read notes if exists → convert to plain text
     - Get labels/status from XML
     - Generate markdown with YAML frontmatter
   - Create folder structure matching binder
4. **Add progress feedback** - show which files are being converted
5. **Handle errors gracefully** - show user-friendly messages

## Reusable Code

The **scrivener-mcp** project has Scrivener parsing code that can be reused:
- `scrivener/project.py` - ScrivenerProject class
- `scrivener/binder.py` - Binder parsing
- `scrivener/rtf.py` - RTF to text conversion

Location: `~/scrivener-mcp/src/scrivener_mcp/scrivener/`

Consider copying these modules or importing from scrivener-mcp if installed.

## Key Constraints

1. **No CLI** - target users don't know command line
2. **No options** - just source and destination, that's it
3. **Works offline** - no cloud, no accounts, runs locally
4. **Preserves structure** - Obsidian vault mirrors Scrivener binder
5. **Non-destructive** - never modifies the .scriv file

## File Naming

Obsidian filenames should be safe:
- Replace `/` with `-`
- Replace other problematic characters
- Keep it readable

Example: "Chapter 01/Scene 1" → folder `Chapter 01/` with file `Scene 1.md`

## Error Handling

Show friendly messages:
- "Please select a Scrivener project (.scriv folder)"
- "Please select an output folder"
- "Output folder is not empty - files may be overwritten. Continue?"
- "Conversion complete! Converted X documents."
- "Error: Could not read [filename]. Skipping..."

## Related Projects

- **scrivener-mcp** - Read-only MCP for Claude Desktop + Scrivener
- **prose-pipeline** - AI prose generation

## Getting Started

```bash
cd ~/Obsidian\ Converter
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn striprtf

# Then build the app following the structure above
```
