#!/usr/bin/env python3
"""Plugin hook launcher — advisory fail-open when the target script is missing.

Cursor may treat a missing ``python3 ./hooks/<script>.py`` invocation (Python exit 2)
as an explicit hook block even when ``failClosed`` is false. The team-marketplace
plugin routes hook commands through this launcher so incomplete installs (for example
during marketplace clone) do not block prompt submission.

Intentional blocks inside hook scripts (prompt validation, failClosed tools) are unchanged.
This launcher only skips when the entrypoint file is absent or the script name is unsafe.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent

# When skipping a missing script, emit the same allow-style stdout hooks expect.
_STDOUT_ON_SKIP: dict[str, object] = {
    "before_submit_prompt.py": {"continue": True},
}


def _safe_script_name(raw: str) -> str | None:
    name = os.path.basename(raw.strip())
    if not name or name != raw.strip() or ".." in raw or "/" in raw or "\\" in raw:
        return None
    if not name.endswith(".py"):
        return None
    return name


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "mat_hook_launcher: missing hook script name "
            "(usage: python3 mat_hook_launcher.py <script>.py)",
            file=sys.stderr,
        )
        sys.exit(0)

    script_name = _safe_script_name(sys.argv[1])
    if script_name is None:
        print(
            f"mat_hook_launcher: refusing unsafe hook script name: {sys.argv[1]!r}",
            file=sys.stderr,
        )
        sys.exit(0)

    target = HOOKS_DIR / script_name
    if not target.is_file():
        print(
            "mat_hook_launcher: hook script not found (incomplete plugin install?): "
            f"{target}",
            file=sys.stderr,
        )
        payload = _STDOUT_ON_SKIP.get(script_name)
        if payload is not None:
            print(json.dumps(payload))
        sys.exit(0)

    extra = sys.argv[2:]
    cmd = [sys.executable, str(target), *extra]
    completed = subprocess.run(cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
    sys.exit(completed.returncode)


if __name__ == "__main__":
    main()
