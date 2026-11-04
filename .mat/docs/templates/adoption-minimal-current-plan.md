# Current plan

**Tier:** lite (execution projection)
**Contract:** v0.1 — [`docs/architecture/plan-contract.md`](../plan-contract.md) (full design: [`specs/shared-plan-contract.md`](../specs/shared-plan-contract.md))

<!-- Plan contract v0.1 depth tiers (Decision A):
     lite    — this template (adoption bootstrap, /mat-sprint, narrow slices)
     standard — docs/templates/execution-plan-template.md (projected docs/current-plan.md)
     onboarding — /mat-plan-onboarding four-file package + plan-summary bridge
     See docs/architecture/plan-contract.md -->

## Task

Bootstrap the workflow surfaces into a fresh repository.

## DoR

- The repository exists and is already initialized with git.
- The adoption command runs non-interactively.
- The fixture stays focused on workflow-contract validation.

## Binary acceptance criteria

- [] `.cursor/commands/` exists in the adopted repository.
- [] `docs/current-plan.md` exists.
- [] `docs/architecture/long-run-state.md` exists.

## Non-goals

- No project-specific product implementation.
- No claim that observability or runtime integrations are fully configured.

## Verification plan

<!-- Plan contract v0.1 Decision E — validation loops (SOP; hard gates remain build-result.md / verify-result.md).
     See docs/architecture/plan-contract.md -->

### Per-phase (loop until pass)

| Phase | Command | Loop until pass |
|-------|---------|-----------------|
| Sidecar contract tests | `python3 -m unittest discover -s .mat/tests -p 'test_*.py' -v` | Re-run after fixes until green |

### Global validation commands (before handoff)

1. `python3 -m unittest discover -s .mat/tests -p 'test_*.py' -v`
2. `bash scripts/phase1-verify.sh` (when present on adopted tree)

<!-- Plan contract v0.1 (Slice 2): substantive execution plans include append-only ## Amendments
     as the last section. Format: - YYYY-MM-DDTHH:MM:SSZ — role — summary (ISO-8601 UTC).
     Authority: operator/parent; builder during active build for scope drift; verifier read-only.
     See docs/architecture/plan-contract.md -->

<!-- Plan contract v0.1 (Slice 3): checklist lines use contract status markers:
     [] idle · [wip] in progress · [x] done · [f] failed/blocked (reason on same line).
     State machine: [] → [wip] → [x] or [] → [wip] → [f] → [wip]. Builder mutates in-place;
     markers are advisory — MAO gates use build-result.md / verify-result.md only.
     See docs/architecture/plan-contract.md -->

<!-- Plan contract v0.1 (planf3 audit-trail Slice 3): optional ## Plan metadata — NOT YAML
     frontmatter. Append-only ### modified / ### session / ### commit lists; operator/parent
     append only; hooks do not auto-write. See docs/architecture/plan-contract.md -->

<!-- ## Plan metadata
     ### modified
     - YYYY-MM-DDTHH:MM:SSZ — role — projection note
     ### session
     - cursor-session-id — sprint milestone
     ### commit
     - short-sha — optional merge note
-->

## Amendments

<!-- Append-only audit trail. Do not rewrite or delete prior lines. -->
