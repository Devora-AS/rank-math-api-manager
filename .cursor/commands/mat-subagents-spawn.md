# MAT Subagents Spawn

Decompose a task and run **multiple Cursor Task subagents in parallel** when work streams are independent—under **this repository’s** agents and honesty boundaries.

## Usage

```
/mat-subagents-spawn <task description>
```

## When to use

- The task splits into **2+ independent** tracks (different files, no shared mutable state mid-flight).
- You are acting as **parent orchestrator** and will **integrate** results (merge plans, resolve conflicts, re-run verification)—not “fire and forget.”

Prefer **`/mat-long-run`** when the mission needs **ordered slices**, `docs/architecture/long-run-state.md`, and the **post-slice mission gate**. Prefer **`/mat-plan-team`** for a **single** plan → build → verify cycle. Use **`/mat-subagents-spawn`** for **parallel fan-out** inside one slice or investigation burst.

## Repo-local agent types (Task `subagent_type`)

**Cursor built-ins (examples):**

- `explore` — fast codebase search and mapping (read-only).
- `generalPurpose` — multi-step research or implementation when no specialist fits.

**Project agents (see [`.cursor/agents/`](../agents/builder.md)):**

| `subagent_type` | Role |
|-----------------|------|
| `parent-orchestrator` | Sequencing, delegation, synthesis (orchestrator mode—not nested lightly) |
| `builder` | Implementation + `build-result.md` |
| `verifier` | Read-only validation; structured verify payload only — parent serializes `verify-result.md` |
| `test-writer` | Focused tests |
| `style-reviewer` | Docs/style consistency; claim hygiene |
| `scout-report-suggest` | Read-only investigation |
| `docs-scraper` | Fetch and save external docs |
| `meta-agent` | Generate new agent definitions |
| `create-worktree-subagent` | Worktree automation |
| `demo-agent` | Self-contained demo flow |

Other `subagent_type` values may exist in Cursor; only use names that match **this** repo’s `.cursor/agents/` unless you have a deliberate reason.

## Parallel pattern (honest)

1. **Decompose** — list independent modules and **sequential** dependencies; if everything depends on everything, parallel speedup is a trap—serialize.
2. **Isolate** — optional git worktrees: [`/mat-wt-create`](mat-wt-create.md), [`/mat-wt-check`](mat-wt-check.md) (see [`AGENTS.md`](../../AGENTS.md) worktree section). **Do not claim auto worktree-per-Task** — Cursor does not invent a worktree per Task by default for editor Task fan-out; create checkouts explicitly when write isolation is required.
3. **Spawn** — one Task per stream; **single message, multiple Task calls** when running agents in parallel.
4. **Wait** — follow **wait-before-supersede** ([`parent-orchestrator`](../agents/parent-orchestrator.md)): allow startup latency; resume stalled agents before replacing them.
5. **Integrate** — **parent-mediated integration only** (merge results, run `bash scripts/phase1-verify.sh` or targeted tests, fix conflicts). There is **no peer task-board** and no teammate-to-teammate messaging contract in MAT.

## File-ownership / path-class matrix

Assign **one primary writer** per path class before spawning. Concurrent readers are fine; concurrent writers on the same class are not. When in doubt, serialize under the parent. Aligns with [`docs/reference/role-write-policy.md`](../../.mat/docs/role-write-policy.md) and team composition in [`docs/architecture/agent-teams.md`](../../.mat/docs/agent-teams.md).

| Path / glob class | Primary writer | Concurrent readers OK? | Conflict resolution |
|-------------------|----------------|------------------------|---------------------|
| `docs/current-plan.md` | Parent orchestrator (markers: builder of the active slice only) | Yes | Parent owns plan text; builder may mutate in-plan markers for its slice only — never two builders on the same plan file |
| `build-result.md` | Active builder for this slice | Yes (verifier/parent) | Single writer; parent discards/supersedes stale drafts after serialize |
| `verify-result.md` | Parent orchestrator (from verifier payload) | Yes | Parent-owned handoff; verifier must not write this file |
| `docs/architecture/long-run-state.md`, `docs/session-summary.md` | Parent orchestrator | Yes | Parent serialize only; workers read |
| Plan-listed implementation paths (disjoint globs) | Assigned stream’s builder / specialist | Yes | Pre-assign disjoint ownership; overlapping globs → parent serialize or refuse parallel spawn |
| `.cursor/agents/**`, `.cursor/commands/**` | One designated writer stream | Yes | Serialize if two streams touch the same command/agent file |
| `tests/**` matching a stream’s ownership | That stream’s `test-writer` or builder | Yes | Shared test modules → parent serialize |
| `ai_docs/**` (scraped) | `docs-scraper` for that URL set | Yes | Distinct output paths per scrape; parent merges index links |
| `.env`, `.mat.env`, credentials | **Nobody** (protected) | No writes | Always breach; never assign |

