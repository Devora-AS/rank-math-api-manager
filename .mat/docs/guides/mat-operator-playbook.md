# MAT operator playbook — shipped-capability working habits

- **Purpose:** Day-to-day habits for operators using MAT capabilities that already ship — not a slash-command catalog.
- **Audience:** Maintainers on the MAT source tree, adopted product repos, and teammates using the advisory team plugin.
- **Status:** complete
- **Last updated:** 2026-10-19
- **Canonical depth:** Link out to reference docs; this guide answers *when*, *what to check*, *what to expect*, and *what is not guaranteed*.

## Related reference

| Topic | Doc |
|-------|-----|
| MAO protocol | [`todo-orchestration.md`](../todo-orchestration-protocol.md) |
| Handoff artifacts | [`workflow-artifact-contract.md`](../workflow-artifact-contract.md) |
| Verification profiles | [`verification-profiles.md`](../verification-profiles.md) |
| Env writes | [`env-write-contract.md`](../env-write-contract.md) |
| Context budget | [`context-budget-policy.md`](../context-budget-policy.md) |
| Loop policy | [`loop-policy.md`](../loop-policy.md) |
| PostToolUse scoped lint | [`configuration.md`](../configuration.md) (`CURSOR_MAT_POST_TOOL_SCOPED_VALIDATE`, `.cursor/hooks/post_tool_validate.py`) |
| Adoption / mat-sync | [`getting-started-existing-projects.md`](getting-started-existing-projects.md) |
| Plugin install | [`cursor-plugin-install.md`](cursor-plugin-install.md) |
| Events / dashboard | [`events-and-visualization.md`](../architecture/events-and-visualization.md) |

---

## A. File-backed orchestration and handoffs

### A1. MAO transitions — Files → check → TodoWrite → dispatch

**Canonical sequence:** Files → parent transition check → TodoWrite → dispatch.

**When:** Any orchestrated plan → build → verify cycle (`/mat-plan-team`, parent-orchestrator flow, or equivalent).

**Sequence (parent-owned):**

1. **Files** — Write or refresh `docs/current-plan.md` (substantive, not the repo placeholder).
2. **Parent transition check** — Confirm the canonical handoff rules (below). Optionally read `artifacts/mao/gate.json` only if it is **fresh, valid, internally consistent, and aligned** with live files; it never replaces this check.
3. **TodoWrite** — Apply MAO status updates (`[mao:plan]` → `completed`, `[mao:build]` → `in_progress`, then after build gate `[mao:build]` → `completed`, `[mao:validate]` → `in_progress`). Helpers: `capture_transition_decision()`, `scripts/mao-todo-write-merge.py`.
4. **Dispatch** — Spawn builder or verifier with plan + prior artifacts and optional `MAO_TASK_CONTEXT_JSON` (advisory).

**Build → validate requirements (live `build-result.md`):**

| Check | Rule |
|-------|------|
| Plan | `docs/current-plan.md` ready (same as plan→build) |
| Build artifact | `build-result.md` exists |
| Status | First declared `## Status` is **PASS** or **PARTIAL** |
| Acceptance criteria | Every row under `## Acceptance Criteria` includes `: PASS`, `: PARTIAL`, or `: FAIL` (no unresolved checklist-only rows) |
| Lint | `## Linting / Type-Check` is **PASS** (or `**PASS**` / `PASS - …` per validator) |

**`artifacts/mao/gate.json` (advisory):** Refreshed on PostToolUse when `docs/current-plan.md` or `build-result.md` changes (`CURSOR_MAO_GATE=1`). Use `build_may_start` / `validate_may_start` and `advisory_pending` as **hints** only. Stale, disabled, contradictory, or negative gate data → fall back to manual file checks.

**Does not mutate todos or spawn agents:**

- PostToolUse **todo observation** (`artifacts/mao/todo-write-events.jsonl`, `last-todo-write-observation.json`) — audit only.
- `artifacts/mao/suggested-todo-mutation.json` — parent may merge; hooks do not call `TodoWrite`.
- `artifacts/mao/verifier-autostart-intent.json` (opt-in `CURSOR_MAO_VERIFIER_AUTOSTART=1`) — parent still spawns verifier and consumes/deletes intent.

