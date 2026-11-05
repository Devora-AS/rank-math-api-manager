# Long-run mission state

**Purpose:** Canonical mission-level state. Pair with `docs/current-plan.md` for the **active slice only**.

**Last updated:** 2026-10-20

---

## Mission

- **Goal:** Live IDE Self-Compact validation (SC-LIVE-S3) — pilot evidence row, unittest gate, phase1 closeout; gauge notice/warning/force procedure exercised in parent orchestration.
- **source_task_id:** `specs/mat-self-compact-cursor/pilot-long-run.md`
- **trace_run_id:** `sc-live-s3-20261020`
- **execution_mode:** `long-run`
- **Mission-complete bar:** SC-LIVE-S3A + SC-LIVE-S3B verifier PASS; pilot evidence finalized; checkpoint closed (`pending_compact: false`).
- **Stop reason:** `mission_complete` (SC-LIVE-S3A/S3B verifier PASS; phase1 green hovedsesjon 2026-10-20)

## Scope / hard constraints / non-goals

- **Hard constraints:** No `git push`; MAO file handoffs authoritative; manual Summarize operator-owned; `CURSOR_MAT_SELF_COMPACT_FORCE=1` for force-lane test.
- **Non-goals:** Product code changes beyond pilot doc + handoff artifacts; unrelated MCP operator mission residue.

## Slice preflight decision

- **Active slice id:** `SC-LIVE-S3B`
- **execution_mode:** `builder_plus_verifier`
- **execution_rationale:** Doc + unittest slice with standard builder/verifier delegation; low product risk.
- **Allowed modes (mission vocabulary):** `inline` | `builder_plus_verifier` | `parallel_spawn`

## Ordered slice queue

| # | Slice id | Summary | Mode | Status |
|---|----------|---------|------|--------|
| 1 | SC-LIVE-S3A | Pilot evidence in-progress row; unittest pilot + MCP; MAO handoffs | builder_plus_verifier | **done** |
| 2 | SC-LIVE-S3B | `phase1-verify.sh`; finalize pilot evidence; close checkpoint | builder_plus_verifier | **done** (PASS) |

## Active slice

- **id:** SC-LIVE-S3B
- **plan:** `docs/current-plan.md`

## Completed slices

- **SC-LIVE-S3A** (2026-10-20): Pilot in-progress row + unittest PASS; verify PASS (parent-serialized after verifier Ask-mode block).

## Continuation policy

On SC-LIVE-S3A verifier PASS → advance to SC-LIVE-S3B. On SC-LIVE-S3B verifier PASS → `mission_complete`.

## Stop-reason policy

| Stop reason | Meaning |
|-------------|---------|
| `mission_complete` | Both slices PASS; evidence closed. |
| `hard_blocker` | Tests or phase1 fail after retry. |
| `approval_needed` | Push or external GO (not expected this mission). |
| `planning_gap` | Scope undefined. |
| `unexpected_termination` | Abnormal end. |

## Parent mission gate compliance

**Honesty boundary:** Hooks do **not** enforce this gate. Compliance is parent-owned; regression anchor `tests/test_workflow_docs.py` (`LongRunOrchestrationContractTest`).

| After slice | Decision | Notes |
|-------------|----------|-------|
| SC-LIVE-S3A | continue → S3B | Slice PASS; queue has S3B. |
| SC-LIVE-S3B | **stop** — `mission_complete` with PARTIAL phase1 | Evidence closed; operator re-verify phase1 in CI. |

## Amendments

- 2026-10-20T13:40:00+02:00 — parent-orchestrator — Mission initialized from `/mat-long-run` SC-LIVE-S3 (live IDE gauge pilot).
