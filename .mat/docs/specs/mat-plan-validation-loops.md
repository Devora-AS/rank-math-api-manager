> **Preflight classification:** `ready_for_execution_handoff` — bounded design for extending Decision E validation loops into `/mat-plan`'s Tier 2 contract. Human approval required before `/mat-plan-team` build slice or projection to `docs/current-plan.md`. **Planning only** — no implementation in this session.

# MAT Plan Validation Loops — `/mat-plan` Tier 2 Extension

## Task Description

Close the **partial** ROADMAP Later item *Validation loops in planning templates* (L112–113) by defining how **Decision E** validation-loop semantics integrate into `/mat-plan`'s fixed 13-section solo spec contract **without** adding a new top-level section or breaking `scripts/validate_planning_artifacts.py` Tier 2 section order.

Plan contract v0.1 Slices 1–6 are **done** on `main` (remote CI green). Slice 5 shipped per-phase and global validation-loop prose in **lite** and **standard execution templates** only (`docs/templates/adoption-minimal-current-plan.md`, `docs/templates/execution-plan-template.md`) plus a cross-link in `docs/templates/spec-template.md`. The meta-skill already documents Decision E SOP at a high level. This spec scopes the **remaining** gap: `/mat-plan` command instructions and optional Tier 2 content checks for new `specs/<slug>.md` files.

## Objective

Produce an implementable contract so a future `/mat-plan-team` slice can:

1. Update `.cursor/commands/mat-plan.md` so new solo plans embed validation-loop SOP inside `## Testing Strategy`.
2. Optionally extend `validate_planning_artifacts.py` Tier 2 with content checks that mirror execution-template patterns.
3. Grandfather existing `specs/*.md` without a big-bang retrofit.
4. Allow ROADMAP partial-closeout wording to reflect `/mat-plan` coverage while keeping execution templates unchanged.

## Scope

### In scope

- Section placement and canonical subsection headings inside `## Testing Strategy`.
- Required prose/table pattern (per-phase command + **loop until pass** + global validation block).
- Grandfather and opt-in-on-edit policy aligned with `LEGACY_SOLO_PLANS` and Decision G.
- Future build-slice touch paths: `.cursor/commands/mat-plan.md`, `scripts/validate_planning_artifacts.py`, `tests/test_planning_artifacts_validation.py`, operator docs (`docs/architecture/plan-contract.md`, `docs/guides/planning-commands-guide.md`, `docs/reference/MAINTAINER.md`), doc-test lock in `tests/test_workflow_docs.py`, ROADMAP checkbox update.
- Projection note: when a solo spec with validation loops is approved, parent copies loop blocks into projected `docs/current-plan.md` `## Verification plan` (execution template already has the target shape).

### Out of scope (this spec and the build slice it defines)

- Rewriting `.cursor/skills/mat-plan-contract/SKILL.md` beyond a one-line cross-link if strictly needed (see Non-Goals).
- Editing `docs/templates/execution-plan-template.md` or `docs/templates/adoption-minimal-current-plan.md` (Slice 5 delivered).
- Onboarding four-file package changes (`spec-template.md` already cross-links Decision E for downstream execution).
- Tier 4 execution-plan validator changes (loops stay SOP; hard gates remain handoff files).
- Making in-plan loop prose authoritative for MAO transitions.

## Assumptions

1. **Tier 2 section list stays fixed** — `MAT_PLAN_REQUIRED_SECTIONS` in `scripts/validate_planning_artifacts.py` continues to enumerate exactly 13 headings; `## Amendments` remains optional and may appear between `Risks and Open Questions` and `Recommended Next Command` without entering the required list (same as Slice 2).
2. **Decision E authority model unchanged** — validation loops are **SOP for builders/subagents**; `build-result.md` / `verify-result.md` and hook gates remain the **hard** orchestration truth (`specs/shared-plan-contract.md` Decision E).
3. **Execution projection is human-owned** — operators copy or adapt loop blocks from `## Testing Strategy` into `## Verification plan` when projecting to `docs/current-plan.md`; no automatic projection tooling in v0.1.
4. **Stdlib-only validator posture** — Tier 2 loop checks use substring/structure heuristics (headings, table columns, numbered lists), not new pip dependencies.
5. **Source repo only** — Tier 2 applies to MAT source `specs/`; adopted sidecar trees keep existing skip behavior in `phase1-verify.sh`.

## Non-Goals

