"""Safe `.mat.env.sample` merge for MAT-managed keys between MAT-tool markers."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BEGIN_MAT_TOOL = "# ─── MAT-tool ─────────────────────────────────────────────────────────────────"
END_MAT_TOOL = "# ─── /MAT-tool ────────────────────────────────────────────────────────────────"
API_KEYS_MARKER = "# ─── API Keys ───"

_ENV_SAMPLE_REL = ".mat.env.sample"


@dataclass(frozen=True, slots=True)
class EnvSampleMergePreview:
    eligible: bool
    merged_text: str | None
    skip_reason: str | None

    def as_plan_field(self) -> dict[str, Any] | None:
        if not self.eligible or self.merged_text is None:
            return None
        return {
            "path": _ENV_SAMPLE_REL,
            "changed": True,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "eligible": self.eligible,
            "skip_reason": self.skip_reason,
            "path": _ENV_SAMPLE_REL,
            "changed": self.merged_text is not None,
        }


def _resolve_upstream_sample(repo_root: Path, upstream_path: Path | None) -> Path | None:
    if upstream_path is not None and upstream_path.is_file():
        return upstream_path
    sidecar = repo_root / ".mat" / "docs" / "templates" / ".mat.env.sample"
    if sidecar.is_file():
        return sidecar
    script_primary = Path(__file__).resolve().parents[2] / ".mat.env.sample"
    if script_primary.is_file():
        return script_primary
    return None


def extract_mat_tool_inner(text: str) -> str | None:
    begin = text.find(BEGIN_MAT_TOOL)
    end = text.find(END_MAT_TOOL)
    if begin == -1 or end == -1 or end <= begin:
        return None
    inner_start = begin + len(BEGIN_MAT_TOOL)
    return text[inner_start:end].strip("\n")


def build_mat_tool_block(inner: str) -> str:
    body = inner.rstrip()
    return f"{BEGIN_MAT_TOOL}\n{body}\n{END_MAT_TOOL}" if body else f"{BEGIN_MAT_TOOL}\n{END_MAT_TOOL}"


def merge_env_sample_text(upstream_text: str, target_text: str) -> str:
    upstream_inner = extract_mat_tool_inner(upstream_text)
    if upstream_inner is None:
        upstream_inner = upstream_text.strip()

    new_block = build_mat_tool_block(upstream_inner)
    begin = target_text.find(BEGIN_MAT_TOOL)
    end = target_text.find(END_MAT_TOOL)
    if begin != -1 and end != -1 and end > begin:
        end_pos = end + len(END_MAT_TOOL)
        before = target_text[:begin].rstrip()
        after = target_text[end_pos:].strip("\n")
        parts = [part for part in (before, new_block, after) if part]
        return "\n\n".join(parts).rstrip() + "\n"

    api_idx = target_text.find(API_KEYS_MARKER)
    if api_idx != -1:
        before = target_text[:api_idx].rstrip()
        after = target_text[api_idx:].strip("\n")
        return "\n\n".join([before, new_block, after]).rstrip() + "\n"

    return target_text.rstrip() + "\n\n" + new_block + "\n"


def compute_env_sample_merge_preview(
    repo_root: Path,
    *,
    upstream_path: Path | None = None,
) -> EnvSampleMergePreview:
    target_path = repo_root / _ENV_SAMPLE_REL
    upstream = _resolve_upstream_sample(repo_root, upstream_path)
    if upstream is None:
        return EnvSampleMergePreview(eligible=False, merged_text=None, skip_reason="upstream .mat.env.sample missing")
    if not target_path.is_file():
        return EnvSampleMergePreview(
            eligible=True,
            merged_text=upstream.read_text(encoding="utf-8"),
            skip_reason=None,
        )

    target_text = target_path.read_text(encoding="utf-8")
    upstream_text = upstream.read_text(encoding="utf-8")
    merged = merge_env_sample_text(upstream_text, target_text)
    if merged == target_text:
        return EnvSampleMergePreview(eligible=False, merged_text=None, skip_reason="already up to date")
    return EnvSampleMergePreview(eligible=True, merged_text=merged, skip_reason=None)


def apply_env_sample_merge(
    repo_root: Path,
    *,
    upstream_path: Path | None = None,
    merged_text: str | None = None,
) -> dict[str, Any]:
    target_path = repo_root / _ENV_SAMPLE_REL
    if merged_text is None:
        preview = compute_env_sample_merge_preview(repo_root, upstream_path=upstream_path)
        if not preview.eligible or preview.merged_text is None:
            return {"applied": False, "reason": preview.skip_reason or "not eligible"}
        merged_text = preview.merged_text

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(merged_text, encoding="utf-8")
    return {"applied": True, "path": str(target_path)}


def compare_env_sample_for_update(
    source_path: Path,
    target_path: Path,
) -> tuple[bool, str | None]:
    """Return (needs_update, merged_text). needs_update False when identical after merge."""
    if not source_path.is_file():
        return False, None
    if not target_path.is_file():
        return True, source_path.read_text(encoding="utf-8")

    upstream_text = source_path.read_text(encoding="utf-8")
    target_text = target_path.read_text(encoding="utf-8")
    merged = merge_env_sample_text(upstream_text, target_text)
    if merged == target_text:
        return False, None
    return True, merged


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge MAT-tool section in .mat.env.sample")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--upstream", type=Path, default=None)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    preview = compute_env_sample_merge_preview(args.repo_root, upstream_path=args.upstream)
    if args.json:
        print(json.dumps(preview.as_dict(), indent=2, sort_keys=True))
    if args.apply:
        result = apply_env_sample_merge(
            args.repo_root,
            upstream_path=args.upstream,
            merged_text=preview.merged_text,
        )
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("applied") else 1
    return 0 if preview.eligible else 1


if __name__ == "__main__":
    raise SystemExit(main())
