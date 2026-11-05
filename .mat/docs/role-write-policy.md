# Role write policy (ADR) — parent-owned verify handoff

**Status:** Accepted (D2 / E2, 2026-08-24)  
**Spec:** [`specs/role-scope-audit-v1.md`](../../specs/role-scope-audit-v1.md)  
**Related:** [`workflow-artifact-contract.md`](workflow-artifact-contract.md), `scripts/mat-scope-audit.py`

## Context

MAT documented the verifier as read-only while also requiring it to write `verify-result.md`. Cursor’s native subagent `readonly: true` blocks **all** writes, so “read-only except the verify handoff” is not expressible. Builder/verifier boundaries were prose-only with no start/stop audit trail.

## Decision

Adopt **parent-owned verify handoff**:

1. **Verifier** uses frontmatter `readonly: true` and returns a **structured verify payload** in subagent output. It does **not** write `verify-result.md`.
2. **Parent orchestrator** serializes `verify-result.md` from that structured output (must match the verify contract).
3. **Scope audit** (advisory) snapshots git porcelain at subagent start/stop, diffs introduced paths against per-role allowlists, and writes JSON under `artifacts/mao/scope-audit/` (gitignored). Hooks stay **fail-open** (`exit 0`).

## Per-role write allowlists (v1)

| Role | Allowed writes (beyond pre-existing dirty) |
|------|---------------------------------------------|
| `builder` | Plan-listed implementation paths + `build-result.md` (+ `docs/current-plan.md` marker mutations) |
| `verifier` | _(none — readonly)_ |
| `parent-orchestrator` | `verify-result.md`, `docs/current-plan.md`, mission state (`docs/architecture/long-run-state.md`, `docs/session-summary.md`) |

**Stop-hook runtime projection (D2b):** On `SubagentStop`, `.cursor/hooks/subagent_stop.py` extends the builder allowlist with (1) MAO `handoff_inputs` and `primary_artifact`, and (2) paths parsed from the active plan (`docs/current-plan.md` by default) via `plan_listed_paths()` in `scripts/mat-scope-audit.py` (Relevant Files / Implementation path bullets). Verifier gets no plan-path projection. Protected paths always breach even if listed.

## Protected paths (global)

Always treated as breaches (even if listed in an allowlist):

- `.env`, `.mat.env`, and common credential/secret filename patterns

Optional future: operator extend via `artifacts/mao/scope-protected-paths.json`.

## Consequences

- Gate-authoritative `verify-result.md` remains on disk and parent-owned; MAO and validators unchanged in authority.
- Verifier prompts and `MAO_TASK_CONTEXT_JSON` may still name `verify-result.md` as the **logical** primary artifact; the **writer** is the parent.
- Scope audit never auto-reverts files and never blocks the agent; hook exit stays **0** (fail-open).
- **D2c canonical scope gate:** Parent issues a bounded `run_id` (`issue-run`) before builder dispatch and records `artifacts/mao/scope-audit/active-builder-run.json`. After builder stop, parent and readonly verifier evaluate `gate --run-id <id>` (helper: `evaluate_canonical_builder_scope_gate()`). **Protected-path breaches** and **ordinary out-of-scope writes** force canonical `verify-result.md` **FAIL** when correlation matches the active run. Missing, malformed, stale, or mismatched audit evidence also forces **FAIL** (never silent pass). Hooks remain advisory; only the parent serializes `verify-result.md`.
- Builder stop-hook allowlists include plan-listed implementation paths so operational start/stop audits match the ADR allowlist prose.
- CLI: `python3 scripts/mat-scope-audit.py check --self-test` (wired into `phase1-verify` `scope_audit` check on source profiles); D2c: `issue-run`, `gate`.

## Alternatives considered

- **Verifier may write only `verify-result.md`:** Rejected — Cursor `readonly` is all-or-nothing; partial allowlists would be prose-only without native enforcement.
- **Auto-revert on breach:** Rejected — risk of destroying concurrent work; report-only for v1.
