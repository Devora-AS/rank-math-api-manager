# MAT Plan

Create a lightweight solo planning artifact and save it to `specs/<slug>.md`.

## Usage

```text
/mat-plan <task description>
/mat-plan --depth=<value> <task description>
/mat-plan --depth <value> <task description>
```

- **Canonical flag form:** `--depth=<value>` (preferred in docs and examples).
- **Accepted alternate:** `--depth <value>` (space-separated value).
- When `--depth` is **absent**, run the solo `/mat-plan` workflow below unchanged.
- When `--depth=standard` or `--depth standard`, treat as omitting `--depth` (solo `/mat-plan`).
- Direct commands (`/mat-sprint`, `/mat-plan-onboarding`, `/mat-plan-team`, `/mat-long-run`) remain valid; the router is optional DX only.

## Depth router (`--depth`)

Optional **thin, transparent router**: parse a leading `--depth` flag and dispatch to an existing slash command. **Explicit aliases only** — no fuzzy intent classification, no LLM routing, no merged command behavior.

### Fixed mapping (five values)

| `--depth` | Target command | Command file |
|-----------|----------------|--------------|
| `lite` | `/mat-sprint` | [`.cursor/commands/mat-sprint.md`](mat-sprint.md) |
| `standard` | `/mat-plan` (default solo workflow) | `.cursor/commands/mat-plan.md` (this file) |
| `onboarding` | `/mat-plan-onboarding` | [`.cursor/commands/mat-plan-onboarding.md`](mat-plan-onboarding.md) |
| `team` | `/mat-plan-team` | [`.cursor/commands/mat-plan-team.md`](mat-plan-team.md) |
| `long-run` | `/mat-long-run` | [`.cursor/commands/mat-long-run.md`](mat-long-run.md) |

### Parse procedure

1. Inspect the user prompt for a **leading** depth flag before the task text:
   - `--depth=<value>` (canonical), or
   - `--depth <value>` (accepted alternate).