**Files-only fallback:** If `TodoWrite` is unavailable, continue with `docs/current-plan.md`, `build-result.md`, and `verify-result.md`; note the skip in `docs/session-summary.md`. Do not add a third-party task MCP.

**Outcome:** Predictable phase gates; todos mirror but do not replace file handoffs.

**Not guaranteed:** Live Cursor todo UI parity with MAO tags; hook auto-spawn from todos (blocked by design).

### A1b. Verifier readonly handoff (D2/E2)

**When:** After build gate passes and the parent spawns a **readonly** verifier Task (`/mat-review`, `/mat-plan-team` Step 3).

**Split responsibilities:**

| Role | Owns |
|------|------|
| **Verifier (readonly)** | Read/Grep/list evidence; structured verify **payload** in chat (JSON or contract-shaped markdown); per-criterion PASS/FAIL from available read-only tools only |
| **Parent** | `python3 scripts/mat-scope-audit.py gate` when correlated; **global validation commands** from the plan (`phase1-verify.sh`, targeted unittest, etc.); `serialize_verify_result()` → **`verify-result.md`**; MAO `[mao:validate]` completion after the on-disk handoff is final |

**Cursor product limits (expected, not auto-FAIL):** Readonly subagents may run in Ask-like mode — Shell, writes, and sometimes TodoWrite can be blocked. Missing `verify-result.md` **during** the verifier run is normal; the parent waits for the **structured payload**, then serializes the file. Do not supersede the verifier because the handoff file is absent mid-run.

**Outcome:** Operators distinguish real verify FAIL from tooling restrictions.

---

### A2. Path-scoped plans and AC-N triad

**When:** Any non-trivial slice — especially delegated builder/verifier runs.

**Habits:**

- List **concrete paths** under Relevant Files / implementation steps in `docs/current-plan.md`.
- Number acceptance criteria **AC-1**, **AC-2**, … and repeat the same IDs in `build-result.md` and verifier criteria review.
- Delegate with the **smallest** file set that satisfies the slice.

**B3 (shipped):** `soft_inspect_typed_output_triad` in `.cursor/hooks/artifact_contract.py` runs **only when** the plan lists typed `AC-N` IDs. Plans without typed IDs are grandfathered (no triad warnings). Partial handoffs (plan only, or plan + build before verify exists) compare only supplied artifacts.

**Tier 2c (solo planning only):** `[new]` / `[existing]` prefixes on every `## Relevant Files / Areas` bullet are enforced by `scripts/validate_planning_artifacts.py` on **solo** `/mat-plan` files under `specs/<slug>.md`, not on `docs/current-plan.md`. Use tagged bullets when authoring specs; use path-scoped bullets on execution plans as a convention.

| Concern | Applies to | Enforced in CI? |
|---------|------------|-----------------|
| Typed `AC-N` triad | `docs/current-plan.md` + handoffs when plan uses IDs | Soft warnings via `validate_artifacts.py` |
| `[new]` / `[existing]` tags | `specs/*.md` solo plans | Yes (Tier 2c; grandfather list) |
| Execution path lists | `docs/current-plan.md` | Habit / verifier scope — not Tier 2c |

**Outcome:** Verifier stays file-scoped; less cost and fewer surprise edits.

**Not guaranteed:** Mechanical enforcement of every acceptance bullet; parent and verifier still judge semantics.

---

### A3. Verification-profile honesty

**When:** Interpreting green CI, local `phase1-verify`, or `make verify`.

**Profile IDs (exact):** `source-full`, `source-python-only`, `adopted-operational`, `adopted-contract` — see `scripts/verification_profiles.py`.

| Profile | Typical use |
|---------|-------------|
| `source-full` | MAT source repo; full checks including Bun client/server |
| `source-python-only` | Fast Python/docs loop; Bun checks recorded as **skip** |
| `adopted-operational` | Default on adopted sidecar (`.mat/README.md`); many checks **skipped** |
| `adopted-contract` | Packaged `.mat/tests` + `adopted-sidecar` doc links; still skips Bun on typical adopted trees |

