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
- AC-1: PASS — <brief evidence>
- AC-2: FAIL — <reason>

## Linting / Type-Check
PASS | FAIL
<optional supporting detail lines>

## Issues / Blockers
None | <open issues>

## Notes for Verifier
<specific guidance for verification>

## Closeout (YYYY-MM-DD)
<brief closeout summary>

## Trace Correlation
session_id: <optional>
conversation_id: <optional>
trace_run_id: <optional>
subagent_id: <optional>
parent_session_note: <optional freeform>
```

### Build rules

- `## Status` must start with `PASS`, `FAIL`, or `PARTIAL`.
- `## Changes Made` must contain at least one non-empty entry.
- `## Acceptance Criteria` must contain bullet lines, and every bullet must include `: PASS`, `: FAIL`, or `: PARTIAL`.
- When the active plan defines typed `AC-N` IDs, each build bullet must preserve the same ID and order.
- `## Linting / Type-Check` must start with `PASS` or `FAIL`.
- `## Issues / Blockers`, `## Notes for Verifier`, and `## Closeout (YYYY-MM-DD)` must not be empty.
- The closeout heading must use an ISO date.
- `## Trace Correlation` is **optional** — see [Optional Trace Correlation](#optional-trace-correlation).

### MAO build-to-validate dependency

The MAO gate reads the same contract. A build artifact is only transition-ready for validate when:

- the build contract is structurally valid
- `## Status` starts with `PASS` or `PARTIAL`
- every acceptance-criteria bullet resolves to `PASS` or `PARTIAL`
- `## Linting / Type-Check` starts with `PASS`

`## Trace Correlation` is **never** part of this MAO gate requirement. Absence of the section must not block build→validate.

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

### Criterion 1: AC-1 — <text from plan>
**Result:** PASS | FAIL | PARTIAL
**Evidence:** `path/to/file.py:42` — <relevant evidence>

## Issues Found
None | <issues with file and line references>

## Recommendations
None | <specific next actions>

## Closeout (YYYY-MM-DD)
<brief verification closeout summary>

## Trace Correlation
session_id: <optional>
conversation_id: <optional>
trace_run_id: <optional>
subagent_id: <optional>
parent_session_note: <optional freeform>
```

### Verify rules

- `## Status` must start with `PASS`, `FAIL`, or `PARTIAL`.
- `## Criteria Review` must contain at least one `### Criterion ...` block.
- Every criterion block must include a non-empty `**Result:**` line and a non-empty `**Evidence:**` line.
- When the active plan defines typed `AC-N` IDs, `Criterion N` and the explicit `AC-N` label must preserve the same plan order.
- `## Plan`, `## Builder Result`, `## Issues Found`, `## Recommendations`, and `## Closeout (YYYY-MM-DD)` must not be empty.
- The closeout heading must use an ISO date.
- `## Trace Correlation` is **optional** — see [Optional Trace Correlation](#optional-trace-correlation). Absence must not fail verify-result validation or MAO gates.

## Typed Output Triad

For active plans that use typed acceptance IDs, the canonical mapping is plan `AC-N` → build `AC-N` → verifier `Criterion N: AC-N`. The descriptive text may be shortened in downstream handoffs, but the identifier set and order must stay unchanged.

Example:

```markdown
# docs/current-plan.md
- [] **AC-1:** Contract alignment

# build-result.md
- AC-1: PASS — contract alignment is documented

# verify-result.md
### Criterion 1: AC-1 — Contract alignment
**Result:** PASS
**Evidence:** `docs/reference/workflow-artifact-contract.md` documents the triad.
```

`.cursor/hooks/artifact_contract.py` and `.cursor/scripts/validate_artifacts.py` soft-check the triad **only when** the active plan’s acceptance section contains at least one typed `AC-N` bullet. Plans without typed IDs are **grandfathered** (no triad warnings). When `build-result.md` or `verify-result.md` is omitted or still in progress, validators compare only the handoffs that were supplied — partial phases do not fail solely because downstream artifacts are missing.

### Relevant Files vs Tier 2c (planning validator)

These are separate contracts:

| Surface | What is enforced | Where |
|---------|------------------|-------|
| **Typed triad** | `AC-N` ID set and order across plan → build → verify | Soft inspection in `artifact_contract.py` / `validate_artifacts.py` when the plan uses typed IDs |
| **Tier 2c** | Every `## Relevant Files / Areas` list bullet starts with `[new]` or `[existing]` | `scripts/validate_planning_artifacts.py` on **solo** `/mat-plan` outputs at `specs/<slug>.md` only (grandfather registry for legacy specs) |
| **Execution Relevant Files** | Concrete path scoping habit for builders/verifiers | `docs/current-plan.md` and operator playbook — **not** Tier 2c CI on the execution projection |

Do not treat missing `[new]`/`[existing]` tags on `docs/current-plan.md` as a planning-validator failure; do treat untagged solo specs (non-grandfathered) as Tier 2c failures in `phase1-verify.sh` on the MAT source tree.

This check preserves traceability only. It does not create another status or gate authority: MAO transition readiness still comes from the existing build status, acceptance outcomes, and lint/type-check fields, while the parent owns transition decisions.

## Parent-owned verify serialization

**Decision (D2/E2):** The verifier subagent uses native frontmatter `readonly: true` and **must not** write `verify-result.md`. The **parent orchestrator** serializes the on-disk handoff from the verifier’s structured output.

See [`role-write-policy.md`](role-write-policy.md) for the ADR.

### Parent responsibilities

1. Spawn the verifier with instructions to return a structured verify payload (JSON or contract-shaped markdown **in chat**).
2. After the verifier completes, write `verify-result.md` so it matches the [Verify Result Contract](#verify-result-contract) exactly (including dated `## Closeout`).
3. Prefer `scripts/mat-scope-audit.py` helper `serialize_verify_result()` when converting a JSON payload to markdown.
4. Treat missing or incomplete structured output as a verifier failure / retry — do not invent PASS evidence.

### Verifier responsibilities

- Inspect plan + `build-result.md` with read-only tools only.
- Return structured `status`, `criteria[]` (`name` / `result` / `evidence`), `issues`, `recommendations`, and `closeout` / `closeout_date`.
- Do **not** create or edit `verify-result.md` (or any other file).

### MAO note

`MAO_TASK_CONTEXT_JSON` may still list `primary_artifact: "verify-result.md"` as the **logical** handoff name. File authorship is parent-owned; advisory scope audit expects **zero** verifier-introduced paths.

## Optional Trace Correlation

`## Trace Correlation` may appear on `build-result.md` and/or `verify-result.md` so operators can bridge git-tracked handoffs to Cursor session / agent / run identifiers for support and billing.

**Posture:** optional; **omit the whole section** when no IDs are known; **omit individual fields** when unknown. Never invent identifiers. IDs are best-effort and are **not** always available from the agent runtime.

**Not a MAO gate requirement:** required headings and MAO build→validate / verify parsing do **not** include Trace Correlation. Missing the section is valid. When the section **is** present, the runtime soft-checks a non-empty body and reasonable field keys (see `.cursor/hooks/artifact_contract.py`).

**Run manifest (N4):** optional `artifacts/mat-runs/<run-id>/manifest.json` is a derived advisory index (hashes + trace IDs). Stale hash mismatch is visible via `bash scripts/doctor.sh --run-manifest` or `mat_run_manifest.py check` — **`gate_impact: none`**; it does not change this contract or MAO gates. Operator flow: [`docs/architecture/orchestration-workflow.md`](orchestration-workflow.md#run-manifest-n4-advisory).

### Field glossary

| Field | Meaning | Typical source (best-effort) |
|-------|---------|------------------------------|
| `session_id` | Cursor / hook session identifier when present | Hook payload or env (`session_id`, `CURSOR_SESSION_ID`, …) via `session_id.py` |
| `conversation_id` | Conversation / chat thread id when distinct from session | Hook payload keys such as `conversation_id` |
| `trace_run_id` | Operator/orchestration trace run folder id | `CURSOR_AGENT_TRACE_RUN_ID` / `CURSOR_ORCHESTRATION_TRACE_RUN_ID` via `spawn_trace.resolve_trace_run_id` |
| `subagent_id` | Builder / verifier (or other) subagent id when known | Parent spawn / Task metadata when exposed |
| `parent_session_note` | Optional freeform note linking parent context | Operator or parent-orchestrator prose |

Suggested shape (any subset of known keys; bullet or `key: value` lines):

```markdown
## Trace Correlation
- session_id: <value>
- conversation_id: <value>
- trace_run_id: <value>
- subagent_id: <value>
- parent_session_note: <optional note>
```

## Optional Loop Iteration Log

`## Loop Iteration Log` may appear on `build-result.md` when MAT loop policy is enabled (`CURSOR_MAT_LOOP_POLICY=1`) for orchestrated runs. It records one row per loop iteration for operator audit without replaying full transcripts.

**Posture:** When `CURSOR_MAT_LOOP_POLICY` is unset or `0`, the section is optional — the parser soft-validates when present. When `CURSOR_MAT_LOOP_POLICY=1`, the section is **required** for orchestrated runs whose slice class is **not** `lite` or `docs` (strict validation via `.cursor/scripts/validate_artifacts.py` / `artifact_contract.py`).

**Not a MAO transition gate by itself.** Missing the section fails artifact validation only under the opt-in policy rules above — it does not replace `docs/current-plan.md` / build→validate file checks.

### Suggested shape

Markdown table (preferred) or bullet lines:

```markdown
## Loop Iteration Log

| iter | action | failure_class | fingerprint | note |
|------|--------|---------------|-------------|------|
| 1 | retry | transient | a1b2c3d4 | ruff timeout |
| 2 | escalate | correctable | e5f6g7h8 | same lint error twice |
```

Bullet alternative:

```markdown
## Loop Iteration Log
- iter 1: retry — transient — fp:a1b2c3d4 — ruff timeout
```

When present, the section must contain at least one non-header table row or bullet entry. See `docs/reference/loop-policy.md` for loop lifecycle and budget rules.

## Optional Gate Evidence

`## Gate Evidence` may appear on **`build-result.md` only**. It records SSSF GateReport-style per-check rows (`item`, `ok`, `note`) for operator audit without replacing MAO transition gates.

**Posture:** Optional — the parser **soft-validates when present** (at least one data row with `item` and `ok`). When absent, no issues are raised. **Not a MAO transition gate.** Distinct from `## Loop Iteration Log` (loop-policy iteration audit).

### Suggested shape

Markdown table (preferred):

```markdown
## Gate Evidence

| item | ok | note |
|------|-----|------|
| ruff check | true | clean |
| unittest gate_evidence | PASS | targeted subset green |
```

Bullet alternative:

```markdown
## Gate Evidence
- item: ruff check | ok: true | note: clean
```

When present, the section must contain at least one non-header table row or bullet entry with both `item` and `ok` fields. The `ok` field accepts `true`/`false` or `PASS`/`FAIL` (case-insensitive).

**Observability (B5):** the dashboard may display these rows via `GET /api/runtime/gate-evidence` and the Gate evidence sidebar panel — **advisory only**. See [`docs/architecture/events-and-visualization.md`](../architecture/events-and-visualization.md) (Gate evidence widget). Dashboard display does **not** change MAO build→validate readiness or replace `## Status` / `## Acceptance Criteria` / `## Linting / Type-Check`.

## Change Discipline

When touching this contract:

- update `.cursor/hooks/artifact_contract.py`
- update prompt and command examples in the same change
- update validator and MAO tests in the same change
- run the workflow validation commands before claiming the contract is aligned

## In-plan status markers vs gate-authoritative handoffs

Plan contract v0.1 (Slice 3) allows **advisory** progress markers on checklist lines in `docs/current-plan.md`:

| Marker | Meaning |
|--------|---------|
| `[]` | Idle / not started |
| `[wip]` | In progress |
| `[x]` | Done for this slice |
| `[f]` | Failed / blocked (reason on same line) |

**Advisory:** in-plan markers on execution plan checklists — builder mutates in-place during build; parent may set `[wip]` at slice start; verifier is read-only (warn-not-fail when markers disagree with a passing build handoff).

**Gate-authoritative:** this document’s **`build-result.md`** and **`verify-result.md`** sections — especially `## Status`, `## Acceptance Criteria` (`: PASS` / `: PARTIAL` / `: FAIL`), and `## Linting / Type-Check` — remain the sole inputs for MAO **build→validate** transition checks. In-plan `[x]` does not replace a PASS row in `build-result.md`.

See [`docs/architecture/plan-contract.md`](plan-contract.md) and design spec Decision D in [`specs/shared-plan-contract.md`](specs/shared-plan-contract.md).
