# Current plan — Ignore live MAT/env secrets (PR #6 Codex finding 1)

**Status:** Active orchestration slice
**Tier:** standard (execution projection)
**Contract:** v0.1 — [`.mat/docs/plan-contract.md`](../.mat/docs/plan-contract.md)
**Preflight:** `builder_plus_verifier`
**Last updated:** 2026-11-05
**Branch:** `chore/mat-env-secrets-ignore`
**Mission:** `docs/architecture/long-run-state.md` slice `env-secrets-ignore`
**PR target:** Update https://github.com/Devora-AS/rank-math-api-manager/pull/6 then merge when green

---

## Task

Make live environment credential files untracked and unindexed: add `.mat.env` (and related live `.env*` / `.mat.env*` variants) to root `.gitignore` and `.cursorignore`, keep samples (`.mat.env.sample`, `.env.sample`) tracked/visible, confirm with `git check-ignore -v .mat.env`, remove from index with `git rm --cached` only if ever tracked (do **not** delete the local file), then re-run `bash scripts/doctor.sh` and `bash scripts/phase1-verify.sh`. Parent owns push to PR #6 head, CI loop, and merge.

## Verified root cause (re-checked)

- `.mat.env.sample` line 2 claims `.mat.env` is gitignored.
- Root `.gitignore` lists several `.env*` names but **not** `.mat.env` / `.mat.env.local`.
- Root `.cursorignore` has `.env` and `.env.*` (with `!.env.sample`) but **not** `.mat.env` (filename does not match `.env.*`).
- `git ls-files` / history: `.mat.env` was **never** committed on this branch; local `?? .mat.env` is expected until ignore rules land.
- PR #6 prior Plugin Check failure (`outdated_tested_upto_header` 7.0 < 7.1) and early textdomain notice are addressed by already-merged `main` (Issue #5 / PR #7); this branch already contains `merge(main)` at `3c1b540`.

## Non-goals

- Implementing `resolved_sha` pin in `scripts/mat-sync.sh` (slice 2 = upstream issue only)
- Deleting or rewriting local `.mat.env` contents
- Broad `/cleanup` purge of unrelated artifacts
- Changing WordPress plugin PHP beyond what `main` already provides for CI

## Context

| Anchor | Role |
|--------|------|
| PR #6 Codex review | Finding 1 — unignored `.mat.env` |
| `.gitignore` / `.cursorignore` | Ignore surfaces |
| `.mat.env.sample` | Sample must remain tracked |
| `scripts/doctor.sh` / `scripts/phase1-verify.sh` | Validation |
| PR #6 | Merge target after green CI |

## Implementation steps

- [x] **Step 1 — Extend `.gitignore`**
  - Under Environment files (and/or MAT section): ignore live `.mat.env`, `.mat.env.local`, and keep broad live env coverage (e.g. `.env`, `.env.*`, `.mat.env.*`) with negations so `.env.sample`, `.mat.env.sample`, and `**/.mat.env.sample` stay trackable.

- [x] **Step 2 — Extend `.cursorignore`**
  - Mirror live-env ignores for indexing: `.mat.env`, `.mat.env.*` (and existing `.env` / `.env.*`), with `!.env.sample` and `!.mat.env.sample` (and `!**/.mat.env.sample` if needed).

- [x] **Step 3 — Index hygiene**
  - If `git ls-files --error-unmatch .mat.env` succeeds: `git rm --cached .mat.env` (keep working tree file).
  - Confirm: `git check-ignore -v .mat.env` prints a matching rule.

- [x] **Step 4 — Validation**
  - `bash scripts/doctor.sh`
  - `bash scripts/phase1-verify.sh`
  - Low-risk slice-related `/update-docs` note only if README/CHANGELOG truly need a one-line hygiene mention; skip drive-by docs.

- [x] **Step 5 — Handoff**
  - Write `build-result.md` per workflow artifact contract; mutate plan markers to `[x]`/`[f]` as appropriate.

## Binary acceptance criteria (verifier)

- [x] **AC-1:** `.gitignore` ignores live `.mat.env` (and documented live variants) while `.mat.env.sample` remains tracked / not ignored.
- [x] **AC-2:** `.cursorignore` ignores live `.mat.env` (and documented live variants) while sample negations keep samples visible to indexing policy.
- [x] **AC-3:** `git check-ignore -v .mat.env` succeeds with an explicit matching rule; `.mat.env` is not in the git index.
- [x] **AC-4:** `bash scripts/doctor.sh` and `bash scripts/phase1-verify.sh` exit successfully (or doctor advisory-only warnings documented honestly without FAIL on this slice’s ignore changes).

## Verification plan

### Per-phase validation loops (loop until pass)

| Phase | Command | Loop until pass |
|-------|---------|-----------------|
| Ignore proof | `git check-ignore -v .mat.env` | Must print a rule; fix patterns until it does |
| Sample still trackable | `git check-ignore -v .mat.env.sample`; `git ls-files .mat.env.sample` | Sample must NOT be ignored; must remain tracked |
| Doctor | `bash scripts/doctor.sh` | Re-run until exit 0 or only documented advisories |
| Phase1 | `bash scripts/phase1-verify.sh` | Re-run until exit 0 |
| Optional local CI job | `gh act -j php-lint --container-architecture linux/amd64` (or repo job id) | Prefer before push if Docker healthy |

### Global validation commands (before handoff)

1. `git check-ignore -v .mat.env`
2. `git ls-files --stage -- .mat.env .mat.env.sample .env.sample`
3. `bash scripts/doctor.sh`
4. `bash scripts/phase1-verify.sh`

## Expected output artifacts

- `build-result.md` — builder handoff
- `verify-result.md` — parent-serialized after verifier payload
- Updated PR #6 (parent push + CI + merge) — post-verify closeout

## Parent closeout (after verify PASS — not builder)

- [ ] Low-risk `/update-docs` + `/cleanup` for slice-related hygiene only
- [ ] Commit slice (no force-push)
- [ ] Push to update PR #6 (`chore/mat-sync-refresh` or retarget)
- [ ] `/loop-on-ci` until green
- [ ] Merge PR #6 when green
- [ ] Advance long-run queue to slice 2

## Amendments

- 2026-11-05T07:36:09Z — orchestrator — Initial execution plan for env-secrets-ignore; branch `chore/mat-env-secrets-ignore` from `chore/mat-sync-refresh` + merge(main) for Plugin Check; preflight `builder_plus_verifier`.
- 2026-11-05T08:02:37Z — orchestrator — Verifier PASS; parent re-proof + serialized verify-result.md; phase1 exit 0; proceeding to commit/push PR #6.
