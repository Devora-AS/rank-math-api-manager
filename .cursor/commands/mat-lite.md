# MAT Lite

Handle a small docs, config, content, or quality task without invoking the full multi-agent pipeline.

## Usage

```
/mat-lite <task description>
```

## Instructions

Use this command for low-risk work where a full `plan -> build -> verify` orchestration would be heavier than the task itself.

### Good Fits

- Small documentation improvements
- README or configuration cleanup
- Command or prompt wording updates
- Tiny non-behavioral quality fixes

### Workflow

1. Restate the task in one sentence and confirm it is small enough for a lite pass.
2. Read the specific files involved; avoid broad repo exploration unless needed.
3. Make the minimal change.
4. Run focused verification appropriate to the edit.
5. Report the result briefly, including any caveats.

### Verification Expectations

- For markdown/docs changes, at minimum review the changed sections and run `git diff --check`.
- For config or prompt changes, also confirm the edited instructions remain internally consistent.
- Add tests only when the change affects executable behavior or a nearby test pattern makes the gap important.

### Guardrails

- If the task grows beyond a small bounded change, switch to `/mat-sprint`, `/mat-plan-team`, or `/mat-long-run` when the work is a **queued multi-slice mission** (see `docs/architecture/long-run-state.md`).
- Do not invent new architecture or broad process changes from a lite task.
- Do not commit unless the user explicitly asks for it.
