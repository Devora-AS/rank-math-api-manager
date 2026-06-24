# Multi-Agent Teams Docs

Purpose: Table of contents and entry point for the Cursor-native multi-agent workflow documentation.
Audience: Developers, integrators, and operators adopting this workflow in Cursor.
Prerequisites: Familiarity with Cursor, Git, shell commands, and basic LLM API setup.
Status: complete
Last updated: 2026-04-20
Author: Cursor agent (GPT-5.4)

## Overview

This docs set explains how the repository's Cursor-first multi-agent workflow is structured, configured, operated, and validated. It complements the root-level [README](../README.md) and the agent-focused [AGENTS.md](../AGENTS.md) with operator and integrator documentation. For **worktrees**, treat **Cursor 3** as explicit isolation (`/worktree`, `/best-of-n`, or `git worktree add`); MAT bootstrap and `runtime.env` are repo-local layers documented in [`worktree-decision-matrix.md`](worktree-decision-matrix.md), [`configuration.md`](configuration.md), and [`../AGENTS.md`](../AGENTS.md).

## Artifact Taxonomy

This docs set follows one repo-wide artifact taxonomy:

- **Canonical tracked handoffs**: tracked contracts and handoff examples that define accepted workflow interfaces. In this repo, that includes `docs/current-plan.md`, `build-result.md`, and `verify-result.md`.
- **Tracked distilled evidence**: curated tracked summaries or dated sign-off artifacts kept for review and historical reference.
- **Local mutable runtime exhaust**: rolling local outputs that help operators during a session but should not churn in commits.
- **Raw/sensitive captures**: prompt, payload, transcript, or similar captures that may contain high-volume or sensitive runtime detail.

Use [README.md](../README.md) for the short taxonomy summary and [MAINTAINER.md](MAINTAINER.md) for operational handling rules.

## Core Docs

| File | Status | Description |
| --- | --- | --- |
| [quick-start.md](quick-start.md) | complete | Fastest path for first use: copy `.env`, start observability, open Cursor, and run slash commands. |
| [adoption-safe-defaults.md](adoption-safe-defaults.md) | complete | Internal safe-defaults profile: conservative first-run commands, env posture, checklist, escalation. |
| [getting-started-new-projects.md](getting-started-new-projects.md) | complete | How to bring this workflow into a brand new project with the required `.cursor` layout and environment. |
| [getting-started-existing-projects.md](getting-started-existing-projects.md) | complete | Safe migration guide for layering the workflow onto an existing repository, including rollback guidance. |
| [MAINTAINER.md](MAINTAINER.md) | complete | Maintainer readiness checklist covering environment, env vars, rollback, blocked claims, and evidence limits. |
| [components.md](components.md) | complete | Reference for agents, hooks, skills, utilities, and their inputs, outputs, and file locations. |
| [configuration.md](configuration.md) | complete | `.env`, `.cursor/hooks.json`, `.cursor/worktrees.json`, `.cursor/mcp.json`, retries, and observability tuning. |
| [technical-stack.md](technical-stack.md) | complete | High-level overview of the runtime stack: LLM clients, TTS, observability, and isolation model. |

## Architecture Docs

