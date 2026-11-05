---
name: mat-self-compact
description: MAT Self-Compact procedure — checkpoint context into gitignored handoff files before Cursor compaction.
---

# MAT Self-Compact (v1 + v2 MCP)

Use when context pressure is rising (gauge **notice** ≥ 55%, **warning** ≥ 70%, **force** ≥ 85% with opt-in force lane) or after native compaction.

## Prerequisites

- Opt-in hooks: `CURSOR_MAT_SELF_COMPACT=1` in `.mat.env` (see [`docs/reference/configuration.md`](../../../.mat/docs/configuration.md)).
- Optional PreToolUse spike: `CURSOR_MAT_SELF_COMPACT_LOG_PRETOOL=1` logs gauge samples to `artifacts/context-handoff/pre-tool-context-usage.jsonl`.
- Optional MCP (operator local config): `view_context` and `mat_self_compact` via stdio server `scripts/mcp/mat_self_compact_server.py` (MAT **source** tree only; adopted repos use gauge CLI or operator MCP snippet in [`docs/security/mcp.md`](../../../docs/security/mcp.md)) — requires `mcp` Python package.
- MAO handoffs stay **authoritative** over conversation memory and MCP output.

## Procedure

1. **Write checkpoint** — `artifacts/context-handoff/note-to-self.md` with intent, open decisions, next commands, and pointers to MAO files.
2. **Refresh orchestration files** — update `docs/current-plan.md` markers, `build-result.md` / `verify-result.md` if mid-slice.
3. **Run gauge** — `python3 scripts/mat-context-gauge.py` or MCP `view_context` (Pi-like JSON: `percent`, `level`, `pending_compact`).
4. **Optional state** — set `artifacts/context-handoff/context-state.json` (`pending_compact`, cycle count) when coordinating with hooks.
5. **Compaction honesty** — Cursor has **no** agent API to invoke summarization; ask the operator for manual **Summarize** / wait for auto compact. `preCompact` is observe-only (cannot steer summary text).

## After preCompact

Hooks may set `pending_compact`. Complete the procedure, then clear `pending_compact` in `context-state.json` when the checkpoint is done.

## References

- Spec: [`specs/mat-self-compact-cursor.md`](../../../specs/mat-self-compact-cursor.md)
- Pilot: [`specs/mat-self-compact-cursor/pilot-long-run.md`](../../../specs/mat-self-compact-cursor/pilot-long-run.md)
- Playbook: [`docs/guides/mat-operator-playbook.md`](../../../.mat/docs/guides/mat-operator-playbook.md) § B10
- Context budget: [`docs/reference/context-budget-policy.md`](../../../.mat/docs/context-budget-policy.md)