- **Meta-skill rewrite** — do not expand `.cursor/skills/mat-plan-contract/SKILL.md` Decision E beyond an optional single-line pointer to `/mat-plan` subsection names after the build slice; procedural SOP already lives there and in `docs/architecture/plan-contract.md`.
- **Execution template changes** — do not modify lite/standard execution templates; they are the projection **target**, not the planning **source**.
- New top-level `/mat-plan` section (e.g. `## Validation commands`) — rejected because it would break Tier 2 order or require a 14th required heading.
- Enforcing loop completion at plan-write time (plans describe SOP; builders execute loops during build).
- Retrofitting all historical `specs/*.md` in one PR.
- Unifying planning preflight (`solo_plan_only`) with execution preflight (`builder_plus_verifier`) — deferred ROADMAP item.

## Problem Statement

MAT borrowed planf3 **validation-without-enforcement** semantics: in-document **loop until pass** instructions guide builders while hook-enforced handoffs gate orchestration (`docs/archive/planf3-comparison-2026-07.md` Key Learnings § "Validation without enforcement is still valuable").

| Surface | Validation loops today | Gap |
|---------|------------------------|-----|
| Lite execution template | `## Verification plan` subsections shipped (Slice 5) | None for lite tier |
| Standard execution template | Same | None for standard execution |
| `/mat-plan` solo spec | `## Testing Strategy` requires manual/automated/TDD prose only | No required per-phase command table or global block |
| Tier 2 validator | Section order + non-empty bodies | No loop-structure checks |
| Meta-skill | Decision E points at Testing Strategy / Verification plan | No `/mat-plan`-specific subsection contract |

Operators authoring `/mat-plan` specs therefore produce **testing intent** without the **executable loop SOP** that execution templates already encode, causing drift at projection time and leaving ROADMAP L112–113 partially unchecked.

## Solution Approach

### Decision — placement inside `## Testing Strategy` (not a new top-level section)

**Chosen:** extend **section 10 only** via two **level-3 subsections**. Do **not** add `## Verification plan` or `## Validation commands` as top-level `/mat-plan` sections.

**Rationale:**

- `specs/shared-plan-contract.md` Decision E already maps standard planning loops to `## Testing Strategy`.
- Tier 2 validates a fixed ordered list ending at `Recommended Next Command`; inserting a new `##` would fail `tier2_section_order` or force a breaking 14-section migration.
- Existing specs already use rich `###` subsections under Testing Strategy (manual, automated, edge cases, TDD); validation loops fit the same pattern.

**Canonical subsection order** within `## Testing Strategy` (recommended; not all enforced by validator):

1. `### Manual verification` (or equivalent — existing command rule)
2. `### Automated coverage` (implementation phase) — optional heading variants allowed
3. `### Edge cases` / `### Edge cases and regression focus`
4. `### TDD expectation` (for later build phase)
5. **`### Per-phase validation loops (loop until pass)`** — **new, required for non-grandfathered specs after build slice**
6. **`### Global validation commands (before handoff)`** — **new, required for non-grandfathered specs after build slice**

Subsections 5–6 must appear **after** testing-intent subsections (1–4) and **before** `## Acceptance Criteria`. If a plan omits 1–4 for a trivial slice, 5–6 still required.

### Decision — required prose pattern

Mirror execution-template semantics (`docs/templates/execution-plan-template.md` L47–62) inside Testing Strategy.

#### Per-phase block (required)

Use exact level-3 heading:

```markdown
### Per-phase validation loops (loop until pass)

| Phase | Command | Loop until pass |
|-------|---------|-----------------|
| <phase name> | `<shell command>` | Re-run after fixes until green |
```

**Rules:**

- Minimum **one** table row (plus header).
- **Command** column must contain a backtick-wrapped or plain shell command invocable from repo root.
- **Loop until pass** column must include the phrase **`loop until pass`** OR **`Re-run`** + **`until`** (case-insensitive) — prefer the literal phrase **loop until pass** for consistency with Decision E and execution templates.
- Phase names are free text tied to planned tasks (e.g. unit tests, lint, doc contract tests).

#### Global block (required)

Use exact level-3 heading:

```markdown
### Global validation commands (before handoff)

1. `<command>` — loop until pass / re-run until exit 0
2. `<command>` — …
```

**Rules:**

- Minimum **one** numbered command.
- Final global command for MAT source repo slices should normally include `bash scripts/phase1-verify.sh` when the slice touches repo-wide gates (document exception in Risks if omitted).
- Include a single advisory line (plain text, not a new section) that hard orchestration gates remain `build-result.md` / `verify-result.md` — may reuse execution-template comment wording.

#### Relationship to existing Testing Strategy rules

Retain current `/mat-plan` Content Rules (manual verification, automated coverage later, edge cases, TDD expectation). Validation-loop subsections **add** executable SOP; they do not replace testing-intent prose.

