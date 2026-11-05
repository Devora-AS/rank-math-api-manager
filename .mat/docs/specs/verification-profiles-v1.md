# Verification profile matrix (v1)

**Status:** Spec authored (normative v1 design contract) — 2026-08-24 `/mat-plan-team` documentation cycle
**Tier:** standard
**Task type:** `feature`
**Complexity:** `medium`
**ROADMAP:** E3

> This document is the **normative design contract** for named Phase 1 verification profiles and honest green status. Operator-facing matrix lives in `docs/reference/verification-profiles.md`. Implementation already exists from a prior `/mat-long-run` slice; this cycle does **not** claim a new implementation complete.

## Task Description

Define the authoritative v1 contract for MAT verification profiles: four named profiles (`source-full`, `source-python-only`, `adopted-operational`, `adopted-contract`), pass/fail/skip semantics with mandatory skip reasons, placeholder-command restrictions, CI vs local defaults, machine-readable `verification-manifest.json` expectations, stable `CHECK_ID` policy, and required evidence per check. Align with ROADMAP E3 acceptance bullets. **E3 has no hard dependency on D1** and may be planned in parallel; **D2 depends on both** D1 and E3.

## Objective

Ensure every green Phase 1 verification run:

1. States which profile executed.
2. Emits (or can emit) a manifest with honest per-check `pass` / `fail` / `skip` + reason.
3. Never labels a skip as pass, and never records pass for placeholder verify commands.
4. Documents CI (`source-full` + adopted-contract fixture) vs local default selection.

## Scope

### In scope (contract)

- Profile registry definitions and normative behavior table
- Pass / fail / skip semantics and overall aggregation
- Placeholder-command guard
- Manifest schema expectations (`artifacts/verification-manifest.schema.json`)
- Default runtime path `artifacts/phase1/verification-manifest.json` (gitignored)
- CI vs local behavior and doctor guidance surface
- Stable `CHECK_ID` policy
- Cross-refs to operator doc and `scripts/verification_profiles.py`

### Out of scope (this contract)

- Role scope audit enforcement (**D2**) beyond noting `scope_audit` as a check id
- Changing the underlying Phase 1 check bodies beyond profile instrumentation semantics
- Replacing file handoffs (`docs/current-plan.md`, `build-result.md`, `verify-result.md`) with the manifest
- Auto-spawning subagents from profile/manifest state
- Re-authoring implementation or CI in this documentation cycle

## Normative requirements

These rules are **normative** for v1. Implementations that claim E3 compliance MUST satisfy them.

### N1 — Profile definitions

Exactly four profile ids are valid in v1 (`PROFILE_IDS`):

| Profile | Repo layout | Normative behavior |
|---------|-------------|--------------------|
| `source-full` | `source` (no `.mat/README.md`) | Run all Phase 1 checks including Bun server/client |
| `source-python-only` | `source` | Python/docs checks run; Bun server/client checks MUST be recorded as **skip** with non-empty reason (never pass) |
| `adopted-operational` | `adopted` (`.mat/README.md` present) | Default adopted profile; source-only checks skipped with reason; `.mat/tests` skipped unless opted in |
| `adopted-contract` | `adopted` | Same adopted skips for source-only checks, but runs packaged `.mat/tests` (`PHASE1_VERIFY_ADOPTED_CONTRACT_TESTS=1` or equivalent profile path) |

Unknown profile ids MUST be rejected.

### N2 — Pass / fail / skip semantics

1. Per-check `status` MUST be one of: `pass`, `fail`, `skip`.
2. **skip ≠ pass.** A skipped check MUST use `status: skip` and MUST include a **non-empty** `reason`.
3. A reason that indicates skipping (for example contains “skip”, “skipped”, “omitted”, “not run”, “profile excludes”) MUST NOT be paired with `status: pass`.
4. Manifest `overall` MUST be `pass` or `fail` only. Any check with `status: fail` makes `overall: fail`; otherwise `overall: pass` (skips do not fail the overall result by themselves).
5. Recording APIs MUST reject invalid combinations rather than coercing skip into pass.

### N3 — Placeholder-command restrictions

