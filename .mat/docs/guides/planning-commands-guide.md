# Planning Commands Guide

Use this guide to choose between `/mat-plan`, `/mat-plan-onboarding`, and `/mat-plan-update`.

**Plan contract (v0.1):** Depth tiers, amendments, status markers, and truth hierarchy are defined in [`docs/architecture/plan-contract.md`](../plan-contract.md) (full design: [`specs/shared-plan-contract.md`](../specs/shared-plan-contract.md)). **Preflight escalation:** canonical routing across planning depth, command depth, and execution mode — [`docs/architecture/preflight-escalation-ladder.md`](../preflight-escalation-ladder.md). Procedural steps: [`.cursor/skills/mat-plan-contract/SKILL.md`](../../.cursor/skills/mat-plan-contract/SKILL.md) (does not replace slash commands).

## Command routing (quick reference)

| Intent | Command | Output |
|--------|---------|--------|
| **Create** lightweight plan | `/mat-plan` | `specs/<slug>.md` |
| **Heavy** discovery / traceability | `/mat-plan-onboarding` | `specs/<slug>/` four-file package |
| **Drift** — surgical amendment to existing plan | `/mat-plan-update` | Amended planning file + append-only `## Amendments` line |
| **Execute** approved slice | `/mat-plan-team` or `/mat-long-run` | `build-result.md` / `verify-result.md` (after projection to `docs/current-plan.md`) |
| **Layer 0** external landscape / optional literature | `/mat-preflight-research` | `specs/<slug>/preflight/*` (advisory; not MAO handoffs) |

## Layer 0 preflight (research)

Optional **discovery-first** step **below** the planning preflight ladder ([`docs/architecture/preflight-escalation-ladder.md`](../preflight-escalation-ladder.md) Layer 1–3). Use when comparables, build-vs-buy, or technical-mechanism choice is unclear **before** choosing planning depth.

| Operator need | Use | Does **not** replace |
|---------------|-----|----------------------|
| External landscape + optional G2-gated arXiv scan | `/mat-preflight-research` → [`.cursor/skills/mat-preflight-gated/SKILL.md`](../../.cursor/skills/mat-preflight-gated/SKILL.md) | `/mat-plan`, `/mat-plan-onboarding` |
| Phase A only (comparables, cost framing) | [`.cursor/skills/advise-project-approach/SKILL.md`](../../.cursor/skills/advise-project-approach/SKILL.md) | Full orchestrator when gate + G2 path may apply |
| Phase B only (after `novel_research_required` + G2) | [`.cursor/skills/neuroarxiv/SKILL.md`](../../.cursor/skills/neuroarxiv/SKILL.md) | Phase A intake or novelty gate |
| In-repo bug / root-cause / "where is X?" | `scout-report-suggest` agent | External landscape or literature |
| Session orientation ("what is this repo?") | `/mat-prime` | Planning preflight or discovery |
| Save known vendor docs to `ai_docs/` | `docs-scraper` agent | arXiv search or comparables discovery |

**G2 / never auto-escalate:** Phase B literature scan runs only when `novelty-gate.json` is `novel_research_required` **and** the operator passes explicit G2 approval in-thread. The orchestrator **never auto-escalates** from Phase A to Phase B in the same response.

Design reference: [`specs/mat-discovery-research-skills.md`](../specs/mat-discovery-research-skills.md). Doc-test lock: `MatPreflightResearchIntegrationTest` in `tests/test_workflow_docs.py`.

## Depth router