| File | Status | Description |
| --- | --- | --- |
| [what-it-can-do-and-how-it-works.md](what-it-can-do-and-how-it-works.md) | complete | Plain-language explanation of capabilities, limits, scope, and internal behavior. |
| [agent-teams.md](agent-teams.md) | complete | How teams are composed in Cursor using parent orchestration, subagents, and worktrees. |
| [orchestration-workflow.md](orchestration-workflow.md) | complete | Detailed sequencing, retries, lifecycle transitions, and final synthesis behavior. |
| [continual-learning-safe-handling.md](continual-learning-safe-handling.md) | draft | Queue-first memory-maintenance design, intentional AGENTS handling, and fallback rules. |
| [update-mat/index.md](update-mat/index.md) | MVP | Slice 1 updater foundation: footprint manifest, prompt templates, summary schema, rollout. |
| [long-run-state.md](long-run-state.md) | MVP | Multi-slice mission state template; mission section records `execution_mode`, and each active-slice/queue row uses `execution_mode` plus `execution_rationale`; when a slice originates from an approved onboarding package, the matching `TASK-###` must stay visible in the active slice so `tasks.json` can be synced; pair with [`/mat-long-run`](../.cursor/commands/mat-long-run.md) and [parent orchestrator](../.cursor/agents/parent-orchestrator.md) post-slice mission gate. |
| [mat-plan-team-spec.md](mat-plan-team-spec.md) | MVP | Plan fixture schema, subagent assignment semantics, trace/honesty boundaries for `/mat-plan-team`. |
| [todo-orchestration-protocol.md](todo-orchestration-protocol.md) | MVP | Strict MAO Cursor To-do tags, statuses, build→validate gate, hooks notes, fallback. |
| [todo-orchestration-pilot.md](todo-orchestration-pilot.md) | MVP | Manual end-to-end pilot checklist for the todo protocol. |
| [todo-orchestration-runtime-evidence.md](todo-orchestration-runtime-evidence.md) | MVP | Committed-artifact audit for TodoWrite/hook proof; local capture via observability DB. |
| [runtime-messaging.md](runtime-messaging.md) | MVP | Repo-local MAT runtime messaging and durable transport foundation with an adapter-backed store, typed envelopes, outbox/inbox rows, delivery attempts, conservative worker/retry/DLQ handling, and the operator-facing runtime review surface. |
| [mao-advisory-go-criteria.md](mao-advisory-go-criteria.md) | MVP | Phase 4: maps decision-record advisory go-criteria to procedures and PASS/INCONCLUSIVE outcomes. |
| [phase4-roadmap-reassessment-checklist.md](phase4-roadmap-reassessment-checklist.md) | MVP | Phase 4: operator checklist for reassessing blocked runtime limitations using evidence procedures. |
| [todo-write-observability-discovery.md](todo-write-observability-discovery.md) | MVP | Discovery + shipped opt-in **`MaoTodoObservation`** path (`CURSOR_MAO_EMIT_TODO_OBSERVATION_OBSERVABILITY`); live todo column remains runtime-blocked, not merely deferred. |
| [todo-orchestration-mao-todowrite-application.md](todo-orchestration-mao-todowrite-application.md) | MVP | Focused verification for parent `TodoWrite merge` helpers and optional merge CLI. |
| [data-flow.md](data-flow.md) | complete | End-to-end flow of prompts, files, hooks, subagents, observability, and outputs. |
| [events-and-visualization.md](events-and-visualization.md) | complete | The 11 hook events, their payloads/logs, and recommended dashboard widgets. |
| [observability-retention-policy.md](observability-retention-policy.md) | complete | Advisory retention and sampling policy: SQLite `hook_events`, preview truncation vs stored rows, gitignored growth paths, operator cleanup. |

## Usage Docs

| File | Status | Description |
| --- | --- | --- |
| [planning-commands-guide.md](planning-commands-guide.md) | complete | When to use lightweight `/mat-plan` versus heavyweight `/mat-plan-onboarding`, plus projection/handoff guardrails. |
| [usage-examples-and-cases.md](usage-examples-and-cases.md) | complete | Concrete command-driven examples for planning, building, reviewing, scraping docs, and worktree workflows. |
| [features-demonstrated.md](features-demonstrated.md) | complete | Inventory of the behaviors this project demonstrates, with pointers to the implementing files. |
| [best-practices.md](best-practices.md) | complete | Operator and integrator guidance for reliability, safety, cost control, and validation. |
| [capability-precedence.md](capability-precedence.md) | MVP | Project-first precedence for `.cursor/`, `.mat/`, plugins, and global capabilities; authoritative vs advisory. |
| [model-routing-policy.md](model-routing-policy.md) | MVP | Conservative MAT routing tiers (`cheap`, `standard`, `strong`), escalation rules, advisory telemetry fields, and deferred adapter boundary. |
| [routing_advisory.md](routing_advisory.md) | MVP | Advisory-only routing record shape, session rollups, analysis CLI, operational baseline guidance, safe surfacing rules, and operator responses to context pressure. |
| [context-budget-policy.md](context-budget-policy.md) | MVP | Bounded context per role; artifact-first handoffs; default avoid-list for mega-docs (`README`, `ROADMAP`, `AGENTS`, full `docs/` tree). |
| [local-app-verification-ladder.md](local-app-verification-ladder.md) | complete | Verification order for local-app pilots: manual/staging baseline, deterministic automation, browser tools, and fallback posture. |
| [deployment-guide.md](deployment-guide.md) | complete | Deployment and rollout checklist for local/operator environments, observability, and validation. |
| [troubleshooting.md](troubleshooting.md) | complete | Common problems with Bun, hooks, lifecycle capture, observability, and worktrees. |

