# AGENTS.md — Cursor-First Agentic Workflow Guide

This file replaces `CLAUDE.md` and any Claude-specific agent guidance files. It provides
Cursor-native instructions for agents operating in this repository.

---

## Repository Purpose

This repository implements a Cursor-first multi-agent engineering workflow adapted from
IndyDevDan's (disler) Claude Code agentic patterns. The architecture uses Cursor subagents,
hooks, worktrees, and MCP integrations instead of Claude-specific team/task-board primitives.
It is an internal/reference-oriented repository for the maintainer team, not a public packaging target by default.

When this repo is adopted into another codebase, use the sidecar helper to keep product-owned `AGENTS.md` files intact, add the short pointer note by default, and reserve the inline delimited MAT section for explicit fallback runs only. The **workflow artifact contract** for `build-result.md` / `verify-result.md` lives at `docs/workflow-artifact-contract.md` in this source repo and is packaged to **`.mat/docs/workflow-artifact-contract.md`** on bootstrap; adopted `.cursor/` prompts are rewritten to reference the sidecar path so operators are not pointed at a missing root `docs/` file.

**Source vs adopted (layout honesty):** this repository is the MAT **source** tree: it ships the full `docs/` manual set, `specs/`, `apps/` (observability), the primary `tests/` regression suite, and CI-oriented checks. A **bootstrapped product repo** gets `.cursor/`, selected `scripts/` (including `phase1-verify.sh`), `.mat/docs/`, `.mat/tests/` (copies of a small contract subset), `.mat/AGENTS.mat.md`, and minimal root `docs/current-plan.md` plus `docs/long-run-state.md` — not a mirror of MAT’s entire documentation or application stack. Detection for tooling is primarily **filesystem-based** (for example `scripts/phase1-verify.sh` treats a present `.mat/README.md` as the adopted sidecar marker; optional env `MAT_REPO_LAYOUT=adopted|source` may be introduced by operators for future tooling but is not required today).

For later MAT refreshes in adopted repos, prefer the `update-mat.py` dry-run → review → optional `--apply` flow; re-running `bootstrap-workflow-into-repo.sh` is a heavier full refresh from the layout manifest. **Dry-run** includes a structured **legacy cleanup preview** (same engine as apply, non-writing) in the plan JSON and stdout; **apply** and **re-bootstrap** run real **legacy migration cleanup** (`scripts/adoption/apply_mat_legacy_cleanup.py` + `mat-legacy-migrations-v1.json`) so obsolete pre-`mat-*` command files are not left beside the current bundle by default. The migration manifest is validated before runs (it must not target footprint preserve/protected paths; fingerprinted entries require `fingerprint_provenance`). Operators can re-check fingerprint unions with `scripts/adoption/mat-legacy-fingerprints.py` (`--verify-all` in `phase1-verify.sh` on source trees) and inspect audits via `apply_mat_legacy_cleanup.py --report` or `bash doctor.sh --legacy-cleanup`. Details: `docs/update-mat/architecture-and-rollout.md`, `docs/getting-started-existing-projects.md`.

---

## Directory Layout

```
.cursor/
  hooks.json              # Cursor hook manifest (11 events)
  hooks/                  # Hook scripts (Python)
    before_submit_prompt.py   # Prompt logging/validation (beforeSubmitPrompt)
    session_start.py          # Session init, env validation (SessionStart)
    session_end.py            # Session completion logging (SessionEnd)
    pre_tool_use.py           # Pre-execution validation (PreToolUse)
    post_tool_validate.py     # Post-tool linting / type-check (PostToolUse)
    send_event.py             # Observability event emitter (PostToolUse, Stop, SubagentStop)
    after_file_edit.py        # Auto-format after edits (afterFileEdit)
    post_tool_use_failure.py  # Tool failure logging (PostToolUseFailure)
    stop_validator.py         # Wired on Stop: Phase 1 permissive checks + TTS (see Validation Policy)
    subagent_start.py         # Subagent spawn logging (SubagentStart)
    pre_compact.py            # Context compaction observer (PreCompact)
    bootstrap_worktree.sh     # Worktree environment bootstrap
    validators/               # Optional utilities — not wired on shipped `stop` (see Validation Policy)
      validate_file_contains.py  # Optional helper: file content checks (use from a custom hooks.json if desired)
      validate_new_file.py       # Optional helper: new-file presence checks (use from a custom hooks.json if desired)
    utils/
      constants.py            # Shared paths and session helpers
      summarizer.py           # LLM-based event summarization
      hitl.py                 # Human-in-the-loop WebSocket requests
      llm/
        anth.py               # Anthropic client (Haiku 4.5)
        oai.py                # OpenAI client (GPT-4.1-nano)
      tts/
        elevenlabs_tts.py     # ElevenLabs Flash v2.5 TTS
        openai_tts.py         # OpenAI gpt-4o-mini-tts
        pyttsx3_tts.py        # Offline TTS (no API key required)

  agents/                 # Cursor subagent definitions
    parent-orchestrator.md    # Task sequencing, retry, result synthesis
    builder.md                # Code implementation with self-validation
    verifier.md               # Read-only validation with evidence
    test-writer.md            # Focused test authoring and regression coverage
    style-reviewer.md         # Documentation/style consistency and claim hygiene
    meta-agent.md             # Agent factory — generates new agent definitions
    scout-report-suggest.md   # Read-only codebase analysis and issue detection
    docs-scraper.md           # Documentation fetching and saving
    create-worktree-subagent.md  # Automated worktree creation
    demo-agent.md             # Self-contained workflow demo

  commands/               # Custom slash commands
    mat-plan-team.md          # Multi-agent orchestrated planning
    mat-long-run.md           # Queued multi-slice missions (long-run contract)
    mat-plan.md               # Solo planning (simpler alternative)
    mat-plan-onboarding.md    # Heavyweight planning package authoring
    mat-build.md              # Builder subagent delegation
    mat-review.md             # Verifier subagent delegation
    mat-prime.md              # Codebase context loader
    mat-question.md           # Read-only Q&A
    mat-git-status.md         # Git state summary
    mat-wt-create.md         # Create isolated worktree
    mat-wt-list.md           # List all worktrees with status
    mat-wt-remove.md         # Remove worktree and cleanup
    mat-wt-check.md          # Check worktree health and collisions
    mat-doctor.md            # Run local setup/runtime diagnostics
    mat-start.md             # Start observability server+client
    output-styles/
      concise.md              # Brief bullet-point output
      detailed.md             # Comprehensive with rationale
      report.md               # Structured report format

  skills/                 # Portable SKILL.md skill definitions
    the-library/              # Meta-skill for private skill distribution
    meta-skill/               # Skill creation guide
    worktree-manager/         # Comprehensive worktree management
    create-worktree/          # Lightweight worktree creation

  worktrees.json          # Parallel agent worktree configuration
  mcp.json                # MCP server definitions

AGENTS.md                 # This file — agent guidance and validation policy
docs/
  README.md              # Documentation index / TOC
  quick-start.md         # First-run setup for operators
  getting-started-new-projects.md      # Integrate workflow into a new repo
  getting-started-existing-projects.md # Safely retrofit an existing repo
  components.md          # Component reference
  configuration.md       # Env vars, hooks, worktrees, MCP config
  data-flow.md           # Prompt → agents → outputs → observability
  events-and-visualization.md # Hook events, payloads, and dashboard views
  agent-teams.md         # Team composition guidelines
  orchestration-workflow.md # Sequencing, retries, synthesis, lifecycle
  technical-stack.md     # Runtime stack overview
  features-demonstrated.md   # Implemented capabilities inventory
  usage-examples-and-cases.md # Concrete usage examples
  what-it-can-do-and-how-it-works.md # Plain-language capabilities and limits
  best-practices.md      # Operator and integrator guidance
  inventory.json          # Asset inventory (Stage 0)
  migration-backlog.md    # Historical migration backlog archive
  orchestration.md        # Orchestration design (Stage 2)
  hooks-mapping.yaml      # Hook translation mapping (Stage 3)
  events.yaml             # Observability event normalization spec (Stage 4)
  artifacts-index.md      # Stage acceptance tracking
  pilot-report.md         # Stage 6 pilot results
  decision-record.md      # Stage 7 optional enhancement decisions

apps/
  server/                 # Bun observability server (reused from disler)
  client/                 # Vue observability client (reused from disler)
```

