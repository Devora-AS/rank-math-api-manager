# Current plan — <slice title>

**Status:** Active orchestration slice
**Tier:** standard (execution projection)
**Contract:** v0.1 — [`docs/architecture/plan-contract.md`](../plan-contract.md) (full design: [`specs/shared-plan-contract.md`](../specs/shared-plan-contract.md))
**Preflight:** `builder_plus_verifier` | `inline` | `solo_plan_only`
**Last updated:** YYYY-MM-DD

<!-- Plan contract v0.1 depth tiers (Decision A):
     lite    — /mat-sprint, adoption bootstrap → docs/templates/adoption-minimal-current-plan.md
     standard — /mat-plan, /mat-plan-team, /mat-long-run → this template (projected docs/current-plan.md)
     onboarding — /mat-plan-onboarding → specs/<slug>/ four-file package + plan-summary bridge
     See docs/architecture/plan-contract.md -->

---

## Task

<One-paragraph execution slice summary. Source planning truth from specs/ when applicable.>

## Non-goals

- <Explicit out-of-scope item>

## Context

| Anchor | Role |
|--------|------|
| `specs/<slug>.md` or `specs/<slug>/` | Upstream planning truth |
| `docs/current-plan.md` | Active execution projection |

## Implementation steps

- [] **Step 1 — <title>**
  - <Concrete deliverable or file path>

- [] **Step 2 — <title>**
  - <Concrete deliverable or file path>

## Binary acceptance criteria (verifier)

- [] **AC-1:** <Criterion with observable evidence>
- [] **AC-2:** <Criterion with observable evidence>

## Verification plan

<!-- Plan contract v0.1 Decision E — Tier 2b validation-loop discipline for execution
     projections (SOP; hard gates remain build-result.md / verify-result.md).
     Keep both subsections below and replace placeholders with repo-native commands.
     See docs/architecture/plan-contract.md -->

### Per-phase validation loops (loop until pass)

| Phase | Command | Loop until pass |
|-------|---------|-----------------|
| Unit / targeted tests | `python3 -m unittest tests.test_<module> -v` | Re-run after fixes until green |
| Lint / type-check | `ruff check .` / project equivalent | Re-run until clean |
| Full gate | `bash scripts/phase1-verify.sh` | Re-run until exit 0 before handoff |

### Global validation commands (before handoff)

1. `python3 scripts/validate_planning_artifacts.py --repo-root .`
2. `python3 .cursor/scripts/validate_artifacts.py --repo-root . --require-current-plan`
3. `bash scripts/phase1-verify.sh`

## Expected output artifacts

- `build-result.md` — builder handoff (PASS/PARTIAL + acceptance criteria rows)
- `verify-result.md` — verifier evidence per binary acceptance criteria

<!-- Plan contract v0.1 (Slice 2): substantive execution plans include append-only ## Amendments
     as the last section. Format: - YYYY-MM-DDTHH:MM:SSZ — role — summary (ISO-8601 UTC).
     Authority: operator/parent; builder during active build for scope drift; verifier read-only.
     See docs/architecture/plan-contract.md -->

<!-- Plan contract v0.1 (Slice 3): checklist lines use contract status markers:
     [] idle · [wip] in progress · [x] done · [f] failed/blocked (reason on same line).
     State machine: [] → [wip] → [x] or [] → [wip] → [f] → [wip]. Builder mutates in-place;
     markers are advisory — MAO gates use build-result.md / verify-result.md only.
     See docs/architecture/plan-contract.md -->

<!-- Plan contract v0.1 (planf3 audit-trail Slice 3): optional ## Plan metadata on execution
     projections — NOT YAML frontmatter. Append-only ### modified / ### session / ### commit
     list subsections. Authority: operator/parent append only; builder/verifier read-only;
     complements session-summary.md and MAO advisory events — does not replace them.
     Hooks do not auto-write metadata. See docs/architecture/plan-contract.md -->

<!-- ## Plan metadata
     Append-only audit trail on the active execution projection.
     ### modified
     - YYYY-MM-DDTHH:MM:SSZ — role — projection or re-projection note
     ### session
     - cursor-session-id — slice milestone note
     ### commit
     - short-sha — optional post-merge note
-->

## Amendments

<!-- Append-only audit trail. Do not rewrite or delete prior lines. -->

- YYYY-MM-DDTHH:MM:SSZ — orchestrator — Initial execution plan from approved planning slice.