**Commands:**

```bash
make verify   # wrapper → scripts/phase1-verify.sh with manifest
bash scripts/phase1-verify.sh --profile source-full --manifest artifacts/phase1/verification-manifest.json
```

**Manifest:** `artifacts/phase1/verification-manifest.json` — **skip ≠ pass**; read `reason` on skipped checks.

**Adopted-operational honesty:** Skips may include doc link validation (use `adopted-contract`), full `python_unittest` on `.mat/tests`, Bun smoke, and more. A green **operational** run does **not** mean the product’s own test suite ran.

**Outcome:** You know what actually executed.

**Not guaranteed:** Product-specific integration/E2E coverage from MAT verify alone.

---

### A3b. PostToolUse scoped lint vs full verify

**When:** Interpreting hook feedback after file writes, or comparing `build-result.md` **`## Linting / Type-Check`** rows to CI and `make verify`.

**Layer:** `.cursor/hooks/post_tool_validate.py` runs on PostToolUse for **file-writing** tools only (not on `TodoWrite`). Default **scoped** mode is on via **`CURSOR_MAT_POST_TOOL_SCOPED_VALIDATE`** (unset or `1`; set `0` to force legacy project-wide checks on every qualifying PostToolUse). Env details and trade-offs: [`configuration.md`](../configuration.md).

| Mode | Behavior |
|------|----------|
| Scoped (default) | `ruff check` and `ty check` on **changed** `.py` paths; `tsc -p <package>` when all changed `.ts`/`.tsx` share one known package (`apps/client`, `apps/server`, or repo-root `tsconfig.json` when present) |
| Broad fallback | Project-wide `ruff` / `ty` / root `tsc --noEmit` when the scoped path is unsafe or unavailable |

**Broad fallback triggers (summary):** empty or untrusted change list; paths outside the repo; **mixed** TypeScript packages in one edit; missing package `tsconfig.json`; **`CURSOR_MAT_POST_TOOL_SCOPED_VALIDATE=0`**.

**Does not replace § A3 verification-profile honesty or the full gate:**

- **`bash scripts/phase1-verify.sh`** / **`make verify`** — manifest-driven checks including **`vue-tsc`**, Bun client/server smoke, doc link validation, and full unittest suites on the MAT source tree
- Product CI, integration/E2E, or adopted-repo test suites
- MAO **build → validate** rules — verifier still expects a truthful lint row on `build-result.md`; hook stderr during edits is advisory (`failClosed: false` on PostToolUse)

**Outcome:** Faster edit-loop feedback without treating hook pass as a green **`source-full`** (or adopted-profile) run.

**Not guaranteed:** Issues visible only in `phase1-verify`, cross-package TypeScript, or Bun paths; profile **skip ≠ pass** (§ A3) still applies.

**Reference:** Profile IDs and manifest honesty — [`verification-profiles.md`](../verification-profiles.md); scoped toggle — [`configuration.md`](../configuration.md).

---

### A4. Optional Gate Evidence

**When:** Multi-step slices where correlating plan/build/verify timestamps helps debugging (optional).

**Example (non-gating appendix in plan or build-result):**

```markdown
## Gate Evidence

| Artifact | mtime (UTC) | note |
|----------|-------------|------|
| docs/current-plan.md | 2026-10-16T12:00:00Z | plan frozen for build |
| build-result.md | 2026-10-16T12:45:00Z | Status PASS |
```

**B5 (shipped):** Observability **Gate Evidence** panel (`GateEvidencePanel.vue`, server `gate-evidence.ts`) can display related events — advisory UI only.

**Outcome:** Faster forensics alongside canonical Status rows.

**Not guaranteed:** Gate Evidence does not replace Status, acceptance criteria, lint rows, or MAO transition checks.

---

### A5. Scope-audit review

