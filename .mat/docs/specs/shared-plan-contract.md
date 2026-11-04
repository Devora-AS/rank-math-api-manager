# MAT Shared Plan Contract v0.1 — Design Spec

> **Preflight classification:** `ready_for_execution_handoff` — bounded design spec with explicit decisions for depth tiers, three-schema reconciliation, amendments, status markers, grandfathering, and ordered implementation slices. Human approval required before operator projection to `docs/architecture/plan-contract.md` or any build slice. This session is **planning only** (Slice 1).

**Last updated:** 2026-07-01  
**Contract version:** `0.1` (design only — not enforced at runtime until later slices)  
**ROADMAP anchor:** Later → Planning & execution contracts → *Shared MAT plan contract (meta-skill pattern)* (Effort L | Impact High); sibling items *Amendments section*, *In-plan status markers*, *Validation loops in templates*  
**Implementation order:** Slice 1 (this file) per `docs/archive/planf3-comparison-2026-07.md` — after automated planning validation (#1, **done 2026-07-01**), before Amendments (#2) and status markers (#3). Do not implement from roadmap bullets or the archive alone.

---

## Task Description

Define **MAT shared plan contract v0.1** — canonical plan semantics across depth tiers (`lite` / `standard` / `onboarding`) — so follow-on slices (Amendments, status markers, validator extensions, `.cursor/skills/mat-plan-contract/SKILL.md`, template unification) share one source of truth. Reconcile the three live plan shapes today (solo `specs/<slug>.md`, onboarding four-file package + `tasks.json`, execution slice `docs/current-plan.md` + MAO handoffs) without inventing a fourth informal shape.

This is **Slice 1 of N** (planning only). No code, templates, command edits, skills, hooks, or validator changes in this session.

## Objective

Give operators and implementers a single design artifact that:

1. Names depth tiers and maps them to existing commands and file shapes (no wholesale format migration).
2. Specifies amendments and in-plan status-marker protocols borrowed from planf3 **semantics** while preserving MAT file-handoff authority (`build-result.md` / `verify-result.md`, MAO gates).
3. Aligns grandfathering with `scripts/validate_planning_artifacts.py` patterns.
4. Orders implementation slices with acceptance-criteria stubs for future `/mat-plan-team` runs.
5. Supplies an **Architecture projection appendix** for future copy into `docs/architecture/plan-contract.md` (not written this session).

## Scope

### In scope (this design spec)

- Decisions A–J (depth tiers, schema reconciliation, amendments, status markers, authority model, grandfathering, validation loops posture, meta-skill reference, implementation order).
- Per-slice scope, touch paths, and acceptance-criteria stubs for Slices 2–6.
- Architecture projection appendix (markdown block for operator-facing doc).
- Session 2 projection checklist (operator steps after human approval).

### Out of scope (this session and explicit non-goals for v0.1)

- Creating `docs/architecture/plan-contract.md`, `docs/current-plan.md`, `build-result.md`, or `verify-result.md`.
- Editing `.cursor/commands/*`, `docs/templates/*`, `.cursor/skills/*`, hooks, or `validate_planning_artifacts.py`.
- HTML plan export, diagram generation, plugin/SDK distribution, new trace-ID schemes beyond existing `TASK-###` / `SPEC-###` / PRD IDs.
- Full meta-skill implementation (design reference only).
- Live authoritative MAO / Cursor todo parity (remains blocked per `ROADMAP.md`).

## Assumptions

1. **Shipped baseline:** `scripts/validate_planning_artifacts.py` (Tier 1–3), `tasks-schema-mat-plan-team.json`, and Dependabot client policy are on `main` (2026-07-01).
2. **Planning vs execution truth** stays split: `specs/` = upstream planning truth; `docs/current-plan.md` = execution truth for the active slice; `build-result.md` / `verify-result.md` = outcome truth for orchestration gates.
3. **Human approval gate** before projection from planning artifacts to `docs/current-plan.md` remains mandatory.
4. **MAO todos** (`[mao:plan|build|validate]`) stay advisory and slice-scoped; they do not replace file handoffs or in-plan status markers.
5. **Stdlib-only validators** remain the CI posture; contract extensions add checks incrementally, not new pip dependencies in v0.1.
6. When both `specs/<slug>.md` and `specs/<slug>/` exist, the **folder package is authoritative** (same as validator Tier 2 skip rule).
7. Operators promote ROADMAP items from **Later → Next** only after linking `docs/architecture/plan-contract.md` (projected from this spec’s appendix).

## Non-Goals

- Replacing slash commands with a single `/mat-plan --depth=…` entry point (deferred ROADMAP item).
- Merging onboarding four-file packages into solo `specs/<slug>.md`.
- Making in-plan status markers authoritative for MAO transition gates (hooks stay on handoff files).
- Retrofitting all historical `specs/` files to new optional sections in one slice.
- Enforcing contract v0.1 in CI before Slice 4 validator extensions land.

## Problem Statement

MAT planning is strong on orchestration, preflight classification, traceability IDs, and hook-enforced build/verify contracts, but **plan semantics are fragmented**:

| Live shape | Primary command | Enforcement today |
|------------|-----------------|-------------------|
| Solo `specs/<slug>.md` (13 sections) | `/mat-plan` | Tier 2 section order (non-grandfathered) |
| Onboarding `specs/<slug>/` (4 files + `tasks.json`) | `/mat-plan-onboarding` | Tier 1 + Tier 3 traceability |
| Execution `docs/current-plan.md` | `/mat-plan-team`, `/mat-long-run`, `/mat-sprint` | `artifact_contract.py`, MAO gates; **no** unified section contract |
| Adoption minimal plan | Bootstrap / adoption fixtures | `adoption-minimal-current-plan.md` template only |

`docs/archive/planf3-comparison-2026-07.md` recommends borrowing **in-document execution semantics** (status markers, amendments, validation loops) without abandoning multi-file handoffs. Automated planning validation (#1) is shipped; the **shared contract** must be designed before meta-skill, template unification, or validator extensions diverge.

## Solution Approach

### Decision A — Depth tiers (`lite` / `standard` / `onboarding`)

Contract v0.1 defines **three depth tiers**. Each tier names a **command entry**, **primary artifacts**, and **required semantic blocks** (not necessarily identical heading names across tiers).

| Tier | Intent | Primary commands | Primary artifacts | Required blocks (v0.1) |
|------|--------|------------------|-------------------|------------------------|
| **`lite`** | Smallest executable slice; adoption bootstrap or one bounded change | `/mat-sprint`, bootstrap adoption flows, narrow `inline` `/mat-plan-team` exceptions | `docs/current-plan.md` (execution) | `## Task`, binary acceptance checklist, `## Non-goals`, `## Verification plan`; optional `## DoR`; **no** full 13-section solo plan required |
| **`standard`** | Default planning + execution for bounded or projected work | `/mat-plan`, `/mat-plan-team`, `/mat-long-run` (per-slice projection) | Planning: `specs/<slug>.md`; Execution: `docs/current-plan.md` | **Planning:** existing 13 `/mat-plan` sections (Tier 2). **Execution:** projected subset — `## Task`, `## Acceptance criteria` (or `Binary acceptance criteria`), implementation steps, validation checks, explicit `TASK-###` when sourced from onboarding; **plus** contract extensions in Slices 2–3 (`## Amendments`, status markers on checklist lines) |
| **`onboarding`** | Heavyweight discovery, PRD/spec separation, traceable tasks | `/mat-plan-onboarding` | `specs/<slug>/prd.md`, `spec.md`, `tasks.json`, `plan-summary.md` | Existing four-file package + `tasks.json` per `docs/templates/tasks-schema.json`; `plan-summary.md` carries bridge + recommended next command; **plus** `## Amendments` on `plan-summary.md` (Slice 2) |

**Tier selection rule:** Commands do not auto-infer tier from intent alone — operators choose command (deterministic routing). `/mat-plan` always produces **standard** planning artifacts. `/mat-plan-onboarding` always produces **onboarding**. Execution writers pick **lite** vs **standard** execution shape based on slice complexity (document rationale in plan header one line).

### Decision B — Three-schema reconciliation (no fourth shape)

Map the three live shapes to tiers **without** introducing a new file format:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTRACT v0.1 (semantic layer)                │
│         lite │ standard │ onboarding + shared extensions         │
└─────────────────────────────────────────────────────────────────┘
         ▲              ▲                    ▲
         │              │                    │
  docs/current-plan.md  specs/<slug>.md   specs/<slug>/
  (execution projection) (planning)        (4-file package)
         │              │                    │
         └──────────────┴────────────────────┘
              Projection (human-owned, post-approval)
              plan-summary.md / solo spec → docs/current-plan.md
```

| Artifact | Tier | Role in v0.1 |
|----------|------|----------------|
| `specs/<slug>.md` | **standard** (planning) | Upstream planning truth; 13 sections; may receive optional `## Amendments` in Slice 2 (Decision C) |
| `specs/<slug>/` package | **onboarding** | Upstream planning truth; `plan-summary.md` is projection bridge |
| `docs/current-plan.md` | **lite** or **standard** (execution) | **Not a fourth schema** — always a **projection** of an approved planning artifact (solo spec, `plan-summary.md`, or `tasks.json` slice). Inherits tier from slice complexity. MAO handoffs attach to this file during orchestration |
| `docs/templates/adoption-minimal-current-plan.md` | **lite** (template) | Canonical **lite** execution skeleton for adopted repos |
| `tasks.json` (`plan_onboarding` / `mat-plan-team`) | Metadata sidecar | Stays JSON; not merged into markdown. `planning_mode` selects schema profile (existing validator behavior) |

**Reconciliation rules:**

1. **One active execution truth:** At most one substantive `docs/current-plan.md` per orchestration cycle (long-run may rewrite between slices; document in `docs/architecture/long-run-state.md`).
2. **Planning wins on drift:** If execution diverges from approved planning package, update planning artifacts first, then re-project (per `docs/guides/planning-commands-guide.md`).
3. **Validator scope unchanged in Slice 1:** Tier 1–3 continue to target `specs/` only; execution contract extensions land in Slice 4+.

### Decision C — Amendments protocol (Slice 2)

| Field | v0.1 rule |
|-------|-----------|
| **Section name** | `## Amendments` (exact level-2 heading) |
| **Placement** | **Last section** in the file (after all other content, including `Recommended Next Command` on solo specs if present — *or* immediately before `Recommended Next Command` when that section must remain final for `/mat-plan` Tier 2; **chosen:** `## Amendments` is **second-to-last**, `## Recommended Next Command` remains **last** on solo specs; on execution/onboarding bridge files without that section, `## Amendments` is last) |
| **Format** | Append-only bullet list; each entry starts with ISO-8601 timestamp in UTC (`YYYY-MM-DDTHH:MM:SSZ`) followed by author role and summary |
| **Example line** | `- 2026-07-01T14:30:00Z — operator — Narrowed scope: defer validator Tier 4 to Slice 5.` |
| **Files in scope (Slice 2)** | **Required:** `docs/current-plan.md`, `specs/<slug>/plan-summary.md`. **Optional (recommended):** root `specs/<slug>.md` when used as living planning doc. **Excluded v0.1:** `prd.md`, `spec.md`, `tasks.json` (structured JSON — use task status fields + plan-summary amendments instead) |
| **Mutation authority** | **Operator / parent orchestrator** may always append. **Builder** may append only during an active build when recording scope negotiation or plan drift tied to a `[f]` item (must cite triggering checklist line). **Verifier** append **prohibited** (read-only). **Planning agents** (`/mat-plan`, `/mat-plan-onboarding`) append only while authoring that file in the same session before approval |
| **Forbidden** | Rewriting prior amendment lines; editing historical timestamps; deleting entries |

### Decision D — Status marker state machine (Slice 3)

**Markers** (planf3-compatible, applied to **checklist lines** in execution plans and, optionally, task lists in `docs/current-plan.md`):

| Marker | Meaning | Typical next states |
|--------|---------|---------------------|
| `[]` | Idle / not started | `[wip]` |
| `[wip]` | In progress (builder owns) | `[x]`, `[f]` |
| `[x]` | Done for this slice | terminal |
| `[f]` | Failed / blocked (requires reason text on same line or next bullet) | `[wip]` after fix, or plan amendment |

**State machine (per checklist line):**

```
[] ──(builder starts)──► [wip] ──(success)──► [x]
                            │
                            └──(blocked)──► [f] ──(retry)──► [wip]
```

| Concern | v0.1 rule |
|---------|-----------|
| **Where required (Slice 3)** | `docs/current-plan.md` acceptance criteria and implementation step checklists |
| **Where optional** | Solo `specs/<slug>.md` acceptance criteria; onboarding `plan-summary.md` task rollups |
| **Mutation authority** | **Builder** transitions `[]→[wip]→[x]` during build. **Builder** sets `[f]` with reason. **Parent** may set `[wip]` at slice start. **Verifier** does not mutate markers (reports in `verify-result.md` instead) |
| **MAO todos** | **Advisory only.** `[mao:build] in_progress` does not imply `[wip]` on plan lines. Parent should not use MAO status as a substitute for in-plan markers |
| **`build-result.md` / `verify-result.md`** | **Authoritative for orchestration gates** (PASS/PARTIAL/FAIL, lint row, acceptance criteria rows). Status markers are **advisory executability** inside the plan; gate transitions still require handoff file contract per `docs/reference/workflow-artifact-contract.md` |
| **Sync expectation** | Before build→validate transition, parent checks handoff files, not marker completeness. Verifier may **warn** when plan markers disagree with `build-result.md` but gate truth is the handoff file |

### Decision E — Validation loops posture (Slice 5+ / templates)

v0.1 **defines** but does **not implement** validation-loop blocks:

- **Per-phase:** In `## Testing Strategy` (standard planning) or `## Verification plan` (lite/execution), each phase lists a command and **“loop until pass”** instruction.
- **Global:** Execution plans include a `## Validation commands` or reuse `## Verification plan` with ordered commands before handoff.
- **Enforcement:** Hook-enforced `build-result.md` / `verify-result.md` remain the **hard** gate; in-plan loops are **SOP** for builder/subagent prompts.

Defer template edits to Slice 5 (template unification).

### Decision F — Meta-skill reference (Slice 6)

`.cursor/skills/mat-plan-contract/SKILL.md` (future) will:

1. Encode tier selection, amendments, and status-marker rules as procedural steps.
2. Point to `docs/architecture/plan-contract.md` for operator-facing summary.
3. **Not** replace slash commands; cross-reference `/mat-plan`, `/mat-plan-onboarding`, `/mat-plan-team`.
4. Package to `.mat/skills/` on bootstrap (portable adoption).

Slice 6 depends on Slices 2–5 stabilizing semantics.

### Decision G — Migration and grandfathering

Align with `scripts/validate_planning_artifacts.py` registries:

| Class | Handling |
|-------|----------|
| **`LEGACY_SOLO_PLANS`** | Remain Tier 2 grandfathered; amendments/status markers **not required** until operator opts in or file is substantively revised |
| **New solo `specs/<slug>.md`** | Standard tier + Tier 2 enforcement; after Slice 2/3, new plans **should** include optional amendments section and markers only when `ready_for_execution_handoff` |
| **Onboarding specimen `plan-and-plan-onboarding-v1/`** | Reference package; amend `plan-summary.md` first when piloting contract extensions |
| **`specs/update-mat/tasks.json`** | Stays Tier 1b excluded until migrated to `mat-plan-team` or onboarding schema |
| **Idle / placeholder `docs/current-plan.md`** | No retroactive amendments; contract applies on next substantive orchestration write |
| **Adopted repos** | **Lite** tier default via `adoption-minimal-current-plan.md`; full contract docs in `.mat/docs/` after projection |

**Migration principle:** Opt-in on edit, not big-bang retrofit.

### Decision H — Preflight vocabulary (unchanged in v0.1)

Planning preflight terms stay separate from execution preflight:

| Layer | Terms |
|-------|-------|
| Planning (`/mat-plan`) | `solo_plan_only`, `ready_for_execution_handoff`, `needs_plan_onboarding` |
| Execution (`/mat-plan-team`) | `inline`, `builder_plus_verifier`, `parallel_spawn` |

v0.1 does **not** unify these vocabularies (deferred ROADMAP item). The contract doc may reference both layers but must not collapse them.

### Decision I — File tagging (`new` vs `existing`) — deferred

ROADMAP item *Tag Relevant Files as `new` vs `existing`* is **out of v0.1** except as a forward pointer in Slice 5 template work.

### Decision J — Ordered implementation slices

| Slice | ROADMAP item | Effort | Scope summary |
|-------|--------------|--------|---------------|
| **1** | Shared plan contract (design) | — | **This file** — planning only |
| **2** | Amendments section | S | Add `## Amendments` protocol to commands/templates for `docs/current-plan.md`, `plan-summary.md`, optional solo specs |
| **3** | In-plan status markers | M | Marker state machine in `docs/current-plan.md`; builder command instructions |
| **4** | Validator extensions | M | Optional Tier 4 checks: amendments presence/format, marker syntax on execution plans (source repo only) |
| **5** | Template unification | L | Align `adoption-minimal-current-plan.md`, execution plan template, validation loops prose |
| **6** | Meta-skill | L | `.cursor/skills/mat-plan-contract/SKILL.md` + `.mat/` packaging |

**Dependency chain:** 1 → 2 → 3 → (4 ∥ 5) → 6. Slice 4 may start after Slice 3; Slice 5 may overlap Slice 4 but must not contradict Decisions A–D.

#### Slice 2 — Amendments (implementation stub)

| Field | Detail |
|-------|--------|
| **Touch paths** | `.cursor/commands/mat-plan-team.md`, `.cursor/commands/mat-long-run.md`, `.cursor/commands/mat-plan-onboarding.md` (plan-summary), `.cursor/commands/mat-plan.md` (optional solo), `docs/templates/adoption-minimal-current-plan.md` (comment block), `docs/guides/planning-commands-guide.md`, `docs/architecture/orchestration-workflow.md` (short pointer) |
| **Acceptance criteria stub** | New substantive `docs/current-plan.md` from `/mat-plan-team` includes `## Amendments` with ≥1 seed line or explicit `none yet`; append-only rule documented in MAINTAINER; no validator required in Slice 2 |

#### Slice 3 — Status markers (implementation stub)

| Field | Detail |
|-------|--------|
| **Touch paths** | `.cursor/commands/mat-plan-team.md`, `.cursor/agents/builder.md`, `docs/templates/adoption-minimal-current-plan.md`, `docs/reference/workflow-artifact-contract.md` (advisory vs authoritative note) |
| **Acceptance criteria stub** | Builder instructions require `[]` default on new checklist lines; demo orchestration updates markers in-place; `build-result.md` gate still drives MAO build→validate |

#### Slice 4 — Validator extensions (implementation stub)

| Field | Detail |
|-------|--------|
| **Touch paths** | `scripts/validate_planning_artifacts.py`, `tests/test_planning_artifacts_validation.py`, `docs/reference/MAINTAINER.md` |
| **Acceptance criteria stub** | Tier 4 optional flag validates amendments heading on fixture `docs/current-plan.md`; marker regex check; grandfather execution plans unchanged before contract adoption date |

#### Slice 5 — Template unification (implementation stub)

| Field | Detail |
|-------|--------|
| **Touch paths** | `docs/templates/adoption-minimal-current-plan.md`, new `docs/templates/execution-plan-template.md` (if created), `docs/templates/spec-template.md` (cross-links only), validation loops prose |
| **Acceptance criteria stub** | Lite and standard execution templates document shared tier mapping; `phase1-verify.sh` unchanged unless Tier 4 landed |

#### Slice 6 — Meta-skill (implementation stub)

| Field | Detail |
|-------|--------|
| **Touch paths** | `.cursor/skills/mat-plan-contract/SKILL.md`, `scripts/adoption/adoption-layout-v1.json`, `docs/reference/components.md`, `README.md` |
| **Acceptance criteria stub** | Skill encodes Decisions A–D; bootstrap packages skill; commands link to skill |

## Relevant Files / Areas

| Path | Role |
|------|------|
| `specs/shared-plan-contract.md` | **This file** — canonical v0.1 design |
| `specs/planning-artifacts-validation.md` | Structural precedent (decisions, grandfather, Session 2 checklist) |
| `docs/archive/planf3-comparison-2026-07.md` | Semantic borrowing source; implementation order context |
| `ROADMAP.md` L91–144 | Later → Planning & execution contracts checkboxes |
| `docs/guides/planning-commands-guide.md` | Handoff and projection rules |
| `.cursor/commands/mat-plan.md` | Standard tier 13-section contract |
| `.cursor/commands/mat-plan-onboarding.md` | Onboarding tier package |
| `.cursor/commands/mat-plan-team.md` | Execution orchestration + MAO |
| `docs/templates/adoption-minimal-current-plan.md` | Lite tier template |
| `docs/templates/tasks-schema.json` | Onboarding `tasks.json` schema |
| `docs/templates/tasks-schema-mat-plan-team.json` | Team tasks profile |
| `scripts/validate_planning_artifacts.py` | Existing Tier 1–3; extension point Slice 4 |
| `docs/reference/workflow-artifact-contract.md` | Authoritative handoff gates |
| `docs/reference/todo-orchestration.md` | MAO advisory model |
| Future `docs/architecture/plan-contract.md` | Operator projection target (appendix below) |

## Task Traceability

| Task ID | Work unit | Traces to |
|---------|-----------|-----------|
| TASK-001 | Document depth tiers `lite` / `standard` / `onboarding` | Decision A; Objective §1 |
| TASK-002 | Reconcile solo spec, onboarding package, `current-plan` projection | Decision B; Problem Statement |
| TASK-003 | Specify amendments protocol (format, files, authority) | Decision C; Slice 2 stub |
| TASK-004 | Specify status marker state machine + authority vs MAO/handoffs | Decision D; Slice 3 stub |
| TASK-005 | Align grandfathering with validator registries | Decision G; Assumption 6 |
| TASK-006 | Order implementation Slices 2–6 with acceptance stubs | Decision J; ROADMAP anchor |
| TASK-007 | Draft architecture projection appendix | Objective §5; Session 2 checklist |
| TASK-008 | Binary acceptance criteria for design spec approval | Acceptance Criteria section |

## Testing Strategy

### Manual verification (this design spec — before any build slice)

1. Human reviewer confirms Decisions A–J match MAT orchestration constraints (MAO blocked bundle, file handoffs authoritative).
2. Confirm `## Amendments` placement choice (second-to-last on solo specs) does not break Tier 2 order — if it would, Slice 2 must add Tier 2 alias or validator exception (flag as open risk).
3. Operator review: appendix is sufficient to seed `docs/architecture/plan-contract.md` without copying the full spec.

### Automated coverage (future slices)

| Slice | Automated checks |
|-------|------------------|
| Slice 2 | Doc substring tests in `tests/test_workflow_docs.py` (if MAINTAINER locks added) |
| Slice 3 | Builder/agent doc tests; optional fixture orchestration replay |
| Slice 4 | `tests/test_planning_artifacts_validation.py` Tier 4 fixtures |
| Slice 5–6 | `phase1-verify.sh` green; skill packaging manifest tests if applicable |

### Edge cases and regression focus

- Long-run multi-slice: amendments append across slices; `current-plan` replaced — archive prior slice amendments in `long-run-state.md` (operator SOP, not v0.1 automation).
- `inline` parent execution: parent may mutate markers (builder role merged).
- Grandfathered solo spec edited for new feature: Tier 2 may start failing — operator adds full 13 sections or keeps grandfather via registry update (explicit MAINTAINER act).
- Marker/gate disagreement: verifier must not FAIL solely on marker drift if `build-result.md` PASS and criteria met.
- Onboarding package without `plan-summary` amendments: Slice 2 command edit must require section on new packages only.

### TDD expectation for later build phases

**Not strict TDD** for doc/command slices (2–3). Slice 4 validator tests should follow `planning-artifacts-validation.md` pattern (fixtures + unittest). Verifier runs `bash scripts/phase1-verify.sh` on MAT source when acceptance criteria include CI.

## Acceptance Criteria

Binary checks for **approval of this design spec** (before any implementation):

- [ ] `specs/shared-plan-contract.md` exists with preflight classification `ready_for_execution_handoff` and contract version `0.1`.
- [ ] Decisions A–J are present with labeled tables covering depth tiers, three-schema reconciliation, amendments, status markers, grandfathering, and slice order.
- [ ] Decision B explicitly states `docs/current-plan.md` is a **projection**, not a fourth schema.
- [ ] Decision C lists which files receive `## Amendments` and append-only / authority rules.
- [ ] Decision D defines marker transitions `[]` → `[wip]` → `[x]` / `[f]` and names `build-result.md` / `verify-result.md` as gate-authoritative.
- [ ] Slices 2–6 each have scope, touch paths, and acceptance-criteria stub for future `/mat-plan-team`.
- [ ] Architecture projection appendix is present and labeled for copy into `docs/architecture/plan-contract.md`.
- [ ] No implementation files (`commands`, `templates`, `skills`, `validate_planning_artifacts.py`) were modified in this session.
- [ ] `Recommended Next Command` lists human review, operator projection, and Slice 2 `/mat-plan-team` entry.

## Risks and Open Questions

| Risk / question | Mitigation / resolution |
|-----------------|-------------------------|
| `## Amendments` placement vs Tier 2 section order | Slice 2 adds validator allowance: either fixed position before `Recommended Next Command` or Tier 2 update — **open until Slice 2 planning** |
| Operators confuse markers with MAO todos | Decision D explicit; architecture appendix stresses advisory vs authoritative |
| Lite vs standard execution shape ambiguity | Require one-line tier declaration in `docs/current-plan.md` header in Slice 5 |
| Validator Tier 4 scope creep | Slice 4 limited to amendments + marker syntax; no full execution-plan semantic lint in v0.1 |
| Adopted repos miss contract | Package via `.mat/docs/` in Slice 6; lite default sufficient for bootstrap |
| planf3 comparison stale vs shipped validator | Archive updated 2026-07-01; this spec cites shipped baseline |

**Open for human approval before Slice 2:**

1. Confirm amendments on optional solo `specs/<slug>.md` (recommended but not required in Slice 2).
2. Confirm status markers required only on `docs/current-plan.md` (not onboarding `tasks.json` statuses).
3. Confirm Slice 2 does not require validator changes (docs/commands only).

## Recommended Next Command

**Human refinement → operator projection → first implementation slice**

1. **Human review/approval** of `specs/shared-plan-contract.md` — confirm Decisions A–J and open questions above.
2. **Operator projection** — copy/adapt the Architecture projection appendix below into `docs/architecture/plan-contract.md`; promote ROADMAP items (*Shared MAT plan contract*, *Amendments*, *In-plan status markers*) from **Later → Next** with link to the architecture doc. Do not implement from roadmap bullets alone.
3. **Fresh session** — run:

   ```text
   /mat-plan-team Execute Slice 2 (Amendments only) per specs/shared-plan-contract.md Decision C and Slice 2 stub
   ```

Do **not** implement Slice 2 in the planning session that authored this file. Do **not** escalate to `/mat-plan-onboarding` unless human review finds scope insufficient.

---

## Session 2 projection checklist (operator)

Use after human approval, before `/mat-plan-team` Slice 2:

- [ ] `docs/architecture/plan-contract.md` created from appendix (shorter operator-facing doc).
- [ ] `ROADMAP.md` updated: relevant checkboxes moved to **Next** with link to architecture doc; **Last updated** bumped.
- [ ] `docs/current-plan.md` projected for **Slice 2 only** (Amendments; no status-marker or validator work).
- [ ] MAO todos initialized if using orchestrated flow (`[mao:plan]`, `[mao:build]`, `[mao:validate]`).
- [ ] Builder prompt cites `specs/shared-plan-contract.md` Decision C and explicit touch paths from Slice 2 stub.
- [ ] Verifier prompt cites Slice 2 acceptance criteria stub only.

---

## Appendix — Architecture projection (for `docs/architecture/plan-contract.md`)

> **Operator note:** Copy the block below into `docs/architecture/plan-contract.md` when promoting ROADMAP items. Edit for brevity; link to `specs/shared-plan-contract.md` for full decisions.

```markdown
# MAT Plan Contract (v0.1)

**Status:** Adopted (operator projection from `specs/shared-plan-contract.md`)  
**Full design:** [`specs/shared-plan-contract.md`](shared-plan-contract.md)

## Purpose

One semantic contract across MAT planning and execution depths so amendments, in-plan progress markers, and validators share rules without merging file formats.

## Depth tiers

| Tier | Commands | Artifacts |
|------|----------|-----------|
| **lite** | `/mat-sprint`, adoption bootstrap | Minimal `docs/current-plan.md` (task, criteria, verification) |
| **standard** | `/mat-plan`, `/mat-plan-team`, `/mat-long-run` | `specs/<slug>.md` (planning) → projected `docs/current-plan.md` (execution) |
| **onboarding** | `/mat-plan-onboarding` | `specs/<slug>/` four-file package + `tasks.json` |

`docs/current-plan.md` is always a **projection** of approved planning truth — not a separate schema.

## Living-plan extensions

### Amendments

- Append-only `## Amendments` with ISO-8601 UTC timestamps.
- **Required on:** `docs/current-plan.md`, `specs/<slug>/plan-summary.md`.
- **Authority:** operator/parent; builder may append during active build for drift; verifier read-only.

### Status markers (execution plans)

- Checklist markers: `[]` idle · `[wip]` in progress · `[x]` done · `[f]` failed/blocked.
- **Builder** mutates during implementation; **gates** still use `build-result.md` / `verify-result.md`.
- MAO todos remain **advisory** — not a substitute for markers or handoff files.

## Truth hierarchy

1. **Planning:** `specs/` (solo or package) — upstream approved intent.
2. **Execution:** `docs/current-plan.md` — active slice steps and markers.
3. **Outcome gates:** `build-result.md`, `verify-result.md` — orchestration transitions.
4. **MAO todos:** advisory traceability only.

## Drift rule

If execution diverges from planning, update planning artifacts first, then re-project `docs/current-plan.md`.

## Implementation slices

1. Design spec (`specs/shared-plan-contract.md`) — done.
2. Amendments (commands/templates).
3. Status markers (builder + execution template).
4. Validator Tier 4 (optional CI).
5. Template unification + validation loops.
6. `.cursor/skills/mat-plan-contract/SKILL.md` + `.mat/` packaging.

## Grandfathering

Legacy solo plans in validator `LEGACY_SOLO_PLANS` and idle execution plans are not retrofitted until substantively edited. New artifacts follow v0.1 on creation.
```
