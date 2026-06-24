# Todo orchestration protocol (MAO — Multi-Agent Orchestration)

- **Purpose:** Strict, machine- and human-readable conventions for Cursor **To-dos** alongside file handoffs (`docs/current-plan.md`, `build-result.md`, `verify-result.md`).
- **Audience:** Parent orchestrator, builder, verifier; operators using `/mat-plan-team` or equivalent.
- **Status:** MVP (Phase 2 spike)
- **Last updated:** 2026-03-27 (PostToolUse path extraction + SubagentStart root hardening)
- **Rule:** [`.cursor/rules/orchestrator-todos.mdc`](../.cursor/rules/orchestrator-todos.mdc)

## MVP scope

| In scope | Out of scope (later) |
|----------|----------------------|
| Three-task convention + statuses + plan→build / build→validate dependencies | Live mirror of Cursor’s internal todo list UI (beyond MAO `MaoTransition` visibility in the observability dashboard) |
| Orchestrator `.mdc` + agent/command alignment | Hook-driven auto-spawn on `TodoWrite` |
| Deterministic `artifacts/mao/gate.json` after file writes to `docs/current-plan.md` or `build-result.md` (PostToolUse) | OS-level or hook-spawned verifier/mat-builder processes |
| Opt-in hook `capture_transition_decision()` after handoff writes (`CURSOR_MAO_HOOK_AUTO_TRANSITION_CAPTURE=1`, requires `CURSOR_MAO_GATE` on + trusted fresh gate + non-empty `todo_mutations`; deduped) | Subagent spawn from Python hooks |
| Opt-in gitignored `verifier-autostart-intent.json` after successful build→validate hook capture (`CURSOR_MAO_VERIFIER_AUTOSTART=1`) — parent still confirms and spawns verifier | Treating intent file as permission to skip explicit handoff checks |
| Advisory `MAO_TASK_CONTEXT_JSON` prompt injection for builder/verifier subagents | Broader todo-transition automation |
| `PostToolUse` records MAO todo observations (`todo-write-events.jsonl`, `last-todo-write-observation.json`) after normalized `todo_write` — traceability only | External task-board MCPs |
| Hook-written `downstream-readiness.json` — deterministic `unblock_semantic` per MAO edge + optional todo observation cross-check (no `TodoWrite`, no auto-spawn); parent reads via `evaluate_parent_downstream_readiness_advisory()` (live vs on-disk trust); triggers include `transition_capture` and `hook_post_tool_use_auto_capture` | — |
| `evaluate_mao_parent_transition_bundle()` + `interpret_unblock_semantic_for_parent()` — one-call decision + mutations + edge semantics for parents | — |
| Observability dashboard **MAO visibility** panel — surfaces ingested `MaoTransition` events (WebSocket uses an enlarged payload preview for this type); opt-in **`CURSOR_MAO_EMIT_TRANSITION_OBSERVABILITY`** POSTs from hook auto-capture; advisory only | — |
| File handoffs remain required and authoritative | — |

## Task tags (required)

Each orchestrated run uses **exactly three** todos. Every item **must** include its tag verbatim (including brackets) so roles and automation can scan without fuzzy parsing:

| Tag | Role | Primary artifact | Logical dependency |
|-----|------|------------------|-------------------|
| `[mao:plan]` | Parent orchestrator | `docs/current-plan.md` | None |
| `[mao:build]` | Builder | `build-result.md` | Plan complete |
| `[mao:validate]` | Verifier | `verify-result.md` | Build complete |

### Canonical content strings

Use these **exact** strings for the todo `content` (single line):

1. `[mao:plan] role:orchestrator | artifact:docs/current-plan.md`
2. `[mao:build] role:builder | artifact:build-result.md | dep:plan`
3. `[mao:validate] role:verifier | artifact:verify-result.md | dep:build`

Optional suffix (human-readable only, after a space): short task title, e.g. ` — fix login bug`. The `[mao:…]` prefix must remain the **start** of the string.

## Cursor statuses (semantic mapping)

Map Cursor To-do statuses to orchestration semantics as follows:

| Cursor status | Meaning in MAO |
|---------------|----------------|
| `pending` | Not started; waiting on dependency or orchestrator |
| `in_progress` | Active for that role |
| `completed` | Phase done; artifact present and accepted by that actor |
| `cancelled` | User or orchestrator aborted; do not spawn downstream |

### Default lifecycle

