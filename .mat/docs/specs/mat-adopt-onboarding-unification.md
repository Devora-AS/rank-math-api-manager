# MAT existing-project onboarding unification

**Preflight classification:** `ready_for_execution_handoff` — bounded multi-slice engineering work; project into `docs/current-plan.md` per slice after parallel plan-contract work lands.

## Task Description

Unify first-time **existing-project** MAT adoption with the mat-sync update UX: detect → plan (rich preflight JSON) → approve → verify. Close gaps exposed by the Omniroute adoption plan review — especially `.gitignore` silently hiding `.cursor/` workflow assets, stale pre-bootstrap `cursorignore_merge_preview`, thin bootstrap plans, and documentation that still treats raw `bootstrap-workflow-into-repo.sh` as the primary path. Add a zero-checkout installer stub and `/mat-adopt` entry for repos that do not yet have MAT slash commands.

## Objective

Operators adopting MAT into an active product repo get the **same two-step safety model** as `/mat-sync` refresh (plan JSON review, then `--approve-plan`), with automated append-only merges for `.gitignore` and `.cursorignore`, richer preflight in plan JSON, and honest bootstrap from product repo without a maintainer-local MAT checkout — while preserving product-owned `AGENTS.md`, no auto-commit, and conservative safe defaults.

## Scope

### In scope (implementation slices A–F)

| Slice | ID | Deliverable |
|-------|-----|-------------|
| **A** | `docs-first` | mat-sync-first existing-project guide; align `/mat-update-mat`, `/mat-sync`, packaged `.mat/docs/getting-started-existing-projects.md` |
| **B** | `post-bootstrap-cursorignore` | Recompute + apply `cursorignore_merge_preview` after bootstrap/rebootstrap in `phase_gate` |
| **C** | `gitignore-merge` | `mat_gitignore_merge.py`, template fragment, plan preview + apply on approve |
| **D** | `preflight-detect` | Extend mat-sync plan JSON: preflight report (gitignore, env.sample, skills, agents, scripts overlap, policy flags) |
| **E** | `mat-adopt-entry` | `/mat-adopt` command + chat copy-paste blocks; extend mat-sync help/phases table for first adoption |
| **F** | `installer-stub` | Thin `scripts/adoption/mat-adopt.sh` (GitHub materialize → mat-sync plan); document two-step approve |
| **G** | `adoption-scaffold` | Optional `.mat/adoption-profile.json` with `validation_commands` section; bootstrap template when missing |
| **H** | `detect-expand` | mat-sync detect: custom skills/commands inventory; `.env.sample` blocked-by-gitignore detection |

Slices ship in order **A → B → C → D → (E + F parallel) → G → H** where dependencies allow. **C** and **D** may overlap after **B** lands.

### Out of scope (this mission)

- Auto-commit or auto-PR on product repos
- Replacing product `AGENTS.md` prose (pointer note only)
- Observability apps bootstrap by default
- MAO hook automation defaults on
- Live Cursor todo parity or hook-driven subagent auto-spawn
- Full `.gitignore` replacement (append-only marked blocks only)
- Omniroute repo execution (separate operator plan update only)

## Assumptions

- `mat-sync.sh` state machine remains the single orchestration entry; bootstrap stays delegated to `bootstrap-workflow-into-repo.sh`.
- GitHub-first `.mat/source-config.json` v2 remains production default after first approve.
- Existing `mat_cursorignore_merge.py` semantics (marked block, `warn_first`, idempotent) are the template for gitignore merge.
- Operators still run a docs-only pilot before production infra work; scaffold documents commands, does not enforce Azure/SSH gates.
- Parallel in-repo work on shared plan contract / Amendments (Slice 2 shipped) completes before execution handoff; this spec does not block on plan-contract Slice 3 (status markers).
- `tests/test_mat_sync.py` and adopted-contract CI fixture remain the primary regression harness.

## Non-Goals

- One-click mutate without human `--approve-plan` review
- npm/global package distribution (curl/bash stub from MAT repo or GitHub raw is sufficient for v1)
- Merging product `docs/` trees into MAT encyclopedia
- WordPress-only cursorignore stack detection changes beyond existing template map
- Rewriting Omniroute repository (prompt-only deliverable for that repo)

## Problem Statement

MAT refresh was productized (`mat-sync`: detect → route → plan → approve → verify, GitHub-first source, append-only `.cursorignore` merge). First-time existing-project adoption still documented as an 8-phase manual runbook (bootstrap, hand-edit `.gitignore`, env, verify, pilot). Repos like Omniroute with `.cursor/*` ignored except `skills/` **silently drop** workflow assets from git until manual fix — the highest-friction gap.

Additional gaps:

1. **No `mat_gitignore_merge.py`** — cursorignore has merge tooling; gitignore does not.
2. **Pre-bootstrap cursorignore preview** — first approve often skips fragment merge because adoption sidecar and `.cursorignore` do not exist at plan time.
3. **Thin bootstrap plan JSON** — no preflight report (skills, gitignore blockers, env.sample).
4. **Entry confusion** — `/mat-sync` unavailable in product repo before adoption; docs still emphasize raw bootstrap.
5. **No product validation scaffold** — builder/verifier command mapping is ad hoc per operator plan.
6. **Detect skew** — custom skills ignored; only agents counted.

## Solution Approach

### Architecture

```mermaid
flowchart LR
  subgraph entry [Entry points]
    AdoptSh[mat-adopt.sh from product repo]
    MatSync[mat-sync.sh from MAT source or post-adopt]
    SlashAdopt[/mat-adopt in MAT source workspace]
  end

  subgraph machine [mat-sync state machine]
    Detect[detect + preflight]
    Route[route bootstrap]
    Plan[plan JSON + previews]
    Gate[bootstrap + merges]
    Verify[doctor + phase1-verify]
  end

  AdoptSh --> MatSync
  SlashAdopt --> MatSync
  MatSync --> Detect --> Route --> Plan
  Plan -->|approve| Gate --> Verify
  Gate --> GitMerge[mat_gitignore_merge]
  Gate --> CursorMerge[mat_cursorignore_merge post-bootstrap]
```

### Slice A — Documentation (docs-first)

- Rewrite **first adoption** path in `docs/guides/getting-started-existing-projects.md` to mat-sync plan/approve (from MAT source or `--repository`), demote raw bootstrap to maintainer/debug.
- Update `.cursor/commands/mat-update-mat.md` Step 1 branch to mat-sync-first.
- Extend `.cursor/commands/mat-sync.md` with **first adoption** section (cannot run from un-adopted product repo — run from MAT source with `--repo-root` or use `mat-adopt.sh`).
- Add `.cursor/commands/mat-adopt.md` stub pointing to installer + mat-sync semantics.
- Package updated guide fragments via `adoption-layout-v1.json` on next bootstrap (document in slice acceptance).

### Slice B — Post-bootstrap cursorignore recompute

In `scripts/mat-sync.sh` `phase_gate`, for routes `bootstrap|rebootstrap`:

1. Run bootstrap.
2. Recompute `compute_cursorignore_merge_preview(repo_root)`.
3. Apply via `apply_cursorignore_merge` (ignore stale pre-bootstrap lines in approved plan when recompute yields lines; log when plan preview differed).

Regression: virgin fixture with absent `.cursorignore` → after approve, root `.cursorignore` exists with MAT marker block or template-installed file gets append.

### Slice C — `mat_gitignore_merge.py`

Mirror `mat_cursorignore_merge.py`:

| Element | Value |
|---------|--------|
| Markers | `# BEGIN MAT git tracking` / `# END MAT git tracking` |
| Template | `docs/templates/gitignore-mat-existing-project.fragment` (negations + runtime ignores + `!.env.sample`) |
| Preview field | `gitignore_merge_preview` on mat-sync plan JSON |
| Apply | Append-only on `--approve-plan`; idempotent when marker present |
| Policy | Never replace whole `.gitignore`; detect blockers (e.g. `.cursor/*` without negations) in preflight |

Ship helper in `adoption-layout-v1.json` `root_scripts_copy` alongside `mat_cursorignore_merge.py`.

### Slice D — Preflight report in plan JSON

Extend `write_mat_sync_plan` payload:

```json
{
  "preflight": {
    "gitignore_blockers": [],
    "env_sample_blocked_by": [],
    "custom_skills": [],
    "custom_agents": [],
    "custom_commands": [],
    "scripts_path_overlap": [],
    "policy_flags": [],
    "sidecar_present": false
  },
  "gitignore_merge_preview": [],
  "cursorignore_merge_preview": []
}
```

Implement `scripts/adoption/mat_adopt_preflight.py` (detect-only) called from detect/plan phases. Human-readable summary lines on stderr for bootstrap route.

### Slice E — `/mat-adopt` unified entry

- New `.cursor/commands/mat-adopt.md`: orchestrator prints **one** fenced `txt` block per step.
- Step 1 (un-adopted product repo): invoke `mat-adopt.sh` or mat-sync from MAT workspace with `--repo-root`.
- Step 2: review plan JSON fields (`preflight`, merge previews).
- Step 3: approve command.
- Document explicitly: **slash command runs from MAT source repo** (or agent with MAT on PATH), not from product repo until after first approve.

### Slice F — `mat-adopt.sh` installer stub