2. If **no** `--depth` flag → continue with **Instructions** below (solo `/mat-plan`; unchanged).
3. If flag present and `value` is in the table:
   - **`standard`** → same as absent; continue with solo `/mat-plan` **Instructions** below.
   - **Any other valid value** → read the target **command file** from the table and follow its **Instructions** (not this file's solo planning guardrails).
   - Print **one transparency line** to the user before executing, e.g. `Dispatching to `/mat-plan-team` per `--depth=team`.`
   - Pass through the remaining task text (everything after the depth flag) as the target command's task argument.
4. If flag present but `value` is **not** in the table → **fail closed**:
   - Print the mapping table above.
   - State that routing uses explicit aliases only; do **not** auto-infer tier or fall back to solo `/mat-plan`.
   - Recommend invoking the target slash command directly.
   - **Stop** — do not write `specs/<slug>.md` or any planning artifact.

### Guardrails (router vs solo)

- **Solo `/mat-plan`** (no `--depth`, or `--depth=standard`): planning-only guardrails in **Instructions** below apply.
- **`team` and `long-run` dispatch:** follow the target orchestration command SOP (`/mat-plan-team`, `/mat-long-run`) — MAO todos, `docs/current-plan.md`, `build-result.md` / `verify-result.md` as documented there; **not** solo planning-only guardrails.
- **`lite` and `onboarding` dispatch:** follow `/mat-sprint` or `/mat-plan-onboarding` respectively.
- The router does **not** override Decision A in [`specs/shared-plan-contract.md`](../../.mat/docs/specs/shared-plan-contract.md): operators still choose the command that matches work shape; `--depth` is a convenience alias, not intent classification.

Operator cross-link: [`docs/guides/planning-commands-guide.md`](../../.mat/docs/guides/planning-commands-guide.md#depth-router).

## Instructions

**Plan contract skill:** For tier selection, amendments, status markers, and projection semantics, see [`.cursor/skills/mat-plan-contract/SKILL.md`](../skills/mat-plan-contract/SKILL.md) (does not replace this command).

You are a solo planning agent. Produce a bounded plan only. Do not implement anything in this command.

### Guardrails

- Planning only — no implementation.
- All assumptions and non-goals must be explicitly listed.
- `/mat-plan` stays lightweight and writes one file only: `specs/<slug>.md`.
- Do not create `docs/current-plan.md`, `build-result.md`, `verify-result.md`, or onboarding-package artifacts.
- Do not reuse `/mat-plan-team` execution-mode terms here. `/mat-plan` preflight classification is planning-only.
- **Preflight escalation:** see [`docs/architecture/preflight-escalation-ladder.md`](../../.mat/docs/preflight-escalation-ladder.md) (planning depth layer only).
- For how project-local specs relate to global/plugin defaults when planning, see [`docs/reference/capability-precedence.md`](../../.mat/docs/capability-precedence.md).

### Preflight Classification

Place one of these classifications near the top of `specs/<slug>.md`:

- `solo_plan_only` — bounded, self-contained planning is enough.
- `ready_for_execution_handoff` — still lightweight, but a later human may project this into `docs/current-plan.md`.
- `needs_plan_onboarding` — the task is too fuzzy, cross-functional, or trace-heavy for a single-file plan.

If the task grows beyond a lightweight plan, stop expanding the file and recommend `/mat-plan-onboarding`.

### Workflow

**Step 0 — Deep analysis (before any planning artifact writes)**

Before writing or editing any planning artifact (`specs/<slug>.md`, onboarding package files under `specs/<slug>/`, or human-owned projection into `docs/current-plan.md`), **pause and analyze deeply**:

1. **Restate** the task, objective, and constraints in your own words — **no file writes yet**.
2. **Surface** ambiguities, assumptions, and non-goals you must resolve or record explicitly in the plan.
3. **Choose** the narrowest honest scope and planning preflight classification per [`docs/architecture/preflight-escalation-ladder.md`](../../.mat/docs/preflight-escalation-ladder.md) (planning depth layer only).
4. **Decide** which **concrete paths** (not whole-repo reads) you will inspect next; follow [`docs/reference/context-budget-policy.md`](../../.mat/docs/context-budget-policy.md) and [`.cursor/rules/cost-context-hygiene.mdc`](../rules/cost-context-hygiene.mdc).

**Optional Layer 0 preflight (greenfield / unknown landscape):** When the task is novel, comparables are unclear, or build-vs-buy is unresolved, the operator may run [`/mat-preflight-research`](mat-preflight-research.md) (delegates to [`.cursor/skills/mat-preflight-gated/SKILL.md`](../skills/mat-preflight-gated/SKILL.md)) **before** writing planning artifacts. Phase A-only discovery may instead invoke [`.cursor/skills/advise-project-approach/SKILL.md`](../skills/advise-project-approach/SKILL.md) directly. Outputs live under `specs/<slug>/preflight/` — advisory only; does not replace `/mat-plan`, scout, or mat-prime. See [`specs/mat-discovery-research-skills.md`](../../.mat/docs/specs/mat-discovery-research-skills.md) and [`docs/guides/planning-commands-guide.md`](../../.mat/docs/guides/planning-commands-guide.md#layer-0-preflight-research).

This is a **planning SOP / cognitive gate only** — not a separate runtime phase, hook, MAO transition, or validator tier.

**Execution Step 0 is different:** Parent orchestrator Preflight decision and `/mat-plan-team` MAO Step 0 address orchestration — not planning deep analysis.

1. Understand the task and identify ambiguity.
2. Research the repo just enough to produce a bounded plan.

   **Optional planning doc inputs** (optional-when-present, skip-when-absent — no validator tier for directory presence):
   - When **`docs/`** exists: may narrow-read index or entry files (`docs/README.md`, `docs/index.md`) and task-relevant paths under the project docs tree — **not** a habitual full-tree load. See [`docs/reference/context-budget-policy.md`](../../.mat/docs/context-budget-policy.md).
   - When **`ai_docs/`** exists: may narrow-read scraped reference markdown relevant to the task ([`docs-scraper`](../agents/docs-scraper.md) output). The MAT source repo **may lack** `ai_docs/` — skip silently; do not fail-closed.
   - **MAT v1 mapping:** planf3 project-docs (`APP_DOCS/` in planf3 terminology) → repo `docs/`; planf3 scraped-reference naming → repo `ai_docs/`. Literal `APP_DOCS/` directory rename is **deferred**.
   - **`/mat-prime`** is a separate session-priming command — see [`.cursor/commands/mat-prime.md`](mat-prime.md). Step 2 in-planning optional read is **not** a substitute for mat-prime.

3. Choose the preflight classification.
4. Derive a short kebab-case slug and write exactly one file: `specs/<slug>.md`.
5. If `specs/<slug>/` already exists, keep the single-file plan separate and state that the package remains authoritative for heavyweight planning and execution handoff.
6. End with a `Recommended Next Command` section.
7. Report the saved file path to the user.

### Required Structure

The plan must contain these sections in this order:

1. `Task Description`
2. `Objective`
3. `Scope`
4. `Assumptions`
5. `Non-Goals`
6. `Problem Statement`
7. `Solution Approach`
8. `Relevant Files / Areas`
9. `Task Traceability`
10. `Testing Strategy`
11. `Acceptance Criteria`
12. `Risks and Open Questions`
13. `Amendments` (optional — recommended when the plan is a living doc; see below)
14. `Recommended Next Command`

### Amendments (optional)

When the solo plan may evolve before execution handoff, include `## Amendments` **second-to-last** (immediately before `## Recommended Next Command`). Format: append-only bullets `- YYYY-MM-DDTHH:MM:SSZ — role — summary` (ISO-8601 UTC). Planning agent may append while authoring; operator/parent may append later; never rewrite or delete prior lines. See [`docs/architecture/plan-contract.md`](../../.mat/docs/plan-contract.md).

### Content Rules

- `Task Traceability` must map each major task to at least one requirement or decision statement in the same document.
- `Testing Strategy` must be tied to planned tasks, not left as a generic footer.
- The testing section must state:
  - what must be verified manually
  - what automated coverage should exist later if implementation proceeds
  - edge cases and regression focus
  - whether TDD is expected for the later build phase
- Under `## Testing Strategy`, include these required level-3 subsections (after testing-intent prose; do **not** add a 14th top-level section):
  - `### Per-phase validation loops (loop until pass)` — markdown table with columns **Phase | Command | Loop until pass**, minimum one data row; **Command** must be a repo-root shell command; **Loop until pass** should include the phrase **loop until pass** (or Re-run … until).
  - `### Global validation commands (before handoff)` — numbered list with at least one command; for MAT source implementation slices, normally include `bash scripts/phase1-verify.sh` as the final global command unless documented in Risks.
  - One advisory line (plain text in Testing Strategy): hard orchestration gates remain `build-result.md` / `verify-result.md`; in-plan loops are SOP for builders.
  - Shape reference: [`docs/templates/execution-plan-template.md`](../../.mat/docs/templates/execution-plan-template.md) (`## Verification plan` target on projection); specimen: [`specs/mat-plan-validation-loops.md`](../../.mat/docs/specs/mat-plan-validation-loops.md).
- `Acceptance Criteria` must be binary and checkable.
- Under `## Relevant Files / Areas` (alias `## Relevant Files`), every markdown list bullet (`-` or `*`) must start with a case-sensitive tag prefix — **`[new]`** or **`[existing]`** — immediately before the path or description (one space after the closing `]` is allowed). Table rows under Relevant Files are **out of scope** for v1; use bullets as the validated shape. Examples:

  ```markdown
  ## Relevant Files / Areas

  - [existing] `scripts/validate_planning_artifacts.py` — extend Tier 2c checks
  - [new] `tests/fixtures/planning/relevant-files-tag-pass.md` — pass fixture
  ```

- `Recommended Next Command` must explicitly choose one of:
  - continue with human refinement
  - project into `docs/current-plan.md`
  - escalate to `/mat-plan-onboarding`
- After projection into execution, orchestration closeouts use a separate pattern — see [`docs/guides/planning-commands-guide.md`](../../.mat/docs/guides/planning-commands-guide.md#recommended-next-command-execution-commands).
- **Optional `## Related plans` (tail zone):** When long-run or onboarding continuity links help, add this section **after** `## Risks and Open Questions` and **before** optional `## Amendments` / `## Recommended Next Command`. Do **not** insert it between required sections 1–12 (that breaks Tier 2 section order). Use level-3 subsections `### back_refs` and `### forward_refs`; each subsection must have ≥1 markdown list bullet with a **backtick-quoted repo-root-relative path** ending in `.md` or `.json` (no automated graph resolver or path-existence checks in v1). Update drifting refs surgically via [`/mat-plan-update`](mat-plan-update.md) (`back_refs` / `forward_refs` bullets). Example:

  ```markdown
  ## Related plans

  Optional continuity links for long-run and onboarding missions. Paths are repo-root-relative.

  ### back_refs

  - `specs/planf3-polish-mission.md` — prior long-run mission exemplar

  ### forward_refs

  - `docs/architecture/long-run-state.md` — queue projection target for `/mat-long-run`
  ```

- **Optional `## Open Decisions` (tail zone):** When trackable decisions need a file-resident lifecycle log, add this section **after** optional `## Related plans` (when both are present) and **before** optional `## Amendments` / `## Recommended Next Command`. This section is **distinct** from `## Assumptions` (static planning premises) and `## Risks and Open Questions` (unstructured risks/questions) — Open Decisions are numbered `OD-###` items with explicit `open` / `resolved` / `deferred` status. Update decision status surgically via [`/mat-plan-update`](mat-plan-update.md) (append-only amendment + in-place row edit for the same `OD-###` id). Example:

  ```markdown
  ## Open Decisions

  File-resident decision log (optional). Onboarding chat one-at-a-time gate remains canonical for discovery; mirror resolutions here after each answer or explicit deferment.

  - **OD-001** | status: `open` | Should Slice 3 use frontmatter or a section?
  - **OD-002** | status: `resolved` | 2026-07-03 — operator — Use `## Plan metadata` section; frontmatter rejected.
  - **OD-003** | status: `deferred` | HTML toggles deferred to ROADMAP Later HTML export theme.
  ```

- **Optional Task type / Complexity tags (header region):** Solo plans **may** include markdown header lines (not YAML frontmatter) to hint section depth. Allowlists: Task type = `chore` | `feature` | `refactor` | `fix` | `enhancement`; Complexity = `simple` | `medium` | `complex`. Absent tags are valid. Invalid tokens fail soft Tier 2 validation (`tier2_task_type_invalid` / `tier2_complexity_invalid`). These tags **do not** restore planf3 V3 auto-preflight gates and **do not** change which `/mat-plan` sections are required. Depth hint only: `simple` → keep prose terse; `complex` → expand Testing Strategy / Risks; `chore`/`fix` → narrow Scope. Example:

  ```markdown
  **Task type:** `feature`
  **Complexity:** `medium`
  ```

### Output Reminder

- `/mat-plan` stays lightweight and writes one file: `specs/<slug>.md`.
- `/mat-plan-onboarding` is separate and heavyweight.
- For surgical amendments to an existing living plan, use [`/mat-plan-update`](mat-plan-update.md) instead of re-running full onboarding.
- Human approval gate required before any execution handoff.
- Do not replace docs/current-plan.md with onboarding artifacts; use plan-summary.md to instruct projection.