---

## Slash Commands

Use these custom commands (available as `/command-name` in Cursor):

| Command | Purpose |
|---------|---------|
| `/mat-plan <task>` | Lightweight solo planning — writes one file: `specs/<slug>.md` |
| `/mat-plan-onboarding <task>` | Heavyweight planning-only onboarding — writes the four-file package under `specs/<slug>/` |
| `/mat-plan-team <task>` | Orchestrated multi-agent planning with builder and verifier |
| `/mat-long-run <task>` | Queued multi-slice mission with `docs/long-run-state.md` and post-slice mission gate |
| `/mat-subagents-spawn <task>` | Decompose work and run parallel Task subagents (parent integrates results; see command doc) |
| `/mat-build <task>` | Delegate a build task to the builder subagent |
| `/mat-review` | Run the verifier subagent against recent changes |
| `/mat-prime` | Load codebase context for a new session |
| `/mat-question <question>` | Read-only Q&A about the project |
| `/mat-git-status` | Summarize current git repository state |
| `/mat-sprint <task>` | Execute one bounded slice with DoR, implementation, verification, and review |
| `/mat-lite <task>` | Run a lightweight docs/config/quality pass without the full orchestration flow |
| `/mat-update-mat <task>` | Refresh MAT-owned assets from upstream with a dry-run-first, AGENTS-safe updater |
| `/mat-wt-create <branch>` | Create an isolated worktree (explicit `git worktree`; bootstrap writes `runtime.env` hints) |
| `/mat-wt-list` | List all worktrees with status and configuration |
| `/mat-wt-remove <branch>` | Remove a worktree and clean up |
| `/mat-wt-check` | Run worktree health and collision checks |
| `/mat-doctor` | Run local diagnostics for workflow readiness |
| `/mat-start` | Start the observability server and client |

---

## Agent Roles

### Parent Orchestrator (`parent-orchestrator`)
- Owns task sequencing, retry logic, and result synthesis
- Delegates implementation to the builder subagent
- Delegates validation to the verifier subagent
- Uses files, hooks, and session transcripts as durable handoff points
- Does NOT depend on Claude task-board primitives (TaskCreate, TaskList, SendMessage)

### Builder (`builder`)
- Implements code, writes files, runs tools
- Self-validates via PostToolUse hook (Ruff, Ty, or project linter)
- Reports completion by producing a structured output artifact (e.g., `build-result.md`)

### Verifier (`verifier`)
- Operates in read-only mode where possible
- Checks builder output against acceptance criteria
- Reports pass/fail with evidence in `verify-result.md`
- Never modifies implementation files directly

### Test Writer (`test-writer`)
- Adds or improves focused automated tests for existing behavior
- Prioritizes deterministic regression coverage over broad rewrites
- Reports concrete test command evidence and outcomes

### Style Reviewer (`style-reviewer`)
- Reviews docs/command/agent text for clarity and consistency
- Aligns inventories across `README.md`, `AGENTS.md`, and `docs/components.md`
- Removes overclaims that are not backed by shipped runtime evidence

### Repo-Local Agent Contract Metadata (v1.0.0)

All repo-local agents should document an explicit contract section with:
- `contract_version` (current baseline: `1.0.0`)
- `retry_policy` (bounded retries are parent/orchestrator owned)
- `observability_contract` (telemetry is advisory/fail-open, not gate truth by itself)

### Meta Agent (`meta-agent`)
- Generates new agent definition files from descriptions
- An "agent factory" — creates complete, ready-to-use agent configs
- Writes new agents to `.cursor/agents/`

### Scout (`scout-report-suggest`)
- Read-only codebase analysis agent
- Investigates problems, identifies root causes
- Produces structured SCOUT REPORT with findings and suggested resolutions

### Docs Scraper (`docs-scraper`)
- Fetches documentation from URLs
- Saves as properly formatted markdown to `ai_docs/`

