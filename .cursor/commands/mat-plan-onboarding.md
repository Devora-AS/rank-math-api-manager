# MAT Plan Onboarding

Create a heavyweight planning package for work that needs guided discovery, explicit product and technical separation, traceable tasks, and a human approval gate before execution.

## Usage

```text
/mat-plan-onboarding <task description>
```

## Instructions

**Plan contract skill:** For tier selection, amendments, status markers, and projection semantics, see [`.cursor/skills/mat-plan-contract/SKILL.md`](../skills/mat-plan-contract/SKILL.md) (does not replace this command).

You are a heavyweight planning agent. This command is planning-only and must not start implementation or execution handoff.

### Guardrails

- Planning only — no implementation.
- All assumptions and non-goals must be explicitly listed.
- mat-plan-onboarding requires mandatory artifact package: specs/<slug>/prd.md, specs/<slug>/spec.md, specs/<slug>/tasks.json, specs/<slug>/plan-summary.md.
- Each task in tasks.json must trace to spec.md and PRD IDs; spec.md must trace back to prd.md.
- tasks.json must include a per-task execution status field so approved slices can stay aligned with real progress.
- Human approval gate required before any execution handoff.
- Do not replace docs/current-plan.md with onboarding artifacts; use plan-summary.md to instruct projection.
- Project-local rules and commands still take precedence over generic defaults for repo-specific execution; see [`docs/reference/capability-precedence.md`](../../.mat/docs/capability-precedence.md).
- **Preflight escalation:** see [`docs/architecture/preflight-escalation-ladder.md`](../../.mat/docs/preflight-escalation-ladder.md) (command depth layer).
- After approval, living package drift may use [`/mat-plan-update`](mat-plan-update.md) for surgical amendments (usually `plan-summary.md`) instead of regenerating the full package.

### Purpose

Use `/mat-plan-onboarding` when the task needs:

- guided discovery
- explicit product intent in `prd.md`
- explicit technical design in `spec.md`
- traceable execution-ready planning detail in `tasks.json`
- a clear human handoff bridge in `plan-summary.md`
- a task status contract that stays in sync with approved execution slices

### Workflow

**Step 0 — Deep analysis (before any planning artifact writes)**

Before writing or editing any planning artifact (`specs/<slug>.md`, onboarding package files under `specs/<slug>/`, or human-owned projection into `docs/current-plan.md`), **pause and analyze deeply**:

1. **Restate** the task, objective, and constraints in your own words — **no file writes yet**.
2. **Surface** ambiguities, assumptions, and non-goals you must resolve or record explicitly in the plan.
3. **Choose** the narrowest honest scope and planning preflight classification per [`docs/architecture/preflight-escalation-ladder.md`](../../.mat/docs/preflight-escalation-ladder.md) (planning depth layer only).
4. **Decide** which **concrete paths** (not whole-repo reads) you will inspect next; follow [`docs/reference/context-budget-policy.md`](../../.mat/docs/context-budget-policy.md) and [`.cursor/rules/cost-context-hygiene.mdc`](../rules/cost-context-hygiene.mdc).

This is a **planning SOP / cognitive gate only** — not a separate runtime phase, hook, MAO transition, or validator tier.

**Execution Step 0 is different:** Parent orchestrator Preflight decision and `/mat-plan-team` MAO Step 0 address orchestration — not planning deep analysis.

