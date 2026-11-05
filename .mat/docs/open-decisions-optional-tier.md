# Open Decisions optional tier (Tier 2e)

**Status:** Shipped (planf3 audit-trail Slice 2, 2026-07-03)  
**Contract:** v0.1 tail-zone optional tier — see [`plan-contract.md`](plan-contract.md) and [`specs/shared-plan-contract.md`](specs/shared-plan-contract.md) Decision B.

## Purpose

Optional `## Open Decisions` gives solo `/mat-plan` specs and onboarding `plan-summary.md` a **file-resident decision log** with stable `OD-###` ids and explicit lifecycle status. It complements — but does not replace — the onboarding **one-at-a-time chat gate** for unresolved questions.

## Placement (tail zone)

On root `specs/<slug>.md` and `plan-summary.md`, optional sections appear **after** required content and **before** `## Amendments` / `## Recommended Next Command`. When multiple optional sections exist:

1. `## Related plans` (Tier 2d)
2. `## Open Decisions` (Tier 2e)
3. `## Amendments`
4. `## Recommended Next Command` (required last on solo plans)

## Distinction from other sections

| Section | Role |
|---------|------|
| `## Assumptions` | Static planning premises — not a decision lifecycle log |
| `## Risks and Open Questions` | Unstructured risks and questions — not numbered decision ids |
| `## Open Decisions` | Numbered `OD-###` items with `open` / `resolved` / `deferred` status |

## Canonical row shape

Plain markdown list bullets (no HTML `<details>` in v1):

```markdown
- **OD-001** | status: `open` | Question or summary text
- **OD-002** | status: `resolved` | 2026-07-03 — role — Resolution summary
- **OD-003** | status: `deferred` | Explicit deferment reason
```

Allowed status tokens: `open`, `resolved`, `deferred` (lowercase, backtick-wrapped).

Resolved rows **should** include ISO date (`YYYY-MM-DD`), role, and summary after the status pipe. Missing provenance emits a **verbose-only** notice (`tier2_open_decisions_resolved_missing_provenance`) — not a CI failure in v1.

## Onboarding workflow

1. **Discovery:** unresolved-questions scan + **one question at a time in chat** (canonical gate).
2. **After each answer or deferment:** update relevant package files and **mirror** into `## Open Decisions` on `plan-summary.md`.
3. **Amendments:** `/mat-plan-update` may change status in-place for the same `OD-###` id with an append-only `## Amendments` line.

## `tasks.json` interaction (v1)

No schema change. Optional `open_questions` or task notes may **cross-reference** `OD-###` ids when both exist. The single write path after chat resolution remains the file mirror on `plan-summary.md`.

## Validator (Tier 2e)

Enforced by `scripts/validate_planning_artifacts.py` on root solo `specs/<slug>.md` when `## Open Decisions` is present:

| Issue code | Severity |
|------------|----------|
| `tier2_open_decisions_malformed_row` | Fail |
| `tier2_open_decisions_invalid_status` | Fail |
| `tier2_open_decisions_resolved_missing_provenance` | Verbose notice only |

Grace registry: `OPEN_DECISIONS_GRANDFATHERED_SOLO_PLANS` (exemplar without grace: `specs/planf3-audit-trail-mission.md`). Absent section → skip entire Tier 2e.

## Comparison to planf3 `#questionables`

From [`docs/archive/planf3-comparison-2026-07.md`](../archive/planf3-comparison-2026-07.md):

| planf3 | MAT v1 (this tier) |
|--------|-------------------|
| Optional `#questionables` with toggleable HTML `<details>` | Plain markdown bullets; no HTML requirement |
| `questionable=true` flag | Optional section when present |
| Implicit discovery | Onboarding **chat one-at-a-time gate** stays canonical; file mirror after resolution |

## Operator references

- Command: [`.cursor/commands/mat-plan.md`](../../.cursor/commands/mat-plan.md) Content Rules
- Onboarding mirror: [`.cursor/commands/mat-plan-onboarding.md`](../../.cursor/commands/mat-plan-onboarding.md)
- Surgical updates: [`.cursor/commands/mat-plan-update.md`](../../.cursor/commands/mat-plan-update.md)
- Guide: [`docs/guides/planning-commands-guide.md`](../guides/planning-commands-guide.md)
- Maintainer registry: [`docs/reference/MAINTAINER.md`](MAINTAINER.md)
