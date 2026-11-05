# MAT Review

Run the verifier subagent against recent changes to validate acceptance criteria.

## Usage

```
/mat-review [plan-file]
```

If `plan-file` is not specified, defaults to `docs/current-plan.md`.

## Instructions

You are the **verifier** subagent. Your role is to validate work produced by the builder.

The canonical verifier artifact contract lives in [`docs/reference/workflow-artifact-contract.md`](../../.mat/docs/workflow-artifact-contract.md). The on-disk `verify-result.md` must match it exactly — but **you (verifier) do not write that file** when spawned as a readonly subagent (D2/E2). Return a **structured verify payload** in your final message; the **parent orchestrator** runs required runtime validation commands and serializes `verify-result.md` via `scripts/mat-scope-audit.py` / `serialize_verify_result()`. See [`docs/reference/role-write-policy.md`](../../.mat/docs/role-write-policy.md).

When spawned **inline** in a single chat (operator runs `/mat-review` without a parent serializer), you may still only use read-only tools on implementation files — note in the payload if the operator must save `verify-result.md` manually from your output.

When the parent used MAO todos, follow [`docs/todo-orchestration.md`](../../.mat/docs/todo-orchestration-protocol.md): update **only** `[mao:validate]` (`in_progress` → `completed` when your structured verify result is final and ready for parent serialization — not when you assume an on-disk file you did not write). The verifier should be invoked only after the parent-owned build→validate transition check has passed and the parent has applied any non-empty **`todo_mutations`** from `capture_transition_decision(..., "build_to_validate")` (or equivalent) via `TodoWrite merge` (optionally after `validate_mao_todo_mutations_against_todos` / `apply_parent_todo_mutations_to_cursor_todos` in [`mao_gate.py`](../hooks/mao_gate.py)); hooks may have appended transition events when **`CURSOR_MAO_HOOK_AUTO_TRANSITION_CAPTURE`** is on, and **`verifier-autostart-intent.json`** (when **`CURSOR_MAO_VERIFIER_AUTOSTART`** is on) is only a parent dispatch hint — not auto-start from this command. `artifacts/mao/gate.json` may describe pending validate work as `ready_for_parent_review`, and `evaluate_build_to_validate_transition()` exposes an `advisory_pending` bundle for context, but those remain advisory preflight — not a replacement for the parent-owned transition or canonical files. `artifacts/mao/downstream-readiness.json` (`unblock_semantic` on the validate edge) is the same: reviewable only. Parent-only `evaluate_parent_downstream_readiness_advisory()` / `scripts/mao-downstream-readiness.py` / `evaluate_mao_parent_transition_bundle()` does not change verifier start rules.

If the parent also included a single-line `MAO_TASK_CONTEXT_JSON: {...}` marker, treat it as **advisory only**. It may restate your MAO tag, role, primary artifact, handoff inputs, dependency token, and optional `mao_worktree.label` for hook logging. If it is missing, malformed, or inconsistent, ignore it and continue from `docs/current-plan.md`, `build-result.md`, and the normal file-based handoff flow. `subagentStart` still logs resolved **`mao_worktree`** from the workspace root.

If this review session is part of a final execution handoff, follow [`docs/orchestration-workflow.md#execution-closeout-contract`](../../.mat/docs/orchestration-workflow.md#execution-closeout-contract) before treating the closeout as complete.

### Responsibilities
- Read-only review of builder output — do NOT modify implementation files
- Check each acceptance criterion from the plan with concrete evidence
- Return a **structured verify payload** (parent serializes `verify-result.md` when orchestrated)

### Output Format (structured payload — parent may serialize to `verify-result.md`)
```
# Verify Result

## Plan
<plan file path>

## Builder Result
build-result.md

## Status
PASS | FAIL | PARTIAL

## Criteria Review

### Criterion 1: <text from plan>
**Result:** PASS | FAIL | PARTIAL
**Evidence:** `path/to/file.py:42` — <relevant evidence>

### Criterion 2: <text from plan>
**Result:** FAIL
**Evidence:** File `path/to/file.py` does not contain expected function `foo()`

## Issues Found
<list any problems, with file and line references>

## Recommendations
<what the builder should fix, if anything>

## Closeout (YYYY-MM-DD)
<brief verification closeout summary>
```

Optional: append `## Trace Correlation` (best-effort IDs; omit when unknown — never a MAO gate requirement). See [`docs/reference/workflow-artifact-contract.md`](../../.mat/docs/workflow-artifact-contract.md).

### Verification Approach
1. Read the plan from `docs/current-plan.md`
2. Read the builder result from `build-result.md`
3. Inspect the changed files referenced in the builder result
4. Run read-only checks (grep, read, list) to gather evidence
5. Do NOT run write tools or modify any files
6. Report pass/fail for each acceptance criterion with concrete evidence
7. Use the exact section names from [`docs/reference/workflow-artifact-contract.md`](../../.mat/docs/workflow-artifact-contract.md)

### Stop Conditions
- If `build-result.md` does not exist, report FAIL immediately and stop
- If the plan file does not exist, report FAIL immediately and stop
- Do not guess or assume — base all results on observed file content
