# Components Reference

- Purpose: Reference the major components in the Cursor-native multi-agent workflow and show how they fit together.
- Audience: Operators, maintainers, and contributors who need a file-level map of the system.
- Prerequisites: Familiarity with Cursor agents, hooks, and slash commands.
- Status: complete
- Last updated: 2026-04-20
- Author: Cursor agent (GPT-5.4)
- Repo posture: internal/reference-oriented for the maintainer team; not a public packaging target by default.

## Related Files

- [Agent instructions](../AGENTS.md)
- [Hook manifest](../.cursor/hooks.json)
- [Configuration](configuration.md)
- [Agent teams](agent-teams.md)
- [Orchestration workflow](orchestration-workflow.md)
- [Inventory](inventory.json)
- [Artifacts index](artifacts-index.md)
- [Capability precedence](capability-precedence.md) — project-local vs `.mat/`, plugin, and global capabilities
- [Model routing policy](model-routing-policy.md) — conservative `cheap` / `standard` / `strong` MAT routing guidance
- [Routing advisory surface](routing_advisory.md) — advisory record shape and safe surfacing rules
- [Context budget policy](context-budget-policy.md) — bounded context and artifact-first loading

## Component Map

| Component | Purpose | Key paths |
|-----------|---------|-----------|
| Observability client (Vue) | Live hook timeline, pulse chart, transcript, MAO visibility, runtime review, Help modal | `apps/client/src/` (see `App.vue`, `EventCard.vue`, `HelpModal.vue`, `components/RuntimeReviewPanel.vue`) |
| Planning commands | Lightweight solo planning and heavyweight onboarding package authoring | `.cursor/commands/mat-plan.md`, `.cursor/commands/mat-plan-onboarding.md`, `docs/planning-commands-guide.md` |
| Parent Orchestrator | Decompose, delegate, retry, synthesize | `.cursor/agents/parent-orchestrator.md`, `.cursor/commands/mat-plan-team.md`, `.cursor/commands/mat-long-run.md`, `.cursor/commands/mat-subagents-spawn.md` |
| Builder | Implement and self-validate | `.cursor/agents/builder.md`, `.cursor/commands/mat-build.md` |
| Verifier | Read-only acceptance checking | `.cursor/agents/verifier.md`, `.cursor/commands/mat-review.md` |
| Test Writer | Focused regression test authoring | `.cursor/agents/test-writer.md` |
| Style Reviewer | Docs/style consistency and claim hygiene | `.cursor/agents/style-reviewer.md` |
| Meta Agent | Generate new agent definitions | `.cursor/agents/meta-agent.md` |
| Scout | Read-only investigation and issue detection | `.cursor/agents/scout-report-suggest.md` |
| Docs Scraper | Fetch docs into markdown | `.cursor/agents/docs-scraper.md` |
| Worktree Creator | Automate isolated worktree setup | `.cursor/agents/create-worktree-subagent.md`, `.cursor/commands/mat-wt-create.md` |
| Demo Agent | Demonstrate end-to-end behavior | `.cursor/agents/demo-agent.md` |
| Hooks | Lifecycle automation and observability | `.cursor/hooks.json`, `.cursor/hooks/` |
| Cursor rules | Composer constraints (e.g. MAO todos) | `.cursor/rules/orchestrator-todos.mdc` |
| MAT runtime messaging | Repo-local typed event, subscription-policy, outbox/inbox, delivery-attempt, worker/retry/DLQ control plane plus the operator-facing runtime review panel and review API | `.cursor/hooks/utils/runtime_messaging.py`, `scripts/mat-runtime.py`, `apps/server/src/runtime-review.ts`, `apps/client/src/composables/useRuntimeReview.ts`, `apps/client/src/components/RuntimeReviewPanel.vue`, `docs/runtime-messaging.md` |
| Capability policy | Project-first routing doc (not a runtime loader) | `docs/capability-precedence.md` |
| Routing policy | Conservative model tiers and advisory budget notes | `docs/model-routing-policy.md` |
| Routing advisory surface | Advisory-only record shape, session rollups, and safe surfacing | `docs/routing_advisory.md` |
| Context budget policy | Bounded context per role; avoid habitual mega-doc loads | `docs/context-budget-policy.md` |
| Skills | Reusable operator guidance | `.cursor/skills/` |
| Utilities | LLM, HITL, TTS, routing advisories, rollups, summaries, validators | `.cursor/hooks/utils/`, `.cursor/hooks/validators/` |

## Planning Commands

