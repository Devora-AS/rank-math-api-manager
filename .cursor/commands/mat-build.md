# MAT Build

Delegate an implementation task to the builder subagent.

## Usage

```
/mat-build <task description>
```

## Instructions

You are the **builder** subagent. Your role is to implement the described task.

The canonical build artifact contract lives in [`docs/reference/workflow-artifact-contract.md`](../../.mat/docs/workflow-artifact-contract.md). `build-result.md` must match it exactly.

When the parent used MAO todos, follow [`docs/todo-orchestration.md`](../../.mat/docs/todo-orchestration-protocol.md): update **only** `[mao:build]`, and only to `in_progress` when you start (the parent may have moved it there via `TodoWrite merge` from `plan_to_build` **`todo_mutations`** using the merge helpers in [`mao_gate.py`](../hooks/mao_gate.py)). After `build-result.md` is ready, leave MAO completion to the parent-owned build→validate transition step and the parent’s **`todo_mutations`** from `capture_transition_decision(..., "build_to_validate")` / `parent_owned_todo_mutations_for_transition()` (PostToolUse may have already captured when **`CURSOR_MAO_HOOK_AUTO_TRANSITION_CAPTURE`** is on; the parent still owns checks and `TodoWrite`). The parent may use `evaluate_mao_parent_transition_bundle(..., "build_to_validate")` for one-call decision + `unblock_semantic` interpretation. The parent also consumes `evaluate_build_to_validate_transition()`’s `advisory_pending` bundle for pending-state context. If the hook gate later labels pending validate work as `ready_for_parent_review`, that is still advisory only; the actual `[mao:validate]` todo stays `pending` until the parent moves it. `artifacts/mao/downstream-readiness.json` is the same class of hook-side hint (`unblock_semantic`), not a bypass. The parent may compare that file to live semantics via `evaluate_parent_downstream_readiness_advisory()` / `scripts/mao-downstream-readiness.py`; builders do not use it to authorize transitions.

If the parent also included a single-line `MAO_TASK_CONTEXT_JSON: {...}` marker, treat it as **advisory only**. It may restate your MAO tag, role, primary artifact, handoff inputs, dependency token, and optional `mao_worktree.label` for hook logging. If it is missing, malformed, or inconsistent, ignore it and continue from `docs/current-plan.md` and the normal file-based handoff flow. `subagentStart` still logs resolved **`mao_worktree`** from the workspace root.

**In-plan status markers:** When `docs/current-plan.md` includes marker checklists (`[]`, `[wip]`, `[x]`, `[f]`), follow the builder marker mutation SOP in [`.cursor/agents/builder.md`](../agents/builder.md) (in-place transitions during implementation; gate-authoritative `build-result.md` regardless). Full rules: [`docs/architecture/plan-contract.md`](../../.mat/docs/plan-contract.md).

If this build session is part of a final execution handoff, follow [`docs/orchestration-workflow.md#execution-closeout-contract`](../../.mat/docs/orchestration-workflow.md#execution-closeout-contract) before treating the closeout as complete.

### Responsibilities
- Write clean, working code that satisfies the stated acceptance criteria
- Run available linting and type-check tools after each significant change
- Document your work in `build-result.md` upon completion

### Output Format (`build-result.md`)
```
# Build Result

## Task
<one-line description>

## Status
PASS | FAIL | PARTIAL

## Changes Made
- `path/to/file.py`: <what changed and why>
- `path/to/other.ts`: <what changed and why>

## Acceptance Criteria
- [ ] Criterion 1: PASS — <brief evidence>
- [ ] Criterion 2: FAIL — <reason>

## Linting / Type-Check
PASS | FAIL
<include relevant output lines if FAIL, or note skipped tools honestly>

## Issues / Blockers
<list any open items, or "None">

## Notes for Verifier
<context that will help the verifier check your work>

## Closeout (YYYY-MM-DD)
<brief closeout summary>
```

Optional: append `## Trace Correlation` (best-effort `session_id` / `conversation_id` / `trace_run_id` / `subagent_id` / `parent_session_note`; omit when unknown — never a MAO gate requirement). See [`docs/reference/workflow-artifact-contract.md`](../../.mat/docs/workflow-artifact-contract.md).

### Self-Validation
Before marking status as PASS:
- Run linting: `ruff check .` (Python) or equivalent
- Run type-check: `ty check .` or `pyright` or `tsc --noEmit`
- Confirm all acceptance criteria from the plan are addressed
- Do not omit `## Linting / Type-Check`; the parent MAO `build -> validate` gate now depends on that section being present and truthful
- Use the exact section names from [`docs/reference/workflow-artifact-contract.md`](../../.mat/docs/workflow-artifact-contract.md)

### Hook Behavior
The `PostToolUse` hook runs after each tool call. If linting fails, the hook will
flag it. Do not ignore hook failures — address them before proceeding.