### Worktree Creator (`create-worktree-subagent`)
- Automates git worktree creation via the `/mat-wt-create` command
- Parses branch / worktree labels and runs `bootstrap_worktree.sh` with that name (observability ports come from bootstrap, not a CLI offset)

### Demo Agent (`demo-agent`)
- Self-contained demonstration of the multi-agent workflow
- Shows hooks, validation, and observability integration

### Cursor To-dos orchestration (Phase 2 MVP — shipped)

**MVP slice:** Native To-dos use a strict **MAO** protocol (three tagged tasks: `[mao:plan]`, `[mao:build]`, `[mao:validate]`) documented in [`docs/todo-orchestration-protocol.md`](docs/todo-orchestration-protocol.md), enforced for composer runs via [`.cursor/rules/orchestrator-todos.mdc`](.cursor/rules/orchestrator-todos.mdc), and aligned in [`.cursor/agents/parent-orchestrator.md`](.cursor/agents/parent-orchestrator.md), builder, verifier, and `/mat-plan-team`. Parent prompts may also inject an advisory single-line `MAO_TASK_CONTEXT_JSON:` block for builder/verifier starts; `subagent_start.py` logs it when valid, resolves **`mao_worktree`** from the workspace root (`.cursor/worktree/*` bootstrap markers when present), and accepts an optional parent `mao_worktree.label` inside the JSON for cross-checking. Refreshed `artifacts/mao/gate.json` and `transition-events.jsonl` lines include the same **`mao_worktree`** shape for traceability; missing markers never block hooks. Parent-owned `plan -> build` and `build -> validate` decisions are recorded in gitignored `artifacts/mao/transition-events.jsonl` via `capture_transition_decision()` in [`mao_gate.py`](.cursor/hooks/mao_gate.py), which returns **`todo_mutations`** and embeds them on each JSONL line; when the append succeeds it also overwrites gitignored **`artifacts/mao/suggested-todo-mutation.json`**. That mirrors `parent_owned_todo_mutations_for_transition()` — the exact MAO status mutations the parent may apply when `manual_file_check` applies or when `gate_plus_files` stays aligned with a live `advisory_pending` recompute. The same module exposes `apply_parent_todo_mutations_to_cursor_todos()` and `validate_mao_todo_mutations_against_todos()` for deterministic `TodoWrite merge` from tag-prefix mutations; optional CLI [`scripts/mao-todo-write-merge.py`](scripts/mao-todo-write-merge.py). Hooks do **not** call `TodoWrite`. `evaluate_*_transition()` attaches that explicit `advisory_pending` bundle for orchestration summaries. `artifacts/mao/gate.json` may also describe still-`pending` downstream work as `blocked` or `ready_for_parent_review`, but that advisory metadata never changes the real Cursor todo status on its own. **File handoffs remain authoritative**; if `TodoWrite` is unavailable or task context is missing/malformed, use files only and note the skip in `docs/session-summary.md`. When execution is based on an approved onboarding package, the parent must also keep the matching `TASK-###` entry in `specs/<slug>/tasks.json` synchronized with the active slice so progress stays honest without creating a second runtime system. Optional routing/cost telemetry may also be summarized into `artifacts/mao/routing_rollup_<session_id>.json` and inspected with `scripts/analyze_routing_advisory.py`; prompt lint warnings write `artifacts/mao/prompt_lint_<session_id>.log`; session budget notes may append to `docs/session-summary.md` when `CURSOR_MAT_SESSION_BUDGET_USD` is set and the best-effort estimate exceeds the threshold; all of it stays advisory only.

**Wait-before-supersede discipline:** After the parent spawns the builder or verifier, allow a reasonable startup window before treating silence as a stall. Legitimate startup includes repo reads/searches, environment or setup checks, validation output, transcript growth, and partial artifacts. Distinguish normal startup, active progress, unclear state, and true stall/failure: only the last one justifies overlap or takeover. The parent may do other **non-overlapping** orchestration work while waiting, but must not duplicate the same implementation or review work in parallel. Before intervening, check for progress signals such as subagent updates, changed files, validation output, or partial artifact creation. If status is unclear, **resume the same subagent first** with a narrow status follow-up. If the tree is dirty, inspect it with `scripts/inspect_worktree_attribution.py` before declaring any modified file unexpected. Only re-spawn, replace, or supersede a subagent when there is clear evidence of failure, deadlock, or repeated non-progress after a reasonable wait.

**Pilot:** [`docs/todo-orchestration-pilot.md`](docs/todo-orchestration-pilot.md).

**Hooks:** `PostToolUse` still runs `send_event.py` and `post_tool_validate.py`; when a file-writing tool touches `docs/current-plan.md` or `build-result.md`, `post_tool_validate.py` also refreshes gitignored **`artifacts/mao/gate.json`** via [`mao_gate.py`](.cursor/hooks/mao_gate.py) (`build_may_start`, stricter `validate_may_start`, and `advisory_pending` hints; disable with `CURSOR_MAO_GATE=0`). The parent may consume that file only as a **fresh, valid, internally consistent, positive** advisory signal before the explicit parent-owned transition checks: `plan -> build` (`current-plan` ready) and `build -> validate` (`current-plan` ready, build status PASS/PARTIAL, `Acceptance Criteria` with no FAIL, `Linting / Type-Check` PASS). `ready_for_parent_review` in `advisory_pending` is only a description of a still-`pending` downstream todo, not a replacement for `in_progress`. Those explicit checks can also be durably recorded in gitignored **`artifacts/mao/transition-events.jsonl`** (including the `advisory_pending` bundle), and `parent_owned_todo_mutations_for_transition()` returns the exact helper-driven status updates for any passing parent-owned transition decision on the manual/file path or on `gate_plus_files` when `advisory_pending` from the gate file matches the live recompute; misaligned trusted gate + file snapshots yield **no** helper-driven mutation even if canonical files look ready. File handoffs remain canonical and neither capture path may auto-start the builder or verifier. Todo tools are not file-writers, so `post_tool_validate.py` does not run project lint on todo updates (see protocol doc). **`failClosed` is false** — acceptable blocking risk for this spike.

