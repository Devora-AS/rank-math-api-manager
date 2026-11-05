# Long-run mission state — MAT env ignore + upstream SHA pin issue

**Last updated:** 2026-11-05

---

## Mission

- **Goal:** (1) Stop tracking/indexing live env credential files (`.mat.env` and `.env*` live variants) so PR #6 can merge green; (2) file an upstream MAT issue so approve/bootstrap pins to the planned `resolved_sha` (operator re-syncs later — no local `mat-sync.sh` fork).
- **execution_mode:** `long-run`
- **Success signals:** `.mat.env` ignored by git + Cursor; doctor/phase1 green for the slice; PR #6 CI green and merged; upstream GitHub issue created in `Devora-AS/multi-agent-workflow`.
- **Notes:** Parent-orchestrated in this chat; no nested parent-orchestrator subagent.

## Scope / hard constraints / non-goals

- **Hard constraints:** Keep local `.mat.env` on disk; never commit secrets; no force-push; do not implement `resolved_sha` pin in this product repo — issue only upstream.
- **Non-goals:** Local patch to `scripts/mat-sync.sh` for SHA pinning; broad cleanup of unrelated dirty trees; v1.0.9.2 packaging tasks; WordPress plugin feature work beyond what main already merged for CI green.

## Slice preflight decision (active)

- **execution_mode:** `builder_plus_verifier`
- **execution_rationale:** Ignore-file edits + verification + PR/CI closeout need delegated build/verify with file handoffs.

## Ordered slice queue

| # | Slice id | Summary | execution_mode | execution_rationale | Status |
|---|----------|---------|----------------|---------------------|--------|
| 1 | `env-secrets-ignore` | Ignore live `.mat.env` / `.env*` in `.gitignore` + `.cursorignore`; confirm `git check-ignore`; `git rm --cached` only if tracked; doctor + phase1; push to PR #6 head; loop-on-ci; merge when green | `builder_plus_verifier` | Config + CI closeout with handoffs | `active` |
| 2 | `upstream-resolved-sha-issue` | Create GitHub issue in `Devora-AS/multi-agent-workflow`: mat-sync pin approve/bootstrap to plan `resolved_sha` | `inline` | Single `gh issue create`; no product code change | `pending` |

## Active slice

- **Slice id:** `env-secrets-ignore`
- **Pointer:** `docs/current-plan.md`
- **Branch:** `chore/mat-env-secrets-ignore` (push updates PR #6 via `chore/mat-sync-refresh`)
- **execution_mode:** `builder_plus_verifier`
- **execution_rationale:** Path-scoped ignore hygiene + validation + merge gate.

## Completed slices

| Slice id | Outcome | `verify-result.md` reference | Notes |
|----------|---------|------------------------------|-------|
| | | | |

## Continuation policy

- After slice 1 verifier PASS + PR #6 merged: advance to slice 2 (upstream issue).
- After slice 2: `mission_complete`.
- Commit between slices; push only when CI/PR requires it (pre-approved for this mission).

## Stop-reason policy

| Stop reason | Meaning |
|-------------|---------|
| `mission_complete` | Both slices done (PR #6 merged + upstream issue filed). |
| `hard_blocker` | Cannot ignore files, CI blocked, or `gh` cannot open upstream issue. |
| `approval_needed` | Design conflict beyond approved GO. |
| `planning_gap` | Queue empty with work remaining. |
| `unexpected_termination` | Abnormal end. |

---

## Parent mission gate compliance (per verifier PASS)

- [ ] Gate questions answered or one explicit stop reason recorded.
- [ ] Slice PASS is not mislabeled as mission success while slice 2 remains.

---

## Current stop / continuation (living)

- **Last classified stop reason:** _(none — mission active)_
- **Continue:** `yes` — slice 1 in progress
