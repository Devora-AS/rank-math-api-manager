# Components Reference

- Purpose: Reference the major components in the Cursor-native multi-agent workflow and show how they fit together.
- Audience: Operators, maintainers, and contributors who need a file-level map of the system.
- Prerequisites: Familiarity with Cursor agents, hooks, and slash commands.
- Status: complete
- Last updated: 2026-08-24
- Author: Cursor agent (GPT-5.4)
- Repo posture: internal/reference-oriented for the maintainer team; not a public packaging target by default.

## Related Files

- [Agent instructions](../../AGENTS.md)
- [Hook manifest](../../.cursor/hooks.json)
- [Configuration](configuration.md)
- [Agent teams](agent-teams.md)
- [Orchestration workflow](orchestration-workflow.md)
- [Inventory](../inventory.json)
- [Artifacts index](artifacts-index.md)
- [Capability precedence](capability-precedence.md) — project-local vs `.mat/`, plugin, and global capabilities
- [Model routing policy](model-routing-policy.md) — conservative `cheap` / `standard` / `strong` MAT routing guidance
- [Routing advisory surface](../reference/routing_advisory.md) — advisory record shape and safe surfacing rules
- [Context budget policy](context-budget-policy.md) — bounded context and artifact-first loading

## Component Map

| Component | Purpose | Key paths |
|-----------|---------|-----------|
| Observability client (Vue) | Live hook timeline, pulse chart, transcript, MAO visibility, runtime review, Help modal | `apps/client/src/` (see `App.vue`, `EventCard.vue`, `HelpModal.vue`, `components/RuntimeReviewPanel.vue`) |
| Planning commands | Lightweight solo planning, surgical plan updates, heavyweight onboarding, and optional Layer 0 preflight discoverability | `.cursor/commands/mat-plan.md`, `.cursor/commands/mat-plan-update.md`, `.cursor/commands/mat-plan-onboarding.md`, `.cursor/commands/mat-preflight-research.md` (delegates to `mat-preflight-gated`; planning-only), `docs/guides/planning-commands-guide.md`, [`docs/architecture/plan-contract.md`](plan-contract.md), execution templates [`adoption-minimal-current-plan.md`](../templates/adoption-minimal-current-plan.md) (lite), [`execution-plan-template.md`](../templates/execution-plan-template.md) (standard) |
| MAT adoption sync | GitHub-first detect → route → plan → approve → verify; `.mat/source-config.json` v2 materialize; preflight + `.gitignore` merge/rewrite (`gitignore_rewrite_preview`, `gitignore_merge_preview`, `verify-trackable`); first adoption via `/mat-adopt` or mat-sync from MAT source with `--repo-root` | `.cursor/commands/mat-adopt.md`, `.cursor/commands/mat-sync.md`, `docs/guides/mat-sync-team-runbook.md`, `docs/guides/getting-started-existing-projects.md`, `scripts/mat-sync.sh`, `scripts/adoption/mat_adopt_preflight.py`, `scripts/adoption/mat_gitignore_merge.py`, `scripts/adoption/mat_cursorignore_merge.py`, `scripts/adoption/mat_source_config.py`, `scripts/adoption/mat_source_materialize.sh`, `scripts/adoption/update_mat_conflict_routing.py`, `.cursor/commands/mat-update-mat.md` |
| Parent Orchestrator | Decompose, delegate, retry, synthesize; execution closeout prints **exactly one** fenced `txt` block per major phase (`/mat-plan-team`, `/mat-long-run`, `/mat-sprint`) | `.cursor/agents/parent-orchestrator.md`, `.cursor/commands/mat-plan-team.md`, `.cursor/commands/mat-long-run.md`, `.cursor/commands/mat-sprint.md`, `.cursor/commands/mat-subagents-spawn.md`, [`planning-commands-guide.md`](../guides/planning-commands-guide.md#recommended-next-command-execution-commands), [`mat-advisor-strategy-runbook.md`](../guides/mat-advisor-strategy-runbook.md), [`mat-prompt-templates.md`](../guides/mat-prompt-templates.md) |
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
| MAT runtime messaging | Repo-local typed event, subscription-policy, outbox/inbox, delivery-attempt, worker/retry/DLQ control plane plus the operator-facing runtime review panel and review API | `.cursor/hooks/utils/runtime_messaging.py`, `scripts/mat-runtime.py`, `apps/server/src/runtime-review.ts`, `apps/client/src/composables/useRuntimeReview.ts`, `apps/client/src/components/RuntimeReviewPanel.vue`, `docs/architecture/runtime-messaging.md` |
| Capability policy | Project-first routing doc (not a runtime loader) | `docs/reference/capability-precedence.md` |
| Routing policy | Conservative model tiers and advisory budget notes | `docs/reference/model-routing-policy.md` |
| Routing advisory surface | Advisory-only record shape, session rollups, and safe surfacing | `docs/reference/routing_advisory.md` |
| Context budget policy | Bounded context per role; avoid habitual mega-doc loads | `docs/reference/context-budget-policy.md` |
| Doc link validator (M7) | Layout-aware internal markdown link checks (`source` / `plugin` / `adopted-fixture`); wired in `phase1-verify.sh` on MAT source | `scripts/validate_doc_links.py`, `scripts/doc_link_allowlist.json`, `docs/reference/doc-link-validation.md`, `tests/test_validate_doc_links.py` |
| Cursor asset validator (D1) | Manifest ↔ filesystem bijection, obsolete-pattern scan, agent `name` / skill slug checks | `scripts/validate_cursor_assets.py`, `artifacts/cursor-capabilities.manifest.json`, `artifacts/cursor-capabilities.schema.json`, `docs/reference/cursor-capability-baseline.md`, normative spec [`specs/cursor-compatibility-v1.md`](../../specs/cursor-compatibility-v1.md) |
| Cursor plugin packaging (D3a-private / N1) | Local symlink + Devora Team Marketplace from committed `packages/mat-workflow/`; public Marketplace OOS | `scripts/package-cursor-plugin.py`, `.cursor-plugin/plugin.json`, `.cursor-plugin/marketplace.json`, `packages/mat-workflow/`, `tests/test_cursor_plugin_packaging.py`, [`docs/guides/cursor-plugin-install.md`](../guides/cursor-plugin-install.md), [`specs/cursor-plugin-distribution-v1.md`](../../specs/cursor-plugin-distribution-v1.md) |
| Verification profiles (E3) | Named Phase 1 profiles, honest pass/fail/skip manifest | `scripts/verification_profiles.py`, `artifacts/verification-manifest.schema.json`, `docs/reference/verification-profiles.md`, normative spec [`specs/verification-profiles-v1.md`](specs/verification-profiles-v1.md) |
| Skills | Reusable operator guidance | `.cursor/skills/` |
| Utilities | LLM, HITL, TTS, routing advisories, rollups, summaries, validators | `.cursor/hooks/utils/`, `.cursor/hooks/validators/` |

## Planning Commands

- Purpose: Capture planning truth before any execution handoff.
- Responsibilities: Keep `/mat-plan` lightweight and single-file; optional **`--depth` thin router** (explicit aliases to existing commands — see [`.cursor/commands/mat-plan.md`](../../.cursor/commands/mat-plan.md#depth-router-depth)); keep `/mat-plan-onboarding` heavyweight, traceable, and approval-gated; keep `/mat-plan-update` surgical and planning-only for living-plan drift (four phased `txt` closeout blocks per command doc).
- Inputs: User task, relevant repo context, existing `specs/` artifacts when present.
- Outputs: `specs/<slug>.md` for `/mat-plan`, amended planning files for `/mat-plan-update`, or `specs/<slug>/prd.md`, `specs/<slug>/spec.md`, `specs/<slug>/tasks.json`, and `specs/<slug>/plan-summary.md` for `/mat-plan-onboarding`.
- Relevant paths: `../.cursor/commands/mat-plan.md`, `../.cursor/commands/mat-plan-update.md`, `../.cursor/commands/mat-plan-onboarding.md`, `../docs/guides/planning-commands-guide.md`.
- Example invocations:

```text
/mat-plan Improve the onboarding checklist copy
/mat-plan-onboarding Design a new planning workflow with traceable tasks
```

Planning truth stays in `specs/`. `docs/current-plan.md` remains execution truth for downstream builder/verifier flows. Substantive living plans include append-only **`## Amendments`** (ISO-8601 UTC; see [`plan-contract.md`](plan-contract.md)) and advisory status marker checklists (`[]`, `[wip]`, `[x]`, `[f]`; MAO gates stay on handoff files.

## Agents

Full role descriptions, inputs, outputs, and example invocations live in [AGENTS.md](../../AGENTS.md) (`## Agent Roles`). Agent definition files are under `.cursor/agents/`; slash commands are under `.cursor/commands/`.

| Agent | Key file | Purpose |
|-------|----------|---------|
| Parent Orchestrator | `.cursor/agents/parent-orchestrator.md` | Plan, delegate, retry, synthesize |
| Builder | `.cursor/agents/builder.md` | Implement and self-validate |
| Verifier | `.cursor/agents/verifier.md` | Read-only acceptance checking |
| Test Writer | `.cursor/agents/test-writer.md` | Focused regression test authoring |
| Style Reviewer | `.cursor/agents/style-reviewer.md` | Docs/style consistency and claim hygiene |
| Meta Agent | `.cursor/agents/meta-agent.md` | Generate new agent definitions |
| Scout | `.cursor/agents/scout-report-suggest.md` | Read-only investigation and issue detection |
| Docs Scraper | `.cursor/agents/docs-scraper.md` | Fetch docs into markdown |
| Worktree Creator | `.cursor/agents/create-worktree-subagent.md` | Automate isolated worktree setup |
| Demo Agent | `.cursor/agents/demo-agent.md` | Demonstrate end-to-end behavior |

## Hooks

The project wires 11 events in [`../.cursor/hooks.json`](../../.cursor/hooks.json):

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

Cloud / Agents Window posture (Cursor 3 language, no MAT auto-provision): [P1 Audit — Cloud Agents and Agents Window](decision-record.md#p1-audit--cloud-agents-agents-window); setup detail in [`worktree-decision-matrix.md`](../archive/worktree-decision-matrix.md).

| Skill | Purpose | Path | Example use |
|-------|---------|------|-------------|
| `the-library` | Private-first skill distribution | `.cursor/skills/the-library/SKILL.md` | Install or distribute internal skills |
| `meta-skill` | Guide to creating new skills | `.cursor/skills/meta-skill/SKILL.md` | Create a repo-specific skill |
| `worktree-manager` | Full worktree lifecycle guidance | `.cursor/skills/worktree-manager/SKILL.md` | Decide when to create/list/remove worktrees |
| `create-worktree` | Lightweight worktree creation | `.cursor/skills/create-worktree/SKILL.md` | Quick branch-isolated setup |
| `mat-plan-contract` | Shared plan contract v0.1 (tiers, amendments, markers, projection) | `.cursor/skills/mat-plan-contract/SKILL.md` | Choose depth tier or apply living-plan semantics without rereading full design spec |
| `mat-plan-canvas` | Canvas-based plan visualization (derived, advisory) | `.cursor/skills/mat-plan-canvas/SKILL.md` | Generate a `.canvas.tsx` dashboard from bounded markdown handoffs for interactive plan review |
| `advise-project-approach` | Layer 0 preflight — landscape, comparables, cost scenarios before planning | `.cursor/skills/advise-project-approach/SKILL.md` | Greenfield or unclear landscape discovery; writes `specs/<slug>/preflight/landscape.md` and `candidates.json` |
| `neuroarxiv` | Layer 0 preflight Phase B — G2-gated bounded arXiv literature scan | `.cursor/skills/neuroarxiv/SKILL.md` | After `novel_research_required` + G2; writes `arxiv-synthesis.md` and `arxiv-papers.json`; optional `scripts/preflight/fetch_arxiv.py` |
| `mat-preflight-gated` | Layer 0 orchestrator — Phase A → novelty gate → Phase B (G2 only) | `.cursor/skills/mat-preflight-gated/SKILL.md` | Sequences advise + neuroarxiv by path; never auto-escalates; writes `specs/<slug>/preflight/*`; handoff hints for `/mat-plan` only |

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
| `validate_planning_artifacts.py` | Planning artifact contract validation (tasks.json, solo `/mat-plan` sections + Tier 2b validation loops, optional Task type / Complexity soft Tier 2 tags, onboarding traceability, mat-plan-team schema, Tier 4 substantive `docs/current-plan.md`) | `scripts/validate_planning_artifacts.py` | Wired in `scripts/phase1-verify.sh` on MAT source; skipped on adopted sidecar; schemas: `docs/templates/tasks-schema.json`, `docs/templates/tasks-schema-mat-plan-team.json` |
| `mat_loop_policy.py` | Opt-in Alt B loop policy evaluate (budgets, failure classes, continue/retry/escalate/stop) | `scripts/mat_loop_policy.py` | Enable with `CURSOR_MAT_LOOP_POLICY=1`; see [`loop-policy.md`](loop-policy.md) |
| `mat-loop-manifest.py` | Init/read/patch versioned loop manifests under `artifacts/loop/` | `scripts/mat-loop-manifest.py` | Writes per-run + legacy mirror; advisory relative to file handoffs |
| `doctor.sh --loop-policy` | Advisory loop-policy readiness check | `scripts/doctor.sh` | Non-fatal; no npm loop-engineering in CI |
| `validate_quality_commands.py` | Advisory fake-green / placeholder lint scan for MAT verify paths | `scripts/validate_quality_commands.py` | Always exits 0; optional `--json`; wired from doctor and PostToolUse banner (**A1** / **B9**) |
| `doctor.sh --quality-commands` | Non-fatal quality-command honesty diagnostic | `scripts/doctor.sh` | Prints `WARN path:line: …` from `validate_quality_commands.py`; see [`MAINTAINER.md`](MAINTAINER.md#quality-command-honesty--doctor-diagnostics-a1--b9) |
| `validate_research_skills.py` | Advisory discovery/research skill honesty scan (inline citations, G2 gates, no auto-escalate) | `scripts/validate_research_skills.py` | Always exits 0; optional `--json`; wired from doctor; see [`MAINTAINER.md`](MAINTAINER.md#discovery--research-skills) |
| `doctor.sh --research-skills` | Non-fatal research-skills diagnostic | `scripts/doctor.sh` | Prints advisory warnings from `validate_research_skills.py`; pairs with Layer 0 preflight skills |

## Acceptance Checklist

- [ ] Every major component in the workflow is represented in this file.
- [ ] Each component points to at least one concrete file path in the repo.
- [ ] Example invocations align with available slash commands or agent prompts.
- [ ] The component list matches `AGENTS.md` and `../.cursor/hooks.json`.