1. **Orchestrator** creates all three todos. Initial state: `[mao:plan]` → `in_progress`; `[mao:build]` and `[mao:validate]` → `pending`.
2. After `docs/current-plan.md` is written, the parent performs an explicit **plan→build transition check**. Only when that check is transition-ready may `[mao:plan]` move to `completed`, `[mao:build]` move to `in_progress`, and the builder be spawned.
3. After builder finishes, the parent performs an explicit **build→validate transition check**. Only when that check is transition-ready may `[mao:build]` move to `completed`, `[mao:validate]` move to `in_progress`, and the verifier be spawned.
4. After `verify-result.md` meets orchestrator gates: `[mao:validate]` → `completed`.

### Pending advisory substates (gate-only)

`artifacts/mao/gate.json` may add extra meaning for downstream MAO work that is still on Cursor status `pending`:

| Cursor status | Advisory pending substate | Meaning |
|---------------|---------------------------|---------|
| `pending` | `blocked` | Canonical handoff evidence is still missing or insufficient. |
| `pending` | `ready_for_parent_review` | Canonical handoff evidence looks transition-ready, but only the parent may do the explicit check and move real MAO state forward. |

This does **not** introduce a new Cursor todo status. It is descriptive metadata only.

### Parent consumption of `advisory_pending` (orchestration)

`evaluate_plan_to_build_transition()` and `evaluate_build_to_validate_transition()` in [`mao_gate.py`](../.cursor/hooks/mao_gate.py) attach an **`advisory_pending` bundle** on every decision (in addition to the existing `gate` advisory reader result):

| Field | Meaning |
|-------|---------|
| `live` | `advisory_pending` recomputed immediately from canonical files (`evaluate_mao_gate`) — always use this to understand **current** blocked vs `ready_for_parent_review` semantics. |
| `from_gate_file` | Snapshot from `artifacts/mao/gate.json` when that file parses with **valid gate shape**; `null` when missing or invalid shape. |
| `gate_file_shape_valid` | Whether the on-disk gate JSON had a full valid v2 shape (independent of “positive” / trusted preflight). |
| `aligned_with_live` | `true` when `from_gate_file` matches `live` for both MAO tags; `false` when they disagree; `null` when there is no comparable file snapshot. |
| `trusted_positive_gate_for_transition` | Same notion as a usable `read_parent_advisory_gate()` result for the transition under consideration. |
| `interpretation` | Deterministic strings: how to treat the gate file for this transition, and a short summary of the **focus** downstream tag (`[mao:build]` for `plan_to_build`, `[mao:validate]` for `build_to_validate`). |

**How the parent should use it**

1. **Always** run the explicit canonical file transition checks first; the bundle does not replace them.
2. Use **`live`** + **`interpretation`** to explain why `[mao:build]` / `[mao:validate]` should stay `pending`, what `recommended_parent_action` means, and which `blockers` the hook saw.
3. Use **`trusted_positive_gate_for_transition`** only as support for `decision_mode: gate_plus_files`; weak or negative gate data implies manual/file fallback for advisory trust, not for canonical readiness.
4. If `decision_mode` is `gate_plus_files` but **`aligned_with_live` is `false`**, treat the gate file as **contradictory** versus live handoffs: refresh the gate (e.g. re-save handoffs so hooks rewrite `gate.json`) or proceed using manual checks only. **`parent_owned_todo_mutations_for_transition()` returns no mutation** in that case even if canonical file checks passed — fail closed on todo mutations only, not on workflow progress (the parent can still move forward after manual review and a refreshed or ignored gate).

`capture_transition_decision()` persists the same `advisory_pending` bundle on each `artifacts/mao/transition-events.jsonl` line for audits, and **surfaces supported todo mutations** on the same path: each appended line includes `todo_mutations`, `todo_mutations_applicable`, and `todo_mutations_blocked_reasons` derived from `parent_owned_todo_mutations_for_transition(decision)`. When the append succeeds, it also overwrites gitignored **`artifacts/mao/suggested-todo-mutation.json`** with a small summary the parent can read alongside the composer session. **Hooks still do not call `TodoWrite`**; the parent remains the only actor that applies Cursor todo state. If transition capture fails to append (IO error), no suggested file is written for that call; the parent can still run `evaluate_*_transition()` and `parent_owned_todo_mutations_for_transition()` in-process.

### Opt-in PostToolUse transition capture (narrow automation)

