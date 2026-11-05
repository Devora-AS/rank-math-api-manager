# MAT Plan Team

Orchestrate a multi-agent planning and implementation session using Cursor subagents.

## Usage

```
/mat-plan-team <task description>
```

**Plan contract skill:** For tier selection, amendments, status markers, and projection semantics, see [`.cursor/skills/mat-plan-contract/SKILL.md`](../skills/mat-plan-contract/SKILL.md) (does not replace this command).

## Long-run vs single cycle

This command runs **one** plan → build → verify orchestration cycle per invocation pattern described below. For **queued multi-slice missions** (several slices in one session with explicit mission state), prefer **`/mat-long-run`** and maintain [`docs/architecture/long-run-state.md`](../../.mat/docs/long-run-state.md) per [`.cursor/commands/mat-long-run.md`](mat-long-run.md) and [`.cursor/agents/parent-orchestrator.md`](../agents/parent-orchestrator.md). You may still use `/mat-plan-team` for a single cycle, or combine it with a long-run state file **only if** you follow the parent **long-run** rules (post-slice mission gate, stop reasons, no “slice PASS = mission complete” when slices remain).

The canonical handoff contract for `build-result.md` and `verify-result.md` lives in [`docs/reference/workflow-artifact-contract.md`](../../.mat/docs/workflow-artifact-contract.md). Use that contract when describing or checking build/verify artifacts. When **`CURSOR_MAT_LOOP_POLICY=1`**, follow parent Step 2b / loop evaluate guidance in [`.cursor/agents/parent-orchestrator.md`](../agents/parent-orchestrator.md) and [`docs/reference/loop-policy.md`](../../.mat/docs/loop-policy.md).

Orchestration should still **prefer project-local** `.cursor/` assets in the target repo when they define repo-specific behavior; see [`docs/reference/capability-precedence.md`](../../.mat/docs/capability-precedence.md).

For routing-policy slices, keep MAT policy in [`docs/reference/model-routing-policy.md`](../../.mat/docs/model-routing-policy.md) and avoid encoding undocumented Cursor alias-style frontmatter behavior as MAT core policy.

**Cost and context:** Prefer [`docs/reference/context-budget-policy.md`](../../.mat/docs/context-budget-policy.md) — keep parent and subagent prompts focused on `docs/current-plan.md`, `build-result.md`, `verify-result.md`, and touched paths. Avoid unnecessary fan-out (`parallel_spawn` only when truly parallel-independent). Choose the lightest honest preflight mode; do not habitually use premium model tiers for routine bounded work.

When you draft parent/advisor prompts or copied snippets for this command, default to copy-pasteable fenced `txt` blocks unless the user asks for another format.

## Preflight decision

Before writing `docs/current-plan.md`, classify the session with a short rationale:

- `inline` — narrow exception only: use it only when the parent can finish one bounded change honestly without delegated implementation, and say why `/mat-sprint` is not the better entrypoint.
- `builder_plus_verifier` — default and intended mode for `/mat-plan-team`; this command is a delegated multi-agent orchestration command for one plan → build → verify cycle.
- `parallel_spawn` — only when the task breaks into non-overlapping parallel work that truly benefits from fan-out.

This preflight step is a lightweight planning gate, not runtime authority. `builder_plus_verifier` remains the normal/default path here. `inline` is not an equal default path, and `parallel_spawn` is an optional expansion rather than the baseline behavior. Do not let the chosen mode weaken the canonical file-based MAO checks.

**Preflight escalation:** execution-mode layer — [`docs/architecture/preflight-escalation-ladder.md`](../../.mat/docs/preflight-escalation-ladder.md).

**Planning Step 0 vs execution Step 0:** `/mat-plan` and `/mat-plan-onboarding` require deep analysis before any planning artifact writes; this command's Step 0 (MAO todos) and Preflight decision above are orchestration preflight only — not planning deep analysis.

## What This Command Does

