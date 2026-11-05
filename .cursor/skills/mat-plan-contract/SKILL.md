---
name: MAT Plan Contract
description: Apply MAT shared plan contract v0.1 when choosing planning depth tiers, writing append-only amendments, surgical plan updates (/mat-plan-update), mutating in-plan status markers, or projecting approved planning into docs/current-plan.md. Invoke for tier selection, amendments protocol, surgical update procedure (Decision F), status markers, validation-loop SOP, and execution projection — does not replace /mat-plan, /mat-plan-onboarding, /mat-plan-update, or /mat-plan-team slash commands.
---

# MAT Plan Contract (v0.1)

Procedural guidance for MAT shared plan semantics. **This skill does not replace slash commands** — use `/mat-plan`, `/mat-plan-onboarding`, `/mat-plan-update`, `/mat-plan-team`, `/mat-sprint`, and `/mat-long-run` for authoring and orchestration. Cross-reference only.

**Canonical docs:**

- Operator summary: [`docs/architecture/plan-contract.md`](../../../.mat/docs/plan-contract.md)
- Full design (Decisions A–J): [`specs/shared-plan-contract.md`](../../../.mat/docs/specs/shared-plan-contract.md)
- Preflight escalation ladder (pointer): [`docs/architecture/preflight-escalation-ladder.md`](../../../.mat/docs/preflight-escalation-ladder.md)

---

## When to use this skill

- Choosing **lite** vs **standard** vs **onboarding** depth before writing plans
- Applying optional **Task type** / **Complexity** header tags on solo `/mat-plan` specs (depth hints only; not YAML frontmatter; not preflight gates)
- Applying **append-only `## Amendments`** on living plans
- **Surgical plan updates** after first write (`/mat-plan-update`)
- Mutating **status markers** on execution checklists (`[]`, `[wip]`, `[x]`, `[f]`)
- **Projecting** approved `specs/` planning into `docs/current-plan.md`
- Following **validation-loop SOP** (per-phase and global commands before handoff)
- **Planning Step 0** — deep analysis before artifact writes; see [`.cursor/commands/mat-plan.md`](../../commands/mat-plan.md) Workflow Step 0
- **Canvas visualization** (optional, advisory) — generate a `.canvas.tsx` dashboard from bounded markdown handoffs; see [`.cursor/skills/mat-plan-canvas/SKILL.md`](../mat-plan-canvas/SKILL.md)

---

## Decision A — Depth tier selection

