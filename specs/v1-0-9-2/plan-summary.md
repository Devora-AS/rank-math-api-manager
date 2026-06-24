# Plan Summary — v1.0.9.2 Release Hardening

**Package:** [`specs/v1-0-9-2/`](.)  
**Branch:** `feature/v1.0.9.2`  
**Planning slice:** Phase B complete (2026-06-24)  
**Phase C:** Ready — planning approved 2026-06-24; start TASK-001

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
3. ~~**php-lint scope mismatch**~~ — **resolved (OQ-005):** TASK-003 aligns `release.yml` maxdepth 5 with `qa.yml`.
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
| OQ-005 | resolved | Align `release.yml` find maxdepth **5** with `qa.yml` (TASK-003) |
| OQ-006 | resolved | **Single PR** `feature/v1.0.9.2` → `main`; logical local commits per TASK-### |

---

## PR strategy (OQ-006)

- **One pull request** from `feature/v1.0.9.2` to `main` for the full v1.0.9.2 release.
- Phase C may use **multiple logical local commits** mapped to TASK-001 … TASK-006 (and skip TASK-005 if deferred).
- Do not open separate PRs per task; squash is operator choice at merge time.

---

## Operator decisions (audit trail, 2026-06-24)

| ID | Decision |
|----|----------|
| OQ-005 | Align `release.yml` `find` maxdepth to **5** to match `qa.yml` so `tests/` PHP is linted on release path. |
| OQ-006 | **Single PR** to `main`; local commits per TASK during Phase C. |

---

## Recommended next steps

**Planning approved — proceed with Phase C:**

1. **Option A — Long-run mission:** `/mat-long-run` with mission goal “Ship v1.0.9.2 release hardening” and queue TASK-001 through TASK-006 (skip or defer TASK-005 explicitly).

2. **Option B — Per-slice execution:** `/mat-plan-team` once per TASK-###, projecting each task into `docs/current-plan.md` from this package.

**Explicit gate:** Planning **approved** 2026-06-24. Phase C may land WIP per `tasks.json`; push only when operator requests.

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

- [x] Operator reviewed `prd.md`, `spec.md`, `tasks.json`
- [x] Open questions acceptable (OQ-001/OQ-002 deferred; OQ-003–OQ-006 resolved)
- [x] Phase C execution authorized — start **TASK-001**

**Next:** `/mat-plan-team` or `/mat-long-run` for TASK-001; single PR strategy per OQ-006.