When **`CURSOR_MAO_HOOK_AUTO_TRANSITION_CAPTURE=1`**, [`post_tool_validate.py`](../.cursor/hooks/post_tool_validate.py) calls [`maybe_hook_auto_capture_transition()`](../.cursor/hooks/mao_gate.py) **after** `gate.json` refresh on writes to `docs/current-plan.md` or `build-result.md`. Hook capture **does not run** when **`CURSOR_MAO_GATE=0`** (implementation ties hook capture to the same trusted positive fresh gate machinery as the advisory slice). It calls the same `capture_transition_decision()` + evaluators; it skips when `todo_mutations` would be empty, when advisory `gate_plus_files` is misaligned vs live, or when the last `transition-events.jsonl` line for that transition already records the same handoff file mtimes (**dedupe**). Successful hook captures refresh **`downstream-readiness.json`** with `trigger: hook_post_tool_use_auto_capture` instead of `transition_capture`. Fail-open on errors.

### Opt-in verifier dispatch intent (not auto-start)

When **`CURSOR_MAO_VERIFIER_AUTOSTART=1`**, hooks may write gitignored **`artifacts/mao/verifier-autostart-intent.json`** only after a **successful build→validate hook auto-capture** in that PostToolUse chain, and only while canonical build→validate checks still pass on disk, `read_parent_advisory_gate(..., build_to_validate)` is usable, and `gate_is_fresh_on_disk` holds for the build handoff. Optional **`CURSOR_MAO_VERIFIER_AUTOSTART_REQUIRE_TODO_OBSERVATION=1`** additionally requires `last-todo-write-observation.json` to exist with `parse_quality: ok`. Minimal payload: `requested_at`, `transition`, `repo_root`, `mao_worktree`, `plan_mtime_epoch`, `build_mtime_epoch`, `reasons`. **“Autostart” names a conventional parent-owned review step** (not a guarantee of verifier dispatch): review the intent, apply `TodoWrite` if still needed, optionally spawn the verifier with `MAO_TASK_CONTEXT_JSON` when explicit build→validate checks pass, then delete or mark the intent consumed — hooks never start the verifier; the parent may still defer or skip dispatch for policy reasons.

### Exact parent-owned transition mutations

[`parent_owned_todo_mutations_for_transition()`](../.cursor/hooks/mao_gate.py) expresses the only helper-driven MAO status mutations allowed in this slice:

- Passing `plan_to_build` decision => `[mao:plan]` `completed`, `[mao:build]` `in_progress`, `[mao:validate]` unchanged
- Passing `build_to_validate` decision => `[mao:build]` `completed`, `[mao:validate]` `in_progress`, `[mao:plan]` unchanged
- Blocked, unsupported, non-parent, or otherwise failed decisions => **no helper-driven mutation**
- `decision_mode: gate_plus_files` **and** `advisory_pending.aligned_with_live === false` => **no helper-driven mutation** (contradictory on-disk `advisory_pending` vs live recompute; manual path or refresh gate first)

The helper is intentionally conservative about ownership and transition readiness. If stale, invalid, contradictory, or negative gate evidence forces a fallback to manual/file-based review, the parent may still get the exact supported mutation after the explicit canonical-file transition check passes, **except** for the misaligned `gate_plus_files` case above.

### Plan → build gate (strict)

- `[mao:build]` **must not** be `in_progress` until `[mao:plan]` is `completed`.
- The parent/orchestrator **owns** the transition decision; neither the hook gate nor plan-writing tool auto-advances MAO state.
- Exact transition trigger: `docs/current-plan.md` exists, is not the repo placeholder, and is substantive enough to count as a real handoff.
- If any part of that trigger is missing or not satisfied, the parent stays on manual review/file-based behavior and does **not** move build forward.
- `parent_owned_todo_mutations_for_transition()` may translate a passing decision into the exact `[mao:plan]` / `[mao:build]` status changes above after either `gate_plus_files` or `manual_file_check`, but it returns no mutation for blocked, unsupported, or non-parent decisions.

### Build → validate gate (strict)

- `[mao:validate]` **must not** be `in_progress` until `[mao:build]` is `completed`.
- The parent/orchestrator **owns** the transition decision; neither the hook gate nor the builder auto-advances MAO state.
- Exact transition trigger: `docs/current-plan.md` is ready, `build-result.md` exists, the first declared build `Status` is **PASS** or **PARTIAL**, the `Acceptance Criteria` section contains only **PASS** / **PARTIAL** outcomes (no **FAIL**), and `Linting / Type-Check` is **PASS**.
- If any part of that trigger is missing or not satisfied, the parent stays on manual review/file-based behavior and does **not** move validate forward.
- `parent_owned_todo_mutations_for_transition()` may translate a passing decision into the exact `[mao:build]` / `[mao:validate]` status changes above after either `gate_plus_files` or `manual_file_check`, but it returns no mutation for blocked, unsupported, or non-parent decisions.