1. Intake and triage the task.
2. Decide whether heavyweight onboarding is warranted.
3. Run guided discovery.

   **Optional Layer 0 preflight:** When external landscape or literature research may inform the onboarding package, the operator may run [`/mat-preflight-research`](mat-preflight-research.md) (delegates to [`.cursor/skills/mat-preflight-gated/SKILL.md`](../skills/mat-preflight-gated/SKILL.md)) **before** drafting package files. Advisory artifacts under `specs/<slug>/preflight/` — not MAO handoffs. Operator map: [`docs/guides/planning-commands-guide.md`](../../.mat/docs/guides/planning-commands-guide.md#layer-0-preflight-research).

   **Optional planning doc inputs:** Same MAT v1 optional-when-present / skip-when-absent convention as `/mat-plan` workflow step 2 — see [`.cursor/commands/mat-plan.md`](mat-plan.md) (*Optional planning doc inputs* under **Research the repo**). When **`docs/`** or **`ai_docs/`** exist, narrow-read task-relevant paths only (prefer `docs/README.md` / `docs/index.md`); skip silently when absent. Follow [`docs/reference/context-budget-policy.md`](../../.mat/docs/context-budget-policy.md). **`/mat-prime`** remains separate session priming — not a substitute for guided-discovery optional reads.

4. Draft `specs/<slug>/prd.md`.
5. Draft `specs/<slug>/spec.md`.
6. Draft `specs/<slug>/tasks.json`.
7. Draft `specs/<slug>/plan-summary.md`.
8. Scan the package for unresolved open questions.
9. If unresolved questions remain, ask them in the chat one at a time and update the artifacts after each answer or explicit deferment.
10. Run a manual review checklist against the package.
11. Stop for human approval only after required questions are answered or explicitly left open.
12. Only after approval, allow human-owned projection into `docs/current-plan.md`.

### Guided Discovery Questions

Ask and record answers to these six top-level questions:

1. What problem are we solving, for whom, and why now?
2. What outcome would make this planning package successful?
3. What is explicitly in scope and explicitly out of scope for v1?
4. What constraints, dependencies, or repo boundaries must be respected?
5. What assumptions are we making, and what is still unknown?
6. What should the next human/operator action be after planning is approved?

### Conditional Follow-Up Rules

- Ask follow-ups only when a top-level answer is incomplete or contradictory.
- Prefer recording an open question over inventing policy.
- If product intent is fuzzy, stop before task generation.
- If technical boundaries are fuzzy, draft the PRD first and mark spec/tasking as blocked.
- If risks are high but scope is still accepted, continue with explicit risk notes.
- If the repo already contains a clear answer in an earlier artifact, reference it instead of re-asking.

### Unresolved Questions Loop

- After drafting the onboarding package, scan `specs/<slug>/prd.md`, `specs/<slug>/spec.md`, and `specs/<slug>/plan-summary.md` for unresolved open questions before the approval gate.
- Treat file contents as canonical truth; do not rely on chat memory alone.
- Ask unresolved questions in the chat one at a time; after each answer, update the relevant artifact(s) and keep `plan-summary.md` in sync.
- After each answer or explicit deferment, **mirror** the decision into optional `## Open Decisions` on `plan-summary.md` (and `spec.md` / `prd.md` only when the decision is scoped there) using the canonical `OD-###` row shape from [`.cursor/commands/mat-plan.md`](mat-plan.md) Content Rules.
- Do not ask a duplicate question if the answer already exists in the artifacts.
- If the user declines to answer, record that explicitly as an open or deferred question in the artifacts before presenting the final approval gate.
- Keep the interaction lightweight: one question at a time, then sync files, then move to the next unresolved question if one still remains.

### Stop Rules

Do not produce `tasks.json` as execution-ready if:

- the core user/problem definition is missing
- scope and non-goals are not explicit
- critical dependencies are unknown
- traceability to PRD/spec IDs cannot be maintained
- human reviewers request rework before approval

### Projection Rules

- Projection into `docs/current-plan.md` is human/operator-owned.
- Project one approved execution slice at a time.
- Project only the execution-relevant subset: objective, in-scope work, relevant files/areas, acceptance criteria, validation steps, live risks/open questions, and the matching `TASK-###` source id.
- If planning truth changes before execution starts, update the onboarding package first and then regenerate `docs/current-plan.md`.
- If execution truth is clarified during a live run, back-port any lasting planning change into the onboarding package before the next slice or approval checkpoint.
- If both `specs/<slug>.md` and `specs/<slug>/` exist, the folder package is authoritative for heavyweight planning and execution handoff.
- When an approved package is projected into execution, the resulting slice should follow [`docs/orchestration-workflow.md#execution-closeout-contract`](../../.mat/docs/orchestration-workflow.md#execution-closeout-contract) once it reaches closeout.

### Package Requirements

- `prd.md` owns product intent, scope, non-goals, success metrics, assumptions, open questions, stable IDs, user stories, and product acceptance criteria.
- `spec.md` owns technical design, boundaries, dependencies, interfaces, edge cases, validation approach, and TDD/test strategy mapping.
- `tasks.json` owns ordered, traceable execution-ready planning tasks, dependency relationships, and the parent-owned execution status that follows the active slice.
- `plan-summary.md` owns the human handoff, top risks, recommended next command, projection instructions, the current cross-artifact unresolved-questions summary, and a final **`## Amendments`** section (append-only audit trail per [`docs/architecture/plan-contract.md`](../../.mat/docs/plan-contract.md)).
- **Optional `## Related plans` on `plan-summary.md`:** Same tail-zone shape as solo `/mat-plan` — after risks/unresolved summary content, before `## Amendments`. Use `### back_refs` and `### forward_refs` with backtick-quoted repo-root-relative `.md` / `.json` path bullets; amend via [`/mat-plan-update`](mat-plan-update.md) when refs drift. See [`.cursor/commands/mat-plan.md`](mat-plan.md) Content Rules for the canonical example.
- **Optional `## Open Decisions` on `plan-summary.md`:** Tail-zone placement **after** `## Related plans` when both are present, **before** `## Amendments`. Use canonical `OD-###` decision rows (`status: `open|resolved|deferred``) — **distinct** from `## Assumptions` in `prd.md` and unstructured open questions in risks sections. After each chat answer or deferment during the unresolved-questions loop, mirror the decision here (one-at-a-time chat gate remains canonical for discovery). See [`.cursor/commands/mat-plan.md`](mat-plan.md) Content Rules and [`docs/architecture/open-decisions-optional-tier.md`](../../.mat/docs/open-decisions-optional-tier.md).

### Amendments on plan-summary.md

- Include `## Amendments` as the **last** section in `plan-summary.md`.
- Format: append-only bullets `- YYYY-MM-DDTHH:MM:SSZ — role — summary` (ISO-8601 UTC).
- **Authority:** planning agent may append while authoring before approval; operator/parent may append after approval; verifier append prohibited.
- **Forbidden:** rewriting or deleting prior lines; editing historical timestamps.

### Task Status Sync Contract

- Every task in `tasks.json` starts as `planned` unless the planning package explicitly documents a `blocked` or `deferred` decision.
- When an approved slice becomes active in execution, the parent sets the matching task to `in_progress`.
- When the slice passes verification and is complete, the parent sets that task to `done`.
- If a real blocker stops the slice, the parent may set that task to `blocked` with a short note.
- If an operator intentionally skips or postpones the slice, the parent may set that task to `deferred` with a short note.
- Remaining tasks stay `planned`.
- `tasks.json` is planning truth plus synchronized progress metadata, not a separate runtime system.

### Output Reminder

- `/mat-plan` stays lightweight and writes one file: `specs/<slug>.md`.
- `/mat-plan-onboarding` is separate and heavyweight.
- The planning package is upstream planning truth.
- `docs/current-plan.md` remains execution truth.
