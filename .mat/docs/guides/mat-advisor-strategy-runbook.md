# MAT advisor-strategy operator runbook

- **Purpose:** Formalize the **parent-advisor** pattern: one high-context advisor session owns audit, closeout, and roadmap sequencing; the operator runs copy-paste `/mat-plan-team` or `/mat-long-run` prompts in **parallel separate agent sessions** and pastes slice summaries back before the next slice.
- **Audience:** Maintainers running multi-slice orchestration on the MAT source repo (or adopted trees with the same handoff contract).
- **Status:** complete
- **Last updated:** 2026-08-10

## Related files

- [`docs/guides/planning-commands-guide.md`](planning-commands-guide.md) — command routing (`/mat-plan` → execution); Layer 0 [`/mat-preflight-research`](../../.cursor/commands/mat-preflight-research.md) optional before planning
- [`docs/architecture/preflight-escalation-ladder.md`](../preflight-escalation-ladder.md) — planning depth vs execution mode
- [`.cursor/commands/mat-preflight-research.md`](../../.cursor/commands/mat-preflight-research.md) — Layer 0 discoverability entry (delegates to `mat-preflight-gated`)
- [`.cursor/agents/parent-orchestrator.md`](../../.cursor/agents/parent-orchestrator.md) — parent sequencing and mission gate
- [`.cursor/commands/mat-long-run.md`](../../.cursor/commands/mat-long-run.md) — queued multi-slice entry
- [`docs/architecture/long-run-state.md`](../long-run-state.md) — mission queue (when used)
- [`docs/reference/workflow-artifact-contract.md`](../workflow-artifact-contract.md) — handoff shape + optional Trace Correlation
- [`docs/reference/todo-orchestration.md`](../todo-orchestration-protocol.md) — MAO file handoffs
- [`docs/guides/mat-prompt-templates.md`](mat-prompt-templates.md) — advisory copy-paste builder/verifier/advisor prompts

Canonical practice also appears in `AGENTS.md` **Learned User Preferences** (parent-advisor parallel sessions). This runbook is the operator-facing expansion of that preference.

---

## When to use advisor + parallel sessions vs single-parent `/mat-long-run`

| Pattern | Use when | Avoid when |
|---------|----------|------------|
| **Advisor + parallel sessions** | Substantive orchestration / roadmap missions where the advisor holds audit history, ROADMAP sequencing, and closeout; each slice runs in a **fresh** Composer session with a copy-paste prompt; operator pastes summaries back | Tiny single-file edits; one bounded `/mat-sprint` |
| **Single parent `/mat-long-run`** | One continuous parent session can honestly drive the full queue (mission state in `long-run-state.md`, post-slice gate, fresh MAO cycle per slice) without context rot | Advisor context is already huge and you need cheaper delegated execution chats |
| **Single `/mat-plan-team`** | Exactly **one** plan → build → verify cycle | Multi-slice missions (use long-run or advisor+parallel) |

**Default preference for substantive orchestration slices:** Session 1 planning (`/mat-plan` or mission spec) → advisor audit/closeout → fresh Session 2+ execution (`/mat-plan-team` or `/mat-long-run` Slice *N* with `builder_plus_verifier`). Queued multi-slice missions **may** run all slices in one parent `/mat-long-run` when the mission spec requires it.

**Honesty:** Parallel sessions do **not** create a second orchestration authority. File handoffs (`docs/current-plan.md`, `build-result.md`, `verify-result.md`, and `long-run-state.md` when applicable) remain canonical. MAO todos stay the three-phase model for the **active** slice only.

---

## Command relationship (`/mat-plan` → `/mat-plan-team` → `/mat-long-run`)

1. **Plan** — optional Layer 0 [`/mat-preflight-research`](../../.cursor/commands/mat-preflight-research.md) when landscape is unclear; then `/mat-plan` (or `/mat-plan-onboarding` / `/mat-plan-update`) writes planning truth under `specs/`.
2. **Project** — After human approval, project one slice into `docs/current-plan.md`.
3. **Execute one cycle** — `/mat-plan-team` (or `/mat-sprint` when truly small).
4. **Execute a queue** — `/mat-long-run` with ordered slices in `docs/architecture/long-run-state.md`, **or** advisor-driven parallel sessions that each run one `/mat-plan-team` (or one long-run slice) and return summaries.