- `scripts/adoption/mat-adopt.sh` — args: `--repo-root`, optional `--repository`, `--ref`, `--approve-plan`.
- Resolves/materializes MAT source via existing `mat_source_config.py` + `mat_source_materialize.sh`.
- Delegates to `mat-sync.sh` (no duplicate merge engine).
- curl-friendly one-liner documented in getting-started (raw GitHub path or release tag when available).
- **Plan-only default**; second invocation or `--approve-plan` for mutate.

### Slice G — Adoption profile scaffold

- Bootstrap creates `.mat/adoption-profile.json` when missing:

```json
{
  "schema_version": 1,
  "validation_commands": {
    "builder_verify": [],
    "pilot_scope": "docs-only",
    "infra_commands_forbidden": true
  }
}
```

- Template comment block points operators to fill before first `/mat-sprint` or `/mat-plan-team`.
- Optional: mat-sync preflight warns when `validation_commands.builder_verify` empty on existing-project bootstrap.

### Slice H — Detect expansion

- `list_custom_skills()` / `list_custom_commands()` vs MAT baseline (same pattern as `list_custom_agents`).
- Include in `DETECT_JSON` and `preflight`.
- `.env.sample` visibility: parse root `.gitignore` / git check-ignore simulation for `.env.sample` path.

## Relevant Files / Areas

| Path | Action |
|------|--------|
| `scripts/adoption/mat_gitignore_merge.py` | **Add** |
| `scripts/adoption/mat_adopt_preflight.py` | **Add** |
| `scripts/adoption/mat-adopt.sh` | **Add** |
| `scripts/adoption/mat_cursorignore_merge.py` | Reference / align patterns |
| `scripts/mat-sync.sh` | **Modify** — post-bootstrap merge, preflight, detect |
| `scripts/adoption/bootstrap-workflow-into-repo.sh` | **Modify** — emit adoption-profile template |
| `scripts/adoption/adoption-layout-v1.json` | **Modify** — ship new scripts + template fragment |
| `docs/templates/gitignore-mat-existing-project.fragment` | **Add** |
| `docs/guides/getting-started-existing-projects.md` | **Modify** |
| `docs/guides/mat-sync-team-runbook.md` | **Modify** — first adoption section |
| `.cursor/commands/mat-sync.md` | **Modify** |
| `.cursor/commands/mat-update-mat.md` | **Modify** |
| `.cursor/commands/mat-adopt.md` | **Add** |
| `tests/test_mat_gitignore_merge.py` | **Add** |
| `tests/test_mat_adopt_preflight.py` | **Add** |
| `tests/test_mat_sync.py` | **Extend** — bootstrap + gitignore + post-bootstrap cursorignore |
| `scripts/ci/run-adopted-contract-verify.sh` | **Extend** if needed |
| `ROADMAP.md` | **Modify** — Next item when slice starts (not in this planning-only step) |

## Task Traceability

| Task | Requirement / decision |
|------|------------------------|
| A — Docs mat-sync-first | Operators must not need parallel 8-phase runbooks for standard existing-project adoption (Omniroute lesson) |
| B — Post-bootstrap cursorignore | First approve must apply cursorignore fragments when bootstrap creates `.cursorignore` + sidecar |
| C — gitignore merge | `.cursor/*`-only ignore repos must not silently exclude MAT workflow from git (Omniroute Phase 3) |
| D — Preflight JSON | Plan JSON parity with update dry-run richness; single review artifact |
| E — `/mat-adopt` | Slash entry despite product repo lacking MAT commands pre-adoption |
| F — `mat-adopt.sh` | Zero local MAT checkout; GitHub-first like mat-sync refresh |
| G — adoption-profile | Product-specific builder/verifier mapping durable in repo (Omniroute Phase 5) |
| H — Detect skills/gitignore | Skill-heavy repos (OmniRoute) need honest inventory in plan |
| Safety invariants | Same as mat-sync: dry-run default, no auto-commit, preserve AGENTS.md |

## Testing Strategy

### Manual verification

- Disposable git repo with Omniroute-like `.gitignore` (`.cursor/*`, `!.cursor/skills/**`): plan shows `gitignore_blockers`; approve appends marked block; `git check-ignore -v .cursor/agents/builder.md` fails (trackable).
- Virgin repo: mat-sync bootstrap plan → approve → `.mat/AGENTS.mat.md`, `.cursorignore` fragments, `.mat/adoption-profile.json` exist; `phase1-verify.sh` passes with `PHASE1_VERIFY_SKIP_BUN=1`.
- `mat-adopt.sh --repo-root` from product tree without local MAT clone: plan only, then approve.

### Automated coverage (implementation phase)

| Test module | Focus |
|-------------|--------|
| `tests/test_mat_gitignore_merge.py` | Preview, append, idempotent marker, `.env.sample` negation lines |
| `tests/test_mat_adopt_preflight.py` | Blocker detection, skills inventory, env.sample blocked |
| `tests/test_mat_sync.py` | Post-bootstrap cursorignore; gitignore merge on approve; preflight keys in plan JSON |
| `tests/test_workflow_docs.py` | Required doc strings for mat-sync-first adoption (if wired) |

