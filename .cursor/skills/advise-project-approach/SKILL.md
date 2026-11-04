---
name: advise-project-approach
description: Layer 0 preflight — research and advise on project approach (architecture, stack, comparables, cost scenarios) before /mat-plan. Use for greenfield strategy, mid-build course correction, or post-build review when the operator wants landscape discovery. Planning-only; writes preflight artifacts under specs/<slug>/preflight/. Does not replace scout-report-suggest, /mat-prime, docs-scraper, or MAO handoff gates.
---

> **Planning-only — advisory Layer 0 preflight.** This skill guides discovery before planning depth selection. It does **not** write `docs/current-plan.md`, `build-result.md`, or `verify-result.md`. It does **not** start `/mat-plan-team`, builder, or verifier. Markdown handoffs and MAO gates stay authoritative.

# Advise Project Approach (MAT)

MAT-native adaptation of the upstream **advise-project-approach** prompt protocol. Helps operators decide, validate, or improve how a project should be built: requirements framing, bounded repo inspection, credible comparables, stack/architecture options, and cost reality — **before** `/mat-plan`, `/mat-plan-onboarding`, or execution projection.

**Design reference:** [`specs/mat-discovery-research-skills.md`](../../../.mat/docs/specs/mat-discovery-research-skills.md) · **Planning ladder:** [`docs/architecture/preflight-escalation-ladder.md`](../../../.mat/docs/preflight-escalation-ladder.md) (Layer 0 sits below Layer 1–3)

---

## THIRD_PARTY — MIT

Portions adapted from advise-project-approach (MIT)

- Upstream: https://github.com/AaravKashyap12/advise-project-approach
- Pin: `88f1ecc` (v0.6.0 prompt-only reference)
- License: MIT (see upstream repository LICENSE)

MAT localized: Cursor skill paths, bounded `@file` reads, G3 community-research opt-in, preflight artifact contract, explicit boundaries vs scout / mat-prime / MAO gates. No Claude Agent SDK, no `npx skills@latest`, no upstream npm install.

---

## Purpose

Automate the research loop a strong engineer would do manually **before planning**:

1. Frame the project goal and constraints.
2. Inspect available local evidence (read-only).
3. Study credible comparables and primary documentation.
4. Evaluate stack/architecture choices with explicit tradeoffs.
5. Emit **tracked preflight artifacts** for `/mat-plan` handoff.

---

## When to use

- **Greenfield or unclear landscape** — build-vs-buy, stack selection, architecture direction before writing `specs/<slug>.md`
- **Mid-build course correction** — repo exists; compare intent vs implementation vs external references
- **Post-build review** — project mostly complete; architecture, cost, deployment, and gap analysis vs mature comparables
- Operator explicitly invokes Layer 0 preflight or `@advise-project-approach` before planning commands

---

## When NOT to use

| Surface | Use instead |
|---------|-------------|
| In-repo bugs, regressions, "where is X?" | **`scout-report-suggest`** — SCOUT REPORT with file/line evidence |
| Session orientation, project map | **`/mat-prime`** — context loader; not a substitute at session start |
| Saving docs from known URLs | **`docs-scraper`** → `ai_docs/` |
| Orchestration or implementation | **`/mat-plan`**, **`/mat-plan-team`**, builder, verifier |
| Mandatory neuroarxiv / literature scan | **`mat-preflight-gated`** (Later slice) — Phase B requires G2 approval |

This skill **does not replace** scout or mat-prime. It may **cite** paths scout found or docs scraper saved.

---

## Non-negotiable protocol

Apply before all other instructions:

1. **Stop for vague intake.** If two or more decision-critical facts are unknown, ask the concise intake batch (≤7 questions) and end the response. Do not invent target users, stacks, or success metrics. If the operator says skip questions, proceed with visible assumptions.
2. **Read-only repository review.** Inspecting a repo does **not** authorize dependency install, tests, builds, linters, audits, benchmarks, or script execution. Ask before any command that may create caches, artifacts, or state.
3. **Do not outsource judgment to popularity.** Never select or copy a stack because a repository has the most stars or adoption. **Do not rank options by GitHub stars, social popularity, or visible adoption alone.** Explain fit against constraints.
4. **Require receipts before recommendation.** For substantive advice, inspect relevant local evidence and normally two comparables plus primary docs or pricing sources when available. State what was inspected, limits, and observed dates for time-sensitive claims.
5. **Complete the decision.** Every final recommendation includes constraint fit, at least one credible alternative, explicit tradeoffs, failure conditions, and ordered next actions. Mark provisional when evidence is missing.
6. **Stop when evidence is sufficient.** Use bounded research rules below; do not browse indefinitely.

