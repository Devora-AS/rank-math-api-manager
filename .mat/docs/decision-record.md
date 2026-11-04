# Decision Record

**Stage:** 7 — Optional Enhancements  
**Related Todo:** `evaluate-cursor-todos-orchestration`  
**Status:** UPDATED FOR PHASE 2 CLOSEOUT (Optional Enhancement 1 has shipped repo-owned scope plus a blocked remainder; other optional enhancements still require explicit go/no-go decisions)
**Posture:** PARTIAL SHIP / BLOCKED REMAINDER (2026-03-27) — authoritative live todo parity and any authoritative live dashboard todo claim remain blocked; hook-derived observed todo activity stays advisory and non-authoritative.
**Generated:** 2026-03-23

---

## Purpose

This document defines the go/no-go criteria for optional enhancements that are
deliberately excluded from Phase 1. Each enhancement may only be promoted to the
core architecture after the Stage 6 pilot proves the baseline.

---

## Optional Enhancement 1: Hook-Derived Observed Todo Activity (Advisory) vs. Authoritative Live Cursor Todo Parity

**Integration points:** Cursor native **To-dos** / `TodoWrite`, `postToolUse` and related hooks in [`.cursor/hooks.json`](../../.cursor/hooks.json), transcript references from hook payloads, MAO helpers in [`.cursor/hooks/mao_gate.py`](../../.cursor/hooks/mao_gate.py), observability ingest in [`apps/server`](../../apps/server), and the Vue dashboard in [`apps/client`](../../apps/client).

### Purpose

Clarify what this repository can honestly support today for Cursor todo visibility, and draw a hard boundary between:

1. **Authoritative live Cursor todo parity**
2. **Hook-derived observed todo activity (advisory)**

This section replaces any ambiguity that could imply the dashboard already has, or is close to having, a supported mirror of Cursor's internal todo state.

### Direction

Keep **true live authoritative Cursor todo parity** blocked.

Continue the narrower repo-aligned path: **hook-derived observed todo activity**, explicitly labeled as **advisory** and **non-authoritative**, and validate it through prototype/canary evidence rather than broad production claims.

### What this means

- The dashboard may show **observed todo activity** when the runtime actually emits and the repo actually captures relevant hook/tool evidence.
- The dashboard may continue to show **advisory MAO transitions** and related workflow hints.
- The repository must **not** claim:
  - live Cursor todo truth
  - an authoritative mirror of Cursor workspace todos
  - exact parity with all Cursor UI todo changes
  - causal consistency across all todo mutations

### Why this is the current direction

Official Cursor docs currently support:
- hook payload schemas such as `postToolUse`
- `tool_name`, `tool_input`, `tool_output`, and `transcript_path` in hook payloads
- client-facing ACP update methods such as `cursor/update_todos`

Official Cursor docs do **not** currently provide:
- an external read API for authoritative Cursor todo state
- an external subscription/stream for authoritative todo changes
- a documented contract guaranteeing that all todo changes, including manual UI edits, are observable from this repo's runtime surfaces
- a documented external mechanism that would let the Bun/Vue dashboard consume authoritative live todo state directly from Cursor

### Evidence basis

#### Official docs support

The repository may rely on official Cursor docs for:
- the shape of hook payloads when emitted
- the existence of transcript references
- the existence of client-facing todo update behavior inside Cursor/ACP

Those docs do **not** prove:
- that every `TodoWrite` will emit a durable hook event in this environment
- that transcripts will always contain durable, structured todo-tool fidelity
- that manual UI todo changes are externally observable
- that ACP methods expose dashboard-readable authoritative todo state

#### Repo/runtime evidence

The repository's own audited evidence currently shows:
- real `TodoWrite` activity can occur in-session
- durable repo-visible evidence for todo activity is still **conditional**, not guaranteed
- some audited sessions still show missing todo-tool rows in hook DB/transcript/local capture layers
- current shipped dashboard visibility is therefore best treated as **advisory observed state**, not authoritative truth

See:
- [`docs/archive/todo-write-observability-discovery.md`](../archive/todo-write-observability-discovery.md)
- [`docs/archive/todo-orchestration-runtime-evidence.md`](../archive/todo-orchestration-runtime-evidence.md)
- redacted audits under [`artifacts/phase1/`](../../artifacts/phase1/)

### Shipped repo-owned scope

The repository has already shipped an advisory slice that includes:
- file-based canonical MAO orchestration truth
- parent-owned MAO transition decisions
- advisory MAO transition visibility in the dashboard
- optional observed todo hints / `MaoTodoObservation` when relevant hook/runtime evidence is actually emitted and captured
- explicit honesty-boundary language that avoids claiming live authoritative parity