**PostToolUse MAO todo observation (narrow slice):** After a `TodoWrite` tool completes, [`post_tool_validate.py`](.cursor/hooks/post_tool_validate.py) may append **`artifacts/mao/todo-write-events.jsonl`** and overwrite **`artifacts/mao/last-todo-write-observation.json`** via [`record_mao_todo_write_post_tool_observation()`](.cursor/hooks/mao_gate.py) (parsed MAO tags when unambiguous, `mao_worktree`, **`file_handoff_signals`** from handoff files — advisory only). Hooks still do **not** call `TodoWrite`. Disable with `CURSOR_MAO_TODO_POST_TOOL_USE=0`. Optional `CURSOR_MAO_TODO_POST_TOOL_REFRESH_GATE=1` refreshes `gate.json` when `CURSOR_MAO_GATE` is on.

**MAO downstream readiness snapshot (narrow slice):** After `gate.json` refresh, after a successful todo-write observation, after a successful `capture_transition_decision()` JSONL append (`trigger: transition_capture` or `hook_post_tool_use_auto_capture` for opt-in hook capture), or when handoff files change with `CURSOR_MAO_GATE=0`, [`mao_gate.py`](.cursor/hooks/mao_gate.py) may overwrite gitignored **`artifacts/mao/downstream-readiness.json`** with deterministic per-edge **`unblock_semantic`** (same rules as `parent_owned_todo_mutations_for_transition()`), plus optional **`todo_write_cross_check`** vs `last-todo-write-observation.json`. Advisory only — parent still runs explicit transition checks and applies `TodoWrite`. Disable hook writes with `CURSOR_MAO_DOWNSTREAM_READINESS=0`. **Parent consumption:** [`evaluate_parent_downstream_readiness_advisory()`](.cursor/hooks/mao_gate.py) (or [`scripts/mao-downstream-readiness.py`](scripts/mao-downstream-readiness.py), `--interpret-edges`) returns **`live_snapshot`** always and **`trusted_snapshot_for_hint`** only when the on-disk file’s edges match live; stale/missing/invalid data falls back to live semantics — never a substitute for canonical handoff checks.

**MAO parent transition bundle (2026-03-27):** [`evaluate_mao_parent_transition_bundle()`](.cursor/hooks/mao_gate.py) returns one dict: transition `decision`, `todo_mutations`, `edge_readiness`, [`interpret_unblock_semantic_for_parent()`](.cursor/hooks/mao_gate.py) (all four canonical `unblock_semantic` strings), `orchestration_flow_hint`, and optional embedded full readiness advisory. [`scripts/mao-capture-transition.py`](scripts/mao-capture-transition.py) adds `--bundle-only` and embeds `parent_transition_bundle` on normal capture; `--with-downstream-readiness` nests the advisory inside that bundle; `--show-hook-flags` prints opt-in hook automation env toggles. Still no hook `TodoWrite`, no auto-spawn.

**MAO hook auto-capture + verifier intent (2026-03-27):** Opt-in **`CURSOR_MAO_HOOK_AUTO_TRANSITION_CAPTURE`** runs [`maybe_hook_auto_capture_transition()`](.cursor/hooks/mao_gate.py) from [`post_tool_validate.py`](.cursor/hooks/post_tool_validate.py) after gate refresh on handoff writes; requires **`CURSOR_MAO_GATE` on**, trusted positive fresh gate, non-empty `todo_mutations`, and dedupes JSONL by transition + handoff mtimes. Opt-in **`CURSOR_MAO_VERIFIER_AUTOSTART`** may write gitignored **`verifier-autostart-intent.json`** only after a successful build→validate hook capture plus strict checks; optional **`CURSOR_MAO_VERIFIER_AUTOSTART_REQUIRE_TODO_OBSERVATION`**. Parent still owns verifier spawn and should delete or consume the intent after dispatch. Hooks never call `TodoWrite` or start subagents. **Parent consumption (shipped):** [`evaluate_verifier_autostart_intent()`](.cursor/hooks/mao_gate.py), [`delete_verifier_autostart_intent()`](.cursor/hooks/mao_gate.py), and CLI [`scripts/mao-verifier-autostart-intent.py`](scripts/mao-verifier-autostart-intent.py) (optional `--delete-if-consumable` requires **`CURSOR_MAO_PARENT_CONSUME_VERIFIER_INTENT_OK=1`** exactly).

**MAO observability dashboard slice (2026-03-27):** Vue **MAO visibility** panel lists ingested **`MaoTransition`** events and a **mixed-source observed summary** (`deriveMaoObservedSnapshot`): newest row in the window, optional newest row that still has **`advisory_pending.live`** edge lanes (with a staleness banner when a newer row omits them), and latest-by-name `plan_to_build` / `build_to_validate` markers — not a coherent single snapshot and not a Cursor todo column. Bun `toWire()` uses a larger WebSocket payload preview for **`MaoTransition`** and **`MaoTodoObservation`**. Opt-in **`CURSOR_MAO_EMIT_TRANSITION_OBSERVABILITY`** adds fail-open POST from hook auto-capture’s `capture_transition_decision()`; opt-in **`CURSOR_MAO_EMIT_TODO_OBSERVATION_OBSERVABILITY`** adds fail-open **`MaoTodoObservation`** from todo-write PostToolUse observation — PostToolUse-derived hints only, not live Cursor todos; visibility only; files and parent checks stay canonical ([`docs/todo-orchestration-protocol.md`](docs/todo-orchestration-protocol.md)).

**Next (beyond observation, gate file, advisory task context, worktree metadata, capture-time mutation surfacing, parent merge helpers, downstream readiness snapshot, parent bundle, capture-time readiness refresh, opt-in hook capture, verifier intent file, and parent intent evaluation/CLI):** a live dashboard todo column and hook-driven **subagent auto-spawn from live todo state** remain blocked — see [`docs/decision-record.md`](docs/decision-record.md) and [`ROADMAP.md`](ROADMAP.md). Advisory hook-written autostart intents do not imply live authoritative MAO todo parity.

---

## Validation Policy

Every agent run should produce:
1. A structured output artifact (`*-result.md` or equivalent)
2. A pass/fail gate result recorded in `docs/artifacts-index.md`
3. Hook-emitted events visible in the observability dashboard (when running)