---

## Operating modes

Identify which mode applies first:

| Mode | When | Focus |
|------|------|-------|
| **Pre-build strategy** | No repo yet, or deciding how to build | Requirements, comparables, stack, architecture, risks, build path |
| **Mid-build course correction** | Repo or partial implementation exists | Inspect code vs goal; keep / change / defer |
| **Post-build review** | Project mostly complete or deployed | Architecture, quality, deployment readiness, gaps vs mature comparables |

**Selection rules:**

- No repo, folder, code, or URL → default **pre-build strategy**.
- Any repo, folder, code excerpt, GitHub URL, or "I am building…" → default **mid-build course correction** unless the operator says finished/deployed.
- Finished, deployed, production, launch-ready language → default **post-build review**.
- Mid/post-build with description only → **advisory review from description**; say file-level findings need a repo; do not pretend local evidence was inspected.

---

## Project intake gate

Use before research when a pre-build request is vague enough that different answers would materially change the recommendation.

**Decision-critical facts:** primary user, core workflow, project stage, must-haves, team capability, budget/deadline, deployment target, dominant priority.

If constraints are already clear, begin research immediately and ask only missing decision-critical questions.

For a vague idea, ask **at most seven questions** in one concise batch (accept "not sure"):

1. What are you trying to build, and who is it for?
2. Is this an idea, an active project, or nearly ready to ship?
3. What must it do, and what is explicitly out of scope for now?
4. Solo or team — and what tools/languages are comfortable?
5. What matters most: speed, low cost, simplicity, scale, control, or flexibility?
6. Where will it run, and what would you strongly prefer to avoid?
7. (Optional seventh) Any hard deadline, budget cap, or compliance constraint?

Let the operator say **"skip questions and proceed"** — continue with visible assumptions.

For vague requests stopped at intake, the questions are the complete response for that turn.

---

## Community research (G3 — opt-in only)

**Default off.** Do not use X, Reddit, YouTube, or similar social sources unless the operator explicitly opts in (MAT gate **G3**).

When community signals could materially help, ask:

> I can include community research from X, Reddit, and YouTube. It adds noise and time. Which do you want: official docs/GitHub only, social sources, or selected sources?

Record the choice in evidence status. Prefer official documentation, repository evidence, and pricing pages when sufficient.

**Agent-Reach** and similar broad web automation: **off by default** (MAT G5 posture). Do not install or configure without separate operator approval.

---

## Context budget (MAT)

Follow [`docs/reference/context-budget-policy.md`](../../../.mat/docs/context-budget-policy.md) and [`.cursor/rules/cost-context-hygiene.mdc`](../../rules/cost-context-hygiene.mdc):

- Prefer **`@file`** and explicit paths; smallest set that answers the question.
- Do **not** use habitual **Codebase Search** or whole-repo dumps for preflight.
- Map large repos first; sample purposefully; cite files inspected.

---

## Comparable discipline

Use comparables to sharpen judgment, **not** outsource it:

- **Do not rank** options by stars, downloads, or social proof alone.
- For each comparable: state **what transfers** and **what should not be copied**.
- Include direct, adjacent, official/template, heavier, and lighter references when useful.
- If the best fit is less popular, say why fit beats popularity.
- Inline citations for external claims — e.g. `(upstream: advise-project-approach@88f1ecc)` or repository URL with observed date.

---

## Pricing and operating-cost analysis

When budget, hosting, SaaS, cloud, AI APIs, "free tier", or managed services matter, analyze cost deeply enough to avoid misleading "free to start" advice.

Use **scenario-based language** (not fake precision):

| Scenario | Question answered |
|----------|-------------------|
| **Prototype cost** | What is likely free or near-free at tiny usage? |
| **Launch cost** | What changes with real users, storage, jobs, custom domains? |
| **Growth cost** | Which line items scale fastest or create lock-in? |

Check relevant buckets: base plans, compute, database, storage/bandwidth, auth/MAU, API/AI usage, observability, support/compliance, migration/exit.

Cite official pricing with observed date when verified; otherwise name dimensions the operator must check before committing.

---

## Workflow checklist

Follow in order; skip only when impossible and say why:

1. **Frame** — goal, users, stage, constraints, scale, skills, deadline, budget, deployment.
2. **Inspect** — read-only local evidence (README, manifests, entry points, CI, targeted source) or description-only assumptions.
3. **Research landscape** — comparables, official templates, standards, ecosystem guidance (bounded).
4. **Extract criteria** — speed, correctness, cost, portability, security, maintenance, etc.
5. **Check operating costs** — prototype / launch / growth scenarios when pricing affects the decision.
6. **Compare approaches** — 2–4 plausible options with tradeoffs and when each is wrong.
7. **Recommend** — primary path, second-best alternative, ordered next actions.
8. **Adapt to mode** — pre-build strategy, mid-build corrections, or post-build improvement roadmap.
9. **Write preflight artifacts** — see Output contract below.

