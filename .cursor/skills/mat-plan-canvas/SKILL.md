---
name: MAT Plan Canvas
description: Generate Cursor Canvas dashboards for MAT plan review from bounded markdown handoffs (specs/, docs/current-plan.md, optional build-result.md / verify-result.md). Invoke when the operator wants an interactive visual layer for phases, Open Decisions, status markers, architecture, or acceptance criteria — advisory view only; markdown stays canonical. Does not replace /mat-plan, /mat-plan-onboarding, /mat-plan-update, /mat-plan-team, mat-plan-contract, or MAO/handoff gates.
---

> **Advisory only — markdown is canonical.** Canvas is a **derived, read-only** visualization inside Cursor. Never write back to planning or execution markdown. Never substitute `build-result.md`, `verify-result.md`, MAO todos, or hook gates. Tier 1–4 CI validates markdown only.

# MAT Plan Canvas

Procedural guidance for generating **Cursor Canvas** dashboards from MAT plan artifacts. **This skill does not replace slash commands or `mat-plan-contract`** — use planning commands for authoring, [`mat-plan-contract`](../mat-plan-contract/SKILL.md) for tier/amendment/marker semantics, and file handoffs for orchestration gates.

**Platform references:**

- [Cursor Canvas docs](https://cursor.com/docs/agent/tools/canvas)
- [Cursor Canvas blog](https://cursor.com/blog/canvas)

**Canonical contract (truth hierarchy):** [`docs/architecture/plan-contract.md`](../../../.mat/docs/plan-contract.md) · full design: [`specs/shared-plan-contract.md`](../../../.mat/docs/specs/shared-plan-contract.md)

---

## Purpose

Provide MAT's **primary visual/interactive layer** for plan review inside Cursor: an agent-built Canvas that mirrors bounded reads from approved markdown handoffs. Canvas helps operators scan phases, decisions, markers, architecture, and acceptance criteria faster than scrolling long specs — without creating a second source of truth.

This is a **canary**, not a required runtime. The public Cursor page documents standalone views with sections, stats, and tables, reopening and iteration in Cursor, optional Publish, and skills packaging. It does **not** establish a public file-format or programmatic Canvas API contract.

---

## When to use this skill

- Operator asks to **visualize**, **dashboard**, or **canvas** a plan, slice, or onboarding package
- Reviewing **Open Decisions** (`OD-###`), implementation steps, or acceptance criteria interactively
- Presenting **architecture / dependency** graphs when markdown lists nodes and edges
- Optional **build/verify mirror** during orchestration review (read `build-result.md` / `verify-result.md` only — display, never gate)
- **Regenerating** a canvas after markdown handoffs change (operator-triggered refresh)

---

## When NOT to use this skill

- **Authoring or mutating** planning truth — use `/mat-plan`, `/mat-plan-onboarding`, `/mat-plan-update`, or projection into `docs/current-plan.md`
- **Orchestration transitions** — `build-result.md` and `verify-result.md` remain gate-authoritative; canvas `Stat` / `Pill` mirrors are display-only
- **CI validation** — validators and `phase1-verify.sh` run on markdown only; canvas is never required for PASS
- **HTML export or planf3 patterns** — no living HTML execution contract, in-repo HTML renderer, browser-open ritual, or gpt-image-2 pipeline (see Non-goals)
- **Hook-driven auto-generation** — no MAO transition triggers, no post-handoff mandatory canvas in `/mat-plan-team` closeout
- **Replacing `mat-plan-contract`** — tier selection, amendments, markers, and projection stay in that skill and slash commands

---

## Truth hierarchy disclaimer

Canvas reads from markdown; it does **not** change authority order:

1. **Planning:** `specs/` (solo `specs/<slug>.md` or onboarding package)
2. **Execution:** `docs/current-plan.md` (projection of approved planning)
3. **Outcome gates:** `build-result.md`, `verify-result.md` — orchestration transitions
4. **MAO todos / hook events:** advisory traceability only
5. **Canvas:** derived view — **below** all of the above; optional; Cursor-local unless team **Publish** is used

If canvas and markdown disagree, **markdown wins**. Regenerate canvas from fresh handoffs; do not edit specs or handoff files from canvas output.

---

## Depth-tier source matrix

Branch layout and bounded reads by Decision A depth tier:

| Tier | Primary sources (read bounded sections only) | Canvas focus |
|------|-----------------------------------------------|--------------|
| **lite** | `docs/current-plan.md` | Task, implementation steps, validation checks, acceptance criteria |
| **standard** | `specs/<slug>.md` **and/or** active `docs/current-plan.md` | Full planning sections when reviewing spec; execution slice when orchestrating |
| **onboarding** | Bounded reads from `specs/<slug>/plan-summary.md`, `prd.md`, `spec.md`, `tasks.json` | Package overview, tasks traceability, bridge to execution projection |

**Procedure:**

1. Identify tier from plan header, command used, or operator statement — do not auto-infer from intent alone (`mat-plan-contract` Decision A).
2. Read **only** the files and sections needed for the requested view; avoid whole-repo dumps.
3. If both `specs/<slug>.md` and `specs/<slug>/` exist, the **folder package is authoritative** for onboarding-shaped truth.
4. Confirm the same bounded content can be presented through the **Markdown fallback** before attempting the canary.

---

## Trigger phrases

Invoke when the operator uses phrases like:

- "canvas this plan" / "visualize the current plan"
- "dashboard for `docs/current-plan.md`"
- "show Open Decisions interactively"
- "DAG for architecture section"
- "refresh the plan canvas after the spec update"

---

## Canary procedure

1. **Confirm tier** (lite / standard / onboarding), the review goal, and bounded source paths.
2. **Read** only the selected markdown sections; skip absent optional files.
3. **Prepare fallback:** ensure the same content can be summarized with headings, bullets, checklists, and small tables in chat.
4. **Attempt once:** ask Cursor to build the standalone Canvas view. Do not depend on an undocumented file extension, component schema, import path, or programmatic renderer.
5. **Check Canary success:** a Canvas reference opens beside chat, accurately mirrors the selected markdown, and can be reopened or iterated through the documented Cursor UI.
6. **Check Canary failure:** Canvas is unavailable/blocked, does not open, errors, is blank or stale, disagrees with markdown, or would require an undocumented API assumption.
7. **Label authority:** state that the Canvas is advisory and link to canonical markdown paths. Optional build/verify status is "mirror only, not authoritative".
8. **Fallback on failure or poor fit:** immediately use the Markdown fallback below; do not make Canvas failure a planning, build, verify, or MAO failure.
9. **Publish is optional:** sharing depends on account/team/privacy/admin settings and is never a success criterion.

## Markdown fallback

When Canvas is unavailable, unsuitable, or fails the canary:

1. Present the bounded review in chat with the same title and source links.
2. Use short headings and bullets for phases and decisions, checklist text for status markers, and a small table only when it materially improves acceptance-criteria review.
3. Direct all edits and decisions to the canonical `specs/` or `docs/current-plan.md` path through the normal MAT command/role owner.
4. Keep `build-result.md` and `verify-result.md` as gate-authoritative handoffs.
5. Continue markdown validation normally and avoid repeated Canvas retries in the same phase.

---

## Layout template per tier

### Lite

```
Title — slice title (from current-plan header)
Stats — Status / Preflight (from plan header)
Section — Task
Checklist — Implementation steps (markers display-only)
Table or compact section — Validation checks / acceptance criteria
Optional status summary — build-result / verify-result mirror
```

### Standard

```
Title — plan or slice title
Section — Purpose / Task
Sections — phases or major regions from spec or current-plan
Checklist — per-phase []/[wip]/[x]/[f] markers, display-only
Expandable section when available — Open Decisions (OD-###)
Table — Acceptance criteria
Optional relationship view — architecture / dependencies when graph data is present
Optional status row — handoff gate mirror
```

### Onboarding

```
Title — package title (plan-summary)
Section — PRD summary / goals (bounded excerpt from prd.md)
Section — Spec highlights (bounded excerpt from spec.md)
Table — tasks.json rows (id, status, traceability)
Expandable section when available — Open Decisions from plan-summary
Bridge note → projected docs/current-plan.md
```

---

## Content mapping

| Markdown source | Canvas presentation | Notes |
|-----------------|---------------------|-------|
| `## Open Decisions` / `OD-###` | Expandable or grouped section | No write-back |
| Status markers `[]` / `[wip]` / `[x]` / `[f]` | Checklist | **Display only** — do not mutate plan files from Canvas |
| Phases / implementation steps | Sections and stats | Structure mirrors markdown headings |
| Architecture / dependencies | Relationship view | Only when source markdown defines relationships |
| Acceptance criteria | Table or compact section | Quote criteria text; no PASS/FAIL authority |
| Build/verify status (optional) | Status summary | Mirror `build-result.md` / `verify-result.md` only — **not** a gate substitute |

---

## Refresh / regenerate procedure

1. Operator changes canonical markdown (spec, current-plan, or handoff files).
2. Re-read **bounded** sections from the same tier sources — do not diff canvas as truth.
3. Ask Cursor to update or regenerate the saved Canvas from the fresh bounded sources.
4. If published canvas was shared, operator re-publishes after regenerate; git-tracked markdown is still the archive of record.

---

## Documented platform boundaries

Per [Cursor Canvas docs](https://cursor.com/docs/agent/tools/canvas):

- Cursor can create interactive artifacts that render next to chat.
- Views can use sections, stats, and tables and can be reopened and iterated on.
- A skill can package trigger, layout, data-source/query, and formatting guidance.
- Publish can create a team-visible browser snapshot when account and organization settings allow it.

The page provides **no documented public programmatic `.canvas.tsx` file-format or Canvas SDK contract**. Do not present on-disk extensions, import paths, component names, schemas, or headless rendering as stable public APIs. If the active Cursor product supplies internal generation guidance, follow it only for that runtime attempt; MAT's portable contract remains this canary plus Markdown fallback.

---

## Non-goals

- **planf3 HTML patterns** — reject living HTML execution contract, in-repo HTML renderer, browser-open ritual, gpt-image-2 diagram pipeline, or HTML as a required planning artifact
- Any claim of a public programmatic `.canvas.tsx` / Canvas SDK contract
- New **validator tiers**, **hooks**, **MAO gate** logic, or required handoff files
- **Write-back** from canvas to `specs/`, `docs/current-plan.md`, or result artifacts
- **Mandatory canvas** in `/mat-plan-team` closeout or CI (`phase1-verify.sh` does not require canvas)
- **`.mat/` adoption packaging** of this skill (may copy via `cursor_copy` on bootstrap — not a separate product contract)
- Replacing **`mat-plan-contract`** or planning slash commands

---

## Related docs

| Topic | Path |
|-------|------|
| Plan contract semantics | [`.cursor/skills/mat-plan-contract/SKILL.md`](../mat-plan-contract/SKILL.md) |
| Operator plan contract | [`docs/architecture/plan-contract.md`](../../../.mat/docs/plan-contract.md) |
| Planning commands map | [`docs/guides/planning-commands-guide.md`](../../../.mat/docs/guides/planning-commands-guide.md) |
| Workflow handoff contract | [`docs/reference/workflow-artifact-contract.md`](../../../.mat/docs/workflow-artifact-contract.md) |
| Component inventory | [`docs/reference/components.md`](../../../.mat/docs/components.md) |
| Canvas platform | [cursor.com/docs/agent/tools/canvas](https://cursor.com/docs/agent/tools/canvas) |