### Wired `stop` behavior vs `validators/` utilities

- **Shipped `stop` (`.cursor/hooks.json`):** only `send_event.py` then `stop_validator.py`, with `failClosed` false. Nothing else runs on `stop` in the repo-default manifest.
- **`stop_validator.py` (Phase 1, permissive):** for orchestration-style sessions it may **warn** on stderr when `docs/current-plan.md` exists but expected handoff artifacts are incomplete; when no hard-failure path applies, `missing` stays empty and the process exits **0** (warnings are advisory, not a repo-default hard block from that script today).
- **`.cursor/hooks/validators/*.py`:** optional helper scripts. They are **not** additional commands on the shipped `stop` array. Operators may reference them from a **custom** `hooks.json` or other automation; do not treat them as independently wired stop enforcement in this repository.

### Stop Conditions
An agent MUST stop and report failure if:
- A binary acceptance gate fails
- A critical dependency is unavailable (e.g., missing env var, failed tool)
- The `loop_limit` for a hook is reached without resolution

---

## Hook Behavior

Hooks are defined in `.cursor/hooks.json`. Full event coverage:

| Event | Purpose | Script(s) |
|-------|---------|-----------|
| `beforeSubmitPrompt` | Prompt logging/validation | `before_submit_prompt.py` |
| `sessionStart` | Environment validation, session init event | `session_start.py` |
| `sessionEnd` | Session completion logging, statistics | `session_end.py` |
| `preToolUse` | Optional tool blocking, pre-execution logging | `pre_tool_use.py` |
| `postToolUse` | Linting, type-check, observability event | `send_event.py`, `post_tool_validate.py` |
| `afterFileEdit` | Auto-format after file edits | `after_file_edit.py` |
| `postToolUseFailure` | Tool failure logging for debugging | `post_tool_use_failure.py` |
| `stop` | Stop-loop self-validation, TTS notification | `send_event.py`, `stop_validator.py` |
| `subagentStart` | Subagent lifecycle logging | `subagent_start.py` |
| `subagentStop` | Subagent lifecycle event | `send_event.py` |
| `preCompact` | Context compaction observer, transcript backup | `pre_compact.py` |

**Notes:**
- `preToolUse`: `pre_tool_use.py` resolves `tool_name` vs `tool` via `resolve_tool_name()` (unit-tested in `tests/test_phase1_hooks.py`); default blocking list is empty (`failClosed` is false in `hooks.json`).
- `loop_limit` is set per hook in `hooks.json`. Do not bypass hook failures
  by force-exiting — report the failure and let the parent agent decide on retry.
- Claude's `Notification` hook is replaced by `Stop` + `SubagentStop` hooks with
  macOS desktop notifications in `stop_validator.py`.
- Claude's `PermissionRequest` hook has no direct Cursor equivalent — permission
  handling is built into Cursor's agent runtime.

---

## Utilities

### LLM Clients
- `utils/llm/anth.py` — Anthropic Haiku 4.5 for fast completions and agent naming
- `utils/llm/oai.py` — OpenAI GPT-4.1-nano for fast completions
- Used by hooks for generating event summaries and completion messages

### TTS System
- Priority order: ElevenLabs > OpenAI > pyttsx3 (offline fallback)
- Controlled by `--notify` flags on `stop_validator.py` and `session_end.py`
- Requires `ELEVENLABS_API_KEY` or `OPENAI_API_KEY` for cloud TTS

### Human-in-the-Loop (HITL)
- WebSocket-based interactive decision system via `utils/hitl.py`
- Sends questions/choices to the observability dashboard for human response
- Used for permission prompts, choices, and interactive agent decisions

### Event Summarization
- `utils/summarizer.py` uses the Anthropic client to generate one-sentence event summaries
- Enriches observability events with human-readable descriptions

---

## Worktree Usage

When running parallel agents in **separate directories**, treat worktrees as **explicit** git isolation (Cursor 3: use `/worktree`, `/best-of-n`, or manual `git worktree add` — the editor does not silently create a new git worktree per parallel agent). After a worktree exists, **bootstrap** (`.cursor/hooks/bootstrap_worktree.sh`) may run via `.cursor/worktrees.json` setup keys or manually; it copies `.env` when missing, installs deps, and writes `.cursor/worktree/runtime.env` with collision-aware `OBSERVABILITY_PORT` / `OBSERVABILITY_CLIENT_PORT` hints (`3001`/`5173` bases + `cksum(name) mod 200`, then `pick_free_port`).

Typical MAT posture: builder and verifier **can** operate in separate worktrees when you create them; that is orchestration and operator choice, not an automatic Cursor guarantee.

**LSP caveat:** Worktrees may not have full LSP support (linting/type feedback). Run
explicit linting via hook scripts (`post_tool_validate.py`) rather than relying on
editor-integrated feedback inside the worktree.

### Worktree Management Commands
- `/mat-wt-create <branch>` — create/configure an isolated worktree; see command doc for bootstrap + `runtime.env`
- `/mat-wt-list` — view worktrees; prefer `.cursor/worktree/runtime.env` per tree for observability port hints
- `/mat-wt-remove <branch>` — stop services, remove worktree and branch
- `/mat-wt-check` — check local worktree health and collisions
- `/mat-doctor` — run repo diagnostics (`scripts/doctor.sh`)

---

## Observability

The observability stack (Bun server + SQLite + Vue dashboard) receives events via
`.cursor/hooks/send_event.py` on every `PostToolUse`, `Stop`, and `SubagentStop` event.

To start the API and dashboard together (recommended):
```bash
bash scripts/start-system.sh
```

Or start them separately after `bun install` in each app:

```bash
cd apps/server && bun run dev
# other terminal:
cd apps/client && bun run dev
```

Or use the `/mat-start` command, which runs `bash scripts/start-system.sh`.

Events are normalized via the adapter in `apps/server/src/adapter.ts` before
persisting to SQLite.

## Documentation Map

Use `docs/README.md` as the primary documentation entrypoint.

Recommended reading order:
1. `README.md`
2. `docs/quick-start.md`
3. `docs/what-it-can-do-and-how-it-works.md`
4. `docs/configuration.md`
5. `docs/agent-teams.md` and `docs/orchestration-workflow.md`
6. `docs/usage-examples-and-cases.md`