## Role responsibilities

### Parent orchestrator

- Create/update all three todos via `TodoWrite` at orchestration start and at each transition.
- Own `[mao:plan]` from `in_progress` → `completed`.
- Move `[mao:build]` and `[mao:validate]` forward; never mark validate complete before verifier evidence exists.
- Capture each explicit parent-owned transition decision alongside the file check, preferably via `capture_transition_decision()` in [`mao_gate.py`](../.cursor/hooks/mao_gate.py), so the decision is durably recorded without changing the canonical handoff flow. Prefer using the **`todo_mutations` field on the capture return value** (or the latest `suggested-todo-mutation.json` after a successful append) before calling `TodoWrite`, instead of recomputing mutations separately — both paths use the same `parent_owned_todo_mutations_for_transition()` rules.
- When helper-driven MAO state updates are desired, use `parent_owned_todo_mutations_for_transition(decision)` or the `todo_mutations` from `capture_transition_decision()` to obtain the exact allowed mutations. A passing explicit parent transition check may yield the same mutation on either the advisory-gate or manual/file fallback path, unless `gate_plus_files` is paired with `advisory_pending.aligned_with_live === false`. Read `decision["advisory_pending"]["interpretation"]` when explaining pending work to the user. If the helper still returns `{}`, do not mutate MAO state from helper output.
- To turn `todo_mutations` into a **`TodoWrite merge`** payload, use `apply_parent_todo_mutations_to_cursor_todos(todos, todo_mutations)` in [`mao_gate.py`](../.cursor/hooks/mao_gate.py): it matches each todo’s `content` by MAO tag prefix (protocol-allowed optional suffix after the canonical line is fine). Optionally call `validate_mao_todo_mutations_against_todos(todos, todo_mutations)` first; if it returns `ok: false`, skip `TodoWrite` and fix the list or handoffs. Optional CLI: [`scripts/mao-todo-write-merge.py`](../scripts/mao-todo-write-merge.py) (stdin JSON + `--from-suggested` or inline `todo_mutations`).

### Parent transition bundle (single-call orchestration view)

[`evaluate_mao_parent_transition_bundle()`](../.cursor/hooks/mao_gate.py) combines, for one edge (`plan_to_build` or `build_to_validate`):

| Field | Purpose |
|-------|---------|
| `decision` | Full `evaluate_plan_to_build_transition()` or `evaluate_build_to_validate_transition()` output (includes `advisory_pending`). |
| `todo_mutations` | Same map as `parent_owned_todo_mutations_for_transition(decision)`. |
| `todo_mutations_blocked_reasons` | Deterministic reasons when mutations are `{}`. |
| `edge_readiness` | Same per-edge record as inside `compute_mao_downstream_readiness()` (`unblock_semantic`, `transition_ready`, etc.). |
| `unblock_semantic_interpretation` | From `interpret_unblock_semantic_for_parent()` — parent-facing meaning and `todo_mutations_expected`. |
| `orchestration_flow_hint` | One-line tie-together for summaries (still not a substitute for explicit checks). |

Optional `include_downstream_readiness_advisory=True` adds the full-file advisory (`live_snapshot`, `trusted_snapshot_for_hint`, …). Prefer this bundle when you would otherwise chain multiple `mao_gate` calls in the parent composer.

### Parent-owned `unblock_semantic` values (downstream-readiness.json edges)

Hook-written **`artifacts/mao/downstream-readiness.json`** labels each MAO edge with exactly one of:

| `unblock_semantic` | Meaning (parent-owned) | Helper `todo_mutations` |
|---------------------|-------------------------|-------------------------|
| `downstream_blocked` | `transition_ready` is false for that edge. | Not applicable — `{}`. |
| `unblocked_for_parent_action` | `transition_ready` true and mutation map non-empty. | Apply after explicit check. |
| `ready_canonical_files_advisory_misaligned` | `transition_ready` true, `gate_plus_files`, `advisory_pending.aligned_with_live === false`. | Withheld `{}` until gate refresh or manual path. |
| `transition_ready_uncertain_mutation_withheld` | `transition_ready` true but no mutation (rare shapes). | `{}` — manual review. |

[`interpret_unblock_semantic_for_parent()`](../.cursor/hooks/mao_gate.py) expands each value into `meaning`, `parent_next`, and `todo_mutations_expected`. [`scripts/mao-downstream-readiness.py`](../scripts/mao-downstream-readiness.py) `--interpret-edges` attaches the same interpretation to `live_snapshot` edges for CLI use.

