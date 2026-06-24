#!/usr/bin/env python3
"""Cost & context hygiene pack — structured validation (CI + --report doctor mode)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Literal

Severity = Literal["FAIL", "WARN", "INFO"]
EnforceMode = Literal["strict", "warn_first", "auto"]

RULE_REL = Path(".cursor/rules/cost-context-hygiene.mdc")
IGNORE_REL = Path(".cursorignore")
# Canonical template (generic fallback) + stack variants
TEMPLATE_DEFAULT_REL = Path("docs/templates/cursorignore-mat-default")
# Back-compat for tests and scripts that import TEMPLATE_REL
TEMPLATE_REL = TEMPLATE_DEFAULT_REL
ALL_TEMPLATE_RELS: Final[tuple[Path, ...]] = (
    TEMPLATE_DEFAULT_REL,
    Path("docs/templates/cursorignore-mat-node"),
    Path("docs/templates/cursorignore-mat-python"),
    Path("docs/templates/cursorignore-mat-wordpress"),
    Path("docs/templates/cursorignore-mat-rails"),
    Path("docs/templates/cursorignore-mat-shared.inc"),
)
ADOPTION_REL = Path(".mat/cost-hygiene-adoption.json")
BEFORE_SUBMIT_REL = Path(".cursor/hooks/before_submit_prompt.py")

# Honesty + contract strings (see `.cursor/rules/cost-context-hygiene.mdc`)
RULE_REQUIRED_SUBSTRINGS: tuple[str, ...] = (
    "alwaysApply: true",
    "description:",
    "@file",
    "@Codebase",
    "docs/context-budget-policy.md",
    "docs/current-plan.md",
    "docs/model-routing-policy.md",
    "cannot block",
)

# Verifier / orchestration handoff (contract AC — stay narrow)
VERIFIER_SUBSTRINGS: tuple[str, ...] = (
    "verifier",
    "build-result",
)

CURSORIGNORE_REQUIRED_FRAGMENTS: tuple[str, ...] = (
    "node_modules",
    "dist/",
    "build/",
    "coverage/",
    "__pycache__",
    "*.log",
    ".env",
)


@dataclass(frozen=True, slots=True)
class Finding:
    code: str
    severity: Severity
    message: str
    path: str | None = None
    data: dict[str, Any] | None = None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _resolve_template_path(repo_root: Path, rel: Path) -> Path | None:
    """Prefer ``docs/templates/<basename>``; else ``.mat/docs/templates/<basename>`` (adopted layout)."""
    basename = rel.name
    primary = repo_root / "docs" / "templates" / basename
    if primary.is_file():
        return primary
    alt = repo_root / ".mat" / "docs" / "templates" / basename
    if alt.is_file():
        return alt
    return None


def _load_adoption(repo_root: Path) -> dict[str, Any] | None:
    p = repo_root / ADOPTION_REL
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _resolve_effective_enforce(
    repo_root: Path, cli: EnforceMode
) -> Literal["strict", "warn_first"]:
    if cli in ("strict", "warn_first"):
        return cli
    env = os.environ.get("CURSOR_MAT_COST_HYGIENE_ENFORCE", "").strip().lower()
    if env in ("strict", "warn_first"):
        return env  # type: ignore[return-value]
    adoption = _load_adoption(repo_root)
    if adoption and adoption.get("enforcement") in ("strict", "warn_first"):
        return adoption["enforcement"]  # type: ignore[return-value]
    return "strict"


def _warn_first_existing(adoption: dict[str, Any] | None, eff: str) -> bool:
    if eff != "warn_first" or not adoption:
        return False
    return adoption.get("bootstrap_mode") == "existing-project"


def _before_submit_empty_blockedlist(repo_root: Path) -> bool:
    p = repo_root / BEFORE_SUBMIT_REL
    if not p.is_file():
        return False
    in_list = False
    for line in _read_text(p).splitlines():
        if "blocked_patterns" in line and ": list" in line and "=" in line:
            in_list = True
            continue
        if in_list:
            t = line.strip()
            if t.startswith("]"):
                break
            if not t or t.startswith("#"):
                continue
            if t.startswith("("):
                return False
    return in_list


def analyze_pack(
    repo_root: Path, *, effective_enforce: Literal["strict", "warn_first"]
) -> list[Finding]:
    """Return structured findings (use effective_enforce for severity mapping)."""
    out: list[Finding] = []
    adoption = _load_adoption(repo_root)
    wfe = _warn_first_existing(adoption, effective_enforce)
    eff = effective_enforce
    # --- rule ---
    rule_path = repo_root / RULE_REL
    if not rule_path.is_file():
        out.append(
            Finding(
                "pack.missing_rule", "FAIL", f"missing rule file: {RULE_REL}", str(RULE_REL)
            )
        )
    else:
        body = _read_text(rule_path)
        for needle in RULE_REQUIRED_SUBSTRINGS:
            if needle not in body:
                out.append(
                    Finding(
                        "pack.rule_honesty_substring",
                        "FAIL",
                        f"rule file missing required substring {needle!r}: {RULE_REL}",
                        str(RULE_REL),
                        {"needle": needle},
                    )
                )
        for needle in VERIFIER_SUBSTRINGS:
            if needle not in body.lower():
                out.append(
                    Finding(
                        "pack.rule_verifier_accountability",
                        "FAIL",
                        f"rule file missing accountability phrase {needle!r}: {RULE_REL}",
                        str(RULE_REL),
                    )
                )

    # --- all templates (MAT pack completeness) ---
    for trel in ALL_TEMPLATE_RELS:
        tpath = _resolve_template_path(repo_root, trel)
        path_disp = str(tpath.relative_to(repo_root)) if tpath is not None else str(trel)
        if tpath is None or not tpath.is_file():
            out.append(
                Finding(
                    "pack.missing_template",
                    "FAIL",
                    f"missing template file: {trel}",
                    path_disp,
                )
            )
            continue
        ttext = _read_text(tpath)
        for frag in CURSORIGNORE_REQUIRED_FRAGMENTS:
            if frag not in ttext:
                out.append(
                    Finding(
                        "pack.template_fragment",
                        "FAIL",
                        f"template {trel} missing required fragment {frag!r}",
                        path_disp,
                    )
                )
        low = ttext.lower()
        if "escape hatch" not in low:
            out.append(
                Finding(
                    "pack.template_escape_hatch",
                    "FAIL",
                    f"template {trel} must include an escape hatch paragraph",
                    path_disp,
                )
            )

    # --- root .cursorignore ---
    ignore_path = repo_root / IGNORE_REL
    if not ignore_path.is_file():
        out.append(
            Finding(
                "pack.missing_root_cursorignore",
                "FAIL",
                f"missing root cursorignore: {IGNORE_REL}",
                str(IGNORE_REL),
            )
        )
    else:
        itext = _read_text(ignore_path)
        for frag in CURSORIGNORE_REQUIRED_FRAGMENTS:
            if frag not in itext:
                sev: Severity = "FAIL"
                if wfe:
                    sev = "WARN"
                out.append(
                    Finding(
                        "pack.root_cursorignore_fragment",
                        sev,
                        f".cursorignore missing recommended fragment {frag!r} "
                        f"({'warn_first existing-project' if wfe else 'strict'})",
                        str(IGNORE_REL),
                    )
                )
        if "escape hatch" not in itext.lower() and "escape" not in itext.lower():
            sev2: Severity = "WARN" if wfe else "INFO"
            out.append(
                Finding(
                    "pack.root_cursorignore_escape_note",
                    sev2,
                    "root .cursorignore has no 'escape hatch' phrasing; prefer aligning with a MAT template or documenting narrowing policy",
                    str(IGNORE_REL),
                )
            )

    # --- CURSOR_VALIDATE_PROMPTS vs empty list (advisory) ---
    env_sample = repo_root / ".env.sample"
    validate_enabled_in_sample = False
    if env_sample.is_file():
        for line in _read_text(env_sample).splitlines():
            s = line.strip()
            if s.startswith("CURSOR_VALIDATE_PROMPTS=") and "true" in s.split("=", 1)[-1].lower():
                validate_enabled_in_sample = True
    if (repo_root / BEFORE_SUBMIT_REL).is_file() and _before_submit_empty_blockedlist(repo_root):
        msg = (
            "before_submit_prompt has an empty `blocked_patterns` list; with "
            "`CURSOR_VALIDATE_PROMPTS=true` validation is a no-op until you add patterns"
        )
        sev3: Severity = "INFO"
        if validate_enabled_in_sample:
            sev3 = "WARN"
        out.append(Finding("pack.validate_prompts_noop", sev3, msg, str(BEFORE_SUBMIT_REL)))

    return out


def _write_report_artifacts(
    repo_root: Path, findings: list[Finding], effective_enforce: str
) -> None:
    out = repo_root / "artifacts" / "cost-hygiene"
    out.mkdir(parents=True, exist_ok=True)
    rep = {
        "effective_enforce": effective_enforce,
        "summary": {
            "fail": sum(1 for f in findings if f.severity == "FAIL"),
            "warn": sum(1 for f in findings if f.severity == "WARN"),
            "info": sum(1 for f in findings if f.severity == "INFO"),
        },
        "findings": [asdict(f) for f in findings],
    }
    (out / "last-report.json").write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
    line = json.dumps({**rep, "ts_utc": datetime.now(timezone.utc).isoformat()})
    with (out / "report-events.jsonl").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _print_findings(findings: list[Finding], *, warn_only: bool) -> None:
    for f in findings:
        if warn_only and f.severity == "INFO":
            continue
        pfx = f.severity
        loc = f" {f.path}" if f.path else ""
        print(f"{pfx}{loc}: {f.message} [{f.code}]", file=sys.stdout)


def validate_pack(repo_root: Path) -> list[str]:
    """Backward-compatible: messages for FAIL-level findings (auto/strict for unknown repos)."""
    eff = _resolve_effective_enforce(repo_root, "auto")
    return [f.message for f in analyze_pack(repo_root, effective_enforce=eff) if f.severity == "FAIL"]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    p.add_argument(
        "--enforce",
        choices=("strict", "warn_first", "auto"),
        default="auto",
        help="Enforcement mode (auto reads .mat/cost-hygiene-adoption.json, then env CURSOR_MAT_COST_HYGIENE_ENFORCE, else strict).",
    )
    p.add_argument(
        "--report",
        action="store_true",
        help="Print all findings, write artifacts/cost-hygiene/last-report.json and append report-events.jsonl",
    )
    p.add_argument(
        "--warn-only",
        action="store_true",
        help="Omit INFO lines from printed output; implies --no-fail (exit 0).",
    )
    p.add_argument(
        "--no-fail",
        action="store_true",
        help="Do not exit 1 when FAIL findings exist (doctor / local advisory)",
    )
    p.add_argument("--diagnostic", action="store_true", help="Alias for --no-fail")
    args = p.parse_args()
    repo_root = args.repo_root.resolve()
    no_fail = bool(args.no_fail or args.diagnostic or args.warn_only)
    eff = _resolve_effective_enforce(repo_root, args.enforce)  # type: ignore[arg-type]
    findings = analyze_pack(repo_root, effective_enforce=eff)
    if args.report:
        _print_findings(findings, warn_only=bool(args.warn_only))
        _write_report_artifacts(repo_root, findings, eff)
    elif args.warn_only:
        _print_findings(findings, warn_only=True)

    has_fail = any(f.severity == "FAIL" for f in findings)
    if not no_fail and has_fail:
        if not args.report and not args.warn_only:
            print("cost_context_hygiene_pack: FAIL", file=sys.stderr)
            for f in findings:
                if f.severity == "FAIL":
                    pth = f" {f.path}" if f.path else ""
                    print(f"  {f.severity}{pth}: {f.message}", file=sys.stderr)
        return 1
    if not args.report and not args.warn_only:
        print("cost_context_hygiene_pack: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
