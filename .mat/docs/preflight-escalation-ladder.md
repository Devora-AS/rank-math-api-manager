# Preflight escalation ladder

**Status:** Operator reference — planning depth, command depth, and execution mode are **separate layers** (see [`specs/shared-plan-contract.md`](specs/shared-plan-contract.md) Decision H).

**Canonical home** for when to escalate across MAT planning and execution entrypoints. Pair with [`docs/guides/planning-commands-guide.md`](../guides/planning-commands-guide.md) for procedural routing.

---

## Do not collapse vocabulary

Planning preflight terms and execution preflight terms answer **different questions**. Never substitute one layer for another.

| Wrong collapse | Why it fails |
|----------------|--------------|
| `ready_for_execution_handoff` → `builder_plus_verifier` | Planning readiness ≠ delegation choice |
| `solo_plan_only` → `inline` | Planning depth ≠ execution mode |
| `needs_plan_onboarding` → `/mat-long-run` | Heavy planning ≠ multi-slice mission |

**Planning** classifies artifact depth before approval. **Execution** classifies how the parent runs one approved slice. **Long-run** queues multiple slices — it is not a planning preflight term.

---

## Layer 1 — Planning depth (`/mat-plan` preflight)

Place one classification near the top of `specs/<slug>.md`:

| Term | Meaning | Escalate when |
|------|---------|---------------|
| `solo_plan_only` | Bounded; single `specs/<slug>.md` is enough | Scope grows fuzzy, cross-functional, or trace-heavy → `needs_plan_onboarding` |
| `ready_for_execution_handoff` | Lightweight plan approved; human may project into `docs/current-plan.md` | Operator approves → projection + execution command (Layer 3) |
| `needs_plan_onboarding` | Requires four-file package + `tasks.json` | Use `/mat-plan-onboarding` instead of expanding solo plan |

**Command:** [`/mat-plan`](../../.cursor/commands/mat-plan.md)

---

## Layer 2 — Command depth (planning entrypoint)

| Step | Command | Output | Next when insufficient |
|------|---------|--------|------------------------|
| 1 | `/mat-plan` | `specs/<slug>.md` | Fuzzy scope, PRD/spec split, traceable tasks → step 2 |
| 2 | `/mat-plan-onboarding` | `specs/<slug>/` package | After human approval → step 4 |
| 3 | `/mat-plan-update` | Amended planning artifact (`specs/<slug>.md` or package file) | Structural/traceability drift → step 2 or fresh `/mat-plan`; active execution → re-project before Layer 3 |
| 4 | Human projection | `docs/current-plan.md` | Choose execution command (Layer 3) |

**Rules:**

- `specs/` is upstream planning truth; `docs/current-plan.md` is execution projection only.
- Do not replace `docs/current-plan.md` with onboarding artifacts — use `plan-summary.md` as bridge.
- Approval gate required before any execution handoff.

**Commands:** [`/mat-plan`](../../.cursor/commands/mat-plan.md), [`/mat-plan-onboarding`](../../.cursor/commands/mat-plan-onboarding.md), [`/mat-plan-update`](../../.cursor/commands/mat-plan-update.md)

---

## Layer 3 — Execution mode (per approved slice)

Recorded in `docs/current-plan.md` header and [`docs/architecture/long-run-state.md`](long-run-state.md) for long-run missions:

| Mode | Use when | Default? |
|------|----------|----------|
| `inline` | Small, honest single-session work; docs-only or narrow edits | Lightest fit — not “lazy” |
| `builder_plus_verifier` | Implementation + independent verification adds clarity | Normal for `/mat-plan-team` |
| `parallel_spawn` | Multiple non-overlapping tasks justify parallel subagents | Optional expansion only |

**Single-slice commands:**

| Command | When |
|---------|------|
| [`/mat-sprint`](../../.cursor/commands/mat-sprint.md) | One bounded slice: DoR → implement → verify → review |
| [`/mat-plan-team`](../../.cursor/commands/mat-plan-team.md) | One full plan → build → verify cycle |

**Multi-slice command:**

| Command | When |
|---------|------|
| [`/mat-long-run`](../../.cursor/commands/mat-long-run.md) | **Several** ordered slices with mission state in `long-run-state.md`, post-slice mission gate, and fresh MAO cycle per slice |

Use `/mat-long-run` when the mission needs **more than one** plan → build → verify cycle — not when a single `/mat-plan-team` cycle suffices.

**Honesty:** Execution mode does not weaken canonical file-based MAO checks (`docs/current-plan.md` → `build-result.md` → `verify-result.md`).

---

## Quick routing matrix

| Situation | Start | Escalate to |
|-----------|-------|-------------|
| Bounded feature, understood scope | `/mat-plan` (`solo_plan_only`) | `/mat-plan-onboarding` if traceability grows |
| Approved plan drifts slightly (living artifact) | `/mat-plan-update` (`surgical_amendment`) | `/mat-plan-onboarding` if package/traceability breaks; re-project `docs/current-plan.md` before resuming execution |
| Plan ready, one implementation cycle | Project → `/mat-plan-team` (`builder_plus_verifier`) | `/mat-sprint` if truly small and inline-honest |
| Three+ dependent slices in one mission | `/mat-long-run` + queue in `long-run-state.md` | Fresh session per major mission when context is stale |
| Adoption / existing project | `/mat-adopt` or `/mat-sync` | See adoption guides (outside this ladder’s planning layers) |

---

## Related docs

- [`docs/architecture/plan-contract.md`](plan-contract.md) — depth tiers, amendments, markers, truth hierarchy
- [`docs/guides/planning-commands-guide.md`](../guides/planning-commands-guide.md) — operator routing between planning commands
- [`.cursor/skills/mat-plan-contract/SKILL.md`](../../.cursor/skills/mat-plan-contract/SKILL.md) — procedural skill (pointer only; does not replace commands)
- [`docs/reference/todo-orchestration.md`](todo-orchestration-protocol.md) — MAO file handoffs during execution