Current refinement direction for that shipped slice:
- keep `MaoTodoObservation` explicitly **observed / optional / non-authoritative** in the emitted payload contract itself
- keep canonical MAO truth explicitly tied to **file handoffs and parent-owned checks**
- allow row-level MAO display only for clean observations; partial or ambiguous observations stay explanatory, not stateful
- keep absence semantics explicit: no observed todo hint does **not** prove no todo change occurred in Cursor

This means the advisory observed-todo direction is **not greenfield**. It already exists in limited form and now needs refinement, validation, and clearer delivery posture.

### Blocked remainder

The following remain blocked:

- **Authoritative live Cursor todo parity**
- **live Cursor todo mirror/dashboard column**
- **Any claim of live authoritative MAO todo state**
- **Any claim that the dashboard is an exact mirror of Cursor todo UI**
- **hook-driven auto-unblock or subagent spawn based on purported live todo truth**
- **Any rollout language that implies broad production readiness for authoritative parity**

### Next supportable step for blocked auto-spawn work

For the still-blocked auto-spawn problem, the repo-aligned path is **advisory hook-written autostart intent**, not live-todo-driven dispatch.

**Shipped (repo-owned):** hooks may write gitignored `verifier-autostart-intent.json` when opt-in env flags and strict checks apply; **parent-side** evaluation is available via `evaluate_verifier_autostart_intent()` and `scripts/mao-verifier-autostart-intent.py` (advisory only — does not spawn agents). **Still blocked:** authoritative live todo parity, hook-driven subagent spawn from live todo state, and any dashboard column claiming authoritative Cursor todo truth.

That means:
- hooks may emit **advisory intent artifacts** with evidence pointers and dedupe keys
- the **parent orchestrator** remains the only component allowed to spawn builder/verifier
- canonical MAO file checks must still pass before any spawn occurs
- any bounded auto-continuation must stay behind an internal flag and remain explicitly non-authoritative

This keeps the repo inside the current honesty boundary while still allowing ergonomic experimentation on top of parent-owned orchestration.

### Go criteria for the advisory slice

Operator-facing procedures for each criterion (including explicit **PASS** / **INCONCLUSIVE** outcomes for the measurement items) live in [`mao-advisory-go-criteria.md`](../archive/mao-advisory-go-criteria.md). Filing redacted audits: [`artifacts/phase1/mao-advisory-go-criteria-template.md`](../../artifacts/phase1/mao-advisory-go-criteria-template.md).

The advisory slice may continue through prototype/canary only when all of the following remain true:

- [x] Canonical workflow truth remains file-based and parent-owned
- [x] Dashboard wording stays explicitly non-authoritative
- [x] Hooks continue to be treated as observability surfaces, not proof of authoritative todo truth
- [ ] Hook emission reliability has been measured in the current runtime for the scenarios under test
- [ ] Transcript fidelity for todo-relevant runs has been re-checked in the current runtime
- [ ] Tool-driven versus manual UI todo behavior has been compared in controlled canary runs
- [ ] Validation confirms no UI/docs wording overclaims parity or authority

### No-go triggers

Stop or narrow the advisory rollout if any of the following occur:

- measured runtime evidence shows todo observation is too sparse or inconsistent to be materially useful
- manual UI edits diverge from observed hook-derived state in ways that are likely to mislead operators
- dashboard copy, roadmap copy, or operator summaries begin implying live parity or authoritative truth
- implementation pressure pushes the repo toward unsupported reverse-engineering as the default production path
- the feature begins to compete with or weaken canonical file-based MAO orchestration

### Delivery posture

**Authoritative live parity:** keep blocked.

**Hook-derived observed todo activity:** prototype/canary.

This wording is intentional:
- not "fully shipped" for authoritative parity
- not "greenfield" for the advisory slice
- not "broad production go-live" for the advisory slice without stronger evidence

### Preparation automation boundary

Agents may **prepare evidence** for maintainers by collecting citations, summarizing diffs, and prefilling audit or release-planning material. That preparation does not establish runtime authority, does not override canonical file-based MAO truth, and does not let automation make the final operator-owned posture decision about roadmap, packaging, publication, or go/no-go wording.

### Effort estimate

For advisory slice refinement and validation only:

**Medium** — roughly **1-3 focused implementation/validation slices** depending on:
- hook/runtime evidence quality in the current Cursor build
- UI wording refinements
- test/validation breadth across tool-driven and manual todo changes

This estimate does **not** include unsupported reverse-engineering spikes for true parity.

### Rollback plan

If prototype/canary evidence is weak or misleading:

- disable or hide the observed todo activity slice
- retain file-based MAO orchestration as the only canonical workflow truth
- keep `MaoTransition` / MAO advisory visibility only
- leave roadmap and README wording explicit that live authoritative todo parity remains blocked

### Decision

**Status:** ADVISORY SLICE SHIPPED / AUTHORITATIVE PARITY BLOCKED
**Owner:** Repository maintainers
**Deadline:** Reassess only when either:
1. Cursor exposes an officially supported external read/subscribe capability for todo state, or
2. new runtime evidence materially changes what this repo can honestly prove

### Current decision summary

- **Shipped:** hook-derived observed todo activity in advisory form, alongside advisory MAO transitions and file-based canonical orchestration truth
- **In progress:** prototype/canary refinement and validation of the advisory slice
- **Blocked:** any claim of authoritative live Cursor todo parity, authoritative live Cursor todo truth in dashboard, or exact mirror behavior relative to Cursor UI

### Unblock condition for true parity

True parity should remain blocked until Cursor provides an officially supported external capability such as:
- a documented read endpoint for authoritative todo state, or
- a documented subscription/stream for authoritative todo changes

That capability would need clear guarantees around:
- external accessibility
- stable documented behavior
- versioned or causally ordered state
- coverage of manual UI edits as well as tool-driven changes
- latency expectations suitable for a live dashboard claim

---

## Optional Enhancement 2: The Library (Cursor-First Retargeting)

**Repo:** `disler/the-library`  
**Integration point:** `.cursor/skills/the-library/SKILL.md` + `library.yaml`

### What it does

The upstream Library pattern is a meta-skill for private distribution of skills,
agents, and prompts across devices and team members. In this repository, the
shipped work is a Cursor-first translated catalog plus cookbook guidance for
prompt-mediated/manual distribution flows.

### Value Proposition

- Enables team-wide consistent skill distribution
- Supports private repositories for proprietary prompts/skills
- Reduces per-developer setup time

### Go Criteria

- [x] Stage 6 pilot passed
- [ ] Team has 2+ developers who would benefit from shared skill distribution
- [ ] Private prompt/skill assets have been identified that should be distributed
- [x] `library.yaml` has been updated with Cursor-first install paths (`.cursor/skills/`)

### Translation Required

Update `library.yaml` default install paths:
```yaml
# BEFORE (Claude):
default_install_dir: .claude/skills/

# AFTER (Cursor):
default_install_dir: .cursor/skills/
```

Update `SKILL.md` command references from Claude backslash commands to Cursor-first prompt or workflow wording that does not imply bundled slash-command automation.

**Local parity slice (2026-03-27):** This repository now ships Cursor-first cookbook docs under [`.cursor/skills/the-library/cookbook/`](../../.cursor/skills/the-library/cookbook/) for install, use, add, list, and search, and the translated [`.cursor/skills/the-library/SKILL.md`](../../.cursor/skills/the-library/SKILL.md) routes operators through those files instead of implying a bundled `/library` command. This is documentation/parity work only; it does not by itself change the optional enhancement decision to GO.

### Effort Estimate

Low — 1–2 hours to update paths and test installation

### Decision

**Status:** DEFERRED (not yet prioritized post-Stage 6 baseline)

---

## Optional Enhancement 3: E2B Sandbox Integration

**Source:** `disler/agent-sandbox-skill`, `e2b-dev/infra` (self-hosted)  
**Integration point:** `.cursor/skills/agent-sandboxes/SKILL.md`

### What it does

E2B provides isolated cloud sandboxes for running agent code securely. The agent
sandbox skill wraps the E2B CLI for creating, managing, and destroying sandboxes.

### Why Excluded from Phase 1

- Self-hosted E2B requires significant infrastructure investment
- Managed E2B has per-sandbox costs
- Cursor Cloud Agents provide equivalent isolation for most Phase 1 use cases
- The agent sandbox skill (SKL-001) depends on the E2B CLI which is not available locally

### Go Criteria

- [ ] Stage 6 pilot passed
- [ ] A specific use case has been identified where Cloud Agents are insufficient
  (e.g., running untrusted third-party code, browser automation at scale)
- [ ] Cost analysis shows E2B is preferable to Cloud Agents for this use case
- [ ] E2B CLI is available and configured in the environment

### Effort Estimate

High — 4–8 hours for infrastructure setup + integration + testing

### Decision

**Status:** EXCLUDED from Phase 1 — re-evaluate in Phase 2 if needed

---

## P2 Audit — Worktree Wrapper Strategy