**Optional router:** `/mat-plan --depth=…` is documented convenience only in [`.cursor/commands/mat-plan.md`](../../commands/mat-plan.md#depth-router-depth); it does **not** override “do not auto-infer tier” below.

| Tier | Commands | Primary artifacts | Execution template |
|------|----------|-------------------|-------------------|
| **lite** | `/mat-sprint`, adoption bootstrap | Minimal `docs/current-plan.md` | [`docs/templates/adoption-minimal-current-plan.md`](../../../.mat/docs/templates/adoption-minimal-current-plan.md) |
| **standard** | `/mat-plan`, `/mat-plan-team`, `/mat-long-run` | `specs/<slug>.md` → projected `docs/current-plan.md` | [`docs/templates/execution-plan-template.md`](../../../.mat/docs/templates/execution-plan-template.md) |
| **onboarding** | `/mat-plan-onboarding` | `specs/<slug>/` four-file package + `tasks.json` | Bridge via `plan-summary.md`; execution uses lite or standard |

**Procedure:**

1. **Do not auto-infer tier from intent alone** — pick the command that matches the work shape.
2. `/mat-plan` always produces **standard** planning (`specs/<slug>.md`, 13 sections).
3. `/mat-plan-onboarding` always produces **onboarding** (`specs/<slug>/` package).
4. For execution, choose **lite** vs **standard** `docs/current-plan.md` shape from slice complexity; document tier in the plan header one line.
5. `docs/current-plan.md` is always a **projection** of approved planning — not a fourth schema.

**Optional depth hints (solo `/mat-plan` only):** Header lines `**Task type:** \`feature\`` and `**Complexity:** \`medium\`` may tune prose depth. Allowlists: `chore|feature|refactor|fix|enhancement` and `simple|medium|complex`. Do **not** use YAML frontmatter. Tags never change required sections or restore planf3 auto-preflight. See [`.cursor/commands/mat-plan.md`](../../commands/mat-plan.md) Content Rules.

---

## Decision B — Three-schema reconciliation (projection)

**Procedure:**

1. Identify upstream planning truth: solo `specs/<slug>.md`, onboarding package (`plan-summary.md` + `tasks.json`), or approved slice from long-run state.
2. After **human approval**, operator/parent projects into `docs/current-plan.md` using the matching execution template (lite or standard).
3. Maintain **one active execution truth** per orchestration cycle.
4. On drift: update planning artifacts first, then re-project execution (`docs/guides/planning-commands-guide.md`).
5. If both `specs/<slug>.md` and `specs/<slug>/` exist, the **folder package is authoritative**.

**Truth hierarchy:**

1. Planning: `specs/` (solo or package)
2. Execution: `docs/current-plan.md`
3. Outcome gates: `build-result.md`, `verify-result.md`
4. MAO todos: advisory only

---

## Decision C — Amendments protocol

**Procedure:**

1. Add `## Amendments` on living plans that may change after first write.
2. **Required on:** `docs/current-plan.md`, `specs/<slug>/plan-summary.md`.
3. **Optional on:** root `specs/<slug>.md` when used as a living planning doc.
4. **Placement:** On solo `/mat-plan` specs, `## Amendments` is **second-to-last**; `## Recommended Next Command` stays **last**. On execution/onboarding bridge files without that section, `## Amendments` is **last**.
5. **Format:** append-only bullets — `- YYYY-MM-DDTHH:MM:SSZ — role — summary` (ISO-8601 UTC).
6. **Authority:** operator/parent may always append; builder may append during active build for scope drift (cite triggering checklist line); verifier **read-only**; planning agents only while authoring before approval.
7. **Forbidden:** rewrite prior lines, edit timestamps, delete entries.

---

## Decision F — Surgical plan update (v1)

Use **`/mat-plan-update`** when an approved planning artifact needs a bounded in-place change — not a full re-authoring pass.

**Procedure:**

1. Confirm the target exists (`specs/<slug>.md`, `specs/<slug>/plan-summary.md`, or scoped package file).
2. Classify: `surgical_amendment` vs `escalate_to_onboarding` (fuzzy/cross-functional → heavier command).
3. Apply **minimal** section edits; append **exactly one** ISO amendment line under `## Amendments`.
4. **Do not** edit active `docs/current-plan.md` in this command — operator re-projects after planning truth changes.
5. End with one **Recommended Next Command** path (refinement, re-project, `/mat-plan-team`, or escalate).

Command: [`.cursor/commands/mat-plan-update.md`](../../commands/mat-plan-update.md). Operator routing: [`docs/guides/planning-commands-guide.md`](../../../.mat/docs/guides/planning-commands-guide.md).

---

## Decision D — Status marker state machine

**Markers** on checklist lines in `docs/current-plan.md` (implementation steps, acceptance criteria):

| Marker | Meaning | Next states |
|--------|---------|-------------|
| `[]` | Idle / not started | `[wip]` |
| `[wip]` | In progress | `[x]`, `[f]` |
| `[x]` | Done for this slice | terminal |
| `[f]` | Failed / blocked (reason on same line) | `[wip]` after fix |

**State machine per line:** `[] → [wip] → [x]` or `[] → [wip] → [f] → [wip]`.

**Procedure:**

1. **Builder** mutates markers **in-place** during implementation.
2. **Parent** may set `[wip]` at slice start when seeding the plan.
3. **Verifier** does not mutate markers (reports in `verify-result.md`; warn-not-fail on drift).
4. **MAO todos** are advisory — `[mao:build] in_progress` does **not** substitute for plan-line `[wip]`.
5. **Gates stay authoritative:** `build-result.md` / `verify-result.md` determine orchestration transitions; markers are advisory executability inside the plan.

---

## Decision E — Validation loops SOP

In-plan validation loops are **SOP for builders/subagents**; hook-enforced handoff files remain the **hard** gate.

**Procedure:**

1. **Per-phase:** In `## Verification plan` (lite/execution) or `## Testing Strategy` (standard planning), each phase lists a command and **“loop until pass”** instruction.
2. **Global:** Before handoff, run ordered validation commands (e.g. `phase1-verify.sh`, artifact validators) until exit 0.
3. Use execution templates for structure:
   - **Lite:** [`docs/templates/adoption-minimal-current-plan.md`](../../../.mat/docs/templates/adoption-minimal-current-plan.md)
   - **Standard:** [`docs/templates/execution-plan-template.md`](../../../.mat/docs/templates/execution-plan-template.md)
4. Do not treat in-plan loop prose as a substitute for truthful `build-result.md` / `verify-result.md` rows.

---

## Slash command cross-reference (not replacements)

| Need | Command |
|------|---------|
| Lightweight solo planning | `/mat-plan` |
| Heavyweight onboarding package | `/mat-plan-onboarding` |
| Surgical living-plan amendment | `/mat-plan-update` |
| Plan → build → verify orchestration | `/mat-plan-team` |
| Single bounded slice | `/mat-sprint` |
| Queued multi-slice mission | `/mat-long-run` |

Operator map: [`docs/guides/planning-commands-guide.md`](../../../.mat/docs/guides/planning-commands-guide.md).

---

## Adoption note

On bootstrap, `.cursor/skills/` (including this skill) copies via `adoption-layout-v1.json` `cursor_copy.dir_contents`. Operator contract summary packages to `.mat/docs/plan-contract.md` for adopted repos.
