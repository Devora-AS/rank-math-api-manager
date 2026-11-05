# Report Output Style

Use this style for reviews, audits, verification reports, migration summaries, or any task where findings need to be easy to reference and act on later.

## Goals

- Make conclusions auditable.
- Separate findings from commentary.
- Keep severity, evidence, and recommendations explicit.

## Default Shape

1. Executive summary
2. Findings
3. Open questions or assumptions
4. Verification or evidence
5. Recommended next steps

## Findings Format

Use numbered findings ordered by severity. For each finding, include:

- Location
- Issue
- Impact
- Recommendation

If there are no findings, say so explicitly and then note any residual risk or testing gaps.

## Do

- Lead with findings before general summary.
- Cite concrete files, symbols, commands, or observed behavior.
- Distinguish confirmed issues from assumptions.
- Keep recommendations specific and actionable.

## Avoid

- Burying the main problem below background context.
- Mixing confirmed defects with stylistic preferences.
- Using decorative status symbols as the only signal.
- Writing a report format when a short answer would do.

## Good Fits

- Code review
- Verification pass
- Release readiness check
- Evidence-backed documentation audit

## Example

```md
## Executive Summary
One blocking documentation issue remains: the lifecycle comparison still overstates replayability relative to the repo's own runtime evidence.

## Findings
1. Location: `docs/LIFECYCLE_COMPARISON.md`
Issue: The doc implies exact session replay.
Impact: Operators may overestimate the durability of Cursor runtime traces.
Recommendation: Reword the section to match the verified evidence caveats used elsewhere.

## Verification
- Reviewed the changed docs directly.
- Re-ran `git diff --check`.
```
