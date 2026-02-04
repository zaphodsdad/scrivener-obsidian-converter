"""Scrivener to Obsidian conversion logic."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from striprtf.striprtf import rtf_to_text


@dataclass
class BinderItem:
    """A single item in the Scrivener binder."""

    uuid: str
    title: str
    item_type: str
    include_in_compile: bool = False
    label: str | None = None
    status: str | None = None
    position: int = 0  # Position among siblings (0-indexed)
    children: list[BinderItem] = field(default_factory=list)
    parent: BinderItem | None = field(default=None, repr=False)

    @property
    def is_folder(self) -> bool:
        return self.item_type in ("Folder", "DraftFolder", "ResearchFolder", "TrashFolder")

    @property
    def is_text(self) -> bool:
        return self.item_type == "Text"

    @property
    def is_trash(self) -> bool:
        return self.item_type == "TrashFolder"

    def walk(self) -> Iterator[BinderItem]:
        """Iterate over this item and all descendants."""
        yield self
        for child in self.children:
            yield from child.walk()


def read_rtf(path: Path) -> str:
    """Read an RTF file and return plain text."""
    if not path.exists():
        return ""
    rtf_content = path.read_text(encoding="utf-8", errors="ignore")
    if not rtf_content.strip():
        return ""
    try:
        return rtf_to_text(rtf_content).strip()
    except Exception:
        return ""


def sanitize_filename(name: str) -> str:
    """Make a filename safe for the filesystem."""
    # Replace problematic characters
    name = re.sub(r'[<>:"/\\|?*]', '-', name)
    # Remove leading/trailing spaces and dots
    name = name.strip(' .')
    # Collapse multiple dashes
    name = re.sub(r'-+', '-', name)
    return name or "Untitled"


class ScrivenerProject:
    """A Scrivener project for conversion."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Project not found: {self.path}")
        if not self.path.is_dir():
            raise ValueError(f"Not a directory: {self.path}")

        self._scrivx_path = self._find_scrivx()
        if not self._scrivx_path:
            raise ValueError(f"No .scrivx file found in {self.path}")

        self._labels: dict[str, str] = {}
        self._statuses: dict[str, str] = {}
        self._binder_items = self._parse_project()

    def _find_scrivx(self) -> Path | None:
        for f in self.path.iterdir():
            if f.suffix == ".scrivx":
                return f
        return None

    @property
    def name(self) -> str:
        return self.path.stem

    def _parse_project(self) -> list[BinderItem]:
        """Parse the .scrivx file and extract labels/statuses."""
        tree = ET.parse(self._scrivx_path)
        root = tree.getroot()

        # Parse label settings
        label_settings = root.find(".//LabelSettings")
        if label_settings is not None:
            for label in label_settings.findall("Label"):
                label_id = label.get("ID", "")
                label_name = label.text or ""
                if label_id and label_name and label_name != "No Label":
                    self._labels[label_id] = label_name

        # Parse status settings
        status_settings = root.find(".//StatusSettings")
        if status_settings is not None:
            for status in status_settings.findall("Status"):
                status_id = status.get("ID", "")
                status_name = status.text or ""
                if status_id and status_name and status_name != "No Status":
                    self._statuses[status_id] = status_name

        # Parse binder
        binder = root.find("Binder")
        if binder is None:
            return []

        items = []
        for idx, item_elem in enumerate(binder.findall("BinderItem")):
            items.append(self._parse_binder_item(item_elem, position=idx))
        return items

    def _parse_binder_item(self, element: ET.Element, parent: BinderItem | None = None, position: int = 0) -> BinderItem:
        """Parse a BinderItem XML element."""
        uuid = element.get("UUID", "")
        item_type = element.get("Type", "Text")

        title_elem = element.find("Title")
        title = title_elem.text if title_elem is not None and title_elem.text else "Untitled"

        include_in_compile = False
        label_id = None
        status_id = None

        metadata = element.find("MetaData")
        if metadata is not None:
            include_elem = metadata.find("IncludeInCompile")
            if include_elem is not None and include_elem.text:
                include_in_compile = include_elem.text.lower() == "yes"

            label_elem = metadata.find("LabelID")
            if label_elem is not None and label_elem.text:
                label_id = label_elem.text

            status_elem = metadata.find("StatusID")
            if status_elem is not None and status_elem.text:
                status_id = status_elem.text

        item = BinderItem(
            uuid=uuid,
            title=title,
            item_type=item_type,
            include_in_compile=include_in_compile,
            label=self._labels.get(label_id) if label_id else None,
            status=self._statuses.get(status_id) if status_id else None,
            position=position,
            parent=parent,
        )

        children_elem = element.find("Children")
        if children_elem is not None:
            for idx, child_elem in enumerate(children_elem.findall("BinderItem")):
                child = self._parse_binder_item(child_elem, parent=item, position=idx)
                item.children.append(child)

        return item

    def get_content_path(self, item: BinderItem) -> Path:
        return self.path / "Files" / "Data" / item.uuid / "content.rtf"

    def get_synopsis_path(self, item: BinderItem) -> Path:
        return self.path / "Files" / "Data" / item.uuid / "synopsis.txt"

    def get_notes_path(self, item: BinderItem) -> Path:
        return self.path / "Files" / "Data" / item.uuid / "notes.rtf"

    def read_content(self, item: BinderItem) -> str:
        return read_rtf(self.get_content_path(item))

    def read_synopsis(self, item: BinderItem) -> str:
        synopsis_path = self.get_synopsis_path(item)
        if synopsis_path.exists():
            return synopsis_path.read_text(encoding="utf-8", errors="ignore").strip()
        return ""

    def read_notes(self, item: BinderItem) -> str:
        return read_rtf(self.get_notes_path(item))

    def all_items(self) -> Iterator[BinderItem]:
        for item in self._binder_items:
            yield from item.walk()