Optional convenience on `/mat-plan`: a leading `--depth=<value>` (or `--depth <value>`) **thin router** maps to an existing slash command — **explicit aliases only**, no fuzzy routing. When `--depth` is absent (or `standard`), solo `/mat-plan` is unchanged. Invalid values **fail closed** (print table, recommend direct command; no solo-plan fallback). `team` and `long-run` dispatch to orchestration SOPs, not solo planning-only guardrails. Full mapping and parse procedure: [`.cursor/commands/mat-plan.md`](../../.cursor/commands/mat-plan.md#depth-router-depth).

## Canvas visualization (advisory)

Optional **interactive plan review** inside Cursor via [`.cursor/skills/mat-plan-canvas/SKILL.md`](../../.cursor/skills/mat-plan-canvas/SKILL.md): generate a `.canvas.tsx` dashboard from bounded markdown handoffs (`specs/`, `docs/current-plan.md`, optional `build-result.md` / `verify-result.md`). **Markdown stays canonical** — canvas is derived, read-only, and never required for CI or orchestration gates. Operator-triggered only; not a substitute for slash commands or `mat-plan-contract`.

## Deep analysis before writes

**Planning Step 0** applies to `/mat-plan` and `/mat-plan-onboarding` only: deep analysis **before any planning artifact writes** (`specs/<slug>.md`, `specs/<slug>/` package files, or human-owned projection into `docs/current-plan.md`). Canonical four-bullet gate and SOP-only posture: [`.cursor/commands/mat-plan.md`](../../.cursor/commands/mat-plan.md) Workflow Step 0 (onboarding uses the same block before intake/package drafts).

**Execution Step 0 is different:** `/mat-plan-team` MAO Step 0 and Preflight decision / `/mat-long-run` startup preflight address orchestration — not planning deep analysis. See [`docs/architecture/preflight-escalation-ladder.md`](../preflight-escalation-ladder.md).

## Planning doc inputs (`docs/` + `ai_docs/`)

Optional planning-time reads from repository documentation trees — **optional-when-present**, **skip-when-absent** (no validator tier for directory presence in v1).

| planf3 convention | MAT v1 convention | Role |
|-------------------|---------------------|------|
| `APP_DOCS/` | `docs/` | Canonical project documentation (indexes, guides, architecture, reference) |
| `AI_DOCS/` | `ai_docs/` | Optional scraped reference markdown (`docs-scraper` output) |
| Literal `APP_DOCS/` directory | **Deferred** | Do not rename or require in MAT source v1 |

- **`/mat-plan` workflow step 2** ("Research the repo…") — in-command optional narrow read during planning research.
- **`/mat-plan-onboarding` workflow step 3** ("Run guided discovery") — parallel optional-input prose (cross-link to mat-plan step 2).
- **`/mat-prime`** — separate **session priming** command; planning step 2/3 optional read is **not** a substitute for mat-prime.
- **`docs-scraper` agent** — writes fetched web docs to `ai_docs/`; see [`.cursor/agents/docs-scraper.md`](../../.cursor/agents/docs-scraper.md).
- Narrow-read guardrails: [`docs/reference/context-budget-policy.md`](../context-budget-policy.md).

Doc-test lock: `PlanningDocsInputsTest` in `tests/test_workflow_docs.py`.

### Amendments (living plans)

When a plan file may change after first write, use append-only **`## Amendments`**:

| Artifact | Placement |
|----------|-----------|
| `docs/current-plan.md` | Last section |
| `specs/<slug>/plan-summary.md` | Last section |
| `specs/<slug>.md` (optional) | Second-to-last, before `## Recommended Next Command` |

Each line: `- YYYY-MM-DDTHH:MM:SSZ — role — summary` (ISO-8601 UTC). Operator/parent may always append; builder may append during active build for scope drift; verifier read-only; planning agents only while authoring before approval. Never rewrite or delete prior lines.

### Status markers (execution checklists)

When `docs/current-plan.md` (or lite-tier sprint plans) tracks progress on checklist lines, use contract markers:

| Marker | Meaning |
|--------|---------|
| `[]` | Idle |
| `[wip]` | In progress |
| `[x]` | Done for this slice |
| `[f]` | Failed / blocked (reason on same line) |

Builder mutates in-place during build; parent may set `[wip]` at slice start; verifier read-only (warn-not-fail on drift). Markers are **advisory** — orchestration gates stay on `build-result.md` / `verify-result.md`. See [`docs/architecture/plan-contract.md`](../plan-contract.md). Optional `## Trace Correlation` on those handoffs is documented in [`docs/reference/workflow-artifact-contract.md`](../workflow-artifact-contract.md) (omit-when-unknown; never a MAO gate).

### Execution plan templates (lite vs standard)

| Tier | Template | When to use |
|------|----------|-------------|
| **lite** | [`docs/templates/adoption-minimal-current-plan.md`](../templates/adoption-minimal-current-plan.md) | Adoption bootstrap, `/mat-sprint`, or a single bounded change with minimal sections (task, DoR optional, binary criteria, verification loops) |
| **standard** | [`docs/templates/execution-plan-template.md`](../templates/execution-plan-template.md) | `/mat-plan-team`, `/mat-long-run`, or any orchestrated slice projected from approved `specs/` planning — includes implementation steps, binary acceptance criteria, per-phase **loop until pass** commands, and global validation before handoff |

Onboarding packages still use the four-file `specs/<slug>/` layout; project one approved slice into `docs/current-plan.md` using **lite** or **standard** based on slice complexity (document the tier in the plan header).

## `/mat-plan`

Use `/mat-plan` when:
- the work is bounded
- a single planning file is enough
- the problem is already reasonably understood
- you want a fast solo plan without a full onboarding package

Output:
- `specs/<slug>.md`

Rules:
- lightweight only
- planning only
- use planning-local preflight terms only: `solo_plan_only`, `ready_for_execution_handoff`, `needs_plan_onboarding`
- include a `Recommended Next Command` section
- under `## Testing Strategy`, include `### Per-phase validation loops (loop until pass)` and `### Global validation commands (before handoff)` (see `.cursor/commands/mat-plan.md` and [`specs/mat-plan-validation-loops.md`](../specs/mat-plan-validation-loops.md))
- under `## Relevant Files / Areas`, tag every list bullet with `[new]` or `[existing]` before the path (see `.cursor/commands/mat-plan.md` and [`docs/architecture/plan-contract.md`](../plan-contract.md#mat-plan-relevant-files-tagging-tier-2c))
- escalate to `/mat-plan-onboarding` if scope, discovery, or traceability needs become heavier
- use `/mat-plan-update` for surgical amendments to an existing living plan (see below)
- do not reuse `/mat-plan-team` execution-mode terms inside `/mat-plan`

### Planning vs execution validation loops

| Phase | Location | Hard gates |
|-------|----------|------------|
| **Planning** (`/mat-plan`) | `## Testing Strategy` subsections — per-phase table + global numbered commands | Advisory SOP only |
| **Execution** (`/mat-plan-team`, `/mat-long-run`) | `## Verification plan` in projected `docs/current-plan.md` (lite/standard templates) | `build-result.md` / `verify-result.md` |

When projecting an approved solo spec into `docs/current-plan.md`, copy loop blocks from Testing Strategy into `## Verification plan` using the standard execution template shape.

## Preflight escalation ladder

Canonical operator reference for **when to escalate** across three **non-collapsed** layers: planning depth (`solo_plan_only` → `ready_for_execution_handoff` → `needs_plan_onboarding`), command depth (`/mat-plan` → `/mat-plan-onboarding` → projection), and execution mode (`inline` → `builder_plus_verifier` → `parallel_spawn`, plus when `/mat-long-run` applies). Planning preflight terms are **not** execution preflight terms — see [`docs/architecture/preflight-escalation-ladder.md`](../preflight-escalation-ladder.md).

## Advisor-strategy (parallel sessions)

For substantive orchestration where one high-context **advisor** session owns audit/closeout and the operator runs copy-paste `/mat-plan-team` or `/mat-long-run` slices in **parallel separate agent sessions**, see [`docs/guides/mat-advisor-strategy-runbook.md`](mat-advisor-strategy-runbook.md) (paste-back checklist, commit/push rules, Trace Correlation tip).

## Prompt templates (advisory)

Copy-paste builder/verifier/advisor prompts: [`docs/guides/mat-prompt-templates.md`](mat-prompt-templates.md) and `docs/templates/prompt-*.txt`. Advisory only — not hook-injected.

## Task type / Complexity tags (optional)

Solo `/mat-plan` specs may include markdown header lines `**Task type:**` / `**Complexity:**` (allowlisted tokens) as **depth hints only** — not YAML frontmatter, not preflight gates. See [`.cursor/commands/mat-plan.md`](../../.cursor/commands/mat-plan.md) Content Rules and [`docs/architecture/plan-contract.md`](../plan-contract.md).

## `/mat-plan-update`

Use `/mat-plan-update` when:

- a planning artifact already exists (`specs/<slug>.md` or onboarding package file)
- the change is a **surgical** scope or intent adjustment — not a full re-authoring pass
- you need append-only `## Amendments` audit trail without re-running `/mat-plan-onboarding`

Usage:

```text
/mat-plan-update <target-path> — <amendment summary>
```

Output:

- minimal in-place edits to the target planning file
- one new append-only line under `## Amendments`

Rules:

- planning only — no implementation
- classify `surgical_amendment` vs `escalate_to_onboarding` before editing
- **do not** auto-edit active `docs/current-plan.md` — update planning truth first, then operator re-projects
- when execution is in flight, re-projection is required before resuming `/mat-plan-team` or `/mat-long-run`
- closeout uses one fenced `txt` block per phase (see [`.cursor/commands/mat-plan-update.md`](../../.cursor/commands/mat-plan-update.md))
- amend optional `## Related plans` `### back_refs` / `### forward_refs` on solo specs or `plan-summary.md` when continuity links drift (Tier 2d validates solo specs when the section is present)
- amend optional `## Open Decisions` `OD-###` row status on solo specs or `plan-summary.md` when decision lifecycle drifts (Tier 2e validates solo specs when the section is present)

## Solo `/mat-plan` optional Related plans (Tier 2d)

Optional tail-zone `## Related plans` on root `specs/<slug>.md` (after `## Risks and Open Questions`, before optional `## Amendments` / `## Recommended Next Command`) with level-3 subsections `### back_refs` and `### forward_refs`. Each subsection uses markdown list bullets with **backtick-quoted repo-root-relative paths** ending in `.md` or `.json`. Onboarding `plan-summary.md` may use the same shape (prose contract; Tier 2d applies to solo specs only in v1). No automated path-existence or graph validation. Grace registry: `RELATED_PLANS_GRANDFATHERED_SOLO_PLANS` in `scripts/validate_planning_artifacts.py` (exemplar without grace: `specs/planf3-audit-trail-mission.md`). Command reference: [`.cursor/commands/mat-plan.md`](../../.cursor/commands/mat-plan.md) Content Rules; operator summary: [`docs/architecture/plan-contract.md`](../plan-contract.md).

## Solo `/mat-plan` optional Open Decisions (Tier 2e)

Optional tail-zone `## Open Decisions` on root `specs/<slug>.md` (after optional `## Related plans` when both present; before optional `## Amendments` / `## Recommended Next Command`). Each list bullet uses `**OD-###** | status: `open|resolved|deferred` | …` — **distinct** from `## Assumptions` and `## Risks and Open Questions`. Onboarding keeps the **one-at-a-time chat gate** for discovery and mirrors each resolution into `plan-summary.md` `## Open Decisions`. No HTML `<details>` requirement; no `tasks.json` schema change (optional `OD-###` cross-refs in prose only). Grace registry: `OPEN_DECISIONS_GRANDFATHERED_SOLO_PLANS` (exemplar without grace: `specs/planf3-audit-trail-mission.md`). Architecture: [`docs/architecture/open-decisions-optional-tier.md`](../open-decisions-optional-tier.md). Command reference: [`.cursor/commands/mat-plan.md`](../../.cursor/commands/mat-plan.md) Content Rules; update path: [`.cursor/commands/mat-plan-update.md`](../../.cursor/commands/mat-plan-update.md).

## Execution `## Plan metadata` (Tier 4 extension, optional-when-present)

Optional `## Plan metadata` on substantive `docs/current-plan.md` — **not** YAML frontmatter. Use level-3 subsections `### modified`, `### session`, and `### commit` with append-only list bullets (one line per projection, session start, or merge milestone). Operator/parent **may** append during `/mat-plan-team`, `/mat-long-run`, or `/mat-sprint`; hooks **do not** auto-write metadata. Complements `docs/session-summary.md` and MAO advisory events — does not replace them. Tier 4 validates shape when the section is present on substantive execution plans; idle/placeholder skip unchanged. Coexists with `## Amendments` and status markers. Command references: [`.cursor/commands/mat-plan-team.md`](../../.cursor/commands/mat-plan-team.md), [`.cursor/commands/mat-long-run.md`](../../.cursor/commands/mat-long-run.md), [`.cursor/commands/mat-sprint.md`](../../.cursor/commands/mat-sprint.md); templates: [`docs/templates/execution-plan-template.md`](../templates/execution-plan-template.md); operator summary: [`docs/architecture/plan-contract.md`](../plan-contract.md).

## `/mat-plan-onboarding`

Use `/mat-plan-onboarding` when:
- the work needs guided discovery
- product intent and technical design should be separated
- traceable tasks are required
- a human approval gate is needed before execution handoff

Output:
- `specs/<slug>/prd.md`
- `specs/<slug>/spec.md`
- `specs/<slug>/tasks.json`
- `specs/<slug>/plan-summary.md`

Rule:
- mat-plan-onboarding requires mandatory artifact package: specs/<slug>/prd.md, specs/<slug>/spec.md, specs/<slug>/tasks.json, specs/<slug>/plan-summary.md.
- if both `specs/<slug>.md` and `specs/<slug>/` exist, the folder package is authoritative for heavyweight planning and execution handoff
- surface unresolved open questions in chat before approval, one question at a time, while keeping the files canonical

## Handoff Rules

- `specs/` is upstream planning truth.
- `docs/current-plan.md` remains execution truth.
- `plan-summary.md` is the bridge into execution.
- before the approval gate, scan `prd.md`, `spec.md`, and `plan-summary.md` for unresolved open questions and surface them in chat before approval
- Human approval gate required before any execution handoff.
- Do not replace docs/current-plan.md with onboarding artifacts; use plan-summary.md to instruct projection.
- Projection is human/operator-owned and happens only after approval.
- Project one approved execution slice at a time into `docs/current-plan.md`.
- When an approved slice comes from `tasks.json`, carry the matching `TASK-###` into `docs/current-plan.md` and keep the parent-owned status synchronized during execution.
- First perform that manual projection step, then choose the downstream execution command.
- If planning truth and execution truth drift, update the planning package first (`/mat-plan-update` for surgical edits, or heavier `/mat-plan-onboarding` when needed) and then regenerate execution truth before continuing.

## Recommended next command (execution commands)

Planning commands (`/mat-plan`, `/mat-plan-onboarding`) end with a **Recommended Next Command** section that chooses one planning or projection path. **Execution** commands use a different closeout pattern: after each major orchestration phase, the parent prints **exactly one** honest next step in a fenced ` ```txt ` block — no equally-weighted option menus.

| Reference implementation | Discipline |
|--------------------------|------------|
| [`.cursor/commands/mat-sync.md`](../../.cursor/commands/mat-sync.md) | One `txt` block per installer/plan/approve phase |
| [`.cursor/commands/mat-update-mat.md`](../../.cursor/commands/mat-update-mat.md) | “After each phase, print exactly one recommended next command in a fenced txt block.” |

| Execution command | Closeout phases (one `txt` block each) |
|-------------------|----------------------------------------|
| `/mat-plan-team` | Plan written → build gate passed → verify complete → cycle complete / idle |
| `/mat-long-run` | Same per active slice, plus mission gate **continue** (next slice) and **stop** (`docs/session-summary.md`) |
| `/mat-sprint` | DoR satisfied → implement complete → verify complete → sprint review complete |

Command files under `.cursor/commands/` document the exact phase headings and example blocks. The parent orchestrator should mirror the same wording when reporting next steps ([`.cursor/agents/parent-orchestrator.md`](../../.cursor/agents/parent-orchestrator.md)).

## Skills vs commands

The planning quartet (`/mat-plan`, `/mat-plan-onboarding`, `/mat-plan-update`, and downstream execution entries such as `/mat-plan-team`) stay **slash commands** for discovery and MAO orchestration entry. Repeatable procedural playbooks (for example worktree lifecycle) may live in [`.cursor/skills/`](../../.cursor/skills/) and cross-reference commands without replacing them. See [P1 Audit — Skills vs Commands Routing](../decision-record.md#p1-audit--skills-vs-commands-routing) for the full routing matrix.

## CI validation

On the MAT source repo, `bash scripts/phase1-verify.sh` runs `scripts/validate_planning_artifacts.py` after closeout coherence checks. It validates:

- onboarding `tasks.json` against `docs/templates/tasks-schema.json` (Tier 1),
- solo `/mat-plan` section order for root `specs/<slug>.md` files (Tier 2),
- cross-file traceability for onboarding packages (Tier 3).

Adopted product repos skip this block (sidecar banner). Legacy solo plans and non-onboarding `tasks.json` profiles are grandfathered or excluded per the validator registry.

## Rule Of Thumb

- Start with `/mat-plan` for bounded solo planning.
- Use `/mat-plan-onboarding` when uncertainty, cross-functional scope, or traceability needs justify the heavier package.
- Use `/mat-plan-update` for surgical amendments to existing planning artifacts without full re-onboarding.
- After approval, project the approved slice into `docs/current-plan.md`, then use `/mat-plan-team` or `/mat-long-run` only for downstream execution, not planning authoring.
