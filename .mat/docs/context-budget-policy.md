# MAT context budget policy v1

**Operator habits:** [`mat-operator-playbook.md`](../guides/mat-operator-playbook.md) § B6 (daily discipline and Codebase Search honesty); **Self-Compact checkpoints:** § B10 and [`.cursor/skills/mat-self-compact/SKILL.md`](../../.cursor/skills/mat-self-compact/SKILL.md).

- **Purpose:** Define **bounded context** for MAT orchestration so agents load enough to do the job without habitual mega-context or transcript replay.
- **Audience:** Parent orchestrator, builder, verifier, and operators tuning sessions for cost and clarity.
- **Status:** complete — stable bounded-context guidance per role, artifact-first handoffs.
- **Last updated:** 2026-06-25

## Relationship to other policy

- **Routing tiers and cost notes:** [`docs/reference/model-routing-policy.md`](model-routing-policy.md) — advisory tier choice (`cheap` / `standard` / `strong`); does not replace file handoffs.
- **Capability precedence:** [`docs/reference/capability-precedence.md`](capability-precedence.md) — what is authoritative vs advisory for workflow.

## What “bounded context” means

**Bounded context** means: load **only** files and excerpts needed for the **current slice**, prefer **artifacts and diffs** over replaying long chat history, and **stop** before defaulting to repo-wide doc dumps.

Practical signals:

- The active plan in **`docs/current-plan.md`** defines scope; treat it as the primary narrative for the slice.
- **`build-result.md`** lists what changed; use it to drive file-scoped reads for verifier and parent review.
- **Touched paths** from `git diff`, `build-result.md`, or explicit lists beat “read everything under `docs/`.”
- **Short excerpts** (a section, a function, a table row) beat pasting whole large files into prompts when a narrow read suffices.

## Default avoid list (unless the task explicitly needs them)

Do **not** habitually load into subagent or parent prompts as background:

- Root **`README.md`**, **`ROADMAP.md`**, **`AGENTS.md`**
- The full **`docs/`** tree or broad glob reads

Use them **when** the slice is about those files, onboarding, roadmap maintenance, or AGENTS-level contract edits. Otherwise link out (“see `docs/reference/model-routing-policy.md`”) instead of inlining megadocs.

## Artifact-first over transcript replay

Prefer, in order:

1. **`docs/current-plan.md`** — acceptance criteria and steps for this slice.
2. **`build-result.md` / `verify-result.md`** — structured outcomes and evidence.
3. **Changed files and focused excerpts** — from handoffs or `git diff`.
4. **Session summary or long-run state** — when continuing a mission (`docs/architecture/long-run-state.md`, `docs/session-summary.md`).

Avoid replaying long prior chat as a substitute for the above when the work is already captured in files.

## Role-based guidance

### Parent orchestrator

- Owns **preflight** (`inline` vs `builder_plus_verifier` vs `parallel_spawn`) and should pick the **lightest honest** mode; see [`.cursor/agents/parent-orchestrator.md`](../../.cursor/agents/parent-orchestrator.md).
- Delegates with prompts that point at **plan + artifacts**, not whole-repo context.
- Does **not** need to load every doc for every slice; pull policy links on demand.
- When compaction pressure rises or a prompt starts to sprawl, prefer shorter artifact excerpts and touched-file lists before adding more background.

### Builder

- Reads **`docs/current-plan.md`** first; implements against it.
- Loads **implementation paths** only; does not default to README/ROADMAP/AGENTS unless the plan requires them.
- Writes **`build-result.md`** with concrete paths so the verifier can stay narrow.
- When the slice fans out across files, prefer the plan, the diff, and the smallest reviewable code excerpts rather than replaying the whole conversation.

### Verifier

- Reads **`docs/current-plan.md`**, **`build-result.md`**, then **only files listed or implied** by the build result.
- Evidence is **file:line** or grep-backed; no broad exploratory reads unless a criterion requires it.
- If the review needs more than the handoff files, gather only the extra files needed for the criterion instead of widening into repo-wide reading.

## Soft context-pressure signals

These are advisory only, not hard caps:

- **Pre-compact / large prompt payloads** are a cue to reduce background context and prefer artifact-first handoffs.
- **Repeated retries** are a cue to tighten prompts around the specific failure instead of restoring the whole session history.
- **Cross-file work** is a cue to load touched files and concise excerpts, not the full repo.
- **Compaction** is a cue to preserve the plan, build, and verify artifacts as the stable reference points.

**MAT Self-Compact v1** (opt-in `CURSOR_MAT_SELF_COMPACT=1`) adds gitignored
`artifacts/context-handoff/` checkpoints and `scripts/mat-context-gauge.py` with
aligned notice/warning/force thresholds (default **55 / 70 / 85**%). See
[`configuration.md`](configuration.md) and [`specs/mat-self-compact-cursor.md`](../../specs/mat-self-compact-cursor.md).

Routing advisories may surface the same boundary markers (`context_usage_percent`,
`messages_to_compact`, `payload_size_chars`, `payload_size_bytes`, and
`boundary_signals`) using the 70 / 6000 / 25 thresholds, but they remain advisory-only
and cannot override canonical handoff files.

Prompt-size linting follows the same posture. The warning-only helper may emit
`artifacts/mao/prompt_lint_<session_id>.log` when combined prompt size crosses the
rough 6000-character threshold, when more than 10 file references are present, or when
avoid-list docs such as `README.md`, `ROADMAP.md`, or `AGENTS.md` are loaded without
an explicit artifact-first rationale. Warnings are advisory only and never block execution.

Session budget advisories are likewise advisory only. When
`CURSOR_MAT_SESSION_BUDGET_USD` is set, the best-effort session estimate may append a
note to `docs/session-summary.md` if the available routing-advisory cost data crosses
the configured threshold. The estimate can be incomplete, so the note must say so
plainly and must not imply enforcement or budget accounting truth.

## Local cost-hygiene diagnostics (advisory)

The optional `scripts/validate_cost_context_hygiene_pack.py --report` may write a JSON summary to gitignored `artifacts/cost-hygiene/last-report.json` and append `report-events.jsonl`. The same path may receive `bootstrap-events.jsonl` from adoption. These files are **not** a billing or usage ledger, not authoritative token math, and not a substitute for bounded-context discipline in `docs/current-plan.md` and handoff artifacts. They only summarize validator severities and bootstrap metadata for operator triage.

## Non-goals

- Hard token limits enforced by hooks in this slice.
- Replacing authoritative handoff files with “context budget” telemetry.
- Turning prompt warnings or budget notes into workflow enforcement.
- Treating `artifacts/cost-hygiene/*` or routing-advisory output as product billing or full Cursor-behavior observability.

## Related

- [`docs/reference/model-routing-policy.md`](model-routing-policy.md)
- [`docs/reference/workflow-artifact-contract.md`](workflow-artifact-contract.md)
- [`docs/reference/todo-orchestration.md`](todo-orchestration-protocol.md)
