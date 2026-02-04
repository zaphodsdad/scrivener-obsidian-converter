# Scrivener to Obsidian Converter

A simple web app that converts Scrivener projects to Obsidian vaults.

## For Writers, Not Techies

No command line. No complicated options. Just:

1. Select your Scrivener project
2. Select where you want the Obsidian vault
3. Click Convert

That's it.

## What Gets Converted

| Scrivener | → | Obsidian |
|-----------|---|----------|
| Folders | → | Folders |
| Documents | → | Markdown files |
| Synopsis | → | YAML frontmatter |
| Notes | → | Callout block |
| Labels/Status | → | Tags |

## Installation

```bash
git clone https://github.com/zaphodsdad/obsidian-converter.git
cd obsidian-converter
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
obsidian-converter
```

Opens in your browser. Pick your files, click convert.

## Requirements

- Python 3.10+
- Scrivener 3 project (.scriv folder)

## License

MIT