**When:** Protected-path risk, unexpected dirty files after builder stop, or verifier scope questions.

**Surfaces:**

| Surface | Role |
|---------|------|
| `artifacts/mao/scope-audit/*.json` | Hook snapshots at subagent start/stop (gitignored, **fail-open**) |
| `python3 scripts/mat-scope-audit.py gate --run-id <id>` | Parent/verifier **canonical** D2c gate after `issue-run` |
| `scripts/mat-scope-audit.py check --self-test` | Wired as `scope_audit` check on source profiles |

**Habits:**

- Parent runs `issue-run` before builder dispatch when using D2c correlation.
- After builder stop, evaluate `gate`; **protected-path breaches** and out-of-scope writes → canonical **FAIL** in `verify-result.md` when correlated — hooks alone do not enforce.

**Outcome:** Clear separation between advisory snapshots and parent-serialized verify truth.

**Not guaranteed:** Hooks blocking writes; automatic verifier FAIL without parent applying D2c rules.

---

## B. Efficient daily working habits

### B6. Context-budget discipline

**When:** Every session; especially parent orchestration and verifier runs.

**Habits:**

- Prefer `@file`, `@folder`, and paths named in the active plan over habitual full-repo context.
- Hand off via `docs/current-plan.md`, `build-result.md`, `verify-result.md` — not transcript replay.
- Verifier: scope to build-result + plan paths; do not substitute broad search for listed files.

**Honest product limit:** MAT rules, CI, and process encourage narrow context — they **do not block** Codebase Search or other broad controls in the **Cursor UI**. Operators can still choose them.

**Outcome:** Lower cost, fewer cross-slice accidents.

---

### B7. Worktrees (E10)

**When:** Parallel agents, dirty `main`, or collision-prone ports/observability.

**Habits:**

- Create isolation explicitly: `/mat-wt-create`, Agents Window worktree, or `git worktree add` — not assumed per Task.
- Bootstrap default: **`--metadata-only`** — `.cursor/worktree` markers + `runtime.env` only (no install, no env copy).
- Use **`--install`** when dependencies must be installed; add **`--copy-env`** only when intentional copy of root `.env` / `.mat.env` into the worktree is desired.

**Outcome:** Parallel work without stomping the primary checkout.

**Not guaranteed:** Full LSP inside worktrees; run explicit lint via hooks/scripts.

---

### B8. Environment ownership and loading

**When:** Adopting MAT, refreshing samples, or debugging “why hooks don’t see my key”.

**Writes (M10 contract):** mat-sync, bootstrap, and `update-mat.py` **do not** create or mutate live **`.env`** or **`.mat.env`**. They may merge **`.mat.env.sample`** (MAT-tool markers) and bootstrap may add **`.env.sample`** if missing.

**Intentional live writers:**

| Route | When |
|-------|------|
| `scripts/setup-dev.sh` | MAT **source** dev: copies `.env.sample` → `.env` if missing — not the default path for every adopted product repo |
| `bootstrap_worktree.sh --install --copy-env` | Opt-in copy into a worktree |
| Operator | `cp .mat.env.sample .mat.env` after reviewing merged sample |

**Reads (today):** MAT workflow hooks resolve `CURSOR_*` and `OBSERVABILITY_*` via `scripts/lib/mat_env.py` (through `.cursor/hooks/utils/mat_env_resolve.py`) on wired surfaces — MAO, observability POST, loop/stop flags, prompt validation, lifecycle hooks (`session_start`, `session_end`, `stop_validator`, `hook_contract`). Product API keys (`OPENAI_API_KEY`, etc.) still follow process env / `.env` as documented; hooks do not load full `.env` for unrelated keys.

**Outcome:** No false assumption that adopt “created my env files”.

**Not guaranteed:** Universal `.mat.env` hook support before M1/M2; duplicating secrets into both `.env` and `.mat.env` without a documented need.

---

### B9. Optional loop policy and run manifests (N4)

**When:** Long or retry-heavy orchestration; opt-in only.

**Defaults:** `CURSOR_MAT_LOOP_POLICY=0` — loop engine **off**.

