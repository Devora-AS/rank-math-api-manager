---
name: mat-preflight-gated
description: Layer 0 orchestrator — Phase A (advise-project-approach) → novelty-gate.json → Phase B (neuroarxiv) only when gate=novel_research_required AND G2 approved. Never auto-escalates. Planning-only; writes preflight artifacts under specs/<slug>/preflight/. Does not replace scout-report-suggest, /mat-prime, MAO handoffs, or auto-write docs/current-plan.md.
---

> **Planning-only — advisory Layer 0 orchestrator.** This skill sequences Phase A discovery → novelty gate → optional Phase B literature scan. It **never auto-escalates** to neuroarxiv. It does **not** write `docs/current-plan.md`, `build-result.md`, or `verify-result.md`. It does **not** start `/mat-plan-team`, builder, or verifier. Markdown handoffs and MAO gates stay authoritative.

# MAT Preflight Gated (Layer 0 orchestrator)

Combined wrapper that orchestrates **Phase A** (landscape discovery) and **Phase B** (bounded arXiv literature scan) with explicit gates. Discovery-first: Phase A completes before any neuroarxiv fan-out. Research-on-novelty only: Phase B runs **only** when the novelty gate is `novel_research_required` **and** the operator passes **G2** (human approval + cost confirmation).

**Design reference:** [`specs/mat-discovery-research-skills.md`](../../../.mat/docs/specs/mat-discovery-research-skills.md) · **Planning ladder:** [`docs/architecture/preflight-escalation-ladder.md`](../../../.mat/docs/preflight-escalation-ladder.md) (Layer 0 sits below Layer 1–3)

---

## Phase flow

```text
Operator invokes mat-preflight-gated for slug <slug>
    │
    ▼
Phase A — read and apply advise-project-approach protocol
    │  (by path reference — do not merge or duplicate full protocol)
    │  Delegate: .cursor/skills/advise-project-approach/SKILL.md
    │
    ▼
Write Phase A artifacts:
    specs/<slug>/preflight/landscape.md
    specs/<slug>/preflight/candidates.json   (when comparables exist)
    specs/<slug>/preflight/novelty-gate.json   (always)
    │
    ├─ existing_sufficient ──────────► hand off to /mat-plan (no neuroarxiv)
    ├─ integrate_and_extend ─────────► hand off to /mat-plan or /mat-plan-onboarding
    ├─ inconclusive ─────────────────► Open Decisions; operator chooses depth
    │
    └─ novel_research_required
           │
           ▼
       HARD STOP — request G2 approval + cost acknowledgment
       (never auto-escalate; never start Phase B in the same turn)
           │
           ▼  (only after explicit G2 in-thread)
Phase B — read and apply neuroarxiv protocol
    │  Delegate: .cursor/skills/neuroarxiv/SKILL.md
    │
    ▼
Write Phase B artifacts:
    specs/<slug>/preflight/arxiv-synthesis.md
    specs/<slug>/preflight/arxiv-papers.json
    │
    ▼
Emit handoff hints for /mat-plan (Relevant Files, Open Decisions)
    — NOT auto-written docs/current-plan.md
```

---

## Atomic skill delegation (by path — do not merge)

| Phase | Skill path | Responsibility |
|-------|------------|----------------|
| **A** | [`.cursor/skills/advise-project-approach/SKILL.md`](../advise-project-approach/SKILL.md) | Intake, comparables, cost framing, landscape artifacts, initial novelty gate |
| **B** | [`.cursor/skills/neuroarxiv/SKILL.md`](../neuroarxiv/SKILL.md) | G2-gated bounded arXiv scan, synthesis, paper metadata |

**Orchestrator rule:** Read each atomic skill and follow its protocol. Do **not** inline or duplicate the full advise or neuroarxiv workflows in this file. This skill owns **sequencing, gate enforcement, and handoff emission** only.

---

## Discovery-first checklist

Before writing `novelty-gate.json`, Phase A must complete (or explicitly defer items with reason in the gate file):

