# MAT adoption notes — rank-math-api-manager

**Branch:** `chore/mat-adoption`  
**Bootstrap commit:** `74cd610` — `chore: adopt MAT workflow (bootstrap)`  
**Base:** `origin/main` @ `d59341d` (v1.0.9.1)  
**MAT source:** `multi-agent-teams` (bootstrap via `bootstrap-workflow-into-repo.sh --mode existing-project`)

This PR adopts the Multi-Agent Teams (MAT) workflow sidecar. It does **not** include v1.0.9.2 product work (composer, PHPUnit, icons, QA workflow, plugin PHP changes).

## What reviewers see in `74cd610`

| Area | Files | Notes |
| --- | ---: | --- |
| MAT sidecar | `.mat/**` | Docs, contract tests, `AGENTS.mat.md`, cost-hygiene templates |
| Product pointer | `AGENTS.md` | Short product-owned stub → `.mat/AGENTS.mat.md` |
| Operator scripts | `scripts/**` | `phase1-verify.sh`, `doctor.sh`, adoption/updater tooling |
| Workflow handoffs | `docs/current-plan.md`, `docs/long-run-state.md` | Minimal MAO slice/mission files |
| Docs index hook | `docs/README.md` | +15 lines: MAT operator index (product docs preserved) |
| Hygiene | `.cursorignore`, `.env.sample` | Default MAT template (+ WordPress stack lines in follow-up) |
| Plugin PHP | **0** | No `*.php` in commit |

**Total:** 54 files, ~9.7k insertions, zero deletions of product source.

## `.cursor/` coexistence (on disk, not in commit)

Bootstrap installs MAT workflow surfaces under `.cursor/` (agents, commands, hooks, rules). This repo also has **repo-local WordPress skills** under `.cursor/skills/` (18 skill packages, e.g. `wp-plugin-development`, `wp-rest-api`, `rankmath`).

| Layer | Location | In git today |
| --- | --- | --- |
| MAT bundle | `.cursor/agents/`, `commands/`, `hooks/`, `rules/` | **No** — `.cursor/` is in `.gitignore` per `CONTRIBUTING.md` |
| Repo-local skills | `.cursor/skills/**` | **No** — same ignore rule |
| MAT sidecar (tracked) | `.mat/` | **Yes** |

Operators need a local bootstrap (or a future policy change) so `.cursor/` exists on disk. `bash scripts/doctor.sh` validates surfaces at the paths above.

### `update-mat.py` dry-run (post-bootstrap, not applied)

```text
changes detected: 9
conflicts: 111
agents_reconciliation_needed: False
```

Conflicts are **expected**: MAT footprint owns much of `.cursor/`, but **unmanaged** repo-local files under `.cursor/skills/` are not in the MAT manifest. The updater reports them as conflicts until footprint/preserve policy is chosen upstream or locally.

- **`update-mat --apply`** is for **incremental MAT drift refresh** after bootstrap — not required for first adoption.
- **Do not `--apply`** without reviewing the saved plan and resolving skill coexistence (see options below).

Plan artifact (local): `artifacts/update-mat/plan-update-*.json`

## Policy options for `.cursor/` + skills

### Option A — Keep `.cursor/` gitignored (current; matches `CONTRIBUTING.md`)

- **Pros:** No PR conflict with private-only guardrail; skills and hooks stay machine-local; smallest review surface.
- **Cons:** Each operator runs bootstrap locally; team drift possible until someone documents the bootstrap command in onboarding.
- **MAT PR scope:** Commit `.mat/`, `AGENTS.md`, `scripts/`, `.cursorignore`, `.env.sample` only (as in `74cd610`).

### Option B — Selective un-ignore for team sharing

Track MAT-managed workflow files; keep skills private or move skills to a separate tracked path later.

Example `.gitignore` adjustment (illustrative — not applied in bootstrap PR):