**E8b operator map — these layers are not interchangeable** (defaults may align numerically but mean different things):

| Layer | Default / knob | What it limits | Authorizes next orchestration phase? |
|-------|----------------|----------------|-------------------------------------|
| **Slice repair budget** | `repair_attempt_limit` (3) + per-`slice_class` `max_attempts` in loop policy | Builder/loop self-repair iterations when `CURSOR_MAT_LOOP_POLICY=1` | No — advisory; files + parent MAO gates stay canonical |
| **Stop hook follow-up** | `stop_followup_limit` (2) = `hooks.json` `loop_limit` on Stop; opt-in `CURSOR_MAT_STOP_VALIDATOR_FOLLOWUP=1` | Cursor Stop `followup_message` continuations for incomplete handoffs | No — never replaces plan→build or build→validate checks |
| **Mission queue** | `mission_slice_limit` (15) | `/mat-long-run` slices per mission | Parent mission gate only |
| **Parent subagent retries** | Orchestrator policy (bounded; not hook-enforced) | Re-prompt or re-spawn builder/verifier after explicit parent decision | Yes — parent-owned; separate from hook `loop_limit` |
| **Run manifest** | `scripts/mat_run_manifest.py` | Session/run bookkeeping | No |
| **Loop manifest** | `artifacts/loop/<run-id>/manifest.json` | Per-run iteration state when policy on | No |

```bash
python3 scripts/mat_loop_policy.py budgets
bash scripts/doctor.sh --loop-policy
```

**Iteration logs:** Strict validation applies only when policy is on and slice class exemptions do not apply — see [`loop-policy.md`](../loop-policy.md).

**Outcome:** Clear which layer authorizes the next orchestration phase.

**Not guaranteed:** Hooks spawning subagents from loop output; loop state overriding `build-result.md` / `verify-result.md`.

---

### B10. Self-Compact (context checkpoints)

**When:** Long `/mat-long-run` sessions, swarms, or gauge **warning** / **force** pressure.

**Habits:**

- Enable opt-in hooks: `CURSOR_MAT_SELF_COMPACT=1` (force lane `CURSOR_MAT_SELF_COMPACT_FORCE=1` only when you accept tool gating).
- Optional gauge freshness spike: `CURSOR_MAT_SELF_COMPACT_LOG_PRETOOL=1` appends PreToolUse `context_usage_percent` to `artifacts/context-handoff/pre-tool-context-usage.jsonl`.
- Run `python3 scripts/mat-context-gauge.py` for Pi-like JSON (`notice_at` 55 / `warning_at` 70 / `force_at` 85 by default), or MCP tools `view_context` / `mat_self_compact` via [`scripts/mcp/mat_self_compact_server.py`](../../scripts/mcp/mat_self_compact_server.py) (local `.cursor/mcp.json` only).
- Follow [`.cursor/skills/mat-self-compact/SKILL.md`](../../.cursor/skills/mat-self-compact/SKILL.md): write `artifacts/context-handoff/note-to-self.md`, refresh MAO files, then manual Summarize when needed — no agent compaction API.
- Simulated long-run checklist: [`specs/mat-self-compact-cursor/pilot-long-run.md`](../../specs/mat-self-compact-cursor/pilot-long-run.md).

**Outcome:** Durable intent outside the conversation bucket; MAO files remain authoritative.

**Honest limit:** `preCompact` cannot steer summary content; hooks are advisory unless force lane is on.

---

## C. Installation, updates, and troubleshooting

### C10. Safe updates for adopted repositories

**When:** First adopt or ongoing MAT refresh on a product repo.

**Workflow:** **detect → plan → approve → verify** (`scripts/mat-sync.sh`, `/mat-adopt`, `/mat-sync`).

**Habits:**

