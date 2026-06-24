# Long-run mission state

**Purpose:** Minimal valid mission state for adoption smoke fixtures and freshly bootstrapped repos.

**Last updated:** 2026-03-29

---

## Mission

- **Goal:** Validate the non-interactive adoption path in a temporary repository.
- **execution_mode:** `long-run`
- **Success signals:** workflow files are present, repo-level contract tests pass, and the fixture remains honest about runtime boundaries.

## Scope / hard constraints / non-goals

- **Hard constraints:** keep file-based MAO handoffs canonical; keep the fixture repo small; avoid staging session outputs under `artifacts/phase1/**`.
- **Non-goals:** live Cursor todo parity, hook-driven spawn from live todo state, or project-specific feature work.

## Slice preflight decision

- **execution_mode:** `inline`
- **execution_rationale:** adoption smoke uses the lightest honest execution mode. Other documented slice modes are `builder_plus_verifier` and `parallel_spawn`.

## Ordered slice queue

| # | Slice id | Summary | execution_mode | execution_rationale | Status |
|---|----------|---------|----------------|---------------------|--------|
| 1 | `adoption-smoke` | Validate workflow adoption in a temporary repo | `inline` | Smallest bounded fixture path | `pending` |
| 2 | `reserved-builder` | Reserved example row | `builder_plus_verifier` | Contract text only | `skipped` |
| 3 | `reserved-parallel` | Reserved example row | `parallel_spawn` | Contract text only | `skipped` |

## Active slice

- **Slice id:** `adoption-smoke`
- **Pointer:** `docs/current-plan.md`
- **execution_mode:** `inline`
- **execution_rationale:** temporary-repo smoke validation only.

## Completed slices

| Slice id | Outcome | `verify-result.md` reference | Notes |
|----------|---------|------------------------------|-------|
| | | | |

## Continuation policy

- **Default:** stop after the single adoption fixture slice.
- **MAO per slice:** if additional slices are added later, keep the canonical tags aligned with the active slice only.

## Stop-reason policy

| Stop reason | Meaning |
|-------------|---------|
| `mission_complete` | The adoption fixture is complete. |
| `hard_blocker` | A required dependency or tool is missing. |
| `approval_needed` | Human direction is required before continuing. |
| `planning_gap` | No next slice is defined and the mission is not complete. |
| `unexpected_termination` | The run ended abnormally. |

---

## Parent mission gate compliance (per verifier PASS)

**Honesty boundary:** Hooks do **not** enforce this gate. Compliance is parent-owned and prompt-disciplined, with regression coverage in `tests/test_workflow_docs.py`.

- [ ] Gate questions answered or one explicit stop reason recorded.
- [ ] If more slices are later added, queued work is not mislabeled as mission success.

---

## Current stop / continuation (living)

- **Last classified stop reason:** `planning_gap`
- **Continue:** `no`