See [`planning-commands-guide.md`](planning-commands-guide.md) and [`preflight-escalation-ladder.md`](../preflight-escalation-ladder.md) for depth/mode routing. Do not collapse planning preflight terms with execution modes.

---

## Paste-back checklist (after each parallel `/mat-plan-team`)

Return the following to the **advisor** session before starting the next slice. Prefer short bullets over transcript dumps.

- [ ] **Slice id / mission pointer** — queue row or ROADMAP item name
- [ ] **Status** — verifier PASS / FAIL / PARTIAL (cite `verify-result.md`)
- [ ] **Handoff paths** — confirm `docs/current-plan.md`, `build-result.md`, `verify-result.md` for this slice
- [ ] **Preflight artifacts** — when Layer 0 ran: `specs/<slug>/preflight/` paths reviewed (`landscape.md`, `novelty-gate.json`; Phase B files only if G2 approved)
- [ ] **Acceptance summary** — which ACs passed; any FAIL/PARTIAL with one-line reason
- [ ] **Files changed** — short list from `build-result.md` (paths only)
- [ ] **Validation** — `phase1-verify.sh` (or plan-named gate) exit status
- [ ] **Git** — committed locally? commit SHA if yes; **push status** (default: not pushed)
- [ ] **Long-run** — if `long-run-state.md` applies: mission gate answer (**continue** / **stop** + reason)
- [ ] **Trace Correlation** — optional IDs from handoffs if present (see below)
- [ ] **Blockers / decisions needed** — anything requiring advisor or operator approval

Example paste-back shape:

```txt
Slice: mat-advisor-strategy-runbook — verify PASS
Handoffs: docs/current-plan.md, build-result.md, verify-result.md
Gate: phase1-verify.sh exit 0
Git: local commit pending / <sha> — not pushed
Mission gate: continue (slice 3 queued)
Open: none
```

---

## Closeout / commit / push rules

- **Do not `git push`** unless the operator explicitly asks.
- **Do not `git commit`** unless the operator asks, **or** the active mission/long-run continuation policy authorizes parent closeout commits after verifier PASS (still no push by default).
- Advisor owns **audit/closeout narrative** (ROADMAP/spec alignment, scope hygiene, re-verify gates) even when a parallel execution session did the build/verify work.
- Slice PASS ≠ mission success when more queue rows remain — run the post-slice mission gate in [`long-run-state.md`](../long-run-state.md) / [`mat-long-run`](../../.cursor/commands/mat-long-run.md).
- Keep continual-learning `AGENTS.md` edits out of slice commits unless the operator explicitly includes them.

---

## Trace Correlation (optional multi-session tip)

Optional `## Trace Correlation` on `build-result.md` / `verify-result.md` can carry best-effort `session_id`, `conversation_id`, `trace_run_id`, `subagent_id`, and `parent_session_note` when those values are actually visible. Use them when pasting back to the advisor so multi-session work correlates without replaying full transcripts.

- **Omit** the section or individual fields when unknown — never invent IDs.
- **Never** a MAO gate requirement — absence is valid.
- Contract: [`docs/reference/workflow-artifact-contract.md`](../workflow-artifact-contract.md) (Optional Trace Correlation).

---

## Explicit non-goals

This runbook does **not**:

- Add hook auto-spawn of parallel sessions or subagents from live todo state
- Claim MAO live Cursor-todo parity or dashboard todo authority
- Replace file handoffs with chat paste as orchestration truth
- Ship a cloud agents / SDK operator runbook (separate ROADMAP item)
- Auto-inject prompts via hooks (use advisory copy-paste templates instead — [`mat-prompt-templates.md`](mat-prompt-templates.md))
- Ship task-type / complexity tags (separate ROADMAP / later slice)

Hooks, `artifacts/mao/gate.json`, and observability remain **advisory**. Parent-owned transition checks stay mandatory.

---

## Quick start (operator)

1. Keep the **advisor** chat for sequencing, audit, and paste-back review.
2. Copy one bounded execution prompt into a **fresh** agent session (`/mat-plan-team` or `/mat-long-run` active slice).
3. Wait for `verify-result.md` PASS (and mission gate if long-run).
4. Paste the checklist summary back to the advisor (optional skeleton: [`prompt-advisor-pasteback.txt`](../templates/prompt-advisor-pasteback.txt)).
5. Only then advance ROADMAP / `long-run-state.md` / next-slice plan projection.
