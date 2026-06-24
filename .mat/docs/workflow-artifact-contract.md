# Workflow Artifact Contract

**Status:** canonical Phase 1 contract for workflow handoff artifacts

**Purpose:** define the required structure for `build-result.md` and `verify-result.md` so prompts, command docs, validators, MAO parsing, and tests all point at the same contract.

## Source Of Truth

This contract has two layers:

1. **Runtime source of truth:** `.cursor/hooks/artifact_contract.py`
2. **Human-readable reference:** this document

**Where this file lives:** In the MAT **source** repository, the human-readable copy is here at `docs/workflow-artifact-contract.md`. When MAT is **bootstrapped** into another repo, the same text is packaged under **`.mat/docs/workflow-artifact-contract.md`** so product-owned root `docs/` can stay minimal. Hooks and validators resolve the readable contract with `resolve_workflow_artifact_contract_doc(repo_root)` (prefer root `docs/` when present, else `.mat/docs/`). Prompts under `.cursor/` in the source tree link to `../../docs/workflow-artifact-contract.md`; bootstrap rewrites those links in the adopted tree to `../../.mat/docs/workflow-artifact-contract.md` and normalizes inline `docs/workflow-artifact-contract.md` path strings under `.cursor/` to `.mat/docs/workflow-artifact-contract.md`.

The runtime layer owns the enforceable rules used by:

- `.cursor/scripts/validate_artifacts.py` (supports `--optional-handoff-artifacts` for MAT **adopted** trees where `build-result.md` / `verify-result.md` exist only during an active slice; `scripts/phase1-verify.sh` passes this flag when `.mat/README.md` is present)
- `.cursor/hooks/mao_gate.py`
- regression tests under `tests/`

Prompt and command examples must mirror this document and the shared runtime module exactly. If the runtime module changes, update this document and every prompt/example in the same slice.

## Build Result Contract

`build-result.md` must use this structure:

```markdown
# Build Result

## Task
<one-line description>

## Status
PASS | FAIL | PARTIAL

## Changes Made
- `path/to/file.py`: <what changed and why>

## Acceptance Criteria
- Criterion 1: PASS — <brief evidence>
- Criterion 2: FAIL — <reason>

## Linting / Type-Check
PASS | FAIL
<optional supporting detail lines>

## Issues / Blockers
None | <open issues>

## Notes for Verifier
<specific guidance for verification>

## Closeout (YYYY-MM-DD)
<brief closeout summary>
```

### Build rules

- `## Status` must start with `PASS`, `FAIL`, or `PARTIAL`.
- `## Changes Made` must contain at least one non-empty entry.
- `## Acceptance Criteria` must contain bullet lines, and every bullet must include `: PASS`, `: FAIL`, or `: PARTIAL`.
- `## Linting / Type-Check` must start with `PASS` or `FAIL`.
- `## Issues / Blockers`, `## Notes for Verifier`, and `## Closeout (YYYY-MM-DD)` must not be empty.
- The closeout heading must use an ISO date.

### MAO build-to-validate dependency

The MAO gate reads the same contract. A build artifact is only transition-ready for validate when:

- the build contract is structurally valid
- `## Status` starts with `PASS` or `PARTIAL`
- every acceptance-criteria bullet resolves to `PASS` or `PARTIAL`
- `## Linting / Type-Check` starts with `PASS`

## Verify Result Contract

`verify-result.md` must use this structure:

```markdown
# Verify Result

## Plan
docs/current-plan.md

## Builder Result
build-result.md

## Status
PASS | FAIL | PARTIAL

## Criteria Review

### Criterion 1: <text from plan>
**Result:** PASS | FAIL | PARTIAL
**Evidence:** `path/to/file.py:42` — <relevant evidence>

## Issues Found
None | <issues with file and line references>

## Recommendations
None | <specific next actions>

## Closeout (YYYY-MM-DD)
<brief verification closeout summary>
```

### Verify rules

- `## Status` must start with `PASS`, `FAIL`, or `PARTIAL`.
- `## Criteria Review` must contain at least one `### Criterion ...` block.
- Every criterion block must include a non-empty `**Result:**` line and a non-empty `**Evidence:**` line.
- `## Plan`, `## Builder Result`, `## Issues Found`, `## Recommendations`, and `## Closeout (YYYY-MM-DD)` must not be empty.
- The closeout heading must use an ISO date.

## Change Discipline

When touching this contract:

- update `.cursor/hooks/artifact_contract.py`
- update prompt and command examples in the same change
- update validator and MAO tests in the same change
- run the workflow validation commands before claiming the contract is aligned