---

## Project-first capability routing

MAT expects **project-local** `.cursor/` assets and root `AGENTS.md` to take **precedence** over global and plugin defaults for **repo-specific** workflow behavior, while MAT orchestration stays **additive** and file-handoff-centric. See [`docs/capability-precedence.md`](docs/capability-precedence.md) for the full precedence stack, discovery conventions, conflict rule, and what remains **authoritative** (`docs/current-plan.md`, `build-result.md`, `verify-result.md`) versus **advisory** (hooks, gates, routing hints).

In downstream repos, keep root and nested `AGENTS.md` files product-owned. Put the MAT encyclopedia in `.mat/AGENTS.mat.md`, and add only a short pointer note in each `AGENTS.md` by default; reserve the inline MAT section for an explicit exception.

For MAT's conservative model-tier policy, see [`docs/model-routing-policy.md`](docs/model-routing-policy.md); keep that policy docs-first, adapter-agnostic, and separate from any future `agent-model-router` boundary.

For **bounded context** and artifact-first loading (avoid habitual mega-docs and transcript replay), see [`docs/context-budget-policy.md`](docs/context-budget-policy.md).

## Cost & context hygiene (enforced pack)

This repository ships a **default low-token posture**: always-on [`.cursor/rules/cost-context-hygiene.mdc`](.cursor/rules/cost-context-hygiene.mdc), root [`.cursorignore`](.cursorignore) aligned with the MAT template set under [`docs/templates/`](docs/templates/) (see `cursorignore-mat-default` and stack variants: `node`, `python`, `wordpress`, `rails`), and CI checks in [`scripts/validate_cost_context_hygiene_pack.py`](scripts/validate_cost_context_hygiene_pack.py) (invoked from `scripts/phase1-verify.sh` with `--enforce auto` — for this source repo, **strict** in practice). The rule includes the honest UI boundary: MAT **cannot block** `@Codebase` or other broad Cursor context controls in the product — strictness is rules, CI, and operator discipline.

`python3 scripts/validate_cost_context_hygiene_pack.py --report --no-fail` and `bash scripts/doctor.sh --cost-hygiene` are non-fatal diagnostic paths. Adopted **existing-project** runs record `warn_first` in `.mat/cost-hygiene-adoption.json` and never overwrite an existing product `.cursorignore`; when root `.cursorignore` is absent, bootstrap installs the MAT template (same as new-project). Optional **`CURSOR_MAT_COST_HYGIENE_ENFORCE`** in CI can force `strict` until ignore fragments are merged. Local JSON under `artifacts/cost-hygiene/` is **advisory only** (not billing, not a token account).

