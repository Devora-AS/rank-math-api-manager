# MAT Long Run

Run a **queued, multi-slice** mission in one parent-orchestrated session without confusing **slice complete** with **mission complete**.

## Usage

```
/mat-long-run <mission description>
```

The parent must treat this as a **long-run contract** run: mission state lives in [`docs/architecture/long-run-state.md`](../../.mat/docs/long-run-state.md); each slice still uses `docs/current-plan.md` → `build-result.md` → `verify-result.md`.

The canonical handoff contract for `build-result.md` and `verify-result.md` lives in [`docs/reference/workflow-artifact-contract.md`](../../.mat/docs/workflow-artifact-contract.md). Use that contract when describing or validating slice artifacts.

---

**Plan contract skill:** For standard-tier execution projection, amendments, and status markers across slices, see [`.cursor/skills/mat-plan-contract/SKILL.md`](../skills/mat-plan-contract/SKILL.md) (does not replace this command).

**Advisor-strategy alternative:** When a high-context advisor session owns audit/closeout and slices run in parallel separate agent chats (instead of one continuous parent long-run), see [`docs/guides/mat-advisor-strategy-runbook.md`](../../.mat/docs/guides/mat-advisor-strategy-runbook.md). Mission file handoffs remain canonical either way.

## Purpose

- **Canonical entrypoint** for large missions that need **several** plan → build → verify cycles.
- Keep **file-based MAO truth** and **parent-owned transition checks** exactly as in [`docs/todo-orchestration.md`](../../.mat/docs/todo-orchestration-protocol.md).
- Use **MAO todos only for phase state** (`[mao:plan]`, `[mao:build]`, `[mao:validate]`) for the **current slice**—never as a multi-row backlog.

When you draft parent/advisor prompts or copied snippets for this command, default to copy-pasteable fenced `txt` blocks unless the user asks for another format.