**Audit source:** [`artifacts/report/mat-audit-report.md`](../../artifacts/report/mat-audit-report.md) Phase A step A2
**Related:** P0-1 worktree contract alignment (Done), [`docs/archive/worktree-decision-matrix.md`](../archive/worktree-decision-matrix.md), [`.cursor/commands/mat-wt-create.md`](../../.cursor/commands/mat-wt-create.md), [`specs/worktree-native-wrapper-v1.md`](specs/worktree-native-wrapper-v1.md)
**Status:** DECIDED — hybrid defer (2026-06-23); **E10 bootstrap modes shipped 2026-08-24**

### Context

Cursor documents **managed worktrees** (Agents Window), plus product commands **`/worktree`** and **`/best-of-n`**, with a default machine-wide cap (`cursor.worktreeMaxCount`, typically **25**) — see [Cursor Worktrees](https://cursor.com/docs/configuration/worktrees). MAT ships repo-local worktree tooling as the **parity / bootstrap** layer:

- `/mat-wt-*` commands and `create-worktree-subagent`
- [`.cursor/hooks/bootstrap_worktree.sh`](../../.cursor/hooks/bootstrap_worktree.sh) with modes `--metadata-only` (default) | `--install` | `--check`, collision-aware `runtime.env` port hints (`3001` / `5173` bases)
- [`.cursor/worktrees.json`](../../.cursor/worktrees.json) + [`.cursor/worktrees.json.example`](../../.cursor/worktrees.json.example) setup keys
- P0-1 remediation aligned operator docs with explicit isolation; E10 adds safe bootstrap modes and product-parity docs

The audit asked whether MAT should expose a thin native wrapper around product commands or maintain a separate abstraction. E10 implements the **hybrid** half: same markers on every path, safe defaults, no new proxy command that creates Cursor worktrees.

### Options matrix

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **(a) Defer / status quo** | Keep `mat-wt-*` + bootstrap only; no new wrapper | Lowest churn; bootstrap and health checks stay stable | Operators must discover Cursor `/worktree` and `/best-of-n` separately |
| **(b) Thin hybrid wrapper** | Keep `mat-wt-*` as bootstrap/health layer; add operator guidance pointing to Cursor `/worktree` and `/best-of-n` for isolation | Honest split: product isolation + repo bootstrap; no duplicate port/collision logic | Two mental models until docs are read |
| **(c) Product-native only** | Deprecate `mat-wt-*` in favor of Cursor commands alone | Fewer MAT-specific commands | Loses collision-aware `runtime.env`, `check-worktrees.sh`, and adoption-sidecar bootstrap contract |

### Recommendation

**Hybrid defer (option b)** — retained; E10 deepens the bootstrap/docs half:

- **Keep** `mat-wt-*`, `bootstrap_worktree.sh`, and `runtime.env` as the repo-local bootstrap and health layer.
- **Default** bootstrap to `--metadata-only` (zero package/network calls); use `--install [--copy-env]` when deps or env copy are intentional.
- **Document** parity: Agents Window managed trees, `/worktree`, `/best-of-n` (comparison only — no auto-merge), and manual `mat-wt-*` / `git worktree` all produce the same MAT markers when bootstrap runs.
- **Do not** ship a new MAT wrapper command that proxies product worktree creation.

### Impact

- [`AGENTS.md`](../../AGENTS.md) worktree section remains authoritative for MAT bootstrap behavior.
- [`docs/archive/worktree-decision-matrix.md`](../archive/worktree-decision-matrix.md) stays the local-vs-Cloud Agents matrix; this section records the product-vs-MAT wrapper choice.
- Operators creating isolation via Cursor product commands should still run or rely on `.cursor/worktrees.json` bootstrap when the repo defines setup keys.

### Evidence

- [Cursor Worktrees](https://cursor.com/docs/configuration/worktrees) — managed worktrees, `/worktree`, `/best-of-n`, `setup-worktree*`, `cursor.worktreeMaxCount`
- P0-1 remediation — `7b79d27`; `WorktreeContractDocsTest` in [`tests/test_workflow_docs.py`](../../tests/test_workflow_docs.py)
- E10 — [`specs/worktree-native-wrapper-v1.md`](specs/worktree-native-wrapper-v1.md); `tests/test_bootstrap_worktree_modes.py`
- [`docs/archive/worktree-decision-matrix.md`](../archive/worktree-decision-matrix.md)

### Decision

**Status:** HYBRID DEFER — maintain MAT bootstrap (E10 modes); document product command pointers; no native creation proxy.

---

## P2 Audit — Nested and Background Subagents

**Audit source:** [`artifacts/report/mat-audit-report.md`](../../artifacts/report/mat-audit-report.md) Phase A step A3
**Related:** Optional Enhancement 1 (blocked remainder), [`docs/architecture/orchestration-workflow.md`](orchestration-workflow.md), [`docs/architecture/mat-plan-team-spec.md`](../architecture/mat-plan-team-spec.md)
**Status:** DECIDED — selective use with explicit non-goals (2026-06-23)

### Context

Cursor supports **foreground and background subagents**, **child subagent spawning**, and **resume** semantics (see [`artifacts/fetched/cursor-docs.md`](../../artifacts/fetched/cursor-docs.md)). MAT uses **parent-owned** Task delegation with **file handoffs** and MAO todos that remain **advisory** alongside canonical files.

MAT's stricter parent-owned pattern is a **design choice** for file-first honesty, not a platform constraint. The audit asked where nested/background subagents help without weakening that honesty.

### Where nested/background subagents help

| Pattern | MAT surface | Role |
|---------|-------------|------|
| Parallel independent reads | `/mat-subagents-spawn`, explore-style Task fanout | Breadth-first discovery without overlapping implementation |
| Long-running isolated work | Cursor Cloud Agents (documented in worktree matrix) | Hours-long or VM-isolated tasks off the host |
| Unclear subagent state | **Wait-before-supersede** ([`AGENTS.md`](../../AGENTS.md)) | Resume same subagent before re-spawn; normal startup is not failure |
| Builder/verifier isolation | Separate worktrees when **operator** creates them | Parallel build/verify with git isolation; not automatic per agent |
| Orchestrated build/verify | `/mat-plan-team`, `/mat-build`, `/mat-review` | Parent spawns builder then verifier; file handoffs gate progression |

Canonical workflow truth remains **file-based** and **parent-owned**: `docs/current-plan.md`, `build-result.md`, `verify-result.md`, and parent `capture_transition_decision()` checks.

### Explicit non-goals

Aligned with Optional Enhancement 1 blocked remainder — **not** in scope for this strategy slice or current shipped posture:

- **No live todo spawn** — subagents are not started from purported live Cursor todo state
- **No hook auto-delegation** — hooks do not spawn builder/verifier from todo state or `gate.json` alone
- **No authoritative dashboard todo column** — observed todo activity stays **advisory** only
- **No replacing** `capture_transition_decision()` or parent-owned `TodoWrite` — parent orchestrator remains the only spawn authority after explicit file checks
- **No claim** that hook-driven subagent auto-spawn is **shipped** — `verifier-autostart-intent.json` is advisory intent only; parent evaluation does not auto-spawn

### Recommendation

**Selective use:**

- Document allowed patterns (this section + [`docs/architecture/orchestration-workflow.md`](orchestration-workflow.md) cross-links).
- Keep blocked items explicit and aligned with Optional Enhancement 1.
- Prefer resume-same-subagent and non-overlapping parent work over parallel duplicate implementation.
- Use background/nested Task subagents for read-only or independent slices; keep build/verify sequencing parent-owned.

### Evidence

- [`AGENTS.md`](../../AGENTS.md) — wait-before-supersede discipline
- [`docs/architecture/mat-plan-team-spec.md`](../architecture/mat-plan-team-spec.md) — delegation proof tiers
- [`artifacts/fetched/cursor-docs.md`](../../artifacts/fetched/cursor-docs.md) — subagent foreground/background, child spawn
- Optional Enhancement 1 — advisory vs authoritative todo boundaries

### Decision

**Status:** SELECTIVE USE — nested/background subagents allowed where they do not weaken file-first MAO honesty; live-todo-driven spawn and hook auto-delegation remain **blocked**.

---

## P1 Audit — Skills vs Commands Routing

<a id="p1-audit--skills-vs-commands-routing"></a>

**Audit source:** [`artifacts/report/mat-audit-report.md`](../../artifacts/report/mat-audit-report.md) Phase B step B2
**Related:** [`docs/reference/capability-precedence.md`](capability-precedence.md), [`docs/guides/planning-commands-guide.md`](../guides/planning-commands-guide.md), [`.cursor/commands/`](../../.cursor/commands/), [`.cursor/skills/`](../../.cursor/skills/)
**Status:** DECIDED — commands remain orchestration entrypoints; skills complement procedural playbooks (2026-06-23)

### Purpose

Cursor treats **skills** as first-class operator guidance (see [`artifacts/fetched/cursor-docs.md`](../../artifacts/fetched/cursor-docs.md)); product tooling such as `/migrate-to-skills` may convert eligible commands. MAT still ships **23** `mat-*` slash commands as the primary **discovery and orchestration entry** surface. Skills complement commands with repeatable procedural playbooks (worktree lifecycle, skill authoring, private distribution) without replacing MAO entrypoints or file-handoff authority.

### Default posture

- **Orchestration entry = commands** — planning, build/verify delegation, MAO parent flows, diagnostics, and quick utilities stay as `mat-*` slash commands.
- **Procedural how-to = skills or hybrid** — worktree bootstrap and lifecycle guidance may live in skills while commands remain the typed entry and script-backed dispatch.
- **Cross-reference, do not bulk-migrate** — hybrid rows add doc links from commands to skills; no mass deletion or rename of `mat-*` files in this slice.

### Routing matrix (commands)

| Workflow / command | Routing | Rationale | Migration effort |
|--------------------|---------|-----------|------------------|
| `mat-plan` | Keep as command | Solo planning entry; lightweight discovery | None |
| `mat-plan-onboarding` | Keep as command | Heavy planning package entry; approval gate | None |
| `mat-plan-update` | Keep as command | Surgical living-plan amendments; append-only `## Amendments`; planning-only | None |
| `mat-plan-team` | Keep as command | MAO orchestration entry; parent-orchestrator | None |
| `mat-long-run` | Keep as command | Multi-slice mission entry; long-run state contract | None |
| `mat-build` | Keep as command | Delegated builder entry | None |
| `mat-review` | Keep as command | Delegated verifier entry | None |
| `mat-subagents-spawn` | Keep as command | Parallel Task fan-out entry | None |
| `mat-sprint` | Keep as command | Bounded single-slice entry | None |
| `mat-lite` | Keep as command | Lightweight pass entry | None |
| `mat-wt-create` | Hybrid | Command = entry + bootstrap; `create-worktree` skill = playbook | Low — cross-link only |
| `mat-wt-list` | Hybrid | Command = entry; `worktree-manager` skill = lifecycle guidance | Low — cross-link only |
| `mat-wt-remove` | Hybrid | Command = entry; `worktree-manager` skill | Low — cross-link only |
| `mat-wt-check` | Hybrid | Command = entry; `worktree-manager` skill | Low — cross-link only |
| `mat-doctor` | Keep as command | Diagnostics entry; script-backed | None |
| `mat-start` | Keep as command | Observability stack entry | None |
| `mat-update-mat` | Keep as command | Adoption/upstream refresh entry | None |
| `mat-sync` | Keep as command | Shell state machine for adoption sync (`scripts/mat-sync.sh`) | None |
| `mat-adopt` | Keep as command | First-adoption orchestrator entry; delegates to mat-sync | None |
| `mat-git-status` | Keep as command | Quick repo state utility | None |
| `mat-prime` | Keep as command | Context-load entry | None |
| `mat-question` | Keep as command | Read-only Q&A entry | None |

### Skills (repo-local)

| Skill | Relationship to commands | Routing |
|-------|-------------------------|---------|
| `create-worktree` | Playbook for `/mat-wt-create`; lightweight creation steps | Skill candidate (shipped); hybrid with `mat-wt-create` |
| `worktree-manager` | Full lifecycle; references `mat-wt-*` commands | Skill candidate (shipped); hybrid with worktree cluster |
| `the-library` | Private skill distribution meta | Defer migration; meta-skill infrastructure |
| `meta-skill` | Authoring new skills | Defer migration; operator tooling |

### Optional pilot (documented)

- One-line cross-link from [`.cursor/commands/mat-wt-create.md`](../../.cursor/commands/mat-wt-create.md) → [`.cursor/skills/create-worktree/SKILL.md`](../../.cursor/skills/create-worktree/SKILL.md). No file rename or delete.

### Explicit non-goals

- No claim that all `mat-*` commands were migrated to skills
- No bulk `/migrate-to-skills` run in this audit slice
- Commands remain authoritative for MAO/orchestration entry and file-handoff discovery
- No hook or MAO runtime behavior changes from this routing review

### Evidence

- [`artifacts/fetched/cursor-docs.md`](../../artifacts/fetched/cursor-docs.md) — skills first-class; `/migrate-to-skills` for eligible commands
- [`docs/reference/capability-precedence.md`](capability-precedence.md) — project-first routing; canonical handoff files stay authoritative
- Inventory: 20 × `.cursor/commands/mat-*.md`; 4 × `.cursor/skills/*/SKILL.md`

### Decision

**Status:** DECIDED — keep all `mat-*` commands; hybrid cross-refs for worktree cluster only; defer skill migration for `the-library` and `meta-skill`.

---

## P1 Audit — Cloud Agents and Agents Window

<a id="p1-audit--cloud-agents-agents-window"></a>

**Audit source:** [`artifacts/report/mat-audit-report.md`](../../artifacts/report/mat-audit-report.md) Phase B step B3
**Related:** [`docs/archive/worktree-decision-matrix.md`](../archive/worktree-decision-matrix.md), [`AGENTS.md`](../../AGENTS.md), [`docs/reference/configuration.md`](configuration.md)
**Status:** DECIDED — Cursor 3 Agents Window language; MAT does not auto-provision cloud agents (2026-06-23)

### Purpose

Cursor 3 moved agent orchestration to the **Agents Window** and removed cloud agents from the editor as the primary setup surface (see [`artifacts/fetched/cursor-changelog.md`](../../artifacts/fetched/cursor-changelog.md)). MAT docs must describe cloud isolation using current product language without implying MAT provisions or manages cloud VMs.

### Cursor 3 posture

- **Agents Window** is the agent-first interface for running agents across repos and environments ([`artifacts/fetched/cursor-docs.md`](../../artifacts/fetched/cursor-docs.md)).
- Supported modes include **local**, **cloud**, **remote SSH**, and **multi-workspace** from the same surface.
- **Cloud agents** are configured via [`.cursor/environment.json`](../../.cursor/environment.json.example) (repo-local `install` / `start` lifecycle) or **web onboarding** — not editor Settings as the sole path.
- Official reference: [cursor.com/docs/cloud-agent](https://cursor.com/docs/cloud-agent) and [cursor.com/docs/agent/agents-window](https://cursor.com/docs/agent/agents-window).

### MAT posture

- **Default isolation = local worktrees** when operators need git branch isolation on the host (`/mat-wt-create`, explicit `git worktree`, or Cursor `/worktree` / `/best-of-n` per [P2 Audit — Worktree Wrapper Strategy](#p2-audit--worktree-wrapper-strategy)).
- **Prefer cloud VMs** for long-running, resource-intensive, or computer-use tasks where the host should not stay online — documented in [`docs/archive/worktree-decision-matrix.md`](../archive/worktree-decision-matrix.md).
- **File handoffs stay authoritative** — `docs/current-plan.md`, `build-result.md`, and `verify-result.md` gate MAT orchestration regardless of where the agent runs.
- **MAT does not auto-provision cloud agents** — no hook, command, or bootstrap path in this repo starts or schedules cloud VMs; operators configure cloud via Agents Window and `.cursor/environment.json` outside MAT automation.

### Operator setup (summary)

| Step | Action |
|------|--------|
| 1 | Open the **Agents Window** in Cursor (agent-first surface; not editor Settings as sole entry). |
| 2 | Choose **cloud** (or SSH / multi-workspace as needed). |
| 3 | Add or commit [`.cursor/environment.json`](../../.cursor/environment.json.example) with `install` / `start` commands, or complete web onboarding. |
| 4 | Ensure `.cursor/mcp.json` and root `AGENTS.md` are present — cloud agents read them like local agents. |

### Explicit non-goals

- No new cloud automation code or MAT-managed VM provisioning in this audit slice
- No RFU Phase C work (Node pin, vitest-only, dependabot) bundled with this doc refresh
- No editor-only “Settings → Cloud Agents” as the **sole** documented setup path on audited surfaces
- No reopening of the E2B optional enhancement decision — cross-links to [E2B Sandboxes](#e2b-sandboxes) remain unchanged

### Evidence

- [`artifacts/fetched/cursor-docs.md`](../../artifacts/fetched/cursor-docs.md) — Agents Window; `.cursor/environment.json`; web onboarding
- [`artifacts/fetched/cursor-changelog.md`](../../artifacts/fetched/cursor-changelog.md) — Agents Window introduced; cloud removed from editor emphasis
- [`docs/archive/worktree-decision-matrix.md`](../archive/worktree-decision-matrix.md) — local vs cloud decision matrix (refreshed in B3)

### Decision

**Status:** DECIDED — document Cursor 3 Agents Window + `.cursor/environment.json` + official cloud-agent docs; keep local worktrees as MAT default; MAT does not auto-provision cloud agents.

---

## Phase C RFU-7 — Observability Retention and Hook Redaction (Deferred)

**Audit ID:** C6 / **RFU-7**  
**Related policy:** [`docs/architecture/observability-retention-policy.md`](../architecture/observability-retention-policy.md) (advisory; no shipped auto-purge)  
**Related audit row:** [`artifacts/report/mat-audit-report.md`](../../artifacts/report/mat-audit-report.md) Phase C C6

### Context

P2 shipped an **advisory** retention and sampling policy. P0-3 shipped observability security **documentation** (preview truncation vs full SQLite rows, sensitive `tool_output`, shared-environment token guidance). RFU-7 is the optional **code** slice: server-side retention TTL and/or hook redaction before POST in `send_event.py`.

### Operator decision inputs (2026-06-23)

| Factor | Assessment |
| --- | --- |
| Deployment | Observability likely **localhost-only** for the near term |
| Dashboard audience | **Single operator** (no shared team dashboard) |
| Disk growth | Local `apps/server/events.sqlite` can grow large (operator-owned, gitignored); **manual rotate/delete** per retention policy is sufficient before automation |
| Adoption | MAT **is** adopted into external repos — adopters need **guidance**, not silent auto-purge defaults in the MAT source tree |

### Decision

**Status:** **DEFERRED** (2026-06-23) — no automatic retention TTL and no hook redaction code in the MAT source repo until a concrete trigger appears.

**Rationale:**

- MAT observability remains **advisory** and subordinate to file handoffs; the source repo optimizes for **debuggability**, not compliance-grade audit logs.
- Policy + operator discipline (`OBSERVABILITY_API_TOKEN` when shared, manual SQLite rotation, gitignored capture trees) matches current use.
- External adoption should document **opt-in** observability posture and manual cleanup — not inherit always-on TTL or aggressive redaction from upstream by default.

### Reopen criteria (any one may justify a future slice)

1. **Shared observability** beyond localhost (team dashboard, LAN/VPN, or CI-posted events to a central server).
2. **Measured disk pain** on a long-running server **after** documented manual rotation practices.
3. **Compliance-sensitive adopters** require documented **opt-in** redaction flags (implement redaction before TTL; both opt-in, default-off in source).

### If implemented later (order)

1. **Decision doc slice** — retention days, redaction scope, opt-in env flags, rollback.
2. **Opt-in hook redaction** (e.g. env-gated strip/truncate of `tool_output` before POST) — never break MAO handoff files.
3. **Opt-in server TTL** (e.g. env-gated `OBSERVABILITY_RETENTION_DAYS`) — export-first warning; default off in source.
4. Update [`docs/architecture/observability-retention-policy.md`](../architecture/observability-retention-policy.md) and regression tests together.

### Explicit non-goals while deferred

- No always-on auto-purge in shipped observability server
- No default-on redaction that hides debugging evidence in the MAT source repo
- No bundling RFU-7 with unrelated audit or updater slices

---

## Summary Table

| Enhancement | Priority | Effort | Phase | Decision |
|------------|---------|--------|-------|---------|
| Cursor To-dos + hooks orchestration | P1 | Medium | Phase 2 | Partial ship; blocked remainder |
| P2 worktree wrapper strategy | P2 | Low | Phase A | Hybrid defer — see [P2 Audit — Worktree Wrapper Strategy](#p2-audit--worktree-wrapper-strategy) |
| P2 nested/background subagents | P2 | Low | Phase A | Selective use — see [P2 Audit — Nested and Background Subagents](#p2-audit--nested-and-background-subagents) |
| P1 skills vs commands routing | P1 | Low | Phase B B2 | Decided — see [P1 Audit — Skills vs Commands Routing](#p1-audit--skills-vs-commands-routing) |
| P1 cloud agents / Agents Window | P1 | Low | Phase B B3 | Decided — see [P1 Audit — Cloud Agents and Agents Window](#p1-audit--cloud-agents-agents-window) |
| RFU-7 observability retention / redaction code | P2 | Medium | Phase C C6 | **Deferred** — see [Phase C RFU-7](#phase-c-rfu-7--observability-retention-and-hook-redaction-deferred) |
| The Library | P2 | Low | Phase 2 | Deferred |
| E2B Sandboxes | P3 | High | Phase 2+ | Excluded from P1 |

---

### M5 reassessment addendum (2026-10-19)

One-shot **M5** evidence pass ([`docs/evidence/m5-mao-blocked-bundle-reassessment-2026-10-19.md`](evidence/m5-mao-blocked-bundle-reassessment-2026-10-19.md)): official Cursor hooks, ACP (`cursor/update_todos`, `cursor/task`), subagents, and changelog (since 2026-07-01) were re-reviewed on **2026-10-19 UTC**. **Bundle status: still Blocked** — no documented authoritative external todo read/subscribe API; ACP todo updates remain client notifications; subagent spawn is not exposed as live-todo-driven hook RPC.

**Unblock condition for true parity** (above) is **unchanged**. G4–G7 measurement checkboxes were **not** updated — no new live-operator measurement audit in this slice (deferred / INCONCLUSIVE for fresh G4–G7 runs). Repo `mao_gate.py` posture remains file-handoff canonical with advisory hooks only.

---

## Sign-Off Process

With Stage 6 pilot gates passed:
1. Review each enhancement against its go criteria
2. Record go/no-go decision with owner initials and date
3. If GO: create implementation spike branch and update `artifacts-index.md`
4. If NO-GO: document the reason and set a review date

Update the Decision column above with: `GO — [initials] [date]` or `NO-GO — [reason]`