**Optional submit-time guardrails:** See [`docs/MAINTAINER.md`](docs/MAINTAINER.md#submit-time-prompt-validation-opt-in) for `CURSOR_VALIDATE_PROMPTS`, how [`before_submit_prompt.py`](.cursor/hooks/before_submit_prompt.py) evaluates blocked patterns, the empty in-repo default list, and false-positive risk.

---

## Maintaining the roadmap

The canonical product and engineering roadmap is **[`ROADMAP.md`](ROADMAP.md)** at the repository root (repo: [Devora-AS/multi-agent-workflow](https://github.com/Devora-AS/multi-agent-workflow)). Keep it **current during development** so operators and agents share one source of truth.

### When to update

- **Starting** work that matches a roadmap theme (or adding a new theme): place or adjust the item under **Now**, **Next**, or **Later**; use the legend tags ([Done], [Planned], [Deferred], [Idea]).
- **Shipping** a feature that corresponds to a roadmap checkbox: mark the box **`[x]`** in the same PR (or immediately after merge), and bump the **Last updated** date at the top of `ROADMAP.md`.
- **Closing out** shipped or guidance-visible work: keep `README.md`, `AGENTS.md`, `CHANGELOG.md`, `ROADMAP.md`, and related docs synchronized whenever the slice changes shipped behavior or operator guidance.
- **Deferring or dropping** scope: move the item to **Later**, tag **[Deferred]** or **[Idea]**, and add a one-line rationale so history is clear.
- **Borrowing-pattern detail** (full matrices): add or edit rows in the **Appendix** of `ROADMAP.md`; keep section bullets short and milestone-focused—one canonical checkbox per deliverable.

### GitHub Issues (optional, recommended when the team adopts them)

- **Tracking:** You may link a roadmap checkbox to an issue for clearer “done” semantics, e.g. `- [ ] Ship feature X ([#42](https://github.com/Devora-AS/multi-agent-workflow/issues/42))`.
- **Workflow:** Prefer **create the issue first**, then add the link next to the checkbox (or create the issue from the PR and back-link). Close the issue when the checkbox is marked done.
- **Avoid duplication:** Do not maintain the same work as both an unlinked vague bullet and a separate issue with no cross-reference—pick one canonical line in `ROADMAP.md` and link out.
- **Not required:** The roadmap can use checkboxes alone until you choose to enable issue tracking.

### What stays outside the roadmap

- **Staged migration / gate artifacts** — still recorded in [`docs/artifacts-index.md`](docs/artifacts-index.md) (branch, SHA, reviewer, acceptance).
- **Optional enhancement go/no-go** — still governed by [`docs/decision-record.md`](docs/decision-record.md).
- **Deep specs** — link from `ROADMAP.md` into `docs/` instead of pasting long prose into the roadmap file.

### Agent and contributor checklist

- [ ] Roadmap **Vision / Current Focus / Near-Term / Recently Completed / Future Concepts / Icebox / Blocked** reflects the change you are making (or you added a new item explicitly).
- [ ] **Last updated** in `ROADMAP.md` changed when the file changed.
- [ ] `README.md`, `AGENTS.md`, `CHANGELOG.md`, `ROADMAP.md`, and related docs were refreshed when the slice changed shipped behavior or operator guidance.
- [ ] Linked **GitHub issue** (if any) matches the checkbox and is referenced from the PR description.
- [ ] [`docs/artifacts-index.md`](docs/artifacts-index.md) updated when a **staged artifact** or gate result is part of the work.

### Inventory hygiene (rules and skills)

When you add or materially change a **repo-local** surface under `.cursor/rules/` or `.cursor/skills/`:

- Add or update a discoverability row in **this file** (slash commands table, skills list, or hooks section as appropriate).
- Refresh [`docs/components.md`](docs/components.md) and [`README.md`](README.md) when operators need to find the surface without reading the whole tree.
- If the surface changes adoption or verification behavior, also update [`docs/MAINTAINER.md`](docs/MAINTAINER.md) and [`CHANGELOG.md`](CHANGELOG.md).
- Do not rely on plugin-only or global defaults as the only documentation for MAT-shipped operator workflows.

---

## Cloud Agents

For stronger isolation than local worktrees (no filesystem conflicts, fresh VM):

- Use the **Agents Window** (Cursor 3 agent-first surface) and choose **cloud**, **SSH**, or **multi-workspace** as needed — not editor Settings as the sole setup path.
- Configure cloud agents with [`.cursor/environment.json`](.cursor/environment.json) (`install` / `start` lifecycle) or web onboarding; see [cursor.com/docs/cloud-agent](https://cursor.com/docs/cloud-agent) and [cursor.com/docs/agent/agents-window](https://cursor.com/docs/agent/agents-window).
- Cloud agents run in isolated VMs with computer-use capabilities when enabled.
- They read MCP integrations from `.cursor/mcp.json` and guidance from root `AGENTS.md`.
- Prefer cloud agents for long-running or resource-intensive subagent tasks.
- **MAT does not auto-provision cloud agents** — operators configure cloud via the Agents Window and environment file; file handoffs (`docs/current-plan.md`, `build-result.md`, `verify-result.md`) stay authoritative. See [`docs/decision-record.md`](docs/decision-record.md#p1-audit--cloud-agents-agents-window).

---

## Environment Variables

Copy `.env.sample` to `.env` and fill in required values before running agents:

```bash
cp .env.sample .env
```

Required variables are documented in `.env.sample`.

### Bun on `PATH`

The official installer places the binary at `~/.bun/bin/bun`. Interactive shells pick that up from `~/.zshrc`, but **Cursor agent terminals and non-interactive automation often do not**. This repository:

- Sources `scripts/lib/ensure-bun-path.sh` from `scripts/start-system.sh` and `scripts/phase1-verify.sh` so `bun` is discoverable when it exists under `~/.bun/bin` or `BUN_INSTALL`.
- Ships **`.vscode/settings.json`** workspace defaults so the **integrated terminal** prepends `~/.bun/bin` (macOS/Linux) or `%USERPROFILE%\.bun\bin` (Windows) to `PATH`.

Prefer `bash scripts/start-system.sh` from the repository root to start the observability server in any environment.

---

## Learned User Preferences

- For multi-agent orchestration and related roadmap work, treat **Cursor To-dos** plus **Cursor Hooks (v1.7+)** as the intended shared state and handoff mechanism; do not reference or recommend Taskmaster AI in documentation, plans, or suggestions.
- For new projects or substantive new features, start with clarifying questions and PRD-style requirements and planning (for example `/mat-plan` for lightweight work or `/mat-plan-onboarding` for heavier discovery/traceability) before implementation; use explicit planning or deeper reasoning when scope is ambiguous rather than jumping straight to code.
- When scope is unclear or the answer lives on disk (capture folders, lifecycle JSON, large repo dumps), confirm enumeration scope first or read those paths directly instead of asking the user to restate what is already there.
- When adopting or refreshing MAT in **external product repos**, prefer `update-mat.py` dry-run → review → optional `--apply`, keep product-owned `AGENTS.md` intact via the sidecar, and document **opt-in** observability plus manual SQLite rotation in the product repo — do not enable upstream auto-retention/redaction defaults from the MAT source tree.
- For README and other repo documentation, reference images and assets with paths relative to the repository root (and check assets into the repo) instead of machine-local absolute paths (for example under `.cursor/projects/...`).
- For roadmap, closeout, and strategy docs, keep framing aligned to this repository's internal/reference-oriented team use; avoid public-release, packaging, or publication language unless explicitly requested.
- Do not create GitHub Issues for roadmap items unless the user explicitly asks; they may want to review the roadmap and attach issue links themselves before any backlog is created.
- Do not `git push` to remotes unless the user explicitly asks; closeout and slice handoffs should end with a local commit and a confirmed working tree state.
- For explicit **multi-slice** missions (several roadmap slices in one session), prefer **`/mat-long-run`** with [`docs/long-run-state.md`](docs/long-run-state.md) and the parent **post-slice mission gate**; continue with the next slice after each verified slice unless blocked or a classified stop reason applies. Do not end the run after the first slice when the user defined that multi-slice mission. `/mat-plan-team` alone is one orchestration cycle unless paired with the long-run contract.
- For implementation slices that depend on an approved planning or spec package, materialize that package as tracked repository files first and treat those files as the canonical source of truth for the rest of the slice.
- Treat continual-learning `AGENTS.md` edits as intentional memory maintenance when the audit/state trail points to that flow; prefer a fresh maintenance session when safe, otherwise queue updates; keep learned bullets bounded (see [`docs/continual-learning-safe-handling.md`](docs/continual-learning-safe-handling.md)).
- For MAT audit and RFU remediation slices, prefer **`/mat-plan-team`** with **builder_plus_verifier** Task delegation (not inline-only parent implementation); include CI hardening in the same slice when touching `apps/client` rather than deferring.

---

## Durable Repo Facts

- MAT audit remediation is **complete** on `main` (2026-06-23): P0 contract hardening, Phase A (P2), Phase B (P1), Phase C RFU C1–C5 (**RFU-7** code deferred), MAT updater slices 1–3 plus `scripts/demo/updater-operator-walkthrough.sh`; see `artifacts/report/mat-audit-report.md` and `docs/decision-record.md`.
- RFU-7 observability retention/redaction **code** is **deferred** (2026-06-23) per `docs/decision-record.md#phase-c-rfu-7--observability-retention-and-hook-redaction-deferred`: localhost-only dashboard posture, manual `events.sqlite` rotation, no shipped auto-TTL or default-on hook redaction in the MAT source repo; adopted repos need opt-in observability guidance, not upstream auto-purge defaults.
- `docs/adoption-observability-appendix.md` packages to `.mat/docs/` via `scripts/adoption/adoption-layout-v1.json`; disposable pilot PASS at `artifacts/report/adoption-observability-pilot-2026-06-23.md` with operator-doc cross-links and `MatAdoptionObservabilityAppendixTest`.
- Hook capture hygiene: `payload_capture.py` must stay tracked; if `ruff` is missing or times out, `post_tool_validate.py` skips Python lint with `lint_ok` true (align `build-result.md` reporting); `get_changed_files()` supports alternate write-tool payload shapes; `subagent_start.repo_root_from_hook_payload()` matches `post_tool_validate.PROJECT_DIR`.
- `artifacts/mat-runtime/` holds the local MAT runtime SQLite store and stays ignored; `scripts/mat-runtime.py` is the supported inspection entrypoint; `apps/server/src/runtime-review.ts` and `apps/client/src/components/RuntimeReviewPanel.vue` expose an advisory review surface subordinate to tracked handoff files.
- `bash scripts/start-system.sh` picks free TCP ports when defaults are in use; `bash scripts/phase1-verify.sh` runs server Bun smoke plus `apps/client` `bun install --frozen-lockfile`, type-check, `test:vitest`, and build (`PHASE1_VERIFY_SKIP_CLIENT=1` skips client; GitHub Actions pins Node 22 and uses `fetch-depth: 0` for legacy fingerprint checks).
- Shared docs contract tests (`tests/test_workflow_docs.py`, `tests/test_phase2_blocked_closeout_docs.py`, `tests/test_migration_backlog_docs.py`) assert required substrings across `README.md`, `ROADMAP.md`, `AGENTS.md`, and `docs/README.md`; substantive doc rewrites should update those tests and pass `bash scripts/phase1-verify.sh`.
- For MAO build→validate preflight, `build-result.md` `## Acceptance Criteria` rows must be bullet lines that include an explicit `: PASS`, `: PARTIAL`, or `: FAIL` substring; unresolved checklist-only rows may not count as resolved criteria.
- Keep `docs/templates/spec-template.md`, `docs/templates/prd-template.md`, and `docs/templates/tasks-schema.json` aligned on traceability identifiers (for example stable `SPEC-###` references) so machine-readable `tasks.json` can link to spec sections without ambiguity.
- `/mat-plan-onboarding` must surface unresolved questions from `specs/<slug>/prd.md`, `specs/<slug>/spec.md`, and `specs/<slug>/plan-summary.md` in chat one at a time before approval, while keeping the artifacts canonical and updating question status after each answer or deferment.
- `docs/capability-precedence.md` defines MAT's project-first routing policy only; keep it explicit that Cursor's actual Agent rules precedence is `Team Rules -> Project Rules -> User Rules`, while MAT guidance is advisory for IDE/runtime behavior and canonical handoff files remain authoritative.
- Orchestration honesty: optional routing/cost telemetry may append to `artifacts/mao/routing-advisory.jsonl` (advisory only); when `/mat-plan-team` runs inline, closeout must say so and not imply builder/verifier proof without trace evidence; default parent prompts to copy-pasteable fenced `txt` blocks; use [`docs/orchestration-workflow.md#execution-closeout-contract`](docs/orchestration-workflow.md#execution-closeout-contract) for closeout.

## Workspace-Local Operational Facts

- Hook payload capture honors `CURSOR_HOOK_CAPTURE_DIR`: non-absolute paths resolve from the repository root, while leading `/` paths are filesystem-absolute. Use at most one `CURSOR_HOOK_CAPTURE_DIR` assignment in `.env`; duplicate keys are invalid.
- For lifecycle hook verification, compare `conversation_id` across `sessionStart.json`, `stop.json`, `preCompact.json`, and `sessionEnd.json` inside the same capture folder (usually the per-session subdirectory when `CURSOR_HOOK_CAPTURE_PER_SESSION=1`).
- Composer transcript JSONL is often chat-only, and observability `hook_events` may omit todo-tool rows in some Cursor builds; do not rely on those sources alone to prove MAO todo order when higher-fidelity local capture exists.
- When confirming a clean working tree from automation, prefer `git status --porcelain` or raw subprocess capture; some wrappers collapse empty `git status --short` output to the literal string `ok`.
- In `tests/test_phase1_hooks.py`, assertions involving `workspace_roots` should clear `CURSOR_PROJECT_DIR` and `CLAUDE_PROJECT_DIR` and compare canonicalized real paths so macOS `/tmp` versus `/private/tmp` symlink behavior does not create flaky failures.
- `docs/session-summary.md` and per-run trace trees under `artifacts/agent-traces/<run-id>/` are local by default; workspace search or glob can miss gitignored paths, so read the known path directly when validating local evidence.

## Dated Evidence References

- `docs/todo-orchestration-pilot.md` is the dated pilot checklist for the MAO todo workflow.
- `docs/pilot-report.md` is the dated Stage 6 pilot report and evidence template.
- `docs/todo-orchestration-runtime-evidence.md` records dated runtime-proof expectations and audit notes for todo evidence.
- `docs/mao-advisory-go-criteria.md` and `docs/phase4-roadmap-reassessment-checklist.md` are operator-owned reassessment references for blocked MAO/runtime claims.

---

## Migration Notes (for contributors)

- All Claude-specific paths (`.claude/`) have been migrated to `.cursor/`
- `CLAUDE.md` → `AGENTS.md` (this file)
- `.claude/settings.json` → `.cursor/hooks.json`
- `.claude/agents/` → `.cursor/agents/`
- `.claude/commands/` → `.cursor/commands/`
- `.claude/skills/` → `.cursor/skills/`
- `.claude/hooks/` → `.cursor/hooks/`
- `.mcp.json` → `.cursor/mcp.json`

Claude agent frontmatter has been replaced with Cursor-native agent conventions.
Claude team/task-board primitives (TaskCreate, TaskList, SendMessage) are replaced
by parent-agent orchestration using files and hooks as handoff points.
