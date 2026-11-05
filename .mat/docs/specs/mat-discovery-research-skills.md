# MAT discovery / research skills — design spec

**Status:** Design-only — defers `.cursor/skills/` implementation to **Later** (ROADMAP.md *Discovery & research skills* theme).
**Purpose:** Single canonical design for MAT-native Layer 0 preflight adaptations of upstream [advise-project-approach](https://github.com/AaravKashyap12/advise-project-approach) and [neuroarxiv](https://github.com/UditAkhourii/neuroarxiv). File handoffs and MAO gates stay authoritative; these skills guide planning depth only.
**Mission link:** [`specs/sssf-patterns-mission.md`](sssf-patterns-mission.md) · slice `slice-2-discovery-spec`
**Last updated:** 2026-08-21

---

## Executive summary

MAT adopts a **discovery-first, research-on-novelty-only** Layer 0 preflight model before `/mat-plan`, `/mat-plan-onboarding`, or execution projection. Phase A (landscape / comparables) runs by default when the operator invokes preflight; Phase B (neuroarxiv literature scan) runs **only** when the novelty gate resolves to `novel_research_required` **and** the operator passes **G2** (human approval + cost confirmation). A combined wrapper skill directory **`mat-preflight-gated`** orchestrates both phases with explicit gates — it never auto-escalates, never holds live MAO authority, and never runs in CI.

---

## Non-goals

This spec and any future implementation **must not**:

| Non-goal | Rationale |
|----------|-----------|
| **Auto-orchestration** | Skills do not spawn `/mat-plan-team`, builder, or verifier; parent owns execution entry. |
| **Live MAO authority** | Cursor To-dos and hook advisory files do not become preflight truth; `docs/current-plan.md` → `build-result.md` → `verify-result.md` stay canonical. |
| **Mandatory external API in CI** | arXiv, community research, or upstream CLI fetches are operator-opt-in only; `phase1-verify.sh` must not require network research. |
| **`npx skills@latest`** | No auto-install of upstream skill packs; vendoring is G1-gated with pinned SHAs. |
| **Upstream `npm install` in MAT flows** | neuroarxiv's optional Node CLI is not a MAT dependency; prefer prompt-only or optional Python fetch scripts documented in Later implementation. |
| **Replace in-repo investigation** | `scout-report-suggest` remains the path for bug/root-cause analysis inside the repository. |
| **Replace session priming** | `/mat-prime` remains the session context loader; preflight does not dump whole-repo context by default. |
| **Replace URL doc capture** | `docs-scraper` remains the path for saving fetched docs to `ai_docs/`. |

---

## Layer 0 preflight model

Layer 0 sits **below** the planning preflight ladder ([`docs/architecture/preflight-escalation-ladder.md`](../preflight-escalation-ladder.md) Layer 1–3). It answers: *"Before we choose planning depth, do we understand the problem landscape — and is external literature research justified?"*

```text
Operator request
    │
    ▼
Layer 0 — mat-preflight-gated (optional, advisory)
    │  Phase A: advise-project-approach (discovery)
    │  → landscape.md, candidates.json, novelty-gate.json
    │
    ├─ existing_sufficient / integrate_and_extend → hand off to /mat-plan (no neuroarxiv)
    ├─ inconclusive → Open Decisions; operator chooses depth or more discovery
    └─ novel_research_required + G2 approved
           │
           ▼
       Phase B: neuroarxiv (bounded literature scan)
           → arxiv-synthesis.md, arxiv-papers.json
    │
    ▼
Layer 1 — planning depth (solo_plan_only | ready_for_execution_handoff | needs_plan_onboarding)
    │
    ▼
Layer 2 — command depth (/mat-plan | /mat-plan-onboarding | /mat-plan-update)
    │
    ▼
Layer 3 — execution mode (inline | builder_plus_verifier | parallel_spawn)
```

**Discovery-first:** Phase A checklist must complete (or explicitly defer items in `novelty-gate.json`) before any neuroarxiv fan-out.

**Research-on-novelty only:** Phase B is denied unless all observable neuroarxiv escalation criteria pass **and** G2 is approved.

---

## Upstream borrow

| Upstream | License | Form | Pin (commit) | MAT posture |
|----------|---------|------|--------------|-------------|
| [advise-project-approach](https://github.com/AaravKashyap12/advise-project-approach) | MIT | Prompt-only skill (v0.6.0 semantics) | `88f1ecc` | Adopt intake gate, comparables framing, cost/launch modes; reject star-count-only ranking and Claude Agent SDK runtime. |
| [neuroarxiv](https://github.com/UditAkhourii/neuroarxiv) | MIT | Skill + optional Node CLI | `b5d20ef` | Adopt gated literature scan, abstract-only reads, convergence to one recommendation; reject SDK agent loop, mandatory npm install, uncapped fan-out. |

### THIRD_PARTY — MIT notices

When MAT-native skills ship (Later), each borrowed skill directory must include a short **THIRD_PARTY** block in `SKILL.md`:

```markdown
## THIRD_PARTY — MIT

Portions adapted from advise-project-approach (MIT)
- Upstream: https://github.com/AaravKashyap12/advise-project-approach
- Pin: 88f1ecc (v0.6.0 prompt-only reference)
- License: MIT (see repository LICENSE)

Portions adapted from neuroarxiv (MIT)
- Upstream: https://github.com/UditAkhourii/neuroarxiv
- Pin: b5d20ef
- License: MIT (see upstream LICENSE when vendored)
```

MAT source repo **A11** SPDX `LICENSE` (MIT) satisfies the operator requirement to land license file before neuroarxiv skill promotion ([`specs/sssf-patterns-mission.md`](sssf-patterns-mission.md)).

### Reject list (do not port)

- Claude Agent SDK orchestration loops
- `npx skills@latest` or implicit upstream skill installation
- Mandatory cloud / social research in CI
- Uncapped parallel subagents or paper reads
- Treating research output as MAO or build/verify gate truth

---

## Boundary table — vs existing MAT surfaces

| Surface | Role | When to use | Preflight skills do **not** |
|---------|------|-------------|----------------------------|
| **`scout-report-suggest`** | Read-only **in-repo** investigation; SCOUT REPORT with file/line evidence | Bugs, regressions, "where is X implemented?", root-cause analysis | Replace scout for codebase questions; run scout for external landscape |
| **`/mat-prime`** | Session **context loader** — project map, stack, conventions summary | New session orientation; broad "what is this repo?" | Substitute for prime at session start; load whole `docs/` tree by default |
| **`docs-scraper`** | Fetch **known URLs** → save markdown under `ai_docs/` | Vendor docs, API references, pages the operator names | Generic arXiv search; discovery comparables; auto-fetch without URL list |
| **`mat-preflight-gated`** (Later) | Layer 0 **external landscape + optional literature** before planning | Novel domains, build-vs-buy, unclear comparables, research-backed mechanism choice | Execute code, modify repo, start MAO cycles, block build/verify |

**Pairing:** Preflight may **cite** paths discovered by scout or docs saved by docs-scraper, but each tool keeps a single primary job.

---

## Novelty gate enum

Recorded in `specs/<slug>/preflight/novelty-gate.json` (schema TBD at implementation; fields below are normative for this design).

| Value | Meaning | Next step |
|-------|---------|-----------|
| `existing_sufficient` | Repo, docs, or prior specs already cover the approach; no external research justified | Proceed to `/mat-plan` with bounded Relevant Files |
| `integrate_and_extend` | Known pattern exists; work is integration/extension, not greenfield research | Proceed to `/mat-plan` or `/mat-plan-onboarding` per scope |
| `novel_research_required` | Observable criteria below all pass; operator may approve G2 for neuroarxiv | Phase B allowed **only after G2** |
| `inconclusive` | Checklist incomplete, conflicting evidence, or criteria partially met | Record Open Decisions; do **not** auto-escalate to neuroarxiv |

### Observable neuroarxiv escalation criteria

All four must be **true** to set (or maintain) `novel_research_required`. Each is auditable in `novelty-gate.json`:

| # | Criterion | Observable signal |
|---|-----------|-------------------|
| 1 | **Closed-scope deny** | Phase A intake explicitly rejects a closed-scope shortcut (e.g. "just use library X" without mechanism validation) — recorded as `closed_scope_denied: true` with reason string |
| 2 | **Technical-mechanism present** | Task requires choosing or validating a **technical mechanism** (algorithm, architecture pattern, protocol), not only product/process framing — `technical_mechanism_present: true` with one-line mechanism description |
| 3 | **Rework-cost threshold** | Estimated cost of wrong approach exceeds preflight budget — `rework_cost_threshold_met: true` with operator-visible estimate (time, risk, or dependency blast radius) |
| 4 | **No recent duplicate cache hit** | No matching entry in optional shared cache `specs/_research-cache/` (topic slug, default TTL 30 days) — `cache_hit: false` or `cache_slug` absent/stale |

If any criterion is false or missing, gate **must not** be `novel_research_required` (use `integrate_and_extend`, `existing_sufficient`, or `inconclusive`).

---

## Approval gates G0–G7

Gates are **human or operator explicit** checkpoints. Hooks do not enforce them; artifacts record pass/fail for audit.

| Gate | Name | Requirement | Default |
|------|------|-------------|---------|
| **G0** | Preflight task acceptance | Operator invokes Layer 0 for this slug; vague requests complete advise intake checklist first | Required before Phase A |
| **G1** | Vendoring / upstream promotion | Before copying upstream skill text into `.cursor/skills/`, operator confirms pin SHAs (`88f1ecc`, `b5d20ef`) and THIRD_PARTY MIT block | Off until Later implementation |
| **G2** | **Neuroarxiv human approval + cost confirmation** | Operator explicitly approves literature scan **and** acknowledges session cost (papers × subagents, API usage) | **Denied by default**; required before Phase B |
| **G3** | Community research opt-in | X / Reddit / YouTube / similar social sources | **Opt-in only**; default off |
| **G4** | Neuroarxiv fan-out | Parallel read-only paper subagents and category breadth | Capped by MAT limits (≤8 paper reads, ≤3 arXiv categories); no fan-out without G2 |
| **G5** | Agent-Reach | External "agent reach" / broad web automation tools (upstream Agent-Reach class integrations) | **Off by default**; separate operator opt-in if ever added |
| **G6** | Planning projection | Human approval before writing execution projection to `docs/current-plan.md` | Required per [`docs/architecture/plan-contract.md`](../plan-contract.md) |
| **G7** | Preflight artifact review | Operator confirms preflight outputs reviewed; inline citations present for external claims | Required before `/mat-plan-team` or long-run slice start |

**G2 detail (normative):** Phase B must not start until the operator sends an in-thread approval that includes (a) consent to neuroarxiv and (b) explicit cost acknowledgment (e.g. expected paper count ≤8, categories ≤3). The combined wrapper skill documents this as a hard stop.

---

## Combined wrapper — `mat-preflight-gated`

**Operator decision (resolved):** ship one combined skill directory:

```text
.cursor/skills/mat-preflight-gated/
  SKILL.md          # Phase A → gate → Phase B orchestration
```

**Phase flow:**

1. Run advise-project-approach protocol (prompt-only MAT adaptation).
2. Write `landscape.md`, `candidates.json`, `novelty-gate.json`.
3. If gate = `novel_research_required`, **stop** and request G2.
4. On G2 approval only, run neuroarxiv protocol (bounded).
5. Emit handoff hints for `/mat-plan` or `/mat-plan-onboarding`: Relevant Files `[new]`/`[existing]`, Open Decisions, recommended planning depth — **not** auto-written execution plans.

Atomic skills (`advise-project-approach`, `neuroarxiv`) may ship as separate directories Later; the wrapper `@`-invokes or sequences them without merging responsibilities.

---

## Provenance

**Minimum (operator decision — resolved):** **inline citations only** in preflight markdown/json (URLs, arXiv IDs, upstream repo links, pin SHAs). No per-task `manifest.json` requirement.

**Optional advisory:** run logs under `artifacts/external-skills/` (gitignored) may append fetch timestamps, paper IDs, and gate decisions for operator audit — never CI-required, never MAO authority.

Each external claim in `landscape.md` or `arxiv-synthesis.md` should cite source inline, e.g. `(arXiv:2401.01234)` or `(upstream: advise-project-approach@88f1ecc)`.

---

## Artifact contract

All preflight outputs live under **`specs/<slug>/preflight/`** (tracked, planning-adjacent — not MAO handoffs).

| File | Phase | When written | Purpose |
|------|-------|--------------|---------|
| `landscape.md` | A | Always (Phase A complete) | Comparables, constraints, cost framing, discovery checklist |
| `candidates.json` | A | When comparables exist | Structured candidate list (name, source, notes) |
| `novelty-gate.json` | A | Always | Gate enum + observable criteria booleans + timestamps |
| `arxiv-synthesis.md` | B | G2 approved + neuroarxiv run | Single converged recommendation with citations |
| `arxiv-papers.json` | B | Same | Paper metadata (id, title, categories, score notes); ≤8 entries |

Optional shared cache (Later): `specs/_research-cache/<topic-slug>.json` — duplicate-run suppression for criterion 4.

Advisory logs (optional): `artifacts/external-skills/<slug>-<date>.jsonl`.

---

## MAT caps (normative)

Per preflight run (design defaults; implementation must not exceed without operator override documented in `novelty-gate.json`):

| Cap | Limit |
|-----|-------|
| Paper reads (full abstract processing) | **≤8** |
| arXiv categories queried | **≤3** |
| Parallel read-only paper subagents | **≤4** (implementation Later; must respect paper cap) |

Session budget notes may append to `docs/session-summary.md` when `CURSOR_MAT_SESSION_BUDGET_USD` is set (advisory only).

---

## Command / handoff integration

| Doc | Integration |
|-----|-------------|
| [`docs/architecture/plan-contract.md`](../plan-contract.md) | Preflight artifacts inform Tier 1–4 planning; human approval (G6) before `docs/current-plan.md` projection |
| [`docs/architecture/preflight-escalation-ladder.md`](../preflight-escalation-ladder.md) | Layer 0 is **not** a substitute for Layer 1–3 vocabulary |
| [`docs/reference/context-budget-policy.md`](../context-budget-policy.md) | Bounded `@file` reads; no habitual `@Codebase` for preflight |
| [`docs/guides/planning-commands-guide.md`](../guides/planning-commands-guide.md) | Later: Layer 0 section + optional `/mat-preflight-research` discoverability |
| [`docs/guides/sssf-patterns-sidecar.md`](../guides/sssf-patterns-sidecar.md) | Operator borrow/reject framing for SSSF patterns and external skill posture (**B13**) |
| `/mat-plan` Step 0 | Later: pointer to optional preflight when scope is novel |
| MAO / `/mat-plan-team` | **Never** enter orchestration without approved `docs/current-plan.md`; preflight does not write build/verify artifacts |

---

## Resolved questions

| Question | Resolution | Date |
|----------|------------|------|
| Combined wrapper name: `mat-preflight-gated` vs `mat-discover-research`? | **`mat-preflight-gated`** | 2026-08-21 |
| Minimum provenance: `manifest.json` per task vs inline citations? | **Inline citations only** (no per-task manifest requirement) | 2026-08-21 |
| Promote neuroarxiv only after A11 SPDX LICENSE + pins? | **Yes** — slice order satisfies A11 before Later skill work ([`specs/sssf-patterns-mission.md`](sssf-patterns-mission.md)) | 2026-08-21 |
| Pinned upstream SHAs? | advise **`88f1ecc`**, neuroarxiv **`b5d20ef`** | 2026-08-21 |
| MAT paper/category caps? | **≤8** paper reads, **≤3** arXiv categories per run | 2026-08-21 |

### Still open (Later implementation)

- arXiv HTTP-only vs Context7 / docs-scraper pairing for non-arXiv sources
- One combined directory vs meta-skill that `@`-invokes atomic skills (wrapper may delegate either way)

---

## Validation (this design slice)

Doc-test lock: `tests/test_workflow_docs.py` · `MatDiscoveryResearchSkillsSpecTest`

Operator verification:

```bash
grep -q 'mat-preflight-gated' specs/mat-discovery-research-skills.md
grep -q '88f1ecc' specs/mat-discovery-research-skills.md
grep -q 'b5d20ef' specs/mat-discovery-research-skills.md
python3 -m unittest tests.test_workflow_docs.MatDiscoveryResearchSkillsSpecTest -v
```

Implementation of `.cursor/skills/*` is **out of scope** until this spec is merged and ROADMAP *Later* items are promoted.

---

## Amendments

- 2026-08-21T21:00:00Z — builder — Initial design spec (slice 2).