## Related Project Docs

| File | Status | Description |
| --- | --- | --- |
| [../ROADMAP.md](../ROADMAP.md) | living | Product/engineering roadmap (Vision / Current Focus / Near-Term / Recently Completed / Future Concepts / Icebox / Blocked); maintain during development per [AGENTS.md § Maintaining the roadmap](../AGENTS.md#maintaining-the-roadmap). |
| [inventory.json](inventory.json) | existing | Asset inventory and migration classification from the Claude-to-Cursor adaptation work. |
| [migration-backlog.md](migration-backlog.md) | existing | Historical migration backlog from the Stage 0 Cursor translation; use [`../ROADMAP.md`](../ROADMAP.md) for active work and refresh this file only in a dedicated migration audit. |
| [artifacts-index.md](artifacts-index.md) | existing | Acceptance tracking for artifacts created during the migration stages. |
| [pilot-report.md](pilot-report.md) | existing | Pilot checklist and evidence template for an end-to-end validation run. |
| [pilot/pilot-new/README.md](pilot/pilot-new/README.md) | MVP | Adoption pilot for a **new** project (WordPress Switch User scenario): step-by-step, success criteria, risks. |
| [pilot/pilot-existing/README.md](pilot/pilot-existing/README.md) | MVP | Adoption pilot for an **existing** project (Pancakeswap Prediction Bot): safe bootstrap, `/mat-prime`, `/mat-doctor --full`, bounded slices, onboarding, and paper-trading-first guidance. |
| [phase1-validation-report.md](phase1-validation-report.md) | existing | Phase 1 sign-off report with final status, evidence, and lifecycle fallback notes. |
| [hook-payload-verification.md](hook-payload-verification.md) | existing | Hook stdin fields, opt-in capture (`CURSOR_HOOK_CAPTURE_*`, per-session mode), canonical `artifacts/phase1/` samples, contract re-verification when Cursor changes. |
| [orchestration.md](orchestration.md) | existing | Design-stage orchestration notes that informed the current implementation. |
| [LIFECYCLE_COMPARISON.md](LIFECYCLE_COMPARISON.md) | existing | Claude Code vs Cursor lifecycle comparison and hook mapping notes. |

## Recommended Reading Order

1. Start with [quick-start.md](quick-start.md) and [adoption-safe-defaults.md](adoption-safe-defaults.md) for a conservative first adoption.
2. Read [what-it-can-do-and-how-it-works.md](what-it-can-do-and-how-it-works.md).
3. Use either [getting-started-new-projects.md](getting-started-new-projects.md) or [getting-started-existing-projects.md](getting-started-existing-projects.md).
4. Then read [configuration.md](configuration.md), [agent-teams.md](agent-teams.md), and [orchestration-workflow.md](orchestration-workflow.md).
5. Use [planning-commands-guide.md](planning-commands-guide.md), [usage-examples-and-cases.md](usage-examples-and-cases.md), and [best-practices.md](best-practices.md) during day-to-day operation.

## Acceptance Checklist

- [ ] `docs/README.md` links to every doc created in this task.
- [ ] Each linked file exists and opens from this table of contents.
- [ ] Status, last-updated, and author are visible in this file.
- [ ] Root references such as [AGENTS.md](../AGENTS.md) and [README.md](../README.md) resolve correctly.