### Builder

- On start: set `[mao:build]` → `in_progress` (if not already).
- On finish: write a truthful `build-result.md`, but leave the build→validate state transition to the parent. The builder does **not** set `[mao:build]` → `completed`; the parent does that only after the explicit transition check passes. On failure, leave `[mao:build]` as-is and document the outcome in `build-result.md` so the orchestrator can retry or cancel.
- Do **not** mark `[mao:plan]` or `[mao:validate]`.

### Verifier

- On start: set `[mao:validate]` → `in_progress`.
- On finish: set `[mao:validate]` → `completed` when `verify-result.md` is written with final outcome.
- Do **not** mark `[mao:plan]` or `[mao:build]`.

## SubagentStart MAO task context (advisory)

Parent prompts for the builder and verifier may include one machine-readable line:

```text
MAO_TASK_CONTEXT_JSON: {"tag":"[mao:build]","role":"builder","primary_artifact":"build-result.md","handoff_inputs":["docs/current-plan.md"],"depends_on":"plan"}
```

or:

```text
MAO_TASK_CONTEXT_JSON: {"tag":"[mao:validate]","role":"verifier","primary_artifact":"verify-result.md","handoff_inputs":["docs/current-plan.md","build-result.md"],"depends_on":"build"}
```

### Minimal shape

- `tag` — `[mao:build]` or `[mao:validate]`
- `role` — `builder` or `verifier`
- `primary_artifact` — `build-result.md` or `verify-result.md`
- `handoff_inputs` — ordered list of the canonical file handoffs that subagent should read first
- `depends_on` — optional dependency token (`plan` for build, `build` for validate)

### Semantics

- The marker is **advisory only**. It is meant for prompt clarity and for `subagentStart` hook parsing/logging.
- File handoffs remain **canonical**: builder/verifier correctness still comes from `docs/current-plan.md`, `build-result.md`, and `verify-result.md`.
- If the marker is missing, malformed, or unsupported, the subagent and hooks **must fail open** to the existing file-based workflow.
- The marker does **not** authorize verifier auto-start, broader todo state transitions, or any replacement of the normal build→validate gate.

### Optional `mao_worktree` inside `MAO_TASK_CONTEXT_JSON`

Parents may add an optional object so subagent logs can record a **human-provided** label alongside hook-resolved workspace metadata:

```text
MAO_TASK_CONTEXT_JSON: {"tag":"[mao:build]","role":"builder","primary_artifact":"build-result.md","handoff_inputs":["docs/current-plan.md"],"depends_on":"plan","mao_worktree":{"label":"builder-agent"}}
```

- `mao_worktree.label` — non-empty string after trim; source recorded as `parent_prompt` in parsed `mao_task_context`.
- If `mao_worktree` is missing, wrong type, or `label` is empty/invalid, the rest of the marker is still validated; invalid optional blocks are ignored (fail-open).
- [`subagent_start.py`](../.cursor/hooks/subagent_start.py) always adds a top-level **`mao_worktree`** object on the logged payload: resolved `project_dir` (**`CURSOR_PROJECT_DIR` / `CLAUDE_PROJECT_DIR` when set, else first `workspace_roots` entry, else `cwd`** — aligned with `post_tool_validate`), optional `label` / `bootstrapped_at` from `.cursor/worktree/*` when the parallel worktree bootstrap ran, and `source` = `cursor_worktree_marker` or `absent` (see [`mao_worktree.py`](../.cursor/hooks/mao_worktree.py)).

## MAO worktree metadata (protocol shape)

Deterministic, advisory-only context shared across **`artifacts/mao/gate.json`**, **`artifacts/mao/transition-events.jsonl`** lines, and **`subagentStart`** logs:

| Field | Type | Meaning |
|-------|------|---------|
| `project_dir` | string | Resolved absolute path to the repo root used for the hook or transition |
| `label` | string or null | Worktree name from `.cursor/worktree/name` when present |
| `bootstrapped_at` | string or null | Timestamp text from `.cursor/worktree/bootstrapped_at` when present |
| `source` | string | `cursor_worktree_marker` when `label` was read from disk; otherwise `absent` |

Missing files, IO errors, or unknown payload shapes **never** block orchestration or hook exit codes. The parent remains the decision-maker; metadata is for traceability only.

## Advisory gate file (`artifacts/mao/gate.json`)

After a **file-writing** `PostToolUse` whose targets include `docs/current-plan.md` or `build-result.md`, [`post_tool_validate.py`](../.cursor/hooks/post_tool_validate.py) calls [`mao_gate.py`](../.cursor/hooks/mao_gate.py) to **re-read** canonical handoff files and write `artifacts/mao/gate.json` (gitignored) with:

