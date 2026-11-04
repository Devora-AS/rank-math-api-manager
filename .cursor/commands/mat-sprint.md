# MAT Sprint

Run one bounded implementation slice end-to-end in the current session.

## Usage

```
/mat-sprint <task description>
```

## Instructions

**Plan contract skill:** For lite-tier execution shape, amendments, and status markers, see [`.cursor/skills/mat-plan-contract/SKILL.md`](../skills/mat-plan-contract/SKILL.md) (does not replace this command).

You are running a lightweight sprint for a single slice of work. Keep the scope narrow enough to finish with verification in one session.

### Preflight decision

Before editing, classify the slice with a short rationale:

- `inline` — use when the change is small enough to complete honestly in the current session without delegated implementation.
- `builder_plus_verifier` — use when independent implementation plus verification adds clarity for one bounded slice.
- `parallel_spawn` — use only when multiple non-overlapping tasks justify parallel subagents.

Default to `inline` for small local work. Do not force subagent spawning when inline execution is the more honest fit.

**Preflight escalation:** execution-mode layer — [`docs/architecture/preflight-escalation-ladder.md`](../../.mat/docs/preflight-escalation-ladder.md).

After each major sprint phase below, print **exactly one** recommended next command in a fenced `txt` block. Do not list multiple equally-weighted options — pick the honest branch and one command. Reference: [`docs/guides/planning-commands-guide.md`](../../.mat/docs/guides/planning-commands-guide.md#recommended-next-command-execution-commands).

### Closeout — DoR satisfied

When definition of ready is satisfied (bounded slice, binary criteria listed):

```txt
# Implement the smallest coherent change for this slice — gather only needed paths; do not expand scope mid-sprint
```

### Closeout — Implement complete

When implementation satisfies the success criteria on disk:

```txt
# Verify — run the most relevant repo-native checks (tests, lint, build, or documented manual review) before review pass
```

### Closeout — Verify complete

When verification evidence is recorded:

```txt
# Review pass — check regressions, docs drift, missing tests; note residual risk before sprint summary
```

### Closeout — Sprint review complete

When review is done and the sprint is ready to close:

```txt
# Sprint complete — summarize what changed, how it was verified, and any follow-up work; do not commit unless explicitly requested
```

### Execution plan shape (lite tier)

When the sprint writes or updates `docs/current-plan.md`, include a final **`## Amendments`** section (append-only `- YYYY-MM-DDTHH:MM:SSZ — role — summary` per [`docs/architecture/plan-contract.md`](../../.mat/docs/plan-contract.md)). Operator/parent may append during the sprint; builder may append during active build for scope drift (cite the triggering criterion); verifier read-only.

Apply **Tier 2b validation-loop discipline** to the execution projection: under `## Verification plan`, retain a `### Per-phase validation loops (loop until pass)` table with concrete repo-native commands and a `### Global validation commands (before handoff)` numbered list. Fix and re-run each phase until green, then run the global list before handoff. This is execution guidance; Markdown remains authoritative and the sprint does not create or require a living HTML plan. Use [`docs/templates/adoption-minimal-current-plan.md`](../../.mat/docs/templates/adoption-minimal-current-plan.md) for the lite shape and [`docs/templates/execution-plan-template.md`](../../.mat/docs/templates/execution-plan-template.md) when the slice escalates to standard.

**Optional Plan metadata:** Operator/parent **may** append optional `## Plan metadata` with append-only `### modified` / `### session` / `### commit` bullets (one line per projection or session milestone). **Not** YAML frontmatter; complements `docs/session-summary.md` — hooks **do not** auto-write metadata. Builder/verifier read-only.

**Lite-tier marker checklists:** Use contract status markers on implementation and acceptance checklists: `- []` idle · `- [wip]` in progress · `- [x]` done · `- [f]` failed/blocked. Builder mutates in-place during the sprint; markers are advisory — verification gates stay on handoff artifacts when orchestrated. See [`docs/architecture/plan-contract.md`](../../.mat/docs/plan-contract.md).

### Workflow

1. Define a short DoR before editing:
   - confirm the slice is bounded
   - confirm it is implementable with current repo/runtime constraints
   - list 2-4 binary success criteria
2. Gather only the code and docs needed for this slice.
3. Implement the smallest coherent change that satisfies the success criteria.
4. Verify the result with the most relevant commands or direct checks.
5. Do a review pass for regressions, docs drift, and missing tests.
6. Summarize what changed, how it was verified, and any residual risk.

### Defaults

- Prefer the current workspace over creating worktrees unless isolation is clearly needed.
- Use subagents only when the slice is substantial enough to benefit from an independent review or isolated investigation.
- Keep context **bounded**: load only files needed for the slice; prefer `docs/current-plan.md` (if present), diffs, and targeted reads over default-loading `README.md`, `ROADMAP.md`, `AGENTS.md`, or the full `docs/` tree. See [`docs/reference/context-budget-policy.md`](../../.mat/docs/context-budget-policy.md) and [`docs/reference/model-routing-policy.md`](../../.mat/docs/model-routing-policy.md) (cheapest honest tier; no habitual `strong`).
- Update nearby docs when behavior or operator guidance changes.
- Do not expand the scope mid-sprint; note follow-up work instead.

### Onboarding slice sync

If the sprint slice comes from an approved onboarding package, the projected `docs/current-plan.md` must carry the matching `TASK-###`, and the parent must keep the corresponding `tasks.json` status synchronized with the active slice:
- `planned` before the slice starts
- `in_progress` while the slice is active
- `done` after verification and completion
- `blocked` or `deferred` with a short note when execution stops for a real blocker or operator decision

If no onboarding package exists, keep the current sprint behavior unchanged.

### Verification Expectations

- Run at least one concrete verification step before claiming completion.
- Prefer repo-native checks (`python3 -m unittest ...`, `bun test`, `bun run build`, `git diff --check`) when applicable.
- If no automated check makes sense, say what you reviewed manually and why that is sufficient.
- If the slice touches hooks, validators, artifact parsing, MAO transitions, or security-sensitive pilot logic, do not close out on vague or purely smoke-style verification: add targeted regression coverage or record an explicit documented exception.
- For local-app pilots, manual/staging is the default baseline unless deterministic local automation already exists in the target repo. Browser-use and Playwright are ladder tools, not implied defaults.

### Guardrails

- Do not commit unless the user explicitly asks for a commit or the sprint task explicitly includes it.
- Stop and report if you hit a real blocker, risky ambiguity, or unexpected repo changes you did not make.
- Keep the final answer concise unless the user asked for a detailed writeup.