- Review plan JSON: `changed_files`, `env_sample_merge_preview`, gitignore previews, `true_drift` conflicts.
- **`true_drift`** on registered MAT assets → **fail-closed** until resolved; product extensions in `.mat/product-extensions.json` v3 reduce false positives for product-owned skills/rules.
- **Incremental update:** `scripts/adoption/update-mat.py` dry-run → review → `--apply --approved --plan-file …` stages in an **isolated staging worktree** — inspect `staging-worktree=` output; promotion to the live product tree is an explicit operator step (commit/merge from staging), not an silent in-place overwrite of the whole tree by default.

**Outcome:** Predictable, reviewable upgrades.

**Not guaranteed:** Approve without review updates every path you expected; live env files are never auto-created (see B8).

---

### C11. Observability for troubleshooting

**When:** Debugging hook behavior, subagent lifecycle, or MAO timeline — not for proving slice completion.

**Layers:**

| Store | Contents |
|-------|----------|
| Observability SQLite (`apps/server`, hook_events) | Normalized PostToolUse / Stop / SubagentStop events |
| `artifacts/mao/*` | Gate, transitions, todo observations, scope-audit (gitignored, local) |
| `artifacts/loop/*` | Opt-in loop manifests/events |
| `artifacts/mat-runtime/` | Separate runtime review store (advisory) |

**MAO visibility panel:** Mixed-source observed summary — **not** live Cursor todo columns.

**Outcome:** Rich forensic context.

**Not guaranteed:** Dashboard todo parity; authoritative PASS/FAIL (files + parent checks remain canonical).

---

### C12. Plugin versus project adoption

**Decision tree:**

```
Need full MAT workflow on a product repo (.mat/, mat-sync, phase1 profile)?
  YES → mat-sync /mat-adopt path (product tree projection)
  NO → Need only IDE rules/commands/skills on a workstation?
         YES → Team plugin or local symlink (advisory)
         NO → MAT source repo development → clone multi-agent-teams; use source-full verify
```

**Three independent update channels:**

| Channel | Updates what | Writes product repo? |
|---------|--------------|----------------------|
| Team plugin refresh | `packages/mat-workflow/` indexed from `main` | **No** — IDE/plugin surface; enable at **user** scope (Customize → **User** → MAT Workflow) |
| `mat-sync` approve | `.mat/`, `.cursor/`, scripts per layout manifest | **Yes** — canonical adopt/upgrade projection |
| `update-mat.py --apply` | Staging worktree from upstream diff | **Promoted** by operator; not silent whole-tree replace |

**Precedence:** Project-local `.cursor/` and root `AGENTS.md` win for repo-specific behavior; `.mat/AGENTS.mat.md` is the MAT encyclopedia sidecar — see [`capability-precedence.md`](../capability-precedence.md).

**Known limitations (not fixed in O1):**

- **M8:** Adopted-contract doc link graph and `.cursor/` → missing root `docs/` paths in temp fixtures may still fail CI until M8 lands.
- **M9 (closed 2026-10-16):** Placeholder MCP removed; `bash scripts/doctor.sh --plugin` + packager validation. **Operating approach:** user-scope plugin only (Customize → **User** → MAT Workflow) — sufficient for advisory assets; product adopt remains mat-sync. **Add to project** (workspace scope) is an **optional** Cursor action; failures are a **known limitation** with RCA **blocked on evidence** (Plugins.log, Cursor build) per [`cursor-plugin-install.md`](cursor-plugin-install.md#add-to-project-failed-to-install-mat-workflow) — not required for Devora operators.

**Outcome:** Correct channel for adopt vs IDE-only vs source development.

**Not guaranteed:** Plugin install ≡ mat-sync; team plugin alone does not replace `.mat/` sidecar adoption.

---

## Quick checklist (orchestrated slice)

- [ ] Plan lists concrete paths and AC-N rows
- [ ] Parent transition check on files before dispatch
- [ ] MAO todos updated after check (or files-only fallback documented)
- [ ] Builder `build-result.md` meets Status / AC / Lint contract
- [ ] Verifier independent; scope-audit gate if D2c in play
- [ ] `phase1-verify` profile understood (especially on adopted trees)
- [ ] Env: samples merged, live env operator-owned
- [ ] Right update channel (mat-sync vs plugin vs updater staging)
