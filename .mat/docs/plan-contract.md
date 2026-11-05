# MAT Plan Contract (v0.1)

**Status:** Adopted — operator projection from [`specs/shared-plan-contract.md`](specs/shared-plan-contract.md) (design approved 2026-07-01)  
**Full design:** [`specs/shared-plan-contract.md`](specs/shared-plan-contract.md) (Decisions A–J, slice stubs, grandfathering)

## Purpose

One semantic contract across MAT planning and execution depths so amendments, in-plan progress markers, and validators share rules without merging file formats.

Do not implement from [`ROADMAP.md`](../../ROADMAP.md) bullets or [`docs/archive/planf3-comparison-2026-07.md`](../archive/planf3-comparison-2026-07.md) alone — use this doc plus the full design spec for slice scope.

**Preflight vocabulary (Decision H):** Planning preflight terms (`solo_plan_only`, `ready_for_execution_handoff`, `needs_plan_onboarding`) stay separate from execution preflight terms (`inline`, `builder_plus_verifier`, `parallel_spawn`). Escalation routing: [`docs/architecture/preflight-escalation-ladder.md`](preflight-escalation-ladder.md).

## Depth tiers

**Depth router (optional DX):** `/mat-plan --depth=…` is a thin alias router documented in [`.cursor/commands/mat-plan.md`](../../.cursor/commands/mat-plan.md#depth-router-depth); it does not change tier semantics or replace direct commands.

| Tier | Commands | Artifacts | Execution template |
|------|----------|-----------|-------------------|
| **lite** | `/mat-sprint`, adoption bootstrap | Minimal `docs/current-plan.md` (task, criteria, verification) | [`docs/templates/adoption-minimal-current-plan.md`](../templates/adoption-minimal-current-plan.md) |
| **standard** | `/mat-plan`, `/mat-plan-team`, `/mat-long-run` | `specs/<slug>.md` (planning) → projected `docs/current-plan.md` (execution) | [`docs/templates/execution-plan-template.md`](../templates/execution-plan-template.md) |
| **onboarding** | `/mat-plan-onboarding` | `specs/<slug>/` four-file package + `tasks.json` | Bridge via `plan-summary.md`; execution uses lite or standard template |

`docs/current-plan.md` is always a **projection** of approved planning truth — not a separate schema.

## Living-plan extensions

### Amendments (Slice 2 — shipped in commands/templates)

- Append-only `## Amendments` with ISO-8601 UTC timestamps (`YYYY-MM-DDTHH:MM:SSZ`).
- **Required on:** `docs/current-plan.md`, `specs/<slug>/plan-summary.md`.
- **Optional on:** root `specs/<slug>.md` when used as a living planning doc.
- **Authority:** operator/parent; builder may append during active build for drift; verifier read-only.
- **Placement:** On solo `/mat-plan` specs, `## Amendments` is second-to-last; `## Recommended Next Command` remains last (Tier 2 validator allows this order).

### Update workflow (v1)

- **Command:** [`/mat-plan-update`](../../.cursor/commands/mat-plan-update.md) — planning-only surgical amendments to existing `specs/` artifacts.
- **Classify:** `surgical_amendment` (in-place minimal edit + one append-only amendment line) vs `escalate_to_onboarding` when package/traceability needs exceed surgery.
- **Targets:** primary `specs/<slug>.md` and `specs/<slug>/plan-summary.md`; optional `spec.md` / `prd.md` only when clearly scoped (prefer package bridge for slice drift).
- **Drift:** update planning truth first; **do not** auto-edit active `docs/current-plan.md` inside `/mat-plan-update` — operator re-projects after approval, then execution resumes via `/mat-plan-team` or `/mat-long-run`.
- **Routing:** [`docs/guides/planning-commands-guide.md`](../guides/planning-commands-guide.md) · Layer 2 in [`preflight-escalation-ladder.md`](preflight-escalation-ladder.md).

### Status markers (Slice 3 — shipped in agents/commands/templates)

- Checklist markers: `[]` idle · `[wip]` in progress · `[x]` done · `[f]` failed/blocked.
- **Builder** mutates in-place during implementation (`[] → [wip] → [x]` or `[f]` with reason); **gates** still use `build-result.md` / `verify-result.md`.
- **Parent** may set `[wip]` at slice start; **verifier** read-only (warn-not-fail on marker drift when build handoff passes).
- MAO todos remain **advisory** — not a substitute for markers or handoff files.

## Truth hierarchy

1. **Planning:** `specs/` (solo or package) — upstream approved intent.
2. **Execution:** `docs/current-plan.md` — active slice steps and markers (optional `## Plan metadata` is an **audit-only** subsection on this layer — not a separate schema).
3. **Outcome gates:** `build-result.md`, `verify-result.md` — orchestration transitions.
4. **MAO todos / hook events:** advisory traceability only — **not** superseded by Plan metadata.

Optional **Canvas visualization** via [`.cursor/skills/mat-plan-canvas/SKILL.md`](../../.cursor/skills/mat-plan-canvas/SKILL.md) is a derived, read-only view — it does not alter this hierarchy.

Optional `## Plan metadata` on `docs/current-plan.md` complements `docs/session-summary.md` and MAO transition events; it does **not** replace them and is **not** layer-4 MAO authority.

### Planning Step 0 (SOP)

Planning commands (`/mat-plan`, `/mat-plan-onboarding`) require **Step 0 — Deep analysis** before any planning artifact writes. This is a **planning SOP / cognitive gate only** — not a validator tier, hook, MAO transition, or layer-4 MAO authority. Truth hierarchy above is unchanged: Step 0 governs *when* planning agents may start writing `specs/` artifacts; execution Step 0 (Preflight decision, MAO todos) remains orchestration preflight only. Canonical wording: [`.cursor/commands/mat-plan.md`](../../.cursor/commands/mat-plan.md) Workflow; operator routing: [`docs/guides/planning-commands-guide.md`](../guides/planning-commands-guide.md#deep-analysis-before-writes). Doc-test lock: `DeepAnalysisStep0Test` in `tests/test_workflow_docs.py`.

### Planning doc inputs (SOP, optional-when-present)

After Step 0, `/mat-plan` workflow step 2 and `/mat-plan-onboarding` step 3 may **optionally** narrow-read from `docs/` and `ai_docs/` when those directories exist — skip-when-absent; no validator tier. Complements Step 0 path scoping. Operator routing: [`docs/guides/planning-commands-guide.md`](../guides/planning-commands-guide.md#planning-doc-inputs-docs--ai_docs). Doc-test lock: `PlanningDocsInputsTest` in `tests/test_workflow_docs.py`.

## Drift rule

If execution diverges from planning, update planning artifacts first, then re-project `docs/current-plan.md`.

## Implementation slices

| Slice | Scope | Status |
|-------|-------|--------|
| 1 | Design spec (`specs/shared-plan-contract.md`) | **Done** |
| 2 | Amendments (commands/templates) | **Done** |
| 3 | Status markers (builder + execution template) | **Done** |
| 4 | Validator Tier 4 (optional CI) | **Done** |
| 5 | Template unification + validation loops | **Done** |
| 6 | `.cursor/skills/mat-plan-contract/SKILL.md` + `.mat/` packaging | **Done** — skill at [`.cursor/skills/mat-plan-contract/SKILL.md`](../../.cursor/skills/mat-plan-contract/SKILL.md); operator summary packaged to `.mat/docs/plan-contract.md` on bootstrap |

**`/mat-plan` validation loops (Tier 2b):** Solo specs embed per-phase and global **loop until pass** subsections under `## Testing Strategy` (not a 14th top-level section). Tier 2b checks are enforced by `scripts/validate_planning_artifacts.py`; grace registry `VALIDATION_LOOPS_GRANDFATHERED_SOLO_PLANS` mirrors `LEGACY_SOLO_PLANS` opt-in-on-edit policy. Specimen: [`specs/mat-plan-validation-loops.md`](specs/mat-plan-validation-loops.md).

### Execution validation loops (Tier 2b discipline)

Standard and lite execution projections must carry the same operating discipline as Tier 2b: a `### Per-phase validation loops (loop until pass)` table with repo-native commands and a `### Global validation commands (before handoff)` numbered list. Each phase is fixed and re-run until green before the global commands run for handoff. The canonical standard shape lives in [`docs/templates/execution-plan-template.md`](../templates/execution-plan-template.md); `/mat-plan-team` and `/mat-sprint` must preserve these sections whenever they author or re-project `docs/current-plan.md`.

This is execution guidance, not an expansion of the Tier 2b solo-spec validator. Markdown remains the canonical execution contract. MAT commands and templates must not create or require a living HTML plan; HTML may only be a derived, non-authoritative visualization outside the execution handoff.

**`/mat-plan` Relevant Files tagging (Tier 2c):** Every markdown list bullet under `## Relevant Files / Areas` (alias `## Relevant Files`) must start with **`[new]`** or **`[existing]`** (case-sensitive; one space after `]` allowed). Table rows are out of v1 scope — bullets are the validated shape. Issue codes: `tier2_relevant_files_no_bullets`, `tier2_relevant_files_untagged_bullet`, `tier2_relevant_files_invalid_tag`. Grace registry: `RELEVANT_FILES_TAG_GRANDFATHERED_SOLO_PLANS` (separate from `LEGACY_SOLO_PLANS` and `VALIDATION_LOOPS_GRANDFATHERED_SOLO_PLANS`); opt-in-on-edit when a grandfathered spec is revised. Implements [`specs/shared-plan-contract.md`](specs/shared-plan-contract.md) Decision I. Exemplar: [`specs/planf3-polish-mission.md`](../../specs/planf3-polish-mission.md).

**`/mat-plan` Related plans (Tier 2d, optional-when-present):** Tail-zone `## Related plans` on solo specs (after required sections 1–12; before optional `## Amendments` / `## Recommended Next Command`) with required level-3 subsections `### back_refs` and `### forward_refs`. Each subsection needs ≥1 list bullet with a backtick-quoted repo-root-relative path ending in `.md` or `.json`. Issue codes: `tier2_related_plans_missing_back_refs`, `tier2_related_plans_missing_forward_refs`, `tier2_related_plans_empty_subsection`, `tier2_related_plans_unquoted_path`. Grace registry: `RELATED_PLANS_GRANDFATHERED_SOLO_PLANS` (separate frozenset; opt-in-on-edit). No path-existence or graph validation in v1. Implements [`specs/shared-plan-contract.md`](specs/shared-plan-contract.md) Decision B tail-zone optional tiers. Exemplar: [`specs/planf3-audit-trail-mission.md`](../../specs/planf3-audit-trail-mission.md).

**`/mat-plan` Open Decisions (Tier 2e, optional-when-present):** Tail-zone `## Open Decisions` on solo specs (after optional `## Related plans` when both present; before optional `## Amendments` / `## Recommended Next Command`). Each list bullet must match `**OD-###** | status: `open|resolved|deferred` | …`. Distinct from `## Assumptions` and `## Risks and Open Questions`. Issue codes: `tier2_open_decisions_malformed_row`, `tier2_open_decisions_invalid_status`; verbose-only `tier2_open_decisions_resolved_missing_provenance` for resolved rows without ISO date provenance. Grace registry: `OPEN_DECISIONS_GRANDFATHERED_SOLO_PLANS`. Onboarding chat one-at-a-time gate remains canonical; file mirror after each resolution. Architecture: [`docs/architecture/open-decisions-optional-tier.md`](open-decisions-optional-tier.md). Exemplar: [`specs/planf3-audit-trail-mission.md`](../../specs/planf3-audit-trail-mission.md).

**Execution Plan metadata (Tier 4 extension, optional-when-present):** Optional `## Plan metadata` on substantive `docs/current-plan.md` only — **not** YAML frontmatter. When present, requires level-3 subsections `### modified`, `### session`, and `### commit`, each with ≥1 append-only list bullet. Issue codes: `tier4_metadata_missing_modified`, `tier4_metadata_missing_session`, `tier4_metadata_missing_commit`, `tier4_metadata_malformed_entry`. Absent section or idle/placeholder skip → no metadata failures. Coexists with `## Amendments` and status markers; does not replace Amendments or `/mat-plan-update` drift flow. Authority: operator/parent append only; builder/verifier read-only; audit-only (layer 2 execution artifact, not layer 4 MAO). Hooks do not auto-write metadata. Templates: [`docs/templates/execution-plan-template.md`](../templates/execution-plan-template.md), [`docs/templates/adoption-minimal-current-plan.md`](../templates/adoption-minimal-current-plan.md). Exemplar fixture: [`tests/fixtures/planning/plan-metadata-pass.md`](../../tests/fixtures/planning/plan-metadata-pass.md).

**`/mat-plan` Task type / Complexity tags (optional-when-present):** Solo specs may include header lines `**Task type:** \`…\`` and `**Complexity:** \`…\`` (markdown, **not** YAML frontmatter). Allowlists: task type `chore|feature|refactor|fix|enhancement`; complexity `simple|medium|complex`. Soft Tier 2 checks (`tier2_task_type_invalid`, `tier2_complexity_invalid`) when present; absence is valid. Tags are depth hints only — they do **not** change required `/mat-plan` sections and do **not** restore planf3 V3 auto-preflight gates. Documented in [`.cursor/commands/mat-plan.md`](../../.cursor/commands/mat-plan.md) Content Rules.

## Grandfathering

Legacy solo plans in validator `LEGACY_SOLO_PLANS` and idle execution plans are not retrofitted until substantively edited. New artifacts follow v0.1 on creation. Tier 1–3 target `specs/`; Tier 4 enforces amendments and marker syntax on substantive `docs/current-plan.md` only.