### Decision — `/mat-plan` command edits (build slice)

Update `.cursor/commands/mat-plan.md` **Content Rules** under Testing Strategy:

- Require subsections 5–6 for all new plans after the build slice lands.
- Point to `docs/templates/execution-plan-template.md` as the **shape reference** for loop tables (planning uses Testing Strategy; execution uses Verification plan).
- State that `solo_plan_only` plans still include loop blocks when they describe future implementation verification (commands may be `N/A — planning only` only when **no** implementation will follow — rare; prefer explicit doc-review commands).

### Decision — Tier 2 validator extension (build slice)

Add **Tier 2b** content checks inside `validate_tier2()` **after** existing section-order and non-empty checks, **only for non-skipped** solo plans:

| Check | Code | Rule |
|-------|------|------|
| Per-phase heading | `tier2_missing_validation_loops_per_phase` | `## Testing Strategy` body contains `### Per-phase validation loops (loop until pass)` |
| Per-phase table | `tier2_validation_loops_per_phase_table` | Subsection includes a markdown table with header row containing `Command` and `Loop until pass` (case-insensitive) and ≥1 data row |
| Global heading | `tier2_missing_validation_loops_global` | Body contains `### Global validation commands (before handoff)` |
| Global commands | `tier2_validation_loops_global_commands` | Subsection has ≥1 numbered list item matching `^\d+\.\s` |
| Loop phrase | `tier2_validation_loops_phrase` | Testing Strategy body contains `loop until pass` (case-insensitive) at least once |

**Soft vs hard:** ship as **hard fail** (exit 1) for non-grandfathered specs — consistent with existing Tier 2 posture. No separate CLI flag in v0.1 (avoid `--tier2-validation-loops` proliferation); grandfather registry controls rollout.

**Implementation helper:** extract `## Testing Strategy` body via existing `extract_markdown_section()`; locate subsections by `###` heading prefix match (trimmed, case-sensitive heading text for the two canonical names).

### Decision — grandfather policy

Align with Decision G and `LEGACY_SOLO_PLANS` patterns in `scripts/validate_planning_artifacts.py`.

| Class | Validation-loop requirement |
|-------|----------------------------|
| **`LEGACY_SOLO_PLANS`** | Exempt — remain skipped entirely for Tier 2 (no section checks, no loop checks). |
| **Approval sidecars** (`*-APPROVAL.md`) | Exempt — already skipped. |
| **Solo spec when `specs/<slug>/` exists** | Exempt — package authoritative. |
| **Non-grandfathered `specs/*.md` at build slice merge** | **Opt-in grace period:** add current non-legacy solo specs to new `VALIDATION_LOOPS_GRANDFATHERED_SOLO_PLANS` frozenset at merge time (one-time MAINTAINER act) so CI stays green; only **new** specs created after merge must include loop subsections immediately. |
| **Substantive edit to a grandfathered spec** | Operator removes path from `VALIDATION_LOOPS_GRANDFATHERED_SOLO_PLANS` **or** adds loop subsections in the same edit; opt-in on edit, not silent forever. |
| **New `specs/<slug>.md` after grace registry** | Full Tier 2 + loop checks. |

**Registry maintenance:** document in `docs/reference/MAINTAINER.md` — same style as `LEGACY_SOLO_PLANS` (explicit path list, no glob magic).

**Initial grace set (build slice):** at implementation time, **do not hardcode** a static path list from this spec. After Tier 2b checks land, run `python3 scripts/validate_planning_artifacts.py --repo-root . --tier 2 --verbose` and add every failing non-legacy solo spec path to `VALIDATION_LOOPS_GRANDFATHERED_SOLO_PLANS` **except** specs that already include both canonical loop subsections (expected pass without grace: `specs/mat-plan-validation-loops.md`). Typical grace candidates at merge: `dependabot-client-policy.md`, `planning-artifacts-validation.md`, `shared-plan-contract.md`, `observability-server-dashboard-review-plan.md`, `project-first-capability-router-v1.md`, `mat-agent-model-router-boundary-v1.md`, and any other tracked solo spec missing loop blocks. Include `specs/mat-adopt-onboarding-unification.md` **only if it is tracked in git at merge time**; if still untracked (parallel adoption work), omit from the registry — validator only scans tracked `specs/*.md` on disk but CI uses the committed tree.

### Decision — projection to execution

When `ready_for_execution_handoff` solo specs are approved:

1. Parent copies **Per-phase** table and **Global** numbered list from `## Testing Strategy` into `docs/current-plan.md` `## Verification plan` (subsection headings may stay identical to execution template).
2. Testing-intent subsections (manual, TDD, etc.) stay in the spec only unless operator chooses to summarize in `## Context`.
3. No validator requirement on projected files beyond existing Tier 4 (amendments/markers).

### ROADMAP closeout wording (build slice)

Update ROADMAP L112–113 to mark **done** with note: `/mat-plan` Testing Strategy subsections + Tier 2b checks; execution templates unchanged since Slice 5. Update `docs/archive/planf3-comparison-2026-07.md` Pending line to **Done** for `/mat-plan` extension.

## Relevant Files / Areas

| Path | Role |
|------|------|
| `specs/mat-plan-validation-loops.md` | **This file** — build-slice design |
| `specs/shared-plan-contract.md` | Decision E, G, Slice 5 stub |
| `docs/archive/planf3-comparison-2026-07.md` | Partial-closeout context L49, L108 |
| `ROADMAP.md` L112–113 | Checkbox to close after build |
| `.cursor/commands/mat-plan.md` | Primary command edit |
| `scripts/validate_planning_artifacts.py` | Tier 2b loop checks + grandfather registry |
| `tests/test_planning_artifacts_validation.py` | Fixtures for pass/fail loop structure |
| `tests/test_workflow_docs.py` | Doc substring lock for loop subsection names in `mat-plan.md` |
| `docs/templates/execution-plan-template.md` | **Reference only** — shape to mirror |
| `docs/architecture/plan-contract.md` | Operator summary — short Testing Strategy pointer |
| `docs/guides/planning-commands-guide.md` | `/mat-plan` vs execution verification |
| `docs/reference/MAINTAINER.md` | Grandfather registry documentation |
| `.cursor/skills/mat-plan-contract/SKILL.md` | **Read only** — no substantive rewrite |

## Task Traceability

| Task ID | Summary | Traces to |
|---------|---------|-----------|
| TASK-001 | Define Testing Strategy subsection placement | Problem Statement; Solution Approach placement decision |
| TASK-002 | Define per-phase + global prose pattern | Solution Approach prose pattern; Decision E in `shared-plan-contract.md` |
| TASK-003 | Define grandfather / grace registry policy | Solution Approach grandfather; Decision G |
| TASK-004 | Specify `/mat-plan` command Content Rules update | Solution Approach command edits |
| TASK-005 | Specify Tier 2b validator checks + issue codes | Solution Approach Tier 2 extension |
| TASK-006 | Specify tests + doc locks for build slice | Testing Strategy; Acceptance Criteria |
| TASK-007 | Specify ROADMAP / archive closeout | Scope; ROADMAP L112–113 |
| TASK-008 | Document execution projection copy rule | Solution Approach projection |

## Testing Strategy

### Manual verification (this planning spec)

1. Human reviewer confirms proposed subsections do not alter `MAT_PLAN_REQUIRED_SECTIONS` order.
2. Compare sample loop blocks side-by-side with `execution-plan-template.md` for semantic parity.
3. Confirm grandfather policy keeps `phase1-verify.sh` green at merge via grace registry.

### Automated coverage (implementation phase)

| Module | Focus |
|--------|--------|
| `tests/test_planning_artifacts_validation.py` | Pass fixture with full loop subsections; fail fixtures per issue code; grandfather skip notices |
| `tests/test_workflow_docs.py` | Optional lock for `Per-phase validation loops` in `mat-plan.md` |
| `bash scripts/phase1-verify.sh` | Full gate after validator + command edits |

### Edge cases and regression focus

- Spec with extra `###` subsections interleaved in Testing Strategy — canonical headings must still be present.
- Spec with `## Testing Strategy` alias typo — should fail existing `tier2_missing_section` before loop checks.
- Plan with loop table but no `loop until pass` phrase — `tier2_validation_loops_phrase` fails.
- Grandfathered spec edited without loops — remains pass until removed from grace set.
- `solo_plan_only` classification with implementation commands — loops still required when spec anticipates build.
- Amendments section present — must not appear between Testing Strategy and Acceptance Criteria.

### TDD expectation for build phase

**Test-after acceptable** for command/doc edits; **test-first recommended** for `validate_tier2` loop helpers (extract subsection, table row count) to lock issue codes before implementation.

### Per-phase validation loops (loop until pass)

| Phase | Command | Loop until pass |
|-------|---------|-----------------|
| Validator unit tests | `python3 -m unittest tests.test_planning_artifacts_validation -v` | Re-run after fixes until green |
| Command/doc contract | `python3 -m unittest tests.test_workflow_docs -v` | Re-run until green |
| Full repo gate | `bash scripts/phase1-verify.sh` | Re-run until exit 0 before handoff |