---

## Output contract (MAT preflight artifacts)

Write **planning-adjacent tracked files only** under **`specs/<slug>/preflight/`** — not MAO handoffs.

Primary output path: **`specs/<slug>/preflight/landscape.md`** (always). Companion: **`specs/<slug>/preflight/candidates.json`** when comparables exist.

| File | When | Purpose |
|------|------|---------|
| **`landscape.md`** | Always (Phase A complete) | Comparables, constraints, cost framing, discovery checklist, inline citations |
| **`candidates.json`** | When comparables exist | Structured list: name, source, notes, transfer/non-transfer hints |
| **`novelty-gate.json`** | Always | Gate enum + observable criteria for Later neuroarxiv escalation (see design spec) |

**Do not write** `docs/current-plan.md`, `build-result.md`, `verify-result.md`, or implementation code unless the operator separately requests planning projection or execution.

### `landscape.md` minimum sections

```markdown
# Preflight landscape — <slug>

## Evidence status
<What was inspected, external research, gaps, G3 community choice>

## Project frame
<Goal, users, constraints, mode (pre/mid/post-build)>

## Comparables and references
<Named comparables with URLs, what transfers, what not to copy — not star-ranked>

## Cost and vendor reality
<Prototype / launch / growth scenarios; verified or unverified pricing notes>

## Recommendation summary
<Primary path, alternative, failure conditions, ordered next actions>

## Handoff to /mat-plan
<Suggested planning depth, Open Decisions, bounded Relevant Files hints>
```

### `candidates.json` shape (illustrative)

```json
{
  "slug": "<slug>",
  "generated_at": "<ISO-8601>",
  "candidates": [
    {
      "name": "Example comparable",
      "source": "https://…",
      "relevance": "direct | adjacent | template | heavier | lighter",
      "transfers": ["…"],
      "do_not_copy": ["…"],
      "notes": "…"
    }
  ]
}
```

Optional advisory logs: `artifacts/external-skills/` (gitignored) — never CI-required.

---

## Permission boundaries

**May (read-only / planning):**

- Inspect repository structure and architecturally relevant files via bounded reads
- Summarize design and quality signals from files and operator description
- Use web/search for public references when available
- Write preflight artifacts under `specs/<slug>/preflight/`

**Must ask before:**

- Modifying any file outside preflight artifacts the operator approved for this run
- Installing dependencies or running tests, builds, linters, scripts, migrations
- Committing, pushing, or opening PRs
- Starting `/mat-plan-team`, builder, or verifier

**Safety:** Do not read or expose secrets from `.env`, keys, credentials, or production dumps. Report existence only; recommend secure handling.

---

## Boundaries vs MAO and planning gates

| Artifact | Authority |
|----------|-----------|
| `specs/<slug>/preflight/*` | Planning-adjacent; informs `/mat-plan` |
| `specs/<slug>.md` or onboarding package | Planning truth (Tier 1–3) |
| `docs/current-plan.md` | Execution projection — **human approval (G6)** before orchestration |
| `build-result.md`, `verify-result.md` | Gate-authoritative for MAO build/verify |

Preflight output is **advisory**. Never substitute preflight markdown for orchestration gates.

---

## Handoff hints (not auto-written plans)

After Phase A, suggest — do not auto-write:

- Recommended `/mat-plan` vs `/mat-plan-onboarding` depth
- Open Decisions for the planning artifact
- Bounded Relevant Files `[new]` / `[existing]` hints
- Whether `novelty-gate.json` suggests neuroarxiv (Later; requires **G2** — out of scope for this skill alone)

---

## Failure handling

- **No accessible files** — ask for path, URL, or short description; proceed in pre-build with assumptions if needed.
- **External research blocked** — disclose; proceed with local evidence and general judgment.
- **Monorepo / huge repo** — ask for target app; shallow map + scoped recommendation.
- **Vague intake** — stop at intake gate; do not fabricate a full landscape.

---

## Related MAT surfaces

- [`mat-plan-contract`](../mat-plan-contract/SKILL.md) — tier selection, amendments, markers
- [`specs/mat-discovery-research-skills.md`](../../../.mat/docs/specs/mat-discovery-research-skills.md) — full Layer 0 design, G0–G7 gates, Later wrapper `mat-preflight-gated`
- [`.cursor/commands/mat-plan.md`](../../commands/mat-plan.md) — Step 0 optional preflight pointer
