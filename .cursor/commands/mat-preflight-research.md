# MAT Preflight Research

Layer 0 **planning-only** preflight — external landscape discovery and optional G2-gated literature scan **before** `/mat-plan` or `/mat-plan-onboarding`.

## Usage

```
/mat-preflight-research <task or slug description>
```

## Instructions

You are a **thin hybrid command**. **Read and follow** the combined orchestrator skill at [`.cursor/skills/mat-preflight-gated/SKILL.md`](../skills/mat-preflight-gated/SKILL.md). **Do not inline** or duplicate the full advise-project-approach or neuroarxiv protocols in this command — delegate by path reference only.

### Workflow

1. **Restate** the task and choose a planning slug (`<slug>`) for `specs/<slug>/preflight/` artifacts.
2. **Read** [`.cursor/skills/mat-preflight-gated/SKILL.md`](../skills/mat-preflight-gated/SKILL.md) and apply its Phase A → novelty gate → optional Phase B sequence.
3. **Phase A** — delegate to [`.cursor/skills/advise-project-approach/SKILL.md`](../skills/advise-project-approach/SKILL.md) by path; write `landscape.md`, `candidates.json` (when applicable), and `novelty-gate.json`.
4. **Gate** — if `novel_research_required`, **hard stop** and request **G2** (human approval + cost acknowledgment). **Never auto-escalate** to Phase B in the same turn.
5. **Phase B** (G2 approved only) — delegate to [`.cursor/skills/neuroarxiv/SKILL.md`](../skills/neuroarxiv/SKILL.md) by path; write `arxiv-synthesis.md` and `arxiv-papers.json`.
6. **Hand off** — emit `/mat-plan` or `/mat-plan-onboarding` hints (Relevant Files, Open Decisions). Do **not** auto-write `docs/current-plan.md`.

### Guardrails

- **Planning-only** — advisory Layer 0; file handoffs (`docs/current-plan.md` → `build-result.md` → `verify-result.md`) stay authoritative.
- **Never auto-escalate** — Phase B requires explicit in-thread G2; denied by default.
- **Does not** start `/mat-plan-team`, builder, verifier, or MAO cycles.
- **Does not** replace `scout-report-suggest` (in-repo investigation), `/mat-prime` (session priming), or `docs-scraper` (known URL capture).
- **Does not** write `build-result.md` or `verify-result.md`.

### Related

- Design spec: [`specs/mat-discovery-research-skills.md`](../../.mat/docs/specs/mat-discovery-research-skills.md)
- Operator map: [`docs/guides/planning-commands-guide.md`](../../.mat/docs/guides/planning-commands-guide.md#layer-0-preflight-research)
- Planning ladder: [`docs/architecture/preflight-escalation-ladder.md`](../../.mat/docs/preflight-escalation-ladder.md)
