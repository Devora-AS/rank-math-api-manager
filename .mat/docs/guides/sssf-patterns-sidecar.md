# SSSF patterns sidecar guide

- Purpose: Document what MAT **borrows** vs **rejects** from [disler/super-simple-software-factory](https://github.com/disler/super-simple-software-factory) (SSSF) and related external skills — complementary operator guidance only.
- Audience: Internal operators, parent orchestrators, and integrators evaluating SSSF-inspired roadmap items.
- Status: complete
- Last updated: 2026-08-31
- Path: `docs/guides/sssf-patterns-sidecar.md` (doc-test lock: `sssf-patterns-sidecar`)
- Mission: [`specs/sssf-patterns-mission.md`](../specs/sssf-patterns-mission.md) · slice `slice-3-sssf-sidecar` (**B13**)
- Extended by slice `S6-sssf-docs`: operator patterns **A7** (§5), **B1** (§6), **B2** (§7), **B6** (§8)

---

## 1. Purpose

**What this guide is:** A sidecar reference for SSSF-inspired **patterns** MAT may adopt in docs, hooks, validators, and operator discipline — without replacing MAT's Cursor-first runtime.

**What this guide is not:** A proposal to port SSSF's Python orchestrator, Pi harness, or SQLite-centric workflow as MAT's primary execution model. SSSF remains an **upstream reference**; MAT stays **file-handoff authoritative**.

**Authoritative handoffs (unchanged):** `docs/current-plan.md`, `build-result.md`, and `verify-result.md` are the gate truth for orchestrated runs. Hook advisory files, observability events, MAO todos, and research preflight outputs are **hints** — never substitutes for reading those three files before parent transitions. See [`workflow-artifact-contract.md`](../workflow-artifact-contract.md) and [`plan-contract.md`](../plan-contract.md).

---

## 2. Borrow — complementary patterns

These SSSF ideas align with MAT's existing direction and may ship as docs, optional hooks, or contract extensions:

| Pattern | SSSF reference | MAT posture |
| ------- | -------------- | ----------- |
| **Code-owned quality** | Quality commands live in repo scripts (`quality.py`, verify paths) — not "trust the agent said PASS" | MAT already routes through `bash scripts/phase1-verify.sh`, hook lint/type-check, and structured `build-result.md` / `verify-result.md`; extend with doctor honesty (**A1**) and placeholder banners (**B9**) |
| **Gate evidence** | `GateReport`-style per-check rows (`{item, ok, note}`) attached to handoffs | Optional `## Gate Evidence` in build handoffs (**C-A2**); advisory only; distinct from loop-policy `## Loop Iteration Log` |
| **Scope audit** | Post-build diff vs planned file set (`permissions.py`, protected paths) | Builder write-scope audit hook (**C-A3 / A3**); opt-in `CURSOR_MAO_BUILDER_SCOPE_AUDIT=1`; builds on `scripts/inspect_worktree_attribution.py` |
| **Placeholder discipline** | Detect verify/lint paths that echo success without running real commands | Doctor + hook advisory when quality commands are placeholders; pairs **A1** + **B9** — no fake-green research or lint |

**Operator rule:** Borrowed patterns **enhance evidence and honesty** around file handoffs; they do not create a second orchestrator or a parallel gate authority.

---

## 3. Reject — do not port as MAT runtime

Per SSSF × MAT research (2026-08-18) and [`ROADMAP.md`](../../ROADMAP.md) — explicit non-goals unless strategy reverses:

| Pattern | Why MAT rejects it |
| ------- | ------------------ |
| **Python orchestrator owning the graph** | Collides with Cursor parent/Task dispatch + canonical file handoffs; MAT hooks advise, they do not own spawn graphs |
| **Pi harness as default coding agent** | Dual stack; MAT is Cursor-first (subagents, hooks, worktrees) |
| **SQLite replacing file handoffs** | Loses hook-normalized Bun/Vue observability ingest and operator-readable gate artifacts; SQLite stays observability/runtime storage, not MAO truth |

**Do not promote** these as roadmap defaults. Experimental Later items (ADW CI sidecar, roster YAML, phase naming docs) may **cite** SSSF vocabulary while keeping Cursor parent orchestration unchanged.

---

## 4. External skill borrow

Upstream discovery/research skills are **Layer 0 preflight** candidates — not execution or MAO replacements. Full design: [`specs/mat-discovery-research-skills.md`](../specs/mat-discovery-research-skills.md).

| Upstream | Adopt (MAT-native posture) | Reject (do not port) |
| -------- | -------------------------- | -------------------- |
| [advise-project-approach](https://github.com/AaravKashyap12/advise-project-approach) (MIT, prompt-only v0.6.0) | **Gate discipline** — discovery-first checklist before planning depth; **provenance** — inline citations + pinned upstream SHA (`88f1ecc`); **read-only defaults** — landscape/comparables outputs under `specs/<slug>/preflight/`; no repo writes from preflight | Claude Agent SDK runtime loops; star-count-only ranking; auto-orchestration into `/mat-plan-team` |
| [neuroarxiv](https://github.com/UditAkhourii/neuroarxiv) (MIT, skill + optional Node CLI) | **Gate discipline** — Phase B only when novelty gate = `novel_research_required` **and** G2 human approval + cost confirmation; **provenance** — `THIRD_PARTY` MIT block + pin (`b5d20ef`); **read-only defaults** — abstract-only reads, bounded paper/category caps | Claude Agent SDK agent loop; **`npx skills@latest`** auto-install; upstream **`npm install`** as MAT dependency; **mandatory cloud research in CI** (`phase1-verify.sh` must stay offline-deterministic) |

**Combined wrapper (Later):** `mat-preflight-gated` orchestrates Phase A → optional Phase B with explicit gates; see discovery spec for novelty enum, G0–G7 approval gates, and boundary table vs `scout-report-suggest`, `/mat-prime`, and `docs-scraper`.

---

## 5. A7 — ADW CI sidecar operator pattern (optional)

SSSF keeps its deterministic quality phases in Python modules under an `adws/` directory (agentic developer workflows). MAT borrows the **stamp**, not the runtime: a product repo may keep a small `adws/` folder whose only job is to name **CI-only** deterministic quality phases that already exist as MAT commands.

**Cursor parent orchestration unchanged.** The sidecar is a CI convenience wrapper. It never spawns subagents, never writes `docs/current-plan.md` / `build-result.md` / `verify-result.md`, and never decides a MAO transition.

| Phase stamp | Wraps (MAT-owned command) | Runs where |
| ----------- | ------------------------- | ---------- |
| `adw_quality` | `bash scripts/phase1-verify.sh` (lint, type-check, docs contract tests) | CI job / operator shell |
| `adw_build_test` | Project build + targeted test commands named in the active plan | CI job / operator shell |

**Rules for an `adws/` sidecar:**

- **May:** shell out to MAT-owned scripts, print per-phase pass/fail, set a CI exit code, and emit optional `## Gate Evidence` rows for a later handoff.
- **Must not:** reimplement gate logic, parse or mutate handoff artifacts, call `TodoWrite`, or start any agent. It **never spawns subagents**.
- **Single source of truth:** if a stamp drifts from `bash scripts/phase1-verify.sh`, delete the stamp. MAT does not maintain two quality entrypoints.
- **Optional by default:** MAT ships no `adws/` directory; adopted repos add one only when their CI benefits from named phases.

Related: [`workflow-artifact-contract.md`](../workflow-artifact-contract.md) (`## Gate Evidence`), §2 **Code-owned quality**.

---

## 6. B1 — Phase primitive naming (lane map)

SSSF sequences work with `run.phase()` calls in Python. MAT reuses the **phase vocabulary only** as shared operator language across three lanes. **Python does not own the orchestration graph** in MAT: the Cursor parent orchestrator owns sequencing, retries, and subagent spawn, and file handoffs stay gate-authoritative.

| SSSF phase idea | MAT lane | Owner | Durable evidence |
| --------------- | -------- | ----- | ---------------- |
| Plan / spec phase | **operator lane** | Operator + parent orchestrator (`/mat-plan`, `/mat-plan-team`, `/mat-long-run`) | `docs/current-plan.md`, `docs/architecture/long-run-state.md` |
| Implement / test phase | **subagent lane** | `builder`, `test-writer` (parent dispatches) | `build-result.md` |
| Review / gate phase | **subagent lane** | `verifier` (read-only) + parent serialization | `verify-result.md` |
| Quality / observability phase | **hooks + CI lane** | `postToolUse` hooks, `scripts/phase1-verify.sh`, optional `adws/` stamp (§5) | Hook logs, CI output, advisory `artifacts/` files |

**Reading the map:**

- A "phase" is a **name for a step operators already run** — it does not introduce a scheduler, a state machine file, or a second gate authority.
- The **operator lane** decides what happens next; the **subagent lane** produces handoff artifacts; the **hooks + CI lane** only advises and reports.
- Lane names may appear in plans, prompts, and closeouts. They may **not** appear as an execution dependency (nothing in MAT reads a lane name to decide behavior).

---

## 7. B2 — Envelope correction loops via subagent follow-up

SSSF validates typed envelopes between phases and re-runs the producing step when an envelope is malformed. MAT's equivalent is a **narrow re-prompt** of the **same** subagent in the **same session**, instead of re-running the whole slice or spawning a fresh role.

**Envelope defect** here means a handoff that is structurally wrong, not work that is substantively wrong: for example `build-result.md` missing `## Acceptance Criteria`, an acceptance bullet without an explicit `: PASS` / `: PARTIAL` / `: FAIL`, a dropped or reordered `AC-N` identifier, or a `## Linting / Type-Check` row that does not resolve to `PASS` / `FAIL`.

| Defect | Detected by | Correction |
| ------ | ----------- | ---------- |
| Missing or malformed contract section | `.cursor/scripts/validate_artifacts.py`, parent transition check | Narrow re-prompt: name the section and the exact contract shape |
| `AC-N` identifiers dropped or reordered | Typed triad validation (**B3**, shipped) | Narrow re-prompt: restate the plan IDs and required order |
| Status row unparseable | Parent build→validate check | Narrow re-prompt: ask for one declared `Status` line only |

**Loop semantics (pairs with [`loop-policy.md`](../loop-policy.md)):**

- Classify envelope defects as **`correctable`** → action `retry`, bounded by `repair_attempt_limit` (default 3).
- Repeated identical defects hit the repeated-fingerprint rule (≥ 2) and **escalate** to the parent instead of looping.
- Record each correction attempt as a row in `## Loop Iteration Log` when loop policy is enabled for the run.

**Parent owns spawn.** Hooks may observe a malformed handoff and write advisory files, but no hook re-prompts a subagent, retries a role, or starts the verifier. The parent decides whether to re-prompt, escalate, or fail the slice — and the corrected `build-result.md` remains the gate artifact.

---

## 8. B6 — Test loop vs review loop (test-writer and verifier)

SSSF separates its SDLC test loop from its reviewer loop. MAT already ships both roles; this section makes the boundary explicit so operators stop routing review work to `test-writer` (or coverage work to `verifier`).

| | **test loop** (`test-writer`) | **review loop** (`verifier`) |
| --- | --- | --- |
| Goal | Add or strengthen deterministic regression coverage | Judge builder output against plan acceptance criteria |
| Writes | `tests/` only | Nothing — frontmatter `readonly: true` |
| Loop exit | Targeted tests run and pass (or a blocker is reported) | Every `AC-N` has PASS/FAIL with concrete evidence |
| Artifact | Test files + reported commands; builder folds results into `build-result.md` | Structured verify payload; the **parent serializes** `verify-result.md` |
| May fix code? | No — reports blockers instead of changing behavior | No — read-only, reports issues and recommendations |

**Anti-patterns:**

- `verifier` writing a test (or any file) to prove behavior — it must flag the gap in its structured payload instead.
- `test-writer` declaring an acceptance criterion PASS — coverage evidence is an input to the review loop, not a verdict.
- Treating a green targeted test run as a full-suite claim; only run-and-report what was actually executed.

**Scope note:** this section **does not reopen** the typed acceptance-ID triad (**B3**, shipped) — identifier alignment stays in [`workflow-artifact-contract.md`](../workflow-artifact-contract.md) and its validators. B6 is operator-facing loop separation only.

Prompts: [`.cursor/agents/test-writer.md`](../../.cursor/agents/test-writer.md), [`.cursor/agents/verifier.md`](../../.cursor/agents/verifier.md) · policy: [`role-write-policy.md`](../role-write-policy.md).

---

## 9. Truth hierarchy (quick reference)

1. **Canonical:** `docs/current-plan.md` → `build-result.md` → `verify-result.md`
2. **Contract semantics:** [`plan-contract.md`](../plan-contract.md), [`workflow-artifact-contract.md`](../workflow-artifact-contract.md)
3. **Preflight design (advisory until implemented):** [`mat-discovery-research-skills.md`](../specs/mat-discovery-research-skills.md)
4. **SSSF sidecar (this doc):** borrow/reject framing only
5. **Advisory:** hooks, MAO gate files, observability DB, external preflight artifacts

Parent orchestrators still run explicit transition checks before builder or verifier dispatch; see [`todo-orchestration.md`](../todo-orchestration-protocol.md).

---

## Related docs

- [`specs/mat-discovery-research-skills.md`](../specs/mat-discovery-research-skills.md) — Layer 0 preflight design, pins, gates
- [`plan-contract.md`](../plan-contract.md) — plan tiers, markers, truth hierarchy
- [`workflow-artifact-contract.md`](../workflow-artifact-contract.md) — build/verify handoff sections
- [`loop-policy.md`](../loop-policy.md) — retry taxonomy and budgets behind §7 envelope correction
- [`role-write-policy.md`](../role-write-policy.md) — per-role write scope behind §8 loop separation
- [`preflight-escalation-ladder.md`](../preflight-escalation-ladder.md) — planning → execution escalation
- [`ROADMAP.md`](../../ROADMAP.md) — SSSF-inspired Next/Later/Rejected inventory
- [`specs/sssf-patterns-mission.md`](../specs/sssf-patterns-mission.md) — multi-slice mission queue