After each major phase below (per active slice), print **exactly one** recommended next command in a fenced `txt` block. Do not list multiple equally-weighted options — pick the honest branch and one command. Reference implementations: [`.cursor/commands/mat-sync.md`](mat-sync.md), [`.cursor/commands/mat-update-mat.md`](mat-update-mat.md); operator guide: [`docs/guides/planning-commands-guide.md`](../../.mat/docs/guides/planning-commands-guide.md#recommended-next-command-execution-commands).

### Closeout — Plan written complete

When the active slice plan is in `docs/current-plan.md` and the plan→build transition check passes:

```txt
Task subagent_type=builder for the active slice — hand off docs/current-plan.md; wait for build-result.md before build→validate gate
```

### Closeout — Build gate passed

When `build-result.md` for the active slice passes the build→validate transition check:

```txt
Task subagent_type=verifier with docs/current-plan.md and build-result.md — wait for verify-result.md before post-slice mission gate
```

### Closeout — Verify complete

When `verify-result.md` shows PASS for the active slice, proceed to the post-slice mission gate (do not declare mission complete from slice PASS alone):

```txt
# Run post-slice mission gate — answer queue, mission goal, and stop-reason checklist in docs/architecture/long-run-state.md
```

### Closeout — Mission gate continue

When the mission gate says **continue** and another slice is queued:

```txt
# Advance active slice in docs/architecture/long-run-state.md; write fresh docs/current-plan.md for next slice; reset MAO plan phase and start new plan → build → verify cycle
```

### Closeout — Mission gate stop

When the mission gate says **stop** (any classified stop reason):

```txt
# Update docs/architecture/long-run-state.md stop reason; write docs/session-summary.md; report classified stop to operator
```

---

## Relationship to other commands

| Command | Use when |
|---------|----------|
| `/mat-sprint` | **One** bounded slice end-to-end (single DoR → implement → verify → review). |
| `/mat-plan-team` | **One** full orchestrated plan → build → verify cycle (or narrow tasks that fit that single cycle). Not the default entrypoint for **queued multi-slice** missions unless you also maintain [`docs/architecture/long-run-state.md`](../../.mat/docs/long-run-state.md) and follow the parent **long-run** + **mission gate** rules in [`.cursor/agents/parent-orchestrator.md`](../agents/parent-orchestrator.md). |
| `/mat-long-run` | **Multiple** ordered slices with explicit **mission state**, **continuation rules**, and **post-slice mission gate**. |

---

## Preflight decision

Before new work starts, classify the active slice in [`docs/architecture/long-run-state.md`](../../.mat/docs/long-run-state.md):

- `execution_mode: inline`
- `execution_mode: builder_plus_verifier`
- `execution_mode: parallel_spawn`
- `execution_rationale: <one-line why this mode is the honest fit for this slice>`

Use the lightest mode that still matches the work. Do not treat `parallel_spawn` as the default, and do not let an execution-mode label override the canonical file-based MAO checks.

**Preflight escalation:** multi-slice vs single-cycle routing — [`docs/architecture/preflight-escalation-ladder.md`](../../.mat/docs/preflight-escalation-ladder.md).

**Planning Step 0 vs execution Step 0:** `/mat-plan` and `/mat-plan-onboarding` require deep analysis before any planning artifact writes; this command's Preflight decision and startup workflow Step 0 address orchestration — not planning deep analysis.

---

## Startup workflow

1. **Restate** the mission and confirm it truly needs **more than one** slice; otherwise use `/mat-sprint` or `/mat-plan-team`.
2. **Record a preflight decision** for the active slice: bounded scope, chosen `execution_mode`, and a one-line rationale.
3. **Initialize** [`docs/architecture/long-run-state.md`](../../.mat/docs/long-run-state.md) **before** the first builder dispatch: mission, constraints, ordered slice queue, continuation policy, stop-reason policy, and the active-slice `execution_mode` / `execution_rationale` preflight.
4. **Loop manifest (opt-in):** When **`CURSOR_MAT_LOOP_POLICY=1`**, initialize `artifacts/loop/manifest.json` for the **active slice** before the first builder dispatch (`run_id`, `slice_id`, `slice_class`, zeroed counters). See [`docs/reference/loop-policy.md`](../../.mat/docs/loop-policy.md) and parent Step 2b in [`.cursor/agents/parent-orchestrator.md`](../agents/parent-orchestrator.md). Re-initialize the manifest when advancing to the next queued slice.
5. **Sync MAO todos** (`TodoWrite`): three canonical tasks per [`docs/todo-orchestration.md`](../../.mat/docs/todo-orchestration-protocol.md).
6. **Populate** `docs/current-plan.md` **only** from the **active** queued slice (substantive plan handoff—not the whole mission essay). Each substantive slice plan includes append-only `## Amendments` per [`docs/architecture/plan-contract.md`](../../.mat/docs/plan-contract.md); append across slices rather than rewriting history. When replacing `docs/current-plan.md` for the next slice, archive prior slice context in [`docs/architecture/long-run-state.md`](../../.mat/docs/long-run-state.md) (completed-slice notes or queue row evidence)—do not rely on amendments alone for cross-slice mission memory. **Optional `## Plan metadata`:** parent/operator **may** append one line per projection, session start, or merge milestone under `### modified` / `### session` / `### commit` (append-only lists; **not** YAML frontmatter). Complements `docs/session-summary.md` and MAO advisory events — does not replace them; hooks **do not** auto-write metadata. **Lite/standard execution checklists** in `docs/current-plan.md` use contract status markers (`[]`, `[wip]`, `[x]`, `[f]`) per plan-contract Slice 3; markers are advisory — slice gates remain on handoff files.
7. Run **plan → build → verify** for that slice (same steps as `/mat-plan-team` regarding transitions, gate advisory files, subagent prompts, and optional loop policy evaluate after each builder return when `CURSOR_MAT_LOOP_POLICY=1`).

If the active slice comes from an approved onboarding package, carry its matching `TASK-###` into `docs/current-plan.md` and keep `specs/<slug>/tasks.json` synchronized as the slice moves through `planned` → `in_progress` → `done` or `blocked`/`deferred`.

---

## Required artifacts

| Artifact | Role |
|----------|------|
| [`docs/architecture/long-run-state.md`](../../.mat/docs/long-run-state.md) | Mission goal, queue, active slice pointer, completed slices, continuation/stop policy. |
| `docs/current-plan.md` | **Active slice only** — acceptance criteria and handoff for builder/verifier. |
| `build-result.md` | Builder output for the **current** slice. |
| `verify-result.md` | Verifier output for the **current** slice. |
| `docs/session-summary.md` | Written when the mission **ends** (see mission gate). |
| `specs/<slug>/tasks.json` | Optional onboarding package status mirror for the active slice (`TASK-###` mapping and parent-owned execution progress). |

---

## Ordered slice loop

For each slice, in order:

1. Ensure [`docs/architecture/long-run-state.md`](../../.mat/docs/long-run-state.md) names the **active slice** and matches `docs/current-plan.md`.
2. When **`CURSOR_MAT_LOOP_POLICY=1`**, ensure `artifacts/loop/manifest.json` matches the active slice (`slice_id`, `slice_class`) before builder dispatch; re-init when advancing slices.
3. Complete **Step 1–4** of the parent orchestration sequence (plan → builder → optional loop policy evaluate → build gate → verifier).
4. On verifier **PASS**, run the **post-slice mission gate** (below)—do **not** jump to “mission done” from slice PASS alone.
5. If the gate says **continue**: advance the queue, write a fresh `docs/current-plan.md` for the next slice, and start a **new** MAO cycle for that slice (treat plan phase as active again per protocol).
6. If the gate says **stop**: classify stop reason, update long-run state, write `docs/session-summary.md`, report to the user.

When a queued slice originated from an onboarding package, keep the active-slice `TASK-###` marker in both `docs/current-plan.md` and `docs/long-run-state.md` so the parent can update the matching `tasks.json` entry without inventing a second source of truth.

---

## Post-slice mission gate (mandatory after each verifier PASS)

Complete the **Parent mission gate compliance** checklist in [`docs/architecture/long-run-state.md`](../../.mat/docs/long-run-state.md) when that file governs the mission (hooks do **not** enforce it — see checklist honesty note there).

Answer **all** of these before declaring the mission or session complete:

1. **Evidence:** Does `verify-result.md` show **PASS** for the active slice with acceptable evidence?
2. **Queue:** Are there **remaining slices** in the ordered queue?
3. **Mission goal:** If the queue is empty, is the **mission goal** actually satisfied?
4. **Stop reason:** If stopping, which single **primary** reason applies: `mission_complete`, `hard_blocker`, `approval_needed`, `planning_gap`, or `unexpected_termination`?
5. **Honesty:** Am I about to claim **mission success** when only a **slice** passed?

**Run manifest closeout (N4, opt-in):** When **`CURSOR_MAT_RUN_MANIFEST=1`** (see `.mat.env.sample`; default off), after verify PASS write the advisory manifest before advancing the queue or stopping:

```txt
python3 scripts/mat_run_manifest.py closeout-write \
  --repo-root . \
  --mission-slug <mission_slug> \
  --slice-id <active_slice_id>
```

Optional: `python3 scripts/mat_run_manifest.py check --run-id <run_id>`. Stale hash mismatch is advisory only (`gate_impact: none`) — it must not fail verify or override handoff gates.

**Failure mode to avoid:** Verifier PASS for slice 1 while slice 2 is still queued → **continue** or **stop with explicit reason**, but **not** “session successfully completed” for the whole mission.

---

## Stop conditions

Stop and report (with a classified **stop reason** in [`docs/architecture/long-run-state.md`](../../.mat/docs/long-run-state.md) and `docs/session-summary.md`) when:

- **`mission_complete`** — Goal satisfied and no further slices are required (or remaining rows are explicitly skipped with rationale).
- **`hard_blocker`** — Cannot proceed (dependency, environment, repeated builder/verifier failure after retries).
- **`approval_needed`** — Human decision required before continuing.
- **`planning_gap`** — No next slice is defined **and** the mission is not complete, or the queue is empty with work remaining. **Do not** label this as normal mission success.
- **`unexpected_termination`** — Abnormal end; record partial state.

---

## Guardrails

- Do **not** claim autonomous continuation outside the parent-owned file contract; the parent still drives each slice.
- Do **not** use Cursor todos as authoritative multi-slice state; **files** are canonical.
- Do **not** weaken parent-owned plan → build → validate checks.
- Preserve **wait-before-supersede** discipline for builder and verifier startup ([`.cursor/agents/parent-orchestrator.md`](../agents/parent-orchestrator.md)).
- **Context and cost:** Each slice should stay **bounded** — populate `docs/current-plan.md` from the active queue row only; prefer handoff files and touched paths over mega-doc dumps or transcript replay ([`docs/reference/context-budget-policy.md`](../../.mat/docs/context-budget-policy.md)). Use the lightest honest `execution_mode` per slice; avoid extra fan-out without cause. Tier choice follows [`docs/reference/model-routing-policy.md`](../../.mat/docs/model-routing-policy.md) (advisory notes; not habitual `strong`).
- For the final execution handoff, follow [`docs/orchestration-workflow.md#execution-closeout-contract`](../../.mat/docs/orchestration-workflow.md#execution-closeout-contract).

---

## Notes

- Markdown-first mission state keeps parity with the rest of the repo handoff model; optional machine-readable companions are a future decision ([`ROADMAP.md`](../../ROADMAP.md)).
- Hooks, `artifacts/mao/gate.json`, and observability remain **advisory**; they do not replace explicit parent checks.
- Operators using Cursor Agents Window (local / worktree / cloud / SSH tabs): follow [`docs/guides/agents-window.md`](../../.mat/docs/guides/agents-window.md) — window state is never acceptance truth.