**Independence test (before spawn):** every write path appears in **exactly one** stream’s ownership column. If two streams need the same mutable file, do **not** parallelize—run sequentially or have the parent edit after both read-only reports land.

## Concurrency budget

Guidance for `/mat-subagents-spawn` (operator judgment; not a hard runtime enforcer):

| Guidance | Default |
|----------|---------|
| Max parallel **write** Tasks in one fan-out | **2–3** when path ownership is disjoint |
| Max parallel **read-only** Tasks (explore/scout/verify-style) | **3–4**; still prefer fewer if context overlap is high |
| Token cost | Roughly scales with worker count ([Cursor Subagents](https://cursor.com/docs/agent/subagents)); five parallel workers ≈ five contexts |
| Nesting | Prefer flat parent→children; do not design trees that require grandchildren to spawn further workers |
| Worktrees | Optional explicit isolation via `/mat-wt-create` / Agents Window / cloud — **Do not claim auto worktree-per-Task**; Cursor does not invent a worktree per Task by default |

If streams share mutable state or acceptance depends on another stream’s unfinished writes, **serialize**. Parallel speedup is a trap when ownership is unclear.

## Conflict and failure-mode handling

All outcomes below are **parent-mediated**. Workers do not coordinate via a shared task board or peer chat.

| Mode | Parent action |
|------|----------------|
| **Path conflict / concurrent write risk** | Stop or refuse the parallel spawn; re-decompose ownership or serialize. Do not “hope merge works.” |
| **Failed worker** | Consume the error/status from Task output; resume the **same** subagent with a narrow fix prompt once, or replace only after wait-before-supersede evidence of deadlock. Re-run verification after any rewrite. |
| **Abandoned work** | Treat silence after a reasonable startup window as unclear—not abandoned. Check progress signals; resume first. Mark abandoned only with clear non-progress; discard partial writes or re-assign ownership before spawning a replacement. |
| **Duplicate ownership** | Two streams claimed the same path class—halt integration; pick one writer, revert or quarantine the other stream’s edits, then re-verify. |
| **Handoff integration** | Parent merges accepted diffs, refreshes `docs/current-plan.md` markers as needed, ensures a single coherent `build-result.md` / (parent-serialized) `verify-result.md` for the slice. MAO stays the three-todo phase model—not a multi-row backlog of peer tasks. |

## Honesty guardrails (non-negotiable)

- **Do not** claim subagents “ran” or “completed” unless **Task** (or equivalent) actually executed and you consumed its output.
- **Do not** claim **live authoritative Cursor todo** state, **dashboard todo parity**, or **hook-driven subagent spawn from live todos**—see [`docs/decision-record.md`](../../.mat/docs/decision-record.md), [`ROADMAP.md`](../../ROADMAP.md).
- **MAO** file handoffs (`docs/current-plan.md`, `build-result.md`, `verify-result.md`) stay canonical; Cursor To-dos follow [`docs/todo-orchestration.md`](../../.mat/docs/todo-orchestration-protocol.md) for **phase state per slice**, not a multi-row backlog.
- **Parent-mediated integration only** — **no peer task-board** semantics (Claude-style teammate messaging / shared live task lists are out of scope for MAT).
- **Do not claim auto worktree-per-Task.**

## Stop conditions

- Stop and report if parallel work **conflicts** on the same files without a merge plan.
- Stop if a **hard dependency** is missing (env, tool, branch).
- Stop if duplicate ownership is discovered mid-flight before claiming an integrated PASS.
- After integration, prefer a **verifier** pass on the combined change before claiming done.

## Related

- [`docs/architecture/agent-teams.md`](../../.mat/docs/agent-teams.md) — team composition + file-ownership matrix pointer.
- [`docs/guides/agents-window.md`](../../.mat/docs/guides/agents-window.md) — local / worktree / cloud / SSH tab mapping (files stay authoritative).
- [`mat-long-run.md`](mat-long-run.md) — queued multi-slice missions.
- [`mat-plan-team.md`](mat-plan-team.md) — single orchestrated cycle.
- [`mat-sprint.md`](mat-sprint.md) — one bounded slice with DoR/DoD.