1. **G0** — Operator accepted Layer 0 preflight for this slug.
2. **Frame** — Goal, users, constraints, operating mode (pre/mid/post-build).
3. **Inspect** — Bounded read-only local evidence per advise skill.
4. **Landscape** — Comparables with inline citations; no star-ranking.
5. **Cost reality** — Prototype / launch / growth scenarios when pricing matters.
6. **Recommend** — Primary path, alternative, failure conditions.
7. **Gate decision** — Set enum and observable criteria (below).
8. **Write artifacts** — `landscape.md`, `candidates.json` (if applicable), `novelty-gate.json`.

Only after steps 1–8 may the orchestrator evaluate Phase B eligibility.

---

## Novelty gate enum

Recorded in **`specs/<slug>/preflight/novelty-gate.json`**.

| Value | Meaning | Next step |
|-------|---------|-----------|
| `existing_sufficient` | Repo, docs, or prior specs already cover the approach | Hand off to `/mat-plan` with bounded Relevant Files — **no neuroarxiv** |
| `integrate_and_extend` | Known pattern exists; integration/extension work, not greenfield research | Hand off to `/mat-plan` or `/mat-plan-onboarding` — **no neuroarxiv** |
| `novel_research_required` | All four observable criteria below are **true** | **HARD STOP** — request G2; Phase B allowed **only after G2** |
| `inconclusive` | Checklist incomplete, conflicting evidence, or criteria partially met | Record Open Decisions; **never auto-escalate** to neuroarxiv |

---

## Observable criteria for `novel_research_required`

All four must be **true** to set (or maintain) `novel_research_required`. Each is auditable in `novelty-gate.json`:

| # | Field | Observable signal |
|---|-------|-------------------|
| 1 | `closed_scope_denied` | Phase A intake explicitly rejects a closed-scope shortcut (e.g. "just use library X" without mechanism validation) — `true` with `closed_scope_denied_reason` string |
| 2 | `technical_mechanism_present` | Task requires choosing or validating a **technical mechanism** (algorithm, architecture pattern, protocol) — `true` with `mechanism_description` one-liner |
| 3 | `rework_cost_threshold_met` | Estimated cost of wrong approach exceeds preflight budget — `true` with operator-visible `rework_cost_estimate` |
| 4 | `cache_hit` | **Must be `false`** (or absent/stale cache slug) — no matching fresh entry in optional shared cache |

If any criterion is false or missing, gate **must not** be `novel_research_required` (use `integrate_and_extend`, `existing_sufficient`, or `inconclusive`).

### `novelty-gate.json` schema (normative)

```json
{
  "slug": "<slug>",
  "gate": "existing_sufficient | integrate_and_extend | novel_research_required | inconclusive",
  "generated_at": "<ISO-8601>",
  "closed_scope_denied": false,
  "closed_scope_denied_reason": null,
  "technical_mechanism_present": false,
  "mechanism_description": null,
  "rework_cost_threshold_met": false,
  "rework_cost_estimate": null,
  "cache_hit": false,
  "cache_slug": null,
  "cache_checked_at": null,
  "g2_approved": false,
  "g2_approved_at": null,
  "open_decisions": [],
  "deferred_checklist_items": []
}
```

Set `g2_approved: true` and `g2_approved_at` only after explicit in-thread G2 approval.

---

## G2 hard stop (Phase B gate)

**Never run neuroarxiv unless:**

1. `novelty-gate.json` → `gate` = `novel_research_required`, **and**
2. All four observable criteria are **true**, **and**
3. Operator sends in-thread **G2** approval including:
   - Consent to neuroarxiv Phase B for this slug
   - Explicit cost acknowledgment (≤8 paper reads, ≤3 arXiv categories, ≤4 parallel Task subagents)

**Denied by default.** If G2 is missing, respond with what G2 requires and **stop** — do not categorize, fetch, or spawn paper Tasks. **Never auto-escalate** from Phase A to Phase B in the same response.

Record G2 pass in `novelty-gate.json` (`g2_approved`, `g2_approved_at`). Hooks do not enforce G2.

---

## Optional shared cache (document only)

Duplicate-run suppression for criterion 4:

- **Path:** `specs/_research-cache/<topic-slug>.json`
- **TTL:** 30 days from `generated_at`
- **Purpose:** When a fresh cache hit exists for the topic slug, set `cache_hit: true` and gate **must not** be `novel_research_required`
- **Not CI-required** — advisory only; create directory on first use