- Purpose: Capture planning truth before any execution handoff.
- Responsibilities: Keep `/mat-plan` lightweight and single-file; keep `/mat-plan-onboarding` heavyweight, traceable, and approval-gated.
- Inputs: User task, relevant repo context, existing `specs/` artifacts when present.
- Outputs: `specs/<slug>.md` for `/mat-plan`, or `specs/<slug>/prd.md`, `specs/<slug>/spec.md`, `specs/<slug>/tasks.json`, and `specs/<slug>/plan-summary.md` for `/mat-plan-onboarding`.
- Relevant paths: `../.cursor/commands/mat-plan.md`, `../.cursor/commands/mat-plan-onboarding.md`, `../docs/planning-commands-guide.md`.
- Example invocations:

```text
/mat-plan Improve the onboarding checklist copy
/mat-plan-onboarding Design a new planning workflow with traceable tasks
```

Planning truth stays in `specs/`. `docs/current-plan.md` remains execution truth for downstream builder/verifier flows.

## Agents

### Parent Orchestrator

- Purpose: Replaces Claude's team lead pattern with file-based coordination.
- Responsibilities: Write `docs/current-plan.md`, spawn builder and verifier, evaluate retries, write final synthesis; when execution comes from an approved onboarding package, keep the matching `tasks.json` status in sync with the active slice; for long-run missions, maintain `docs/long-run-state.md` and run the post-slice mission gate after each verifier PASS.
- Inputs: User task, `docs/current-plan.md`, `build-result.md`, `verify-result.md`.
- Outputs: `docs/current-plan.md`, `docs/session-summary.md`, final user summary; optional `docs/long-run-state.md` for multi-slice missions; optional `specs/<slug>/tasks.json` status updates when onboarding packages are active.
- Config options: Retry limits are encoded in the prompt and influenced by `loop_limit` in `../.cursor/hooks.json`.
- Relevant paths: `../.cursor/agents/parent-orchestrator.md`, `../.cursor/commands/mat-plan-team.md`, `../.cursor/commands/mat-long-run.md`, `../.cursor/commands/mat-subagents-spawn.md`, `../docs/mat-plan-team-spec.md`, `../.cursor/orchestration-capabilities.json`, `../artifacts/agent-traces/README.md`.
- Example invocation:

```text
/mat-plan-team Implement a small feature and verify it
```

- Multi-slice missions:

```text
/mat-long-run Execute roadmap slices 1–3 with explicit queue in docs/long-run-state.md
```

- Related lightweight command variants: `../.cursor/commands/mat-sprint.md`, `../.cursor/commands/mat-lite.md`, `../.cursor/commands/mat-doctor.md`.

### Builder

- Purpose: Performs implementation work.
- Responsibilities: Make changes, run validation, write `build-result.md`.
- Inputs: `docs/current-plan.md`.
- Outputs: `build-result.md`.
- Config options: Uses project lint/type-check commands; receives feedback through `postToolUse` and `afterFileEdit`.
- Relevant paths: `../.cursor/agents/builder.md`, `../.cursor/commands/mat-build.md`.
- Example invocation:

```text
/mat-build Add a helper function and document the result
```

### Verifier

- Purpose: Validate builder output without changing implementation files.
- Responsibilities: Inspect handoff files and changed files, then write `verify-result.md`.
- Inputs: `docs/current-plan.md`, `build-result.md`.
- Outputs: `verify-result.md`.
- Config options: Read-only workflow; evidence requirements are defined in the verifier prompt.
- Relevant paths: `../.cursor/agents/verifier.md`, `../.cursor/commands/mat-review.md`.
- Example invocation:

```text
/mat-review
```

### Test Writer

- Purpose: Add focused test coverage without expanding feature scope.
- Responsibilities: Identify coverage gaps, add deterministic tests, run targeted test commands.
- Inputs: Existing module behavior and test suite context.
- Outputs: Updated test files and command evidence.
- Relevant paths: `../.cursor/agents/test-writer.md`.

### Style Reviewer

- Purpose: Keep docs and workflow guidance concise, aligned, and truthful.
- Responsibilities: Normalize inventories and remove unsupported runtime claims.
- Inputs: `README.md`, `AGENTS.md`, `docs/`, and `.cursor/commands/`.
- Outputs: Focused copy/style updates with consistency checks.
- Relevant paths: `../.cursor/agents/style-reviewer.md`.

### Meta Agent

- Purpose: Agent factory for new `.cursor/agents/*.md` definitions.
- Responsibilities: Infer name, read-only mode, workflow, output format, and notes for a new agent file.
- Inputs: User description of a desired agent.
- Outputs: A new agent definition file under `.cursor/agents/`.
- Config options: Conventions come from existing agent files and `AGENTS.md`.
- Relevant paths: `../.cursor/agents/meta-agent.md`.
- Example invocation:

```text
Use the meta-agent to create a deployment-checker subagent
```

### Scout, Docs Scraper, Worktree Creator, Demo Agent

| Component | Inputs | Outputs | Example |
|-----------|--------|---------|---------|
| Scout | Problem statement, file references | SCOUT REPORT text | "Investigate why validation is skipped" |
| Docs Scraper | One or more URLs | Markdown files under `ai_docs/` | "Fetch Bun docs to local markdown" |
| Worktree Creator | Branch / worktree label | New git worktree, bootstrap, `runtime.env` hints | `/mat-wt-create feature-x` |
| Demo Agent | Simple task prompt | `demo-output/hello.md` and demo report | "Run the demo agent" |

## Hooks

The project wires 11 events in [`../.cursor/hooks.json`](../.cursor/hooks.json):

| Event | Primary job | Main script(s) |
|-------|-------------|----------------|
| `beforeSubmitPrompt` | Prompt logging and validation | `before_submit_prompt.py` |
| `sessionStart` | Session initialization | `session_start.py` |
| `sessionEnd` | Session statistics and end logging | `session_end.py` |
| `preToolUse` | Pre-execution checks | `pre_tool_use.py` |
| `postToolUse` | Event emission and validation | `send_event.py`, `post_tool_validate.py` (also refreshes `mao_gate.py` → `artifacts/mao/gate.json` when `build-result.md` is written) |
| `postToolUseFailure` | Error logging | `post_tool_use_failure.py` |
| `afterFileEdit` | Post-edit formatting | `after_file_edit.py` |
| `subagentStart` | Subagent lifecycle logging | `subagent_start.py` |
| `subagentStop` | Subagent lifecycle event emission | `send_event.py` |
| `stop` | Observability emit + wired `stop_validator.py` (Phase 1 permissive: advisory stderr warnings for incomplete orchestration handoffs when applicable; repo-default `failClosed` false) | `send_event.py`, `stop_validator.py` |
| `preCompact` | Compaction logging and backups | `pre_compact.py` |

## Skills

Routing posture (commands vs skills, hybrid worktree cluster): [P1 Audit — Skills vs Commands Routing](decision-record.md#p1-audit--skills-vs-commands-routing).

Cloud / Agents Window posture (Cursor 3 language, no MAT auto-provision): [P1 Audit — Cloud Agents and Agents Window](decision-record.md#p1-audit--cloud-agents-agents-window); setup detail in [`worktree-decision-matrix.md`](worktree-decision-matrix.md).

| Skill | Purpose | Path | Example use |
|-------|---------|------|-------------|
| `the-library` | Private-first skill distribution | `.cursor/skills/the-library/SKILL.md` | Install or distribute internal skills |
| `meta-skill` | Guide to creating new skills | `.cursor/skills/meta-skill/SKILL.md` | Create a repo-specific skill |
| `worktree-manager` | Full worktree lifecycle guidance | `.cursor/skills/worktree-manager/SKILL.md` | Decide when to create/list/remove worktrees |
| `create-worktree` | Lightweight worktree creation | `.cursor/skills/create-worktree/SKILL.md` | Quick branch-isolated setup |

## Utilities And Validators

| Utility | Purpose | Path | Notes |
|---------|---------|------|-------|
| Constants | Shared project/session paths | `.cursor/hooks/utils/constants.py` | Centralizes log directory handling |
| Summarizer | One-line LLM summaries | `.cursor/hooks/utils/summarizer.py` | Uses Anthropic utility client |
| HITL | Human approvals and choices | `.cursor/hooks/utils/hitl.py` | Sends WebSocket-backed approval requests |
| Anthropic client | Fast completion helper | `.cursor/hooks/utils/llm/anth.py` | Used for summaries and naming |
| OpenAI client | Alternative completion helper | `.cursor/hooks/utils/llm/oai.py` | Used for summaries |
| TTS helpers | Audio notifications | `.cursor/hooks/utils/tts/` | ElevenLabs, OpenAI, or offline pyttsx3 |
| `validate_file_contains.py` | Optional content check helper | `.cursor/hooks/validators/validate_file_contains.py` | Not wired on shipped `stop`; may block only if you add it to a custom `hooks.json` |
| `validate_new_file.py` | Optional file-creation check helper | `.cursor/hooks/validators/validate_new_file.py` | Not wired on shipped `stop`; may block only if you add it to a custom `hooks.json` |

## Acceptance Checklist

- [ ] Every major component in the workflow is represented in this file.
- [ ] Each component points to at least one concrete file path in the repo.
- [ ] Example invocations align with available slash commands or agent prompts.
- [ ] The component list matches `AGENTS.md` and `../.cursor/hooks.json`.