- `mao_worktree` — resolved worktree metadata for the project directory (same shape as the protocol table above).
- `build_may_start` — `true` only when the plan is present, not the repo placeholder, and ready for the parent-owned `plan -> build` transition.
- `validate_may_start` — `true` only when the plan is ready, `build-result.md` is present, the first declared `Status` line is **PASS** or **PARTIAL**, the `Acceptance Criteria` section contains no **FAIL**, and `Linting / Type-Check` is **PASS**.
- `advisory_pending` — gate-only metadata for downstream pending MAO work, where `[mao:build]` / `[mao:validate]` stay on Cursor status `pending` while being described as either `blocked` or `ready_for_parent_review`, plus a `recommended_parent_action`, `primary_artifact`, and any blocking reasons.
- `checks`, `reasons`, `inputs.plan_mtime_epoch` / `inputs.build_mtime_epoch` — for staleness checks vs disk.

**Semantics:** Handoff files remain **authoritative**. The gate is a deterministic hint; orchestrators must still read `docs/current-plan.md` before spawning the builder and `build-result.md` before spawning the verifier. Treat the gate as usable advisory input only when it is **fresh, valid, internally consistent, and positive** for the specific transition being considered (`build_may_start: true` for `plan -> build`, `validate_may_start: true` for `build -> validate`, expected schema/version, coherent `checks`, coherent `advisory_pending`, and matching mtimes for the files that transition depends on). Even then, the parent still performs the exact file-based transition check above. If the gate is missing, disabled (`CURSOR_MAO_GATE=0`), stale, invalid, contradictory, or negative, use the same rules manually. `ready_for_parent_review` does **not** mean `in_progress`; it only means the parent has enough canonical evidence to review the transition. See [`artifacts/mao/README.md`](../artifacts/mao/README.md).

## Transition decision capture (`artifacts/mao/transition-events.jsonl`)

When the parent performs the explicit `plan -> build` or `build -> validate` transition check, it should also record that decision in gitignored `artifacts/mao/transition-events.jsonl` via `capture_transition_decision()` in [`mao_gate.py`](../.cursor/hooks/mao_gate.py). The capture helper **computes** `todo_mutations` with `parent_owned_todo_mutations_for_transition(decision)` and returns them on the Python result dict; you do not need a second call unless you are evaluating without capturing.

Each append-only JSON line records:

- `mao_worktree` — resolved worktree metadata at capture time (same shape as gate / protocol table).
- `transition` — `plan_to_build` or `build_to_validate`
- `allowed` — whether the parent decided the transition may proceed
- `decision_owner` — `parent_orchestrator`
- `decision_mode` — `gate_plus_files` or `manual_file_check`
- `trigger_rule`, `reasons`, `manual_checks`
- `todo_mutations`, `todo_mutations_applicable`, `todo_mutations_blocked_reasons` — supported MAO status deltas for `TodoWrite` when applicable; empty map with reasons when blocked or misaligned per protocol
- `advisory` — whether the MAO gate was usable and why
- `advisory_pending` — the same structured bundle attached to `evaluate_*_transition()` (`live`, `from_gate_file`, `aligned_with_live`, `interpretation`, …)
- `files` — the handoff files and mtimes involved in the decision

**Suggested mutation file:** When the JSONL append succeeds, `capture_transition_decision()` overwrites gitignored **`artifacts/mao/suggested-todo-mutation.json`** (versioned `file_version` field) with the same mutation summary for quick inspection or scripting. Optional CLI: [`scripts/mao-capture-transition.py`](../scripts/mao-capture-transition.py) from repo root.

Optional observability emission may mirror the same transition payload to the Bun API as `event_type: MaoTransition`, but this is **fail-open only**: if the server is down, auth is missing, or validation fails, the parent still proceeds with the normal file-based workflow and local transition artifact capture remains non-blocking.

## MAO todo-write observation (`PostToolUse`)

When `PostToolUse` names normalize to **`todo_write`** (e.g. Cursor `TodoWrite`), [`post_tool_validate.py`](../.cursor/hooks/post_tool_validate.py) calls [`record_mao_todo_write_post_tool_observation()`](../.cursor/hooks/mao_gate.py), which **append-only** writes gitignored **`artifacts/mao/todo-write-events.jsonl`** and overwrites **`artifacts/mao/last-todo-write-observation.json`**.

