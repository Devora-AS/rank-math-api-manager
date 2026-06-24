# Plan Summary — v1.0.9.2 Release Hardening

**Package:** [`specs/v1-0-9-2/`](.)  
**Branch:** `feature/v1.0.9.2`  
**Planning slice:** Phase B complete (2026-06-24)  
**Phase C:** Not started — requires operator approval before execution

---

## Goal

Produce a traceable, approved planning package for landing v1.0.9.2 release-hardening WIP (CI/QA, packaging, icons, page support, integration tests, docs) without implementing Phase C in the planning slice.

---

## Slice overview (from `tasks.json`)

| Task | Title | Depends on | Status |
|------|-------|------------|--------|
| TASK-001 | Version and documentation sync | — | planned |
| TASK-002 | Land QA toolchain files | TASK-001 | planned |
| TASK-003 | Land CI workflows and align release lint scope | TASK-002 | planned |
| TASK-004 | Land packaging, icons, and integration verification | TASK-003 | planned |
| TASK-005 | PHPCS main-file follow-up (optional) | TASK-004 | planned (deferred) |
| TASK-006 | Release smoke and PR checklist | TASK-004 | planned |

**Critical path:** TASK-001 → TASK-002 → TASK-003 → TASK-004 → TASK-006.  
TASK-005 is optional and may be skipped for v1.0.9.2.

---

## Top risks

1. **Uncommitted WIP drift** — Large untracked set (qa.yml, composer, tests, icons); Phase C must land atomically enough that CI passes on first PR run.
2. **Stale operator docs** — `docs/v1.0.9.2-plan-status.md` contradicts `qa.yml` on PHPUnit-in-CI; reconciled in spec (OQ-004 resolved); update plan-status during TASK-003 if desired.
3. **php-lint scope mismatch** — `release.yml` maxdepth 3 vs `qa.yml` maxdepth 5 (OQ-005 open); misalignment could hide syntax errors in `tests/` on release-only path.
4. **PHPCS main file excluded** — Ship risk is style debt, not functional; deferred TASK-005.
5. **Icon design** — Placeholders ship; brand motif deferred (OQ-001).

---

## Open questions summary

| ID | Status | Summary |
|----|--------|---------|
| OQ-001 | deferred | Icon design final pass |
| OQ-002 | deferred | PHPCS main-file re-include |
| OQ-003 | resolved | docs/README.md → 1.0.9.2 in TASK-001 |
| OQ-004 | resolved | PHPUnit runs in CI via qa.yml |
| OQ-005 | open | Align release.yml php-lint depth with qa.yml |
| OQ-006 | open | Single PR vs per-task commits (operator choice) |

---

## Recommended next steps

**After human approval of this package:**

1. **Option A — Long-run mission:** `/mat-long-run` with mission goal “Ship v1.0.9.2 release hardening” and queue TASK-001 through TASK-006 (skip or defer TASK-005 explicitly).

2. **Option B — Per-slice execution:** `/mat-plan-team` once per TASK-###, projecting each task into `docs/current-plan.md` from this package.

**Explicit gate:** Planning approved → operator runs Phase C separately. The planning slice did **not** land WIP files, commit, or push.

---

## Projection instructions (`docs/current-plan.md`)

When starting Phase C, the operator/parent should:

1. Set **Slice** to the active `TASK-###` title and link `specs/v1-0-9-2/`.
2. Copy **acceptance criteria** from the task’s `prd_ids` / `spec_ids` into binary checkboxes.
3. List **concrete file paths** from `spec.md` for that task only (narrow context).
4. Set **Validation plan** to commands from spec (e.g. `composer install`, `vendor/bin/phpunit`, `bash scripts/package-plugin.sh`, or “CI on PR”).
5. Update `tasks.json` **status** for the active task: `in_progress` → `done` (parent-owned sync per mat-plan-onboarding contract).
6. Keep **Non-goals** from `prd.md` (no MAT adoption, no `.cursor` policy, no RFU-7).

Example projection header for TASK-003:

```markdown
## Slice
**TASK-003** — Land CI workflows (specs/v1-0-9-2/)
**Phase C:** in progress
```

---

## Operator context files (existing)

- [`docs/PR-CHECKLIST-v1.0.9.2.md`](../../docs/PR-CHECKLIST-v1.0.9.2.md)
- [`docs/v1.0.9.2-plan-status.md`](../../docs/v1.0.9.2-plan-status.md) — partial stale; prefer `spec.md` SPEC-002
- [`docs/orchestration-v1.0.9.2.json`](../../docs/orchestration-v1.0.9.2.json) — historical worktree map; superseded by `tasks.json` for execution order

---

## Approval gate

- [ ] Operator reviewed `prd.md`, `spec.md`, `tasks.json`
- [ ] Open questions acceptable (deferred items documented)
- [ ] Phase C execution authorized

**Until checked:** Do not land untracked WIP or open release PR.
