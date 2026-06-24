#!/usr/bin/env python3
"""Restore a mission-level execution_mode in docs/long-run-state.md when safely possible."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


MISSION_SECTION_RE = re.compile(
    r"^##\s+Mission\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)
VALID_EXECUTION_MODE_RE = re.compile(
    r"^\s*-\s+\*\*execution_mode:\*\*\s+`(short-run|long-run)`\s*$",
    re.MULTILINE,
)
ANY_EXECUTION_MODE_RE = re.compile(r"\*\*execution_mode:\*\*")

REMEDIATION = """migrate-long-run-state: docs/long-run-state.md needs a mission-level execution mode.
Add this bullet under `## Mission`:
  - **execution_mode:** `long-run`
See `docs/getting-started-existing-projects.md` for the non-interactive adoption path.
"""


def extract_mission_section(text: str) -> str | None:
    match = MISSION_SECTION_RE.search(text)
    if not match:
        return None
    return match.group("body")


def needs_migration(text: str) -> bool:
    mission_section = extract_mission_section(text)
    if mission_section is None:
        return True
    return VALID_EXECUTION_MODE_RE.search(mission_section) is None


def migrate(text: str) -> str | None:
    match = MISSION_SECTION_RE.search(text)
    if not match:
        return None

    mission_section = match.group("body")
    if VALID_EXECUTION_MODE_RE.search(mission_section):
        return None
    if ANY_EXECUTION_MODE_RE.search(mission_section):
        return None

    insertion = match.start("body")
    return text[:insertion] + "- **execution_mode:** `long-run`\n" + text[insertion:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, help="Path to docs/long-run-state.md")
    args = parser.parse_args()

    path = args.path.resolve()
    if not path.exists():
        print(f"migrate-long-run-state: missing file {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    if not needs_migration(text):
        print(f"migrate-long-run-state: already valid: {path}")
        return 0

    new_text = migrate(text)
    if new_text is None:
        print(REMEDIATION, file=sys.stderr)
        return 2

    path.write_text(new_text, encoding="utf-8")
    print(f"migrate-long-run-state: wrote mission execution_mode into {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