Each observation includes `parse_quality` (`ok`, `no_mao_tags`, `empty_todos`, `invalid_input`, `ambiguous_duplicate_tags`, `partial`), `mao_rows` when parsing succeeds, `parse_notes` for degraded or ambiguous cases, `mao_worktree`, and **`file_handoff_signals`** from `evaluate_mao_gate()` (or a skip reason when `CURSOR_MAO_GATE` is disabled). This is **not** a parent transition decision, does **not** call `TodoWrite`, and does **not** authorize subagent start. Stale, missing, or ambiguous todo payload fields fail open to manual/file review (`parse_quality` documents the gap, and `parse_notes` explain partial results). Disable all recording with `CURSOR_MAO_TODO_POST_TOOL_USE=0`. Optional `CURSOR_MAO_TODO_POST_TOOL_REFRESH_GATE=1` refreshes `gate.json` after an observation when `CURSOR_MAO_GATE` is on.

## Downstream readiness snapshot (`artifacts/mao/downstream-readiness.json`)

Hooks overwrite this gitignored file (when `CURSOR_MAO_DOWNSTREAM_READINESS` is on) after:

- a successful `gate.json` refresh from a handoff write (`trigger`: `handoff_gate_refresh`),
- a successful todo-write observation (`trigger`: `todo_write_post_tool_use`),
- a handoff write while `CURSOR_MAO_GATE=0` (`trigger`: `handoff_post_tool_use_gate_disabled`).

[`compute_mao_downstream_readiness()`](../.cursor/hooks/mao_gate.py) evaluates **`plan_to_build`** and **`build_to_validate`** the same way as the parent helpers and sets per-edge fields including `transition_ready`, `helper_todo_mutation_applicable`, and **`unblock_semantic`**:

| `unblock_semantic` | Meaning |
|--------------------|---------|
| `downstream_blocked` | Canonical `transition_ready` is false for that edge. |
| `unblocked_for_parent_action` | Canonical transition is ready **and** `parent_owned_todo_mutations_for_transition()` would return the supported mutation map (parent may apply `TodoWrite` after its explicit check). |
| `ready_canonical_files_advisory_misaligned` | Canonical transition is ready but helper mutations are withheld because `decision_mode` is `gate_plus_files` and `advisory_pending.aligned_with_live` is false — refresh `gate.json` or use manual review before todo mutation. |
| `transition_ready_uncertain_mutation_withheld` | Defensive bucket for unexpected shapes; treat as manual review. |

The snapshot also includes **`todo_write_cross_check`**: when `last-todo-write-observation.json` exists, it compares recorded `file_handoff_signals` to live `evaluate_mao_gate()` booleans (`file_handoff_signals_match_live_gate` may be null when signals are absent). Missing, stale, or mismatched observation data does **not** change `unblock_semantic`; it only documents evidence quality.

**Parent ownership:** Same as the gate file — files and explicit transition checks remain authoritative. Disable the artifact with `CURSOR_MAO_DOWNSTREAM_READINESS=0`.

### Parent consumption of `downstream-readiness.json` (orchestration)

[`evaluate_parent_downstream_readiness_advisory()`](../.cursor/hooks/mao_gate.py) is the supported parent entry point. It **always** returns a fresh **`live_snapshot`** (same computation as hook-written files) and, when `artifacts/mao/downstream-readiness.json` exists, includes **`from_artifact`** plus trust fields:

| Field | Meaning |
|-------|---------|
| `downstream_readiness_enabled` | False when `CURSOR_MAO_DOWNSTREAM_READINESS` disables hook writes; live recompute is still returned for current edge semantics. |
| `artifact_present` / `artifact_shape_ok` / `artifact_version_ok` | Whether a readable JSON object with expected edge keys exists and matches `DOWNSTREAM_READINESS_VERSION`. |
| `artifact_aligned_with_live_edges` | `true` when on-disk `version` + `plan_to_build` + `build_to_validate` equal the live recompute; `false` when they differ (stale/tampered file); `null` when not comparable. |
| `trusted_snapshot_for_hint` | `true` only when enabled, present, valid version, valid shape, **and** edges match live — then the file’s `unblock_semantic` is a reliable advisory hint alongside explicit checks. |
| `reasons` | Machine codes (`artifact_missing`, `artifact_stale_or_divergent_from_live_edges`, …) when trust is withheld. |
| `interpretation` | One deterministic sentence for operator summaries. |

**How the parent should use it**