1. You (the parent orchestrator) will receive the task description and produce a structured plan.
2. Delegate the implementation work to the **builder** subagent as the normal/default flow.
3. Delegate the validation of the implementation to the **verifier** subagent as the normal/default flow.
4. Synthesize the results and produce a final summary.

**Delegation means Task:** For steps 2–3, use the Cursor **Task** tool with `subagent_type` `builder` and `verifier` respectively. Inline implementation or verification in the parent session is **out of policy** unless the preflight is `inline` with an explicit rationale (see `docs/architecture/mat-plan-team-spec.md`). The repository cannot force Task invocation; hooks and `CURSOR_AGENT_TRACE_RUN_ID` help observe whether spawn actually happened.

If the preflight classification is `inline`, treat that as a justified exception for a narrow case, not as a redefinition of what `/mat-plan-team` normally means. If the work is primarily a small inline slice, prefer `/mat-sprint`. If it is a queued mission with explicit per-slice execution modes, prefer `/mat-long-run`.

---

## Orchestration Instructions

You are the **parent orchestrator**. Follow this sequence.

After each major phase below, print **exactly one** recommended next command in a fenced `txt` block. Do not list multiple equally-weighted options — pick the honest branch and one command. Reference implementations: [`.cursor/commands/mat-sync.md`](mat-sync.md), [`.cursor/commands/mat-update-mat.md`](mat-update-mat.md); operator guide: [`docs/guides/planning-commands-guide.md`](../../.mat/docs/guides/planning-commands-guide.md#recommended-next-command-execution-commands).

### Closeout — Plan written complete

When `docs/current-plan.md` is substantive and the plan→build transition check passes, print one next step before builder dispatch:

```txt
Task subagent_type=builder with docs/current-plan.md, build-result.md handoff, and MAO [mao:build] context — wait for build-result.md before verifier dispatch
```

### Closeout — Build gate passed

When `build-result.md` exists and the build→validate transition check passes, print one next step before verifier dispatch:

```txt
Task subagent_type=verifier with docs/current-plan.md and build-result.md — wait for structured verify payload; parent serializes verify-result.md and runs plan global validation commands before final closeout
```

### Closeout — Verify complete

When `verify-result.md` satisfies gates for this cycle, print one honest next step (idle handoff or session summary — not both):

```txt
# Cycle complete — summarize outcomes in chat; write docs/session-summary.md when the session or mission ends
```

### Closeout — Cycle complete / idle

When the orchestration cycle is finished and no further work is queued in this invocation, print one idle handoff:

```txt
# Idle — no further orchestration this cycle; operator may start a fresh /mat-plan-team or /mat-long-run when ready
```

### Step 0 — To-dos (MAO)

Create or sync the three canonical Cursor todos (`[mao:plan]`, `[mao:build]`, `[mao:validate]`) using **`TodoWrite`**, per [`docs/reference/todo-orchestration.md`](../../.mat/docs/todo-orchestration-protocol.md) and [`.cursor/rules/orchestrator-todos.mdc`](../../.cursor/rules/orchestrator-todos.mdc). If the todo tool is unavailable, skip and note it in `docs/session-summary.md`; continue with files only. When hooks run, `PostToolUse` after `TodoWrite` may record gitignored `artifacts/mao/todo-write-events.jsonl` and `last-todo-write-observation.json` for traceability only (no auto-spawn; see protocol), and may refresh gitignored `artifacts/mao/downstream-readiness.json` with deterministic per-edge `unblock_semantic` (advisory only; `CURSOR_MAO_DOWNSTREAM_READINESS=0` disables).

### Step 1 — Plan
Produce a structured plan with:
- Clear acceptance criteria for the task
- List of implementation steps for the builder
- List of validation checks for the verifier
- Expected output artifacts

If the slice touches hooks, validators, artifact parsing, MAO transitions, or security-sensitive pilot logic, the plan must require targeted regression coverage or an explicit documented exception. For local-app pilots, follow [`docs/guides/local-app-verification-ladder.md`](../../.mat/docs/guides/local-app-verification-ladder.md): manual/staging is the default baseline unless deterministic local automation already exists in the target repo, and browser-use / Playwright are ladder tools rather than implied defaults.

Write the plan to `docs/current-plan.md` before delegating.

**Execution validation loops:** Apply **Tier 2b validation-loop discipline** whenever this command authors or re-projects `docs/current-plan.md`. Under `## Verification plan`, preserve the `### Per-phase validation loops (loop until pass)` table with concrete repo-native commands and the `### Global validation commands (before handoff)` numbered list from [`docs/templates/execution-plan-template.md`](../../.mat/docs/templates/execution-plan-template.md). Each phase loops through fix and re-run until green; run the global list before builder/verifier handoff. Markdown remains the canonical execution contract: this command must not create or require a living HTML plan.

**Living-plan amendments (v0.1):** Substantive `docs/current-plan.md` handoffs must include a final `## Amendments` section (exact level-2 heading). Each line is append-only: `- YYYY-MM-DDTHH:MM:SSZ — role — summary` (ISO-8601 UTC). The parent orchestrator may append during orchestration when scope or intent changes; never rewrite or delete prior lines or edit timestamps. Verifier append is prohibited (read-only). Full rules: [`docs/architecture/plan-contract.md`](../../.mat/docs/plan-contract.md).

**Optional Plan metadata (audit-only):** Parent/operator **may** append optional `## Plan metadata` with append-only `### modified` / `### session` / `### commit` list bullets (one line per projection, session start, or merge milestone). **Not** YAML frontmatter. Complements `docs/session-summary.md` and MAO advisory events — does not replace them; hooks **do not** auto-write metadata. Builder/verifier read-only. Authority disclaimer: [`docs/architecture/plan-contract.md`](../../.mat/docs/plan-contract.md).

**Status marker checklists (v0.1, Slice 3):** Substantive `docs/current-plan.md` handoffs must use contract markers on **implementation steps** and **acceptance/validation** checklists: `- []` idle · `- [wip]` in progress · `- [x]` done · `- [f]` failed/blocked (with reason). State machine: `[] → [wip] → [x]` or `[] → [wip] → [f] → [wip]`. Markers are **advisory** on the plan; MAO build→validate gates stay on `build-result.md` / `verify-result.md` only. Builder mutates markers in-place during build; parent may set `[wip]` at slice start; verifier read-only (warn-not-fail on drift). See [`docs/architecture/plan-contract.md`](../../.mat/docs/plan-contract.md).

### Step 1b — Plan→Build Transition Check

After `docs/current-plan.md` is written by a file tool, hooks may emit `artifacts/mao/gate.json` (`build_may_start`, `validate_may_start`, `advisory_pending`, checks, reasons, mtimes) and refresh `artifacts/mao/downstream-readiness.json` (or only the latter when `CURSOR_MAO_GATE=0`). With **`CURSOR_MAO_HOOK_AUTO_TRANSITION_CAPTURE=1`** and **`CURSOR_MAO_GATE` on**, PostToolUse may also append `transition-events.jsonl` via `capture_transition_decision` when mutations apply (deduped) — you still perform explicit plan→build checks and own `TodoWrite`. Use gate/readiness as **advisory** signals only; files stay authoritative. Only a **fresh, valid, internally consistent, positive** gate may support your decision to continue. Optionally call `evaluate_parent_downstream_readiness_advisory()` in `.cursor/hooks/mao_gate.py` or `python3 scripts/mao-downstream-readiness.py` so the on-disk readiness snapshot is compared to a live recompute (`trusted_snapshot_for_hint` only when edges align); weak or stale readiness data must fall back to explicit file checks — never treat the snapshot as sole truth.

Before any builder dispatch, perform the parent-owned plan→build transition check (via `evaluate_plan_to_build_transition()` in `.cursor/hooks/mao_gate.py` when available):
- `docs/current-plan.md` exists
- the plan is not the repo placeholder
- the plan is substantive enough to count as a real handoff

If the gate is absent, disabled (`CURSOR_MAO_GATE=0`), stale, invalid, contradictory, or negative, fall back to the same manual file-based check. Do not auto-start the builder from the gate alone.

After the explicit check, record the decision via `capture_transition_decision(repo_root, "plan_to_build")` in `.cursor/hooks/mao_gate.py` when available. That helper appends a reviewable line to `artifacts/mao/transition-events.jsonl` (including `todo_mutations` / blocked-reason fields), overwrites gitignored `artifacts/mao/suggested-todo-mutation.json` when the append succeeds, returns the same **`todo_mutations`** map on the Python result, and may optionally emit a fail-open `MaoTransition` API event. It never calls `TodoWrite` or changes MAO state by itself.

If the capture result’s `todo_mutations` is non-empty (same rules as `parent_owned_todo_mutations_for_transition(decision)`), apply it via `TodoWrite` before builder dispatch — the exact `plan -> build` MAO mutation is `[mao:plan]` completed and `[mao:build]` in_progress. A passing explicit canonical-file check may return that same mutation on either the advisory-gate or manual/file fallback path, except when `decision_mode` is `gate_plus_files` and `decision["advisory_pending"]["aligned_with_live"]` is `false` (refresh `gate.json` or use manual review before mutating todos). Use `decision["advisory_pending"]["interpretation"]` when summarizing pending build work. If `todo_mutations` is empty, do not infer a different mutation; use `todo_mutations_blocked_reasons` on the capture result to explain why.

Optional: `python3 scripts/mao-capture-transition.py plan_to_build` from repo root prints the same summary plus embedded `parent_transition_bundle` (decision + `todo_mutations` + `unblock_semantic` interpretation). Use `--bundle-only` for a no-append rehearsal; `--with-downstream-readiness` embeds the full readiness advisory inside the bundle (still no auto-start).

Optional rehearsal before `TodoWrite merge`: echo the three MAO todos as JSON stdin to `python3 scripts/mao-todo-write-merge.py --from-suggested` (after a successful capture append) to confirm `validation_ok` and merged statuses match `todo_mutations_used`.

### Step 1c — Onboarding task status sync

If the projected plan came from an approved onboarding package and `specs/<slug>/tasks.json` exists, carry the matching `TASK-###` into `docs/current-plan.md` and keep that task status synchronized with execution:
- set the matching task to `in_progress` when the slice starts
- keep all unrelated tasks `planned`
- set the matching task to `done` after verifier PASS and slice completion
- set the matching task to `blocked` or `deferred` with a short note if execution stops for a real blocker or operator decision

Do not treat `tasks.json` as a competing runtime authority. If no onboarding package exists, current behavior stays unchanged.

### Step 2 — Delegate to Builder
Spawn the **builder** subagent with:
- The task description
- The plan from `docs/current-plan.md`
- [`docs/reference/todo-orchestration.md`](../../.mat/docs/todo-orchestration-protocol.md) and explicit instruction that the builder may set `[mao:build]` to `in_progress` only; the parent owns completion after the transition check
- An advisory single-line MAO context block (optional `"mao_worktree":{"label":"…"}` when the parent knows the parallel worktree name, e.g. from [`.cursor/worktrees.json`](../worktrees.json)):
  `MAO_TASK_CONTEXT_JSON: {"tag":"[mao:build]","role":"builder","primary_artifact":"build-result.md","handoff_inputs":["docs/current-plan.md"],"depends_on":"plan"}`
- Explicit fallback: if that context is missing or malformed, the builder must continue from `docs/current-plan.md` and the normal file-based handoff flow. `subagentStart` still logs resolved **`mao_worktree`** from the workspace root independently of the JSON line.
- Instruction to produce `build-result.md` upon completion
- Instruction that `build-result.md` must match [`docs/reference/workflow-artifact-contract.md`](../../.mat/docs/workflow-artifact-contract.md)

Wait for the builder to complete. Do not proceed until `build-result.md` exists.

If the builder is still reading, searching, validating setup, or preparing output, treat that as legitimate progress. Missing `build-result.md` alone is not a reason to duplicate implementation work; if status is unclear, use the advisory progress helper or resume the same builder with a narrow status prompt first. If the tree is dirty, inspect it with `scripts/inspect_worktree_attribution.py` before treating any file as an unexpected blocker.

### Step 2b — Build→Validate Transition Check

After `build-result.md` is written by a file tool, hooks may refresh `artifacts/mao/gate.json` (`build_may_start`, `validate_may_start`, `advisory_pending`, checks, reasons, mtimes). With **`CURSOR_MAO_HOOK_AUTO_TRANSITION_CAPTURE=1`**, PostToolUse may append `transition-events.jsonl` when build→validate mutations apply. With **`CURSOR_MAO_VERIFIER_AUTOSTART=1`**, hooks may write gitignored **`artifacts/mao/verifier-autostart-intent.json`** after a successful hook capture — compare `plan_mtime_epoch` / `build_mtime_epoch` in that file to current file mtimes before treating it as current; after you spawn the verifier, **delete or mark consumed** so stale intents do not linger. Use the gate as an **advisory** signal only; files stay authoritative. Only a **fresh, valid, internally consistent, positive** gate may support your decision to continue. Keep the actual Cursor todo on `pending` until the parent decides to move it; `advisory_pending.*.advisory_state = ready_for_parent_review` is only a review hint, not a new MAO status. As after plan write, you may use `evaluate_parent_downstream_readiness_advisory()` or `scripts/mao-downstream-readiness.py` for the same trusted-vs-live readiness comparison before verifier dispatch (`trusted_snapshot_for_hint` is never permission to skip explicit checks).

Before any verifier dispatch, perform the parent-owned build→validate transition check (via `evaluate_build_to_validate_transition()` in `.cursor/hooks/mao_gate.py` when available):
- `docs/current-plan.md` is ready
- `build-result.md` exists
- the first declared build `Status` is **PASS** or **PARTIAL**
- `Acceptance Criteria` contains only **PASS** / **PARTIAL** outcomes
- `Linting / Type-Check` is **PASS**

If the gate is absent, disabled (`CURSOR_MAO_GATE=0`), stale, invalid, contradictory, or negative, fall back to the same manual file-based check. Do not auto-start the verifier from the gate alone.

After the explicit check, record the decision via `capture_transition_decision(repo_root, "build_to_validate")` in `.cursor/hooks/mao_gate.py` when you want a parent-owned capture (hooks may have captured already when **`CURSOR_MAO_HOOK_AUTO_TRANSITION_CAPTURE`** is on — optional duplicate lines when fingerprints differ). That helper appends a reviewable line to `artifacts/mao/transition-events.jsonl` (including `todo_mutations`), overwrites `artifacts/mao/suggested-todo-mutation.json` when the append succeeds, returns **`todo_mutations`** on the Python result, and may optionally emit a fail-open `MaoTransition` API event. It never calls `TodoWrite` or auto-starts the verifier.

### Step 3 — Delegate to Verifier
If the transition check passes, apply the **`todo_mutations`** from the Step 2b `capture_transition_decision(..., "build_to_validate")` result via `TodoWrite merge` when non-empty and `validate_mao_todo_mutations_against_todos()` passes, using `apply_parent_todo_mutations_to_cursor_todos()` (or use `parent_owned_todo_mutations_for_transition(decision)` only if you evaluated without capturing). That is the exact `build -> validate` MAO mutation (`[mao:build]` completed, `[mao:validate]` in_progress). A passing explicit canonical-file check may return that same mutation on either the advisory-gate or manual/file fallback path, except when `gate_plus_files` pairs with `decision["advisory_pending"]["aligned_with_live"] === false`. Use `decision["advisory_pending"]["interpretation"]` when summarizing why validate is still pending. If `todo_mutations` is empty or validation fails, do not auto-mutate MAO state from helper output.

Optional: `python3 scripts/mao-capture-transition.py build_to_validate` from repo root prints the same summary with `parent_transition_bundle` (same flags as plan→build; still no verifier auto-start). Optional merge rehearsal: `scripts/mao-todo-write-merge.py --from-suggested` with stdin JSON listing the three MAO todos.

Spawn the **verifier** subagent with:
- The plan from `docs/current-plan.md`
- The builder result from `build-result.md`
- [`docs/reference/todo-orchestration.md`](../../.mat/docs/todo-orchestration-protocol.md) and ownership of `[mao:validate]` (status updates)
- An advisory single-line MAO context block (optional `"mao_worktree":{"label":"…"}` when known):
  `MAO_TASK_CONTEXT_JSON: {"tag":"[mao:validate]","role":"verifier","primary_artifact":"verify-result.md","handoff_inputs":["docs/current-plan.md","build-result.md"],"depends_on":"build"}`
- Explicit fallback: if that context is missing or malformed, the verifier must continue from `docs/current-plan.md`, `build-result.md`, and the normal file-based handoff flow. `subagentStart` still logs resolved **`mao_worktree`** from the workspace root.
- Instruction to check each acceptance criterion and return a **structured verify payload** (JSON or contract-shaped markdown in chat) — verifier **must not** write `verify-result.md` (`readonly: true`)
- Instruction that the **parent** serializes `verify-result.md` via `serialize_verify_result()` after optional `mat-scope-audit.py gate`, global validation commands from the plan, and merging the verifier payload; on-disk file must match [`docs/reference/workflow-artifact-contract.md`](../../.mat/docs/workflow-artifact-contract.md)

Wait for the verifier to complete and deliver the structured payload. Run parent-owned runtime checks from the plan, then serialize `verify-result.md`. Mark `[mao:validate]` completed when the serialized handoff satisfies your gates.

If the verifier is still gathering evidence, validating setup, or producing partial output, treat that as legitimate progress. Missing `verify-result.md` **during** the verifier run is expected (parent-owned file); missing **structured payload** after verifier stop is not. Do not duplicate review work because the handoff file is absent mid-run; if status is unclear, resume the same verifier with a narrow status prompt first. If the tree is dirty, inspect it with `scripts/inspect_worktree_attribution.py` before treating any file as an unexpected blocker.

### Step 4 — Self-Validate
Before reporting completion, verify:
- [ ] `build-result.md` exists and contains a PASS or structured output
- [ ] `verify-result.md` exists and all acceptance criteria are marked PASS
- [ ] No hook stop conditions were triggered without resolution
- [ ] If observability is running, the dashboard received events for this session
- [ ] Risky workflow or security-sensitive changes have targeted regression coverage, or the exception is documented explicitly in the handoff artifacts

### Step 5 — Report
Summarize the run:
- What was built
- What the verifier found
- Any open issues or follow-up tasks

---

## Stop Conditions

Stop immediately and report failure if:
- The builder subagent fails after 2 retries
- The verifier marks any acceptance criterion FAIL without a clear remediation path
- A required tool or dependency is unavailable

---

## Notes

- This command replaces `.claude/commands/mat-plan-team.md` from `disler/claude-code-hooks-mastery`
- Claude task-board primitives (TaskCreate, TaskList, SendMessage) are replaced by:
  - File-based handoff (`current-plan.md`, `build-result.md`, `verify-result.md`)
  - Cursor **To-dos** with the MAO protocol ([`docs/reference/todo-orchestration.md`](../../.mat/docs/todo-orchestration-protocol.md)) when `TodoWrite` is available
  - Hook-based lifecycle events (PostToolUse, Stop, SubagentStop → observability)
  - Parent-agent sequencing (no shared message bus, no third-party task MCP)
- For the final execution handoff, follow [`docs/architecture/orchestration-workflow.md#execution-closeout-contract`](../../.mat/docs/orchestration-workflow.md#execution-closeout-contract).