---

## Artifact contract

All preflight outputs under **`specs/<slug>/preflight/`** (tracked, planning-adjacent — not MAO handoffs).

| File | Phase | When | Purpose |
|------|-------|------|---------|
| `landscape.md` | A | Always | Comparables, constraints, cost framing, discovery checklist |
| `candidates.json` | A | When comparables exist | Structured candidate list |
| `novelty-gate.json` | A | Always | Gate enum + observable criteria + G2 status |
| `arxiv-synthesis.md` | B | G2 + neuroarxiv run | Single converged recommendation |
| `arxiv-papers.json` | B | Same | Paper metadata; ≤8 entries |

Optional advisory logs: `artifacts/external-skills/<slug>-<date>.jsonl` (gitignored).

---

## Handoff to `/mat-plan` (hints only — not auto execution)

After Phase A (and Phase B when run), **emit handoff hints in chat and in `landscape.md` / synthesis sections** — do **not** auto-write:

- `docs/current-plan.md` (requires human approval **G6** per plan contract)
- `build-result.md` or `verify-result.md`
- Implementation code

**Include in handoff:**

- Recommended planning depth (`/mat-plan` vs `/mat-plan-onboarding`)
- **Open Decisions** for the planning artifact
- Bounded **Relevant Files** hints with `[new]` / `[existing]` prefixes
- Whether Phase B ran and key citations

Operator runs `/mat-plan` separately when ready.

---

## Never auto-escalate

| Rule | Enforcement |
|------|-------------|
| Phase A → Phase B | **Stop** after Phase A when gate = `novel_research_required`; request G2 |
| Gate = `inconclusive` | **Do not** start neuroarxiv; surface Open Decisions |
| Gate ≠ `novel_research_required` | **Do not** start neuroarxiv |
| G2 missing | **Hard stop** — no fetch, no Task subagents |
| Same-turn escalation | **Forbidden** — G2 must appear in a separate operator message |

---

## Boundaries — does not replace

| Surface | Role | This orchestrator |
|---------|------|-------------------|
| **`scout-report-suggest`** | In-repo bug/root-cause investigation | Does **not** replace — use scout for codebase questions |
| **`/mat-prime`** | Session context loader | Does **not** replace — use prime at session start |
| **`docs-scraper`** | Known URL → `ai_docs/` | Does **not** replace — use for vendor docs |
| **MAO / `/mat-plan-team`** | Execution orchestration | Does **not** replace — never holds live MAO authority |
| **`advise-project-approach`** | Phase A protocol | Delegates by path — does not merge |
| **`neuroarxiv`** | Phase B protocol | Delegates by path — does not merge |

Preflight may **cite** paths scout found or docs scraper saved. Each tool keeps a single primary job.

---

## MAT caps (Phase B — via neuroarxiv delegate)

| Cap | Limit |
|-----|-------|
| Paper reads | **≤8** |
| arXiv categories | **≤3** |
| Parallel read-only Task subagents | **≤4** |

Do not exceed without documented operator override in `novelty-gate.json`.

---

## Permission boundaries

**May:**

- Read and apply atomic skills by path reference
- Write preflight artifacts under `specs/<slug>/preflight/`
- Emit `/mat-plan` handoff hints in chat and preflight markdown

**Must not:**

- Auto-start Phase B or neuroarxiv without G2
- Write `docs/current-plan.md`, `build-result.md`, or `verify-result.md`
- Start `/mat-plan-team`, builder, verifier, or modify MAO todos
- Replace scout, mat-prime, or docs-scraper for their primary jobs
- Run mandatory external API calls in CI contexts

---

## Related MAT surfaces

- [`advise-project-approach`](../advise-project-approach/SKILL.md) — Phase A delegate
- [`neuroarxiv`](../neuroarxiv/SKILL.md) — Phase B delegate
- [`mat-plan-contract`](../mat-plan-contract/SKILL.md) — tier selection, G6 projection
- [`specs/mat-discovery-research-skills.md`](../../../.mat/docs/specs/mat-discovery-research-skills.md) — full Layer 0 design, G0–G7 gates
- [`.cursor/commands/mat-plan.md`](../../commands/mat-plan.md) — planning entry after preflight