1. **Never** skip `evaluate_plan_to_build_transition()` / `evaluate_build_to_validate_transition()` or canonical file reads because this helper returned `trusted_snapshot_for_hint: true`.
2. Use **`live_snapshot`** when the file is missing, disabled, malformed, or **`trusted_snapshot_for_hint`** is false — live semantics are always authoritative for hints.
3. When **`trusted_snapshot_for_hint`** is true, you may cite on-disk `unblock_semantic` in explanations to the user; still apply `capture_transition_decision()` / `todo_mutations` / explicit checks before `TodoWrite merge` or subagent dispatch.
4. Optional CLI: [`scripts/mao-downstream-readiness.py`](../scripts/mao-downstream-readiness.py). Optional bundle with transition capture: `python3 scripts/mao-capture-transition.py <transition> --with-downstream-readiness`.

## Hooks and blocking risk

- **`postToolUse`:** Runs [`send_event.py`](../.cursor/hooks/send_event.py) (observability) and [`post_tool_validate.py`](../.cursor/hooks/post_tool_validate.py) (MAO gate refresh when `docs/current-plan.md` or `build-result.md` is touched — handoff detection uses expanded [`get_changed_files()`](../.cursor/hooks/post_tool_validate.py) path extraction; or **downstream-readiness** refresh when the gate is disabled but handoffs changed; **MAO todo observation** when the tool normalizes to `todo_write` via [`record_mao_todo_write_post_tool_observation()`](../.cursor/hooks/mao_gate.py); lint/typecheck after **file-writing** tools only).
- **Todo / list tools:** Cursor exposes todo updates through tool calls whose names may vary by version (e.g. `TodoWrite`). Those names are **not** in `post_tool_validate.py`’s `WRITE_TOOLS` set, so **no project-wide ruff/tsc run** is triggered by todo updates. When the normalized tool is `todo_write`, hooks may append **`artifacts/mao/todo-write-events.jsonl`** and overwrite **`artifacts/mao/last-todo-write-observation.json`** with parsed MAO rows (when unambiguous), `mao_worktree`, and **`file_handoff_signals`** from `evaluate_mao_gate()` — advisory traceability only; disable with `CURSOR_MAO_TODO_POST_TOOL_USE=0`. **`failClosed` is false** for these hooks, so hook failures do not hard-block the editor.
- **Evidence:** Todo updates still produce `PostToolUse` events that `send_event.py` forwards when the observability server is up (same as other tools).
- **`subagentStart`:** [`subagent_start.py`](../.cursor/hooks/subagent_start.py) still logs the raw start payload, attaches resolved **`mao_worktree`** for the workspace root, and records a parsed `mao_task_context` field when the task text contains a valid `MAO_TASK_CONTEXT_JSON:` line (including optional parent `mao_worktree.label`). Invalid or absent task context is ignored for the parsed field only.

### Committed vs local runtime proof

Checked-in hook JSON under `artifacts/phase1/` still does **not** include a raw `PostToolUse` sample whose `tool_name` is a todo tool (e.g. `TodoWrite`). When Cursor **does** deliver todo-tool `PostToolUse` stdin to hooks, gitignored **`artifacts/mao/todo-write-events.jsonl`** and **`last-todo-write-observation.json`** record a deterministic interpretation (see **MAO todo-write observation** above). The repo also includes a **durable redacted session audit** at [`artifacts/phase1/todo-runtime-proof-20260327.md`](../artifacts/phase1/todo-runtime-proof-20260327.md): one live MAO `TodoWrite` sequence was executed, then the observability DB and transcript were checked for the same session. Details and regeneration steps live in [`todo-orchestration-runtime-evidence.md`](todo-orchestration-runtime-evidence.md).

## Fallback

If `TodoWrite` is unavailable: follow [`.cursor/agents/parent-orchestrator.md`](../.cursor/agents/parent-orchestrator.md) using **files only**; note the skip in `docs/session-summary.md`. Do not introduce a third-party task MCP.

## Related docs

- [todo-orchestration-mao-todowrite-application.md](todo-orchestration-mao-todowrite-application.md) — focused verification notes for parent `TodoWrite merge` helpers
- [artifacts/mao/README.md](../artifacts/mao/README.md) — gate output directory (includes `downstream-readiness.json`)
- [Events and visualization](events-and-visualization.md) — optional `MaoTransition` backend event
- [Todo orchestration runtime evidence](todo-orchestration-runtime-evidence.md) — committed-artifact audit + local capture procedure
- [Todo orchestration pilot](todo-orchestration-pilot.md) — minimal end-to-end check
- [Orchestration workflow](orchestration-workflow.md)
- [Decision record](decision-record.md) — Phase 2 criteria
- [AGENTS.md](../AGENTS.md) — operator overview
