# Native-first worktree wrapper (E10) v1

**Status:** Approved (slice 8, `/mat-long-run` 2026-08-24)
**Tier:** standard
**Task type:** `feature`
**Complexity:** `medium`
**ROADMAP:** E10

## Task Description

Ship safe bootstrap modes on `.cursor/hooks/bootstrap_worktree.sh`, document parity across Cursor-managed worktrees / `/worktree` / `/best-of-n` / manual `mat-wt-*`, and remove stale “automatic worktrees removed” claims.

## Objective

Make worktree bootstrap predictable: metadata-only by default (no network/package calls), explicit install mode when needed, and honest docs for Cursor-managed vs MAT-manual paths.

## Scope

### In scope

- Bootstrap modes `--metadata-only` | `--install` | `--check`
- Detect Cursor-managed context for logging; same MAT markers either path
- Document product vs MAT roles; hybrid defer
- Refuse dirty/unmerged exact-path removal unless forced
- Tracked `.cursor/worktrees.json.example`
- `tests/test_bootstrap_worktree_modes.py`

### Out of scope

- Deprecating `mat-wt-*`
- Proxying Cursor `/worktree` creation from a new MAT command
- Auto-purge beyond documented operator policy

## Assumptions

1. Cursor documents managed checkouts, `/worktree`, `/best-of-n`, and a ~25 worktree cap.
2. MAT owns bootstrap/health markers; Cursor owns isolation.
3. Exact branch/path targeting remains required for remove.

## Non-Goals

- Deprecating `mat-wt-*`
- Proxying Cursor `/worktree` creation from a new MAT command
- Auto-purge of worktrees beyond documented operator policy
- Secret values in tracked handoffs

## Problem Statement

MAT bootstrap always copies env material and runs package managers, which is surprising and network-heavy. Operator docs still imply Cursor cannot manage worktrees, while current Cursor documents Agents Window managed checkouts, `/worktree`, `/best-of-n`, and a default ~25 worktree cap.

## Solution Approach

1. Split bootstrap into `--metadata-only` (default), `--install`, and `--check`.
2. Detect Cursor-managed context (`ROOT_WORKTREE_PATH`, path heuristics) for logging; same MAT markers either path.
3. Document product vs MAT roles; keep hybrid defer (MAT = bootstrap/health, Cursor = isolation).
4. Refuse dirty/unmerged exact-path removal unless explicitly forced.
5. Tracked `.cursor/worktrees.json.example` showing native `setup-worktree*` keys with metadata-only default.

## Relevant Files / Areas

- [existing] `.cursor/hooks/bootstrap_worktree.sh`
- [existing] `.cursor/commands/mat-wt-{create,list,check,remove}.md`
- [existing] `.cursor/skills/{create-worktree,worktree-manager}/SKILL.md`
- [new] `.cursor/worktrees.json.example`
- [new] `tests/test_bootstrap_worktree_modes.py`
- [existing] `docs/reference/decision-record.md` (refresh Context; keep hybrid defer)

## Task Traceability

| ID | Statement |
|----|-----------|
| SPEC-E10-01 | Metadata-only makes zero network/package calls |
| SPEC-E10-02 | Managed + manual produce same MAT markers |
| ROADMAP | E10 Native-first worktree wrapper |

## Testing Strategy

Re-run each phase command and loop until pass before advancing.

### Per-phase validation loops (loop until pass)

| Phase | Command | Loop until pass |
|-------|---------|-----------------|
| Unit | `python3 -m unittest tests.test_bootstrap_worktree_modes -v` | exit 0 — loop until pass |
| Docs contract | `python3 -m unittest tests.test_workflow_docs.WorktreeContractDocsTest tests.test_workflow_docs.P2OrchestrationStrategyDocsTest -v` | exit 0 — loop until pass |
| Full | `bash scripts/phase1-verify.sh --profile source-full` | exit 0 — loop until pass |

### Global validation commands (before handoff)

1. `python3 -m unittest tests.test_bootstrap_worktree_modes -v`
2. `bash scripts/phase1-verify.sh --profile source-full`

## Acceptance Criteria

- **AC-1:** `--metadata-only` makes zero network/package-manager calls.
- **AC-2:** `--install` prints planned commands before executing; `--check` validates markers.
- **AC-3:** Managed + manual produce the same `.cursor/worktree/*` markers.
- **AC-4:** Docs cover `/worktree`, `/best-of-n`, `mat-wt-*`; no stale “automatic worktrees removed” on operator surfaces.
- **AC-5:** Cleanup notes Cursor `cursor.worktreeMaxCount` (default 25); dirty remove requires force.
- **AC-6:** `bash scripts/phase1-verify.sh --profile source-full` green.

## Risks and Open Questions

- Cursor-managed path detection may need updates when product env vars change.
- Destructive remove remains confirmation-gated (see E5 command registry).

## Amendments

- 2026-08-24T12:10:00Z — builder — Retrofitted Tier 2 section contract during slice 7 planning-validator hygiene.

## Recommended Next Command

```txt
/mat-long-run continue slice 8 — implement E10 worktree wrapper when that slice is active
```