### Global validation commands (before handoff)

1. `python3 scripts/validate_planning_artifacts.py --repo-root .` — loop until pass (Tier 2b included).
2. `bash scripts/phase1-verify.sh` — re-run until exit 0.

Hard orchestration gates remain `build-result.md` / `verify-result.md`; in-plan loops are SOP for builders.

## Acceptance Criteria

Binary checks for the future `/mat-plan-team` build slice:

- [x] **AC-1:** `.cursor/commands/mat-plan.md` requires `### Per-phase validation loops (loop until pass)` and `### Global validation commands (before handoff)` under `## Testing Strategy` with table + numbered-list rules documented.
- [x] **AC-2:** `scripts/validate_planning_artifacts.py` enforces Tier 2b checks (five issue codes above) for non-skipped, non-`VALIDATION_LOOPS_GRANDFATHERED_SOLO_PLANS` specs.
- [x] **AC-3:** `VALIDATION_LOOPS_GRANDFATHERED_SOLO_PLANS` (or equivalent name) exists, populated so existing repo specs pass at merge; `LEGACY_SOLO_PLANS` behavior unchanged.
- [x] **AC-4:** `tests/test_planning_artifacts_validation.py` includes at least one pass and one fail fixture per new issue code family (heading, table, global list, phrase).
- [x] **AC-5:** `bash scripts/phase1-verify.sh` exits 0 on MAT source after changes.
- [x] **AC-6:** `docs/architecture/plan-contract.md`, `docs/guides/planning-commands-guide.md`, and `docs/reference/MAINTAINER.md` mention `/mat-plan` Testing Strategy loop subsections and grandfather registry (short pointer).
- [x] **AC-7:** ROADMAP L112–113 and `docs/archive/planf3-comparison-2026-07.md` updated to reflect `/mat-plan` completion (execution templates unchanged since Slice 5).
- [x] **AC-8:** No changes to `docs/templates/execution-plan-template.md`, `docs/templates/adoption-minimal-current-plan.md`, or substantive edits to `.cursor/skills/mat-plan-contract/SKILL.md`.
- [x] **AC-9:** `CHANGELOG.md` Unreleased entry for validation-loops `/mat-plan` extension.
- [x] **AC-10:** `tests/test_workflow_docs.py` includes a named lock (`test_mat_plan_validation_loops_in_command` or equivalent) for canonical subsection headings in `.cursor/commands/mat-plan.md`.

## Risks and Open Questions

| Risk | Mitigation |
|------|------------|
| Tier 2 heading strictness frustrates authors | Exact heading strings documented in command + MAINTAINER; table alias columns already case-insensitive |
| Grace registry rots | MAINTAINER entry + remove paths when specs substantively revised |
| Duplicate loop prose at projection | Operator copies once into Verification plan; spec remains planning truth |
| Adopted repos run validate_planning_artifacts | Unchanged skip posture for sidecar trees |

**Open questions (non-blocking for build slice):**

1. Should `CHANGELOG.md` entry reference ROADMAP closeout in the same PR? **Recommend yes** per repo hygiene.
2. Should `docs/templates/spec-template.md` gain the same subsection headings for onboarding? **Defer** — cross-link already points to execution; onboarding uses different section numbering.
3. Should `mat-plan-validation-loops.md` be listed as a command specimen? **Recommend yes** — one-line pointer in `mat-plan.md` to this file as loop-structure example (read-only reference, not a template file).

## Amendments

- 2026-07-02T12:00:00Z — planning-agent — Initial spec authored from `/mat-plan` partial-closeout request.
- 2026-07-02T14:00:00Z — parent-advisor — AC-9/AC-10 added; grace registry enumeration made dynamic; untracked `mat-adopt-onboarding-unification.md` handling clarified.
- 2026-07-02T16:00:00Z — parent-advisor — Build slice shipped (`9efadbf`); AC-1–AC-10 marked done; removed `mat-adopt-onboarding-unification.md` from `VALIDATION_LOOPS_GRANDFATHERED_SOLO_PLANS` (parallel spec gains loop subsections locally before track).

## Recommended Next Command

**Slice complete** — `/mat-plan-team` build landed in `9efadbf`. No further action on this spec unless grandfathered solo specs are migrated off `VALIDATION_LOOPS_GRANDFATHERED_SOLO_PLANS`.

Pick the next **ROADMAP** item (for example deep-analysis Step 0 or file tagging) with `/mat-plan` or `/mat-plan-team` as appropriate.