1. Empty commands, `true`, `:`, `/bin/true`, `/usr/bin/true`, and equivalent no-op placeholders MUST NOT be allowed to record `status: pass`.
2. Attempting to record pass for a placeholder MUST raise / fail closed (implementation: `assert_verify_command_allows_pass` in `scripts/verification_profiles.py`).
3. Doctor / honesty banners MAY additionally warn on placeholder quality commands; that is advisory relative to this hard guard.

### N4 — Defaults and CLI

1. Default profile selection:
   - Source tree → `source-full`
   - Adopted sidecar → `adopted-operational`
2. `bash scripts/phase1-verify.sh` MUST remain usable without flags (auto-select default).
3. Override MUST be supported via `--profile <name>` and optional `--manifest <path>`.
4. When profiles are packaged, runs SHOULD print a profile banner stating the active profile.

### N5 — Manifest schema and evidence

1. Tracked schema path: `artifacts/verification-manifest.schema.json`.
2. Default runtime manifest path: `artifacts/phase1/verification-manifest.json` (gitignored).
3. Manifest MUST include: `profile`, `repo_layout` (`source`|`adopted`), `started_at`, `finished_at`, `overall`, `checks`.
4. Each check object MUST include: `id`, `status`, `reason`, `duration_ms` (non-negative integer).
5. **Required evidence per check:** stable `id`, terminal `status`, human-readable `reason` (required non-empty when `skip`; recommended for `pass`/`fail`), and `duration_ms`.
6. Schema validation MUST reject manifests that violate these shapes.

### N6 — CHECK_ID stability

1. Check ids are part of the public contract for CI consumers. v1 stable ids include (non-exhaustive of future growth, but normative when present):

   `workflow_artifacts`, `closeout_coherence`, `planning_artifacts`, `cost_context_hygiene`, `cursor_capability_assets`, `command_registry`, `agent_roster`, `hooks_json_parse`, `workflow_surfaces`, `script_executability`, `python_unittest`, `legacy_fingerprints`, `mcp_json`, `scope_audit`, `bun_server_smoke`, `bun_client`.

   **`phase1_verify_exit`** is an **early-exit** id recorded only when `phase1-verify.sh` aborts before clean completion. It is **not** part of the stable pass manifest set and MUST NOT appear when `overall: pass`.

2. Renaming or removing a CHECK_ID is a **breaking** change and REQUIRES an amendment to this spec plus consumer notice.
3. Adding a new CHECK_ID is allowed in a minor profile revision if documented in Amendments and operator docs.
4. When `overall: pass`, the manifest MUST include each stable CHECK_ID exactly once; checks planned as `run` for the profile MUST have `status: pass` (not `skip`); profile MUST be compatible with `repo_layout` (`source-*` → `source`, `adopted-*` → `adopted`).
5. **`source-full`** MUST fail (not skip) when Bun server/client checks cannot run; operators use **`source-python-only`** for Bun-free local loops.

### N7 — CI vs local

1. **Release CI (source):** MUST run `source-full` explicitly and SHOULD write a manifest path, for example:

   `bash scripts/phase1-verify.sh --profile source-full --manifest artifacts/phase1/verification-manifest.json`

2. **Adopted fixture CI:** MUST label and run `adopted-contract` (for example via `scripts/ci/run-adopted-contract-verify.sh`), not silently reuse `source-full` semantics on an adopted tree.
3. **Local default:** auto-select as in N4; operators MAY choose `source-python-only` for Bun-free loops.
4. Doctor SHOULD expose profile guidance (`bash scripts/doctor.sh --verification-profile` and/or default output section).

## Assumptions

1. MAT source trees lack `.mat/README.md`; adopted sidecars have it (`detect_repo_layout`).
2. Existing Phase 1 check bodies remain the source of truth for *what* runs; profiles govern *which* checks run vs skip and how status is recorded.
3. Runtime manifests are gitignored; the JSON schema is tracked.
4. E3 may ship and be documented without waiting on D1; D2 consumes trustworthy profiles later.

## Non-Goals

- Auto-spawning subagents from profile state
- Replacing canonical file handoffs with the manifest as gate authority
- Broad Bun/Python toolchain upgrades unrelated to profiling
- Hard dependency on `specs/cursor-compatibility-v1.md` (D1) for E3 validity
- Claiming this documentation cycle re-ships implementation