```gitignore
.cursor/
!.cursor/hooks.json
!.cursor/mcp.json
!.cursor/worktrees.json
!.cursor/agents/
!.cursor/commands/
!.cursor/hooks/
!.cursor/rules/
# Keep repo-local skills untracked (or move to agent-skills/ with its own policy)
.cursor/skills/
```

- **Pros:** Shared slash commands, hooks, and agents across the team without re-bootstrap.
- **Cons:** Requires `CONTRIBUTING.md` exception, merge discipline on `update-mat`, and explicit preserve rules for `.cursor/skills/`.
- **When:** After MAT PR merges and operators agree on skill ownership.

**Recommendation for this PR:** **Option A.** Ship the tracked sidecar first; decide Option B in a follow-up slice with an explicit `CONTRIBUTING.md` amendment.

## Cherry-pick onto a clean branch?

| Question | Answer |
| --- | --- |
| Is cherry-pick required? | **No** — `chore/mat-adoption` is already **one commit** (`74cd610`) on top of `origin/main` @ `d59341d`. |
| Does local v1.0.9.2 WIP affect the PR? | **No** — unstaged/modified product files are not in the commit; they will not appear in the GitHub diff if you push only this branch. |
| When would cherry-pick help? | If the branch later accumulates extra commits, was cut from the wrong base, or you want a new branch name from a freshly fetched `origin/main`. |

**Tradeoffs if you cherry-pick anyway:**

```bash
git fetch origin
git checkout -b chore/mat-adoption-clean origin/main
git cherry-pick 74cd610
```

- **Pro:** Identical tree to `74cd610`; psychologically “clean” branch from remote main.
- **Con:** Redundant if `chore/mat-adoption` already matches; any doc commits after `74cd610` must be cherry-picked too or replayed.

## Verification (re-run before PR)

```bash
bash scripts/phase1-verify.sh   # expect exit 0
bash scripts/doctor.sh          # expect exit 0
```

Product PHP validation remains **out of scope** for the MAT PR. For plugin slices, use `php -l` / PHPCS / Plugin Check per `.github/workflows/release.yml`.

## Hooks, observability, cost hygiene

- **Hooks:** Enable incrementally after `doctor` is clean; review `.cursor/hooks.json` and Python deps before `.env` secrets.
- **Observability:** Opt-in only — see [`.mat/docs/adoption-observability-appendix.md`](../.mat/docs/adoption-observability-appendix.md). RFU-7 deferred; no apps/server stack in this slice.
- **Cost hygiene:** Bootstrap selected `cursorignore-mat-default`. WordPress-specific lines merged into root `.cursorignore` from `.mat/docs/templates/cursorignore-mat-wordpress` (indexing hygiene only). Strict CI enforcement: `CURSOR_MAT_COST_HYGIENE_ENFORCE` when ready.

## PR readiness checklist

- [ ] PR base: `main` @ `d59341d` (or later release tag if main moved — rebase only if needed)
- [ ] PR contains **only** MAT commits (`74cd610` + any doc/hygiene follow-ups); no v1.0.9.2 files
- [ ] `git diff origin/main...HEAD --name-only` shows no `*.php`, no `composer.*`, no `tests/`, no `assets/images/`
- [ ] `bash scripts/phase1-verify.sh` exit 0 on PR branch
- [ ] `bash scripts/doctor.sh` exit 0 on PR branch
- [ ] Reviewer confirms `AGENTS.md` pointer and `.mat/AGENTS.mat.md` split
- [ ] Reviewer aware `.cursor/` is local-only until Option B
- [ ] `update-mat.py --apply` **not** run in this PR
- [ ] CONTRIBUTING private-only guardrail acknowledged (`.cursor/` intentionally absent from diff)

## Related

- Active slice plan: [current-plan.md](current-plan.md)
- Disposable pilot evidence: MAT repo `artifacts/report/adoption-rank-math-api-manager-pilot-2026-06-24.md`