def generate_markdown(
    title: str,
    content: str,
    synopsis: str | None = None,
    notes: str | None = None,
    label: str | None = None,
    status: str | None = None,
    include_in_compile: bool = False,
) -> str:
    """Generate markdown with YAML frontmatter."""
    lines = ["---"]

    # Escape quotes in title
    safe_title = title.replace('"', '\\"')
    lines.append(f'title: "{safe_title}"')

    if synopsis:
        # Handle multi-line synopsis
        if "\n" in synopsis:
            lines.append("synopsis: |")
            for line in synopsis.split("\n"):
                lines.append(f"  {line}")
        else:
            safe_synopsis = synopsis.replace('"', '\\"')
            lines.append(f'synopsis: "{safe_synopsis}"')

    # Tags from label and status
    tags = []
    if label:
        tag_label = re.sub(r'[^a-zA-Z0-9_-]', '-', label.lower())
        tags.append(f"label/{tag_label}")
    if status:
        tag_status = re.sub(r'[^a-zA-Z0-9_-]', '-', status.lower())
        tags.append(f"status/{tag_status}")

    if tags:
        lines.append("tags:")
        for tag in tags:
            lines.append(f"  - {tag}")

    lines.append(f"include_in_compile: {str(include_in_compile).lower()}")
    lines.append("---")
    lines.append("")

    # Content
    if content:
        lines.append(content)
        lines.append("")

    # Notes as callout
    if notes:
        lines.append("> [!note] Author Notes")
        for note_line in notes.split("\n"):
            lines.append(f"> {note_line}")
        lines.append("")

    return "\n".join(lines)


@dataclass
class ConversionResult:
    """Result of a conversion operation."""
    success: bool
    documents_converted: int = 0
    folders_created: int = 0
    errors: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def convert_project(scriv_path: str | Path, output_path: str | Path) -> ConversionResult:
    """Convert a Scrivener project to an Obsidian vault."""
    result = ConversionResult(success=True)

    try:
        project = ScrivenerProject(scriv_path)
    except Exception as e:
        result.success = False
        result.errors.append(f"Could not open project: {e}")
        return result

    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    def get_item_path(item: BinderItem) -> list[str]:
        """Get the path components for an item (with position prefixes)."""
        parts = []
        current = item.parent
        while current is not None:
            if not current.is_trash:
                # Add position prefix for ordering (01, 02, etc.)
                prefix = f"{current.position + 1:02d}"
                parts.append(f"{prefix} {sanitize_filename(current.title)}")
            current = current.parent
        return list(reversed(parts))

    for item in project.all_items():
        # Skip trash
        if item.is_trash:
            result.skipped.append(f"{item.title} (trash)")
            continue

        # Skip items inside trash
        in_trash = False
        current = item.parent
        while current:
            if current.is_trash:
                in_trash = True
                break
            current = current.parent
        if in_trash:
            continue

        try:
            path_parts = get_item_path(item)

            # Position prefix for ordering (01, 02, etc.)
            prefix = f"{item.position + 1:02d}"

            if item.is_folder:
                # Create folder with position prefix
                folder_name = f"{prefix} {sanitize_filename(item.title)}"
                folder_path = output_dir.joinpath(*path_parts, folder_name)
                folder_path.mkdir(parents=True, exist_ok=True)
                result.folders_created += 1

            elif item.is_text:
                # Create markdown file with position prefix
                if path_parts:
                    file_dir = output_dir.joinpath(*path_parts)
                    file_dir.mkdir(parents=True, exist_ok=True)
                else:
                    file_dir = output_dir

                filename = f"{prefix} {sanitize_filename(item.title)}.md"
                file_path = file_dir / filename

                content = project.read_content(item)
                synopsis = project.read_synopsis(item)
                notes = project.read_notes(item)

                markdown = generate_markdown(
                    title=item.title,
                    content=content,
                    synopsis=synopsis if synopsis else None,
                    notes=notes if notes else None,
                    label=item.label,
                    status=item.status,
                    include_in_compile=item.include_in_compile,
                )

                file_path.write_text(markdown, encoding="utf-8")
                result.documents_converted += 1

        except Exception as e:
            result.errors.append(f"Error converting '{item.title}': {e}")

    if result.errors:
        result.success = len(result.errors) < result.documents_converted

    return result