## Problem Statement

Green `phase1-verify.sh` exits historically did not state which profile ran. Skips (adopted sidecar, missing Bun, env flags) were buried in logs. Operators cannot trust CI green without knowing what was skipped vs passed. ROADMAP E3 requires a normative matrix and honest manifest semantics.

## Solution Approach

1. Register four named profiles with deterministic planned skip sets.
2. Record each check through a helper that enforces skip≠pass and placeholder guards.
3. Emit `verification-manifest.json` conforming to the tracked schema.
4. Document the matrix for operators in `docs/reference/verification-profiles.md`; keep this file as the normative contract.
5. Make CI call `source-full` and an `adopted-contract` fixture explicitly.

## Relevant Files / Areas

- [existing] `scripts/verification_profiles.py` — registry, recording, schema validation, CLI
- [existing] `artifacts/verification-manifest.schema.json` — tracked manifest schema
- [existing] `docs/reference/verification-profiles.md` — operator matrix
- [existing] `tests/test_verification_profiles.py` — schema, skip≠pass, placeholder guard
- [existing] `scripts/phase1-verify.sh` — `--profile` / `--manifest` instrumentation
- [existing] `scripts/doctor.sh` — profile guidance
- [existing] `.github/workflows/phase1-verify.yml` — CI explicit `source-full`
- [existing] `scripts/ci/run-adopted-contract-verify.sh` — adopted-contract fixture
- [existing] `ROADMAP.md` — E3 queue row and acceptance bullets
- [existing] `specs/cursor-compatibility-v1.md` — D1 (parallel; D2 depends on both)
- [existing] `docs/reference/role-write-policy.md` — downstream D2 consumer note

## Task Traceability

| ID | Statement | ROADMAP / evidence |
|----|-----------|--------------------|
| SPEC-E3-001 | Four v1 profiles defined with normative behavior | ROADMAP E3 Goal |
| SPEC-E3-002 | Manifest records pass/fail/skip/reason; skip≠pass | ROADMAP E3 Goal / Acceptance |
| SPEC-E3-003 | Placeholder verify commands cannot report PASS | ROADMAP E3 Acceptance |
| SPEC-E3-004 | CI runs `source-full` + adopted-contract fixture | ROADMAP E3 Acceptance |
| SPEC-E3-005 | Operator doc documents matrix | `docs/reference/verification-profiles.md` |
| SPEC-E3-006 | Spec authored; no hard dep on D1; D2 depends on D1+E3 | This cycle; ROADMAP Depends on lines |
| AC-E3-1…AC-E3-6 | Mirror `docs/current-plan.md` documentation acceptance criteria | Parent orchestration plan |

## Testing Strategy

### Per-phase validation loops (loop until pass)

Run each phase command in a loop until pass before advancing.

| Phase | Command | Loop until pass |
|-------|---------|-----------------|
| Spec contract | `python3 scripts/validate_planning_artifacts.py` | Spec paths pass Tier 2 — loop until pass |
| Unit | `python3 -m unittest tests.test_verification_profiles -v` | All green — loop until pass |
| Integration | `bash scripts/phase1-verify.sh --profile source-full --manifest artifacts/phase1/verification-manifest.json` | exit 0 + valid manifest — loop until pass |
| Default path | `bash scripts/phase1-verify.sh` | exit 0 with auto-selected profile — loop until pass |

### Global validation commands (before handoff)

1. `python3 scripts/validate_planning_artifacts.py`
2. `python3 -m unittest tests.test_verification_profiles -v`
3. `bash scripts/phase1-verify.sh --profile source-full`

## Acceptance Criteria

Documentation-cycle criteria (this authoring pass) map to `docs/current-plan.md`:

- **AC-E3-1:** Spec defines all four v1 profiles with a normative behavior table.
- **AC-E3-2:** Spec normatively states pass/fail/skip semantics (`skip ≠ pass`, non-empty skip reason).
- **AC-E3-3:** Spec documents placeholder-command restrictions and required evidence fields in the manifest.
- **AC-E3-4:** Spec covers CI (`source-full` + adopted-contract fixture) vs local default profile selection.
- **AC-E3-5:** Spec documents `verification-manifest.json` schema expectations and stable CHECK_ID policy.
- **AC-E3-6:** Tier 2 solo-plan section order valid; cross-refs to D2 dependency honest (E3 has no hard dep on D1).

Shipped implementation criteria (prior long-run; retained for contract completeness):

- **AC-IMPL-1:** `phase1-verify.sh --profile source-full --manifest …` writes a valid manifest with `overall: pass` on a green source tree.
- **AC-IMPL-2:** Skipped checks record `status: skip` + reason — never `pass`.
- **AC-IMPL-3:** Operator doc documents all v1 profiles.
- **AC-IMPL-4:** CI workflow uses explicit `source-full`; adopted fixture labeled `adopted-contract`.
- **AC-IMPL-5:** `doctor.sh` exposes profile guidance.
- **AC-IMPL-6:** Unit tests cover placeholder guard and manifest schema validation.

## Risks and Open Questions

### Unresolved-risk boundaries

- CHECK_ID renames break CI consumers — treat as breaking (N6).
- Adopted fixture timing in CI may skip Bun via env while still labeling profile `adopted-contract`; profile label must remain honest.
- Placeholder guard must not false-positive legitimate short but real commands.
- Manifest is **advisory evidence**, not a replacement for tracked handoff files.

### Open questions

- Whether future profiles (for example client-only) should be additive ids or flags inside `source-full` — deferred; requires amendment.
- How strictly CI should fail if manifest write fails mid-run — implementation should prefer fail-closed once profiles are packaged; document any fail-open exception in Amendments.

## Compatibility / version assumptions

| Assumption | Contract |
|------------|----------|
| Profile set v1 | Exactly the four ids in N1 |
| Schema | `artifacts/verification-manifest.schema.json` title/shape as shipped |
| Repo layout detection | `.mat/README.md` ⇒ adopted; else source |
| Relation to D1 | **No hard dependency**; may plan/implement in parallel |
| Relation to D2 | D2 **Depends on** D1 **and** E3 (trustworthy verify profiles) |

## Dependencies

- **Foundational for E3:** none (ROADMAP: Depends on none; may plan in parallel with D1).
- **Parallel peer:** `specs/cursor-compatibility-v1.md` (D1/E1).
- **Downstream:** D2 / E2 role scope audit (uses E3 profiles for trustworthy green status).

## Verification methods

1. Tier 2 planning validation: `python3 scripts/validate_planning_artifacts.py`.
2. Unit tests: `python3 -m unittest tests.test_verification_profiles -v`.
3. Integration: `bash scripts/phase1-verify.sh --profile source-full --manifest artifacts/phase1/verification-manifest.json` then schema-validate the manifest.
4. Spot-check operator doc `docs/reference/verification-profiles.md` against N1–N7.
5. Spot-check CI workflow and `scripts/ci/run-adopted-contract-verify.sh` for explicit profile labels.

## Amendments

- 2026-08-24T10:30:00Z — orchestrator — Initial spec for slice 2.
- 2026-08-24T12:45:00Z — builder — Expanded solo-plan required sections for Tier 2 validation.
- 2026-08-24T13:30:00Z — builder — Normative v1 design contract rewrite for `/mat-plan-team` documentation cycle (Status: spec authored; Normative requirements; honest D1 parallel / D2 dependency; no production code changes).
- 2026-08-24T21:45:00Z — builder — Audit remediation: `source-full` fail-closed on Bun skips; green manifest requires full stable CHECK_ID set + profile/layout compatibility; document `phase1_verify_exit` as early-exit namespace.
- 2026-09-11T08:00:00Z — builder — E3 integrity closeout: composed EXIT handler in `phase1-verify.sh` (bun cleanup + single finalization); forced post–bun-server client failure must emit complete failed manifest with `phase1_verify_exit`; regression `Phase1VerifyExitTrapTest`.

## Recommended Next Command

```txt
/mat-plan-team continue — verifier reads specs/verification-profiles-v1.md against docs/current-plan.md AC-E3-*
```