### Edge cases / regression focus

- Product `.gitignore` already has partial MAT negations → append only missing lines.
- `warn_first` + preserved root `.cursorignore` (existing-project) vs new-project strict install.
- Approve plan stale vs latest-plan hash mismatch (unchanged behavior).
- Bootstrap with existing OmniRoute skills — no SKILL.md overwrites (bootstrap merge semantics unchanged).
- Second approve idempotent for both merge helpers.

### TDD expectation for build phase

- **Slice C / D / H:** write unit tests first for pure Python helpers (`mat_gitignore_merge`, `mat_adopt_preflight`).
- **Slice B / F:** extend `test_mat_sync.py` integration tests before or alongside shell changes.
- **Slice A / E:** doc contract tests after prose lands.

### Per-phase validation loops (loop until pass)

| Phase | Command | Loop until pass |
|-------|---------|-----------------|
| Gitignore merge unit tests | `python3 -m unittest tests.test_mat_gitignore_merge -v` | Re-run after fixes until green |
| MAT sync integration | `python3 -m unittest tests.test_mat_sync -v` | Re-run until green |
| Full repo gate | `bash scripts/phase1-verify.sh` | Re-run until exit 0 before handoff |

### Global validation commands (before handoff)

1. `python3 scripts/validate_planning_artifacts.py --repo-root .` — loop until pass.
2. `bash scripts/phase1-verify.sh` — re-run until exit 0.

Hard orchestration gates remain `build-result.md` / `verify-result.md`; in-plan loops are SOP for builders.

## Acceptance Criteria

- [x] **A:** `getting-started-existing-projects.md` lists mat-sync plan/approve as primary first-adoption path; raw bootstrap labeled maintainer/debug.
- [x] **B:** After bootstrap approve on fixture without prior `.cursorignore`, MAT runtime fragments present in root `.cursorignore` (marker block or equivalent).
- [x] **C:** `mat_gitignore_merge.py` ships in layout; plan JSON includes `gitignore_merge_preview`; Omniroute-like fixture un-ignores `.cursor/agents/` paths after approve.
- [x] **D:** Bootstrap route plan JSON includes non-empty `preflight` object with documented keys; stderr summarizes blockers when present.
- [x] **E:** `.cursor/commands/mat-adopt.md` exists; states product repo cannot use `/mat-sync` until after first approve.
- [x] **F:** `mat-adopt.sh` runs plan without local `MULTI_AGENT_WORKFLOW_ROOT` when `--repository` resolves; delegates to mat-sync.
- [x] **G:** Bootstrap creates `.mat/adoption-profile.json` template when absent.
- [x] **H:** Detect reports custom skill filenames; preflight flags when `.env.sample` would be ignored.
- [x] **Global:** `bash scripts/phase1-verify.sh` passes on MAT source repo after all slices.
- [x] **Global:** No auto-commit on target root; `--approve-plan` still required for mutation.

## Risks and Open Questions

| Risk | Mitigation |
|------|------------|
| gitignore merge append wrong on exotic ignore layouts | Detect-only blockers + human plan review; fail-closed `stop` route when parse ambiguous |
| curl installer supply-chain trust | Document pin-by-SHA/tag; prefer `gh` or git clone for paranoid operators |
| Plan JSON schema drift | `schema_version` bump on mat-sync-plan; contract tests |
| Overlap with plan-contract Slice 3 (status markers) | Keep missions separate; optional `[wip]` in projected plan later |
| Duplicate negation lines in gitignore | Dedupe on apply; idempotent marker block |

**Open questions**

1. Should `gitignore_merge` run on **incremental update** route too, or bootstrap/rebootstrap only? **Recommendation:** all approve paths when preview non-empty.
2. Publish `mat-adopt.sh` via GitHub release asset vs raw `main`? **Recommendation:** document raw path first; release later.
3. Wire `validation_commands` into builder.md template reads? **Defer** to follow-up slice after scaffold exists.

## Amendments

- 2026-07-01T12:00:00Z — planner — Initial spec from Omniroute adoption review and mat-sync onboarding gap analysis.

## Recommended Next Command

**Wait for parallel plan-contract work to complete**, then:

1. **Human refinement** — confirm slice order and open question (gitignore merge on update route).
2. **Project slice A** into `docs/current-plan.md` via `/mat-plan-team` or `/mat-long-run` (multi-slice mission recommended: A→H sequential).
3. Do **not** escalate to `/mat-plan-onboarding` unless cross-team PRD/traceability across product repos is required.

```text
/mat-long-run Execute specs/mat-adopt-onboarding-unification.md slices A through H sequentially; start with slice A docs-only after plan-contract parallel session completes
```
