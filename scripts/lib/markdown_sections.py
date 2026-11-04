"""Level-2 markdown heading helpers shared by planning artifact validation."""

from __future__ import annotations

import re

_ATX_LEVEL2_SECTION_RE = re.compile(
    r"(?ims)^\s*##\s+(?P<heading>[^\n]+?)\s*$\s*(?P<body>.*?)(?=^\s*##\s+.+$|\Z)"
)
_ATX_LEVEL2_HEADING_RE = re.compile(r"(?ims)^\s*##\s+([^\n]+?)\s*$")


def extract_markdown_section(text: str, heading: str) -> str | None:
    """Return the body of the first level-2 section with an exact heading match."""
    for match in _ATX_LEVEL2_SECTION_RE.finditer(text):
        if match.group("heading").strip() == heading:
            return match.group("body").strip()
    return None


def extract_last_markdown_section(text: str, heading: str) -> str | None:
    """Return the body of the last level-2 section with an exact heading match."""
    last: str | None = None
    for match in _ATX_LEVEL2_SECTION_RE.finditer(text):
        if match.group("heading").strip() == heading:
            last = match.group("body").strip()
    return last


def collect_level2_headings_in_order(text: str) -> list[str]:
    """Return level-2 ATX headings in document order."""
    return [match.group(1).strip() for match in _ATX_LEVEL2_HEADING_RE.finditer(text)]
