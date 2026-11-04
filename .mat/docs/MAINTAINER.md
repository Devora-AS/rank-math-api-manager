# Maintainer readiness checklist

**Last updated:** 2026-10-19 (M1 lifecycle wired-surfaces cross-ref)

This guide is the maintainer-facing readiness check for operating, adopting, and validating this repository without overstating what the workflow can prove.

## Supported environment

- **OS:** macOS and Linux are the supported maintainer environments. Windows should be treated as best-effort through WSL because the shipped shell scripts assume POSIX paths and tools.
- **Git:** minimum `2.39`; verify with `git --version`.
- **Python:** `>= 3.11`; verify with `python3 --version`.
- **Shells:** `bash` is required for repo scripts such as `scripts/phase1-verify.sh`, `scripts/doctor.sh`, and `scripts/adoption/bootstrap-workflow-into-repo.sh`. `zsh` is fine as an interactive operator shell, but the repo automation examples use `bash`.
- **Optional runtime tooling:** Bun `>= 1.3` is needed only for the observability server and dashboard. Maintainers can still run the core Python/docs checks without Bun.

Quick local preflight:

```bash
git --version
python3 --version
bash --version
zsh --version
```

## Required env vars

No single variable is required for every local task, but maintainers should decide the following before adoption or CI rollout.

| Variable | When it matters | Purpose | Default / local expectation | CI / shared environment note |
| --- | --- | --- | --- | --- |
| `OBSERVABILITY_SERVER_URL` | When hook events should POST to the Bun API | Event sink for `send_event.py` | Defaults in `.mat.env.sample` to `http://localhost:3001/events` | Set explicitly in CI if observability POSTs are part of the job |
| `OBSERVABILITY_API_TOKEN` | Only when the observability server requires auth | Bearer token for event POSTs | Unset by default | Store in CI secrets; never commit |
| `CURSOR_DESKTOP_NOTIFICATIONS` | Local-only convenience | Enables macOS desktop notifications on stop hooks | `false` in `.mat.env.sample` | Usually leave disabled in CI |
| `CURSOR_STORE_PROMPTS` | When you want local prompt persistence | Saves prompt data for session logging | `false` in `.mat.env.sample` | Enable only if your CI/runtime policy allows prompt storage |
| `CURSOR_NAME_AGENT` | Optional naming UX | Lets hooks name agents through an LLM helper | `false` in `.mat.env.sample` | Only useful when the matching API key is present |
| `CURSOR_VALIDATE_PROMPTS` | Optional prompt guardrails | Enables blocked-pattern prompt validation | `false` in `.mat.env.sample` | Roll out deliberately; avoid turning it on blindly in first-time adoption |
| `CURSOR_HOOK_CAPTURE`, `CURSOR_HOOK_CAPTURE_DIR`, `CURSOR_HOOK_CAPTURE_PER_SESSION` | Only for lifecycle audits | Controls raw hook payload capture under `artifacts/phase1/raw_payloads*` | Off unless set | Use an isolated path in CI and treat outputs as temporary evidence |
| `CURSOR_MAO_GATE` | When MAO advisory gate refresh is desired | Writes `artifacts/mao/gate.json` after handoff writes | Enabled unless set to `0`/`false`/`off` | Document the chosen setting in the job |
| `CURSOR_MAO_TODO_POST_TOOL_USE` | When todo-write observation is desired | Writes MAO todo observation artifacts | Enabled unless set to `0`/`false`/`off` | Advisory only; do not treat as live todo truth |
| `CURSOR_MAO_DOWNSTREAM_READINESS` | When readiness hints are desired | Writes `artifacts/mao/downstream-readiness.json` | Enabled unless set to `0`/`false`/`off` | Advisory only; parent file checks still own transitions |
| `CURSOR_MAT_ROUTING_ADVISORY_JSONL` | When per-event routing/cost JSONL capture is desired | Appends rows via `routing_advisory.py` when enabled | **Off** unless set to `1`/`true`/`on` (resolved via `mat_env`) | Advisory only; IO errors fail open; not workflow truth |
| `CURSOR_MAT_ROUTING_ADVISORY_PATH` | When JSONL should land somewhere other than the default | Overrides JSONL path (repo-relative or absolute) | Default `artifacts/mao/routing-advisory.jsonl` when JSONL is on | Ignored when JSONL capture is disabled |
| `CURSOR_MAT_ROUTING_ADVISORY_ROLLUP` | When session rollups should be written for advisory runs | Writes `artifacts/mao/routing_rollup_<session_id>.json` via `routing_rollup.py` | **On** by default unless set to `0`/`false`/`off` (`mat_env`, default true) | Advisory only; completeness ratios describe presence, not correctness |
| `CURSOR_MAT_LOOP_POLICY` | When loop policy integration is desired | Enables parent `mat_loop_policy.py evaluate` guidance and strict iteration-log validation | `0` (off) unless set to `1` | See [`docs/reference/loop-policy.md`](loop-policy.md); file handoffs remain canonical |
| `CURSOR_MAT_LOOP_PAUSE` | When human gate on loop progression is needed | Parent pauses loop until cleared | Unset (no pause) | Advisory only; parent-owned |
| `CURSOR_MAT_LOOP_EVENTS` | When loop handoff audit JSONL is desired | PostToolUse appends to `artifacts/loop/events.jsonl` on plan/build-result writes | `0` (off) unless set to `1` | Fail-open; see `loop_events.py` |
| `CURSOR_MAT_POST_TOOL_SCOPED_VALIDATE` | When faster PostToolUse feedback is desired | Prefer ruff/ty on changed `.py` and `tsc -p` for a single TS package; broader fallback when unsafe | `1` (scoped on) unless set to `0` | Does not replace `phase1-verify.sh` / `vue-tsc` / Bun smoke; see [`configuration.md`](configuration.md) |
| `CURSOR_MAT_STOP_VALIDATOR_FOLLOWUP` | When Stop-hook incomplete-handoff followup is desired | Emits `followup_message` + exit 0 (never exit-1 strict) | `0` (off) unless set to `1` | See [`loop-policy.md`](loop-policy.md) § Stop hook; Cursor treats exit 1 as fail-open |
| `CURSOR_MAT_SESSION_BUDGET_USD` | When advisory session budget notes should be written | Appends to `docs/session-summary.md` only when threshold is set, `session_id` is present, routing JSONL data loads, and best-effort `estimated_cost_usd_total` **exceeds** the threshold (`context_budget.py`) | Unset by default | **Not** a spend cap, block, or enforcement; estimates may be incomplete |
| `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `ELEVENLABS_API_KEY` | Only for LLM/TTS helpers that use them | Enables summaries, naming, or TTS integrations | Unset by default | Inject through CI secrets only if those helpers are in scope |
| `MULTI_AGENT_WORKFLOW_ROOT` | During adoption into another repository | Points the bootstrap command at this repo | Export locally before bootstrap | Set to the checkout path in automation that copies workflow assets |
| `CURSOR_MAT_COST_HYGIENE_ENFORCE` | When CI in an adopted repo should **hard-fail** the hygiene pack | Overrides `.mat/cost-hygiene-adoption.json` when set to `strict` (or set `warn_first` explicitly) | Unset: validator uses adoption file and defaults | Use `strict` in CI to force merge of MAT ignore fragments; leave unset in warn-first adoptions until the team is ready |

Always start from:

```bash
cp .env.sample .env
cp .mat.env.sample .mat.env
```

Never commit `.env`, copied secrets, or ad hoc session capture directories.

## Observability data handling

The observability server is useful for local operator visibility, but it is not a
redacted telemetry pipeline by default.

- Normalized event payloads can include raw `tool_output`.
- Dashboard payload previews may be truncated and should not be treated as the full record.
- The local observability SQLite store should be treated as sensitive local runtime exhaust.
- In shared or less-trusted environments, set `OBSERVABILITY_API_TOKEN` and review
  whether the current capture scope is appropriate before enabling broad event POSTs.

If you export logs or screenshots for bug reports, scrub secrets and private output first.

For SQLite path semantics, WebSocket preview caps vs full stored rows, gitignored growth under `artifacts/phase1/` and related trees, and recommended rotate/prune practices (no shipped auto-purge), see [Observability data retention and sampling policy](../architecture/observability-retention-policy.md).

## Documentation and skill inventory hygiene

When shipping new **adoption scripts**, **doctor/verify helpers**, or **operator workflows** under `scripts/adoption/` or `.cursor/skills/`:

1. List the script in [`docs/update-mat/index.md`](update-mat/index.md) or the command tables in this file when operators must run it.
2. Update [`docs/reference/components.md`](components.md) when the workflow is a first-class MAT capability.
3. Add or refresh a **repo-local skill** under `.cursor/skills/` when the workflow is reusable and longer than a one-line command note (for example worktree bootstrap, updater dry-run, legacy fingerprint verify).
4. Mirror the inventory in [`AGENTS.md`](../../AGENTS.md) per the **Inventory hygiene** subsection when the surface is repo-local and operator-facing.
5. Run `/update-docs` or the README **Docs ownership** checklist before closeout.

## Submit-time prompt validation (opt-in)

`CURSOR_VALIDATE_PROMPTS` gates **optional** substring checks on the user prompt inside [`before_submit_prompt.py`](../../.cursor/hooks/before_submit_prompt.py) (`validate_prompt()`). When set to `true`, the hook may emit `{"continue": false, ...}` for prompts matching configured blocked patterns.

- **Resolution:** in-scope hooks read MAT workflow / observability keys through [`.cursor/hooks/utils/mat_env_resolve.py`](../../.cursor/hooks/utils/mat_env_resolve.py) (`process` → `.mat.env` → `.env` for `CURSOR_*` / `OBSERVABILITY_*` only). Product API keys stay process / `.env` only.
- **Wired surfaces (M1):** same inventory as [Configuration — `.env` and `.mat.env`](configuration.md#.env-and-.mat.env): MAO gate toggles, observability POST URLs/tokens, routing advisory paths, session budget notes, loop policy flags, prompt validation, hook capture settings, Stop follow-up / desktop notifications (`stop_validator.py`), session lifecycle flags (`session_start.py`, `session_end.py`), and contract error POST (`hook_contract.py`) — not product API keys (`OPENAI_API_KEY`, etc.).
- **In-repo default:** the `blocked_patterns` list in `validate_prompt()` is **empty** — nothing is blocked until operators add explicit `(pattern, reason)` tuples in that function (or fork the hook).
- **Opt in:** set `CURSOR_VALIDATE_PROMPTS=true` in `.mat.env` (or `.env` when using the narrow `CURSOR_*` fallback) only after you deliberately add patterns and accept ownership of the behavior. The committed `.mat.env.sample` keeps `CURSOR_VALIDATE_PROMPTS=false` for MAT-wide adopters; do not ship a truthy default for everyone.
- **False positives:** substring checks are blunt — short acronyms or benign prose can match unintended patterns; treat blocks as operator-tuned policy, not security guarantees.
- **Relationship to cost hygiene:** prompt validation is independent of the cost & context hygiene rule (`.cursor/rules/cost-context-hygiene.mdc`) and `.cursorignore`; together they reduce noisy context and risky prompts when you choose to enable them.

## Cost & context hygiene — enforcement and diagnostics

The pack is enforced for this MAT source repository via `scripts/validate_cost_context_hygiene_pack.py` in `bash scripts/phase1-verify.sh`. Adopted **existing-project** runs record `.mat/cost-hygiene-adoption.json` with `enforcement: warn_first` and **never overwrite** a product-owned root `.cursorignore` when it already exists; when root `.cursorignore` is absent, bootstrap installs the same stack-detected template as new-project. See suggested merges under `.mat/docs/templates/*-*.mat-suggest` and the schema copy `docs/schemas/cost-hygiene-adoption.v1.json` (and sidecar copy after bootstrap). **New-project** uses `enforcement: strict` in the adoption file.

- **Override:** set `CURSOR_MAT_COST_HYGIENE_ENFORCE=strict` (or `warn_first`) in CI to bypass adoption defaults when you need a consistent gate.
- **Non-fatal report:** `python3 scripts/validate_cost_context_hygiene_pack.py --report --no-fail` (or `bash scripts/doctor.sh --cost-hygiene`) prints `FAIL` / `WARN` / `INFO` findings. With `--report`, a summary is also written to gitignored `artifacts/cost-hygiene/last-report.json` (append-only `report-events.jsonl`); this is **local advisory telemetry only** — not billing, not a token counter, and not a substitute for `build-result.md` / `verify-result.md` handoffs.
- **Honest UI boundary:** MAT **cannot** block broad `@Codebase` in the Cursor product; rules, CI, and this validator still shape expected defaults.

## Quality-command honesty — doctor diagnostics (A1 / B9)

Advisory scan for placeholder or fake-green patterns in MAT-owned verify/lint paths. Does **not** fail CI or doctor by default.

- **CLI:** `python3 scripts/validate_quality_commands.py --repo-root .` (optional `--json`; always exits 0).
- **Doctor:** `bash scripts/doctor.sh --quality-commands` — non-fatal; prints `WARN path:line: …` hints from `scripts/validate_quality_commands.py`.
- **Scan targets:** `scripts/phase1-verify.sh`, `.cursor/hooks/post_tool_validate.py`, `scripts/doctor.sh`.
- **Hook banner (B9):** when `post_tool_validate.py` skips Python lint (ruff missing/timeout) but would treat the hook as success, it emits one stderr advisory line prefixed with `[mat-quality-honesty]` — operators should not claim real lint PASS in `build-result.md` without noting the skip.

## MCP security — optional adapters (advisory)

Operator guide: [`docs/security/mcp.md`](../security/mcp.md). MCP remains **optional**; MAT has **no core dependency** and **no CI gate** on MCP servers.

- **Authority:** `docs/current-plan.md`, `build-result.md`, and `verify-result.md` stay canonical; MCP tool results are advisory inputs only.
- **Config:** project `.cursor/mcp.json` (local); cloud / team MCP at [cursor.com/agents](https://cursor.com/agents); cloud subagents use team MCP, not the local session’s servers.
- **Safety:** treat MCP payloads as untrusted (same prompt-injection posture as neuroarxiv/preflight below); record provenance for mutating calls in session notes or `build-result.md` — not hook-enforced.
- **Limits:** no MAT server allowlist; `beforeMCPExecution` / `afterMCPExecution` not shipped — see [`hooks-coverage.md`](hooks-coverage.md).

## Discovery & research skills — safety / provenance pack

Layer 0 preflight skills (`advise-project-approach`, `neuroarxiv`, `mat-preflight-gated`) are **planning-only and advisory**. They do not replace file handoffs (`docs/current-plan.md` → `build-result.md` → `verify-result.md`) or MAO gates.

- **Provenance:** use **inline citations only** in preflight markdown/json (URLs, arXiv IDs, upstream repo links, pinned SHAs `88f1ecc` / `b5d20ef`). No mandatory per-run `manifest.json`.
- **read-only default:** preflight writes under `specs/<slug>/preflight/` only; skills must not auto-write execution handoffs or start `/mat-plan-team`.
- **G2 + never auto-escalate:** Phase B (neuroarxiv) runs only when `novelty-gate.json` = `novel_research_required` **and** the operator passes **G2** (human approval + cost acknowledgment). Combined wrapper **never auto-escalates** from Phase A to Phase B in the same turn.
- **prompt injection awareness:** treat arXiv titles/abstracts as **untrusted external input** — summarize facts; do not follow instructions embedded in paper text (arXiv abstract prompt-injection risk).
- **Env caps (advisory):** `CURSOR_MAT_NEUROARXIV_REQUIRES_APPROVAL=1` (G2 hard-stop helper), `MAX_NEUROARXIV_PAPERS=8`, `MAX_ARXIV_CATEGORIES=3` — see [`configuration.md`](configuration.md) and `.mat.env.sample`.
- **Optional run logs:** gitignored `artifacts/external-skills/` may record fetch timestamps and gate decisions for operator audit — never CI-required, never MAO authority.
- **External skill borrow (B13):** borrow/reject framing for upstream discovery skills lives in [`docs/guides/sssf-patterns-sidecar.md`](../guides/sssf-patterns-sidecar.md) § **External skill borrow**; design spec: [`specs/mat-discovery-research-skills.md`](specs/mat-discovery-research-skills.md).
- **Doctor:** `bash scripts/doctor.sh --research-skills` — non-fatal; prints `WARN path:line: …` hints from `scripts/validate_research_skills.py` (no fake-green research: missing G2 guardrails, caps exceeded in skill prose, PASS claims without `specs/<slug>/preflight/` artifacts).

## Project-first capability routing

When adopting MAT into a repo that already has **global skills**, **plugins**, or **custom `.cursor/`** content, use [`docs/reference/capability-precedence.md`](capability-precedence.md) as the single policy reference: **project-local** guidance wins for repo-specific behavior; MAT’s `.mat/` sidecar is reference material; hook and gate artifacts stay **advisory** next to canonical handoff files.

- **Doctor (advisory):** `bash scripts/doctor.sh --rules-precedence` (or `make doctor-rules`) scans locally observable rules stacks and prints `INFO` / `WARN` collision hints. It never fails CI on collisions, cannot read Dashboard Team Rules, and does not reimplement Cursor’s merge engine. Latest JSON lands under gitignored `artifacts/doctor/rules-precedence-last.json`.

For MAT routing tiers and advisory budget guidance, use [`docs/reference/model-routing-policy.md`](model-routing-policy.md); keep any future adapter boundary optional and outside MAT core. Routing telemetry may support operator judgment, but it stays advisory-only and must never override canonical handoff files. For **bounded context** defaults and artifact-first handoffs, see [`docs/reference/context-budget-policy.md`](context-budget-policy.md).

## Cursor plugin releases (team marketplace)

Applies to **private Team Marketplace** distribution (path 2) — not local symlink canary (path 1) and not public Marketplace listing (path 3 / D3a-public).

After any change under `.cursor/` or `.cursor-plugin/` that affects shipped plugin assets:

1. `python3 scripts/package-cursor-plugin.py --repo-root . --stage-committed`
2. `python3 scripts/package-cursor-plugin.py --repo-root . --check-committed-sync`
3. `python3 scripts/package-cursor-plugin.py --repo-root . --validate-committed`
4. Bump `version` in `.cursor-plugin/plugin.json` when the release is user-visible (semver patch for asset refreshes; minor when operators need a clear “what build am I on?” signal).
5. Commit and push `packages/mat-workflow` and manifest files on `main`.
6. Wait for Dashboard **Enable Auto Refresh** (~10 minutes) or click **Refresh** manually.
7. Notify teammates to **Developer: Reload Window** after visible releases.

CI enforces steps 1–3 via `phase1-verify.sh` (`--validate-committed`, `--check-committed-sync`).

**Doc links (M7):** On the MAT source tree, `phase1-verify.sh` also runs `python3 scripts/validate_doc_links.py --repo-root . --profile source`. Policy, profiles, and allowlists: [`doc-link-validation.md`](doc-link-validation.md).

Operator runbook: [`docs/guides/cursor-plugin-install.md`](../guides/cursor-plugin-install.md#team-plugin-update-runbook).

## Pre-adoption checklist

Run these from the repository root before claiming the maintainer workflow is ready:

1. Confirm the supported toolchain:

```bash
git --version
python3 --version
bash --version
```

2. Create a local `.env` and decide which optional integrations you are actually enabling:

```bash
cp .env.sample .env
cp .mat.env.sample .mat.env
```

3. Validate the handoff-doc contract:

```bash
python3 .cursor/scripts/validate_artifacts.py --repo-root . --require-current-plan
```

4. Run the focused maintainer checklist test:

```bash
python3 -m unittest tests.test_maintainer_checklist -v
```

5. If you changed the docs index or shared workflow wording, re-run the shared docs contract test:

```bash
python3 -m unittest tests.test_workflow_docs -v
```

In a **downstream repo** that adopted MAT via bootstrap, workflow contract tests live under `.mat/tests/`. Run:

```bash
PHASE1_VERIFY_ADOPTED_CONTRACT_TESTS=1 bash scripts/phase1-verify.sh
# or directly:
python3 -m unittest discover -s .mat/tests -p 'test_*.py' -v
```

Default adopted `phase1-verify` uses the **adopted_operational** profile (skips `.mat/tests` with a visible banner). `PHASE1_VERIFY_SKIP_UNITTEST=1` remains a deprecated alias that forces the same skip.

**CI adopted-contract coverage (MAT source repo):** GitHub Actions runs `bash scripts/ci/run-adopted-contract-verify.sh` after the main `phase1-verify` step. The helper bootstraps a disposable **existing-project** fixture from the checked-out MAT source, then runs `PHASE1_VERIFY_ADOPTED_CONTRACT_TESTS=1` inside that fixture (Bun smoke skipped). Local dry-run:

```bash
bash scripts/ci/run-adopted-contract-verify.sh
```

6. Run the repo verification script before merge or release-style sign-off:

```bash
bash scripts/phase1-verify.sh
```

7. Check for whitespace/staging mistakes and accidental local artifacts:

```bash
git diff --check
git status --short
```

Adoption commands (MAT v1 installs a **`.mat/`** sidecar for packaged docs and workflow tests; root `README.md` / `CHANGELOG.md` / existing `AGENTS.md` are not overwritten in **existing-project** default runs):

- **New project**

```bash
export MULTI_AGENT_WORKFLOW_ROOT=/absolute/path/to/multi-agent-workflow
bash "$MULTI_AGENT_WORKFLOW_ROOT/scripts/adoption/bootstrap-workflow-into-repo.sh" --mode new-project --non-interactive "$(pwd)"
```

- **Existing project**

```bash
export MULTI_AGENT_WORKFLOW_ROOT=/absolute/path/to/multi-agent-workflow
bash "$MULTI_AGENT_WORKFLOW_ROOT/scripts/adoption/bootstrap-workflow-into-repo.sh" --mode existing-project --non-interactive "$(pwd)"
python3 scripts/adoption/migrate-long-run-state.py docs/architecture/long-run-state.md
python3 scripts/adoption/manage-agents-sidecars.py --repo-root .
python3 scripts/adoption/update-mat.py --source /absolute/path/to/multi-agent-workflow --ref main
```

Machine-readable layout rules: `scripts/adoption/adoption-layout-v1.json` (kept in sync with the bootstrap script). **`cursor_copy.dir_contents`** copies `.cursor/agents`, `.cursor/commands`, `.cursor/hooks`, and **`.cursor/skills`** (including `mat-plan-contract`) to adopted repos. **`mat_docs`** packages selected operator docs to `.mat/docs/` — including [`plan-contract.md`](plan-contract.md) → `.mat/docs/plan-contract.md` (Slice 6).

## MAT updater operator runbook

Use this when refreshing MAT-owned assets in an adopted repo (incremental drift). For bootstrap-style full layout refresh, see adoption commands above.

### Commands

**Dry-run (default — no staging writes on target root):**

```bash
python3 scripts/adoption/update-mat.py --source /absolute/path/to/multi-agent-workflow --ref main --repo-root .
```

**Apply staging (explicit approval + saved plan only):**

```bash
python3 scripts/adoption/update-mat.py --source /absolute/path/to/multi-agent-workflow --ref main --repo-root . \
  --apply --approved --plan-file artifacts/update-mat/<plan-from-dry-run>.json
```

**AGENTS sidecar refresh (non-destructive pointer blocks):**

```bash
python3 scripts/adoption/manage-agents-sidecars.py --repo-root .
```

Add `--inline-fallback` only when the explicit delimited MAT block is required.

### Audit artifacts

Each run writes metadata under **`artifacts/update-mat/`** (gitignored, local):

- Plan JSON from dry-run (`plan-file=` stdout path)
- Patch preview (`patch-file=` stdout path)
- Audit record (`audit-file=` stdout path)
- Legacy cleanup JSONL: `legacy-cleanup.jsonl`
- Quarantine copies: `legacy-quarantine/<run-id>/`

Inspect with `python3 scripts/adoption/apply_mat_legacy_cleanup.py --report` or `bash doctor.sh --legacy-cleanup`.

### Conflict and drift handling (fail-closed)

- Footprint conflicts and ambiguous nested `AGENTS.md` cases block apply until resolved manually.
- Target drift after dry-run (files changed between dry-run and apply) exits non-zero — re-run dry-run.
- Apply without `--approved` or without `--plan-file` exits non-zero with an explicit error.

### Verification

| Scope | Command |
| --- | --- |
| Fast updater verify | `python3 -m unittest tests.test_mat_updater_slice1 tests.test_mat_updater_integration -v` |
| Full updater verify | `python3 -m unittest tests.test_update_mat tests.test_mat_updater_integration tests.test_mat_updater_slice1 -v` |
| Security doc contract | `python3 -m unittest tests.test_workflow_docs.MatUpdaterSecurityDocsTest -v` |
| Full repo gate | `bash scripts/phase1-verify.sh` |

Operator checklist and evidence table: [`validation-report.md`](../../validation-report.md) slice 3. Adoption paths: [`docs/guides/getting-started-existing-projects.md`](../guides/getting-started-existing-projects.md), [`docs/guides/adoption-safe-defaults.md`](../guides/adoption-safe-defaults.md).

## Worktree bootstrap (E10)

- **Isolation paths:** Cursor managed worktrees (Agents Window), `/worktree`, `/best-of-n` (no auto-merge), or manual `git worktree add` / `/mat-wt-create`. Do not assume every parallel Task subagent gets its own tree without those flows. Default machine-wide cap: `cursor.worktreeMaxCount` = **25**.
- **Bootstrap modes:** `.cursor/hooks/bootstrap_worktree.sh [--metadata-only|--install|--check] <label>`
  - `--metadata-only` (default): markers + `runtime.env` only — zero package/network calls; no env copy.
  - `--install`: print planned commands, then install Python/Node deps (including `apps/server` and `apps/client` when `package.json` exists); add `--copy-env` to copy `.env` / `.mat.env` when missing.
  - `--check`: validate markers / `runtime.env`.
  - Port hints: `OBSERVABILITY_PORT` / `OBSERVABILITY_CLIENT_PORT` via `3001`/`5173` seeds + `cksum(label) mod 200` and `pick_free_port`.
- **Example native keys:** `.cursor/worktrees.json.example`
- **Health checks:** `bash scripts/check-worktrees.sh --strict` and `/mat-wt-check` remain the operator-facing collision and layout checks.
- **Remove:** `/mat-wt-remove` refuses dirty/unmerged exact-path removal unless explicitly forced.

## Rollback steps

Use the least-destructive rollback that fits the situation.

- **Disable optional runtime behavior first** by changing `.env` values such as `CURSOR_VALIDATE_PROMPTS=false`, `CURSOR_DESKTOP_NOTIFICATIONS=false`, or `CURSOR_MAO_GATE=0` before removing files.
- **Undo uncommitted workflow edits** in the current repo:

```bash
git restore --staged --worktree .cursor .mat AGENTS.md .env.sample docs scripts tests README.md
```

- **Remove newly added untracked workflow files** after reviewing `git status --short`:

```bash
git clean -fd .cursor .mat docs scripts tests apps
```

- **Back out a committed workflow change** without rewriting shared history:

```bash
git revert <commit-sha>
```

- **Remove an experimental worktree** created for adoption trials:

```text
/mat-wt-remove <branch>
```

- **Back out a staged MAT refresh** by deleting the disposable worktree and restoring any preserved files from `artifacts/update-mat/` backups when the preview or apply step is rejected.

- **Delete local-only capture and session artifacts** that should not survive a trial run:

```bash
rm -rf artifacts/phase1/raw_payloads*
rm -f docs/session-summary.md
```

## Blocked claims

Some claims remain intentionally blocked until stronger evidence exists.

- **Blocked today:** any claim of authoritative live Cursor todo parity, authoritative dashboard todo truth, or hook-driven subagent spawning from live todo state.
- **Canonical documentation for blocked claims:** `docs/reference/decision-record.md` and `ROADMAP.md`.
- **Operational restatement:** `README.md` and `docs/archive/phase4-roadmap-reassessment-checklist.md` summarize the same honesty boundary for maintainers.
- **Rule of thumb:** if a claim depends on hook observations, `artifacts/mao/*.json`, session transcripts, or observability snapshots alone, describe it as advisory evidence instead of shipped truth.

Do not remove a blocked claim from documentation until a dated operator-owned reassessment shows that the claim is now supportable.

## Command matrix

| Command | Use it for | Notes |
| --- | --- | --- |
| `python3 .cursor/scripts/validate_artifacts.py --repo-root . --require-current-plan` | Fast handoff-doc validation | Checks the current plan and required workflow artifacts |
| `python3 scripts/validate_planning_artifacts.py --repo-root .` | Planning artifact validation | Tier 1 onboarding + mat-plan-team `tasks.json` schema, Tier 2 solo `/mat-plan` section order, Tier 3 cross-file traceability, Tier 4 substantive `docs/current-plan.md` amendments + markers; hard-fail in `phase1-verify.sh` on MAT source; skipped on adopted sidecar |
| `python3 -m unittest tests.test_planning_artifacts_validation -v` | Planning validator regression | Temp-dir fixtures for pass/fail per tier |
| `python3 -m unittest tests.test_maintainer_checklist -v` | Focused maintainer guide contract | Fastest slice-local verification for this document |
| `python3 -m unittest tests.test_workflow_docs -v` | Shared docs/index contract | Re-run when `docs/index.md`, `README.md`, or shared wording changes |
| `bash scripts/phase1-verify.sh` | Full repo verification | Runs artifact validation, workflow surface checks, unittest discovery, optional Bun server smoke, and optional `apps/client` `bun install --frozen-lockfile` / `type-check` / `test:vitest` / `build` (skip with `PHASE1_VERIFY_SKIP_CLIENT=1`; no standalone `bun test` in CI path); CI in `.github/workflows/phase1-verify.yml` pins Node **22** for the `apps/client` toolchain and uses `fetch-depth: 0` on checkout because legacy manifest fingerprint tests need full git history; CI also runs `bash scripts/ci/run-adopted-contract-verify.sh` for packaged `.mat/tests` in a temp adopted fixture |
| `bash scripts/ci/run-adopted-contract-verify.sh` | Adopted contract CI helper | Bootstraps disposable existing-project fixture from `MULTI_AGENT_WORKFLOW_ROOT`, runs `PHASE1_VERIFY_ADOPTED_CONTRACT_TESTS=1 bash scripts/phase1-verify.sh` inside it (Bun/client skipped); wired in `.github/workflows/phase1-verify.yml` |
| `bash scripts/doctor.sh` | Operator environment diagnostics | Good first step when setup or PATH behavior is unclear |
| `bash scripts/adoption/bootstrap-workflow-into-repo.sh --mode new-project --non-interactive <target>` | New-project adoption | Installs `.cursor/`, root `scripts/`, minimal `docs/` handoffs, and `.mat/` sidecar (docs + tests) |
| `bash scripts/adoption/bootstrap-workflow-into-repo.sh --mode existing-project --non-interactive <target>` | Existing-project adoption | Same layout; default preserves existing root README/CHANGELOG/AGENTS and adds pointer notes to product-owned `AGENTS.md` files |
| `python3 scripts/adoption/manage-agents-sidecars.py --repo-root .` | Refresh AGENTS sidecar pointers | Re-applies the non-destructive pointer note across root and nested `AGENTS.md` files; add `--inline-fallback` only when the explicit inline block is required |
| `python3 scripts/adoption/update-mat.py --source <upstream> --ref <ref>` | Refresh MAT-owned assets from upstream | Defaults to dry-run, reads `scripts/adoption/mat-footprint-v1.json`, and stages apply-mode changes in a disposable worktree or branch-like path |
| `python3 -m unittest tests.test_mat_updater_slice1 tests.test_mat_updater_integration -v` | Fast MAT updater verify | Slice 1 foundation + slice 2 integration harness only |
| `python3 -m unittest tests.test_update_mat tests.test_mat_updater_integration tests.test_mat_updater_slice1 -v` | Full MAT updater verify | Mechanism tests plus integration harness and slice 1 wrapper tests |
| `python3 scripts/adoption/migrate-long-run-state.py docs/architecture/long-run-state.md` | Existing-project upgrade | Fixes the stale missing-`execution_mode` case only |
| `python3 scripts/adoption/mat_gitignore_merge.py verify-trackable --repo-root .` | Post-adoption `.gitignore` workflow trackability | Fail-closed semantics match `mat-sync.sh` `phase_verify`; use before debugging approve failures |
| `python3 scripts/adoption/mat_gitignore_merge.py rewrite-preview --repo-root .` | Plan-time directory-ignore rewrite preview | Maps `.cursor/` → `.cursor/*` (and `**/.cursor/` variants); never bulk-replaces product `.gitignore` |
| `git diff --check` | Whitespace / patch hygiene | Run before commit |
| `git status --short` | Staging audit | Make sure `.env`, `docs/session-summary.md`, and capture artifacts are not being committed |

## Dependabot (`apps/client`)

`.github/dependabot.yml` opens weekly grouped npm version-update PRs for `apps/client` only (vite, vue, typescript/types, vitest). **Operator expectations:**

- Merge Dependabot PRs only after local or CI `bash scripts/phase1-verify.sh` passes (client block uses `bun install --frozen-lockfile`, `type-check`, `test:vitest`, and `build`).
- **`@types/node` major ignores:** Dependabot ignores semver-major `@types/node` bumps (see `ignore` in `.github/dependabot.yml`) so type definitions stay aligned with the Node **22** pin in `.github/workflows/phase1-verify.yml` (`node-version: 22`) and the current `^22.x` range in `apps/client/package.json`. Minor and patch `@types/node` updates within major 22 still flow through the `typescript-types` group. When deliberately upgrading Node (for example to 24), remove or adjust the ignore, bump the CI Node pin, and update `package.json` together.
- **Lockfile requirement:** Any PR that changes `apps/client/package.json` dependencies **must** include the corresponding `apps/client/bun.lock` diff from `cd apps/client && bun install` (or equivalent). Dependabot npm updates do not reliably maintain Bun lockfiles; PRs without lockfile updates are expected to fail `bun install --frozen-lockfile` in `scripts/phase1-verify.sh`.
- **Security updates:** GitHub security updates may bypass version ignores. If a semver-major `@types/node` security PR appears, treat it as manual review — do not merge without aligning the CI Node pin and `package.json` with the proposed types major.
- No `apps/server` or github-actions ecosystems are configured — server deps and workflow pins stay manual.

## Artifact Taxonomy

Use one artifact taxonomy across the repo:

- **Canonical tracked handoffs**: tracked workflow contracts and handoff examples that define accepted interfaces.
- **Tracked distilled evidence**: curated tracked summaries or dated sign-off artifacts kept for review and historical reference.
- **Local mutable runtime exhaust**: rolling local outputs produced during normal operation or verification that should remain ignored by default.
- **Raw/sensitive captures**: prompt, payload, transcript, or other high-volume captures that may contain sensitive runtime detail.

Operational defaults:

- Treat `docs/current-plan.md`, `build-result.md`, and `verify-result.md` as canonical tracked handoff surfaces in this repo.
- Treat `artifacts/agent-traces/comparison.json` and `comparison.md` as tracked distilled evidence.
- Treat `docs/session-summary.md`, `artifacts/agent-traces/<run-id>/`, `artifacts/phase1/phase1-verify.log`, and local SQLite smoke-test files as local mutable runtime exhaust.
- Treat `.env`, `logs/`, and `artifacts/phase1/raw_payloads*` as raw/sensitive captures.

## Evidence conditionality

File handoffs remain the authoritative workflow state:

- `docs/current-plan.md`
- `build-result.md`
- `verify-result.md`

Everything else is conditional or advisory evidence:

- hook-written MAO artifacts under `artifacts/mao/`
- raw lifecycle capture trees under `artifacts/phase1/raw_payloads*`
- observability database rows and dashboard views
- chat-only transcript exports that may omit tool traces
- continual-learning AGENTS edits, when backed by the hook/state audit trail, are intentional maintenance and should not be treated as generic dirty-worktree mistakes

Maintainers should describe those sources as supporting evidence, not as proof of live Cursor todo truth.

## Delegated subagent troubleshooting

- A builder or verifier can spend real time on repo reads, searches, setup, or validation before the first file write.
- `subagentStart` means the subagent spawned; it does not mean the work is stalled.
- Missing `build-result.md` or `verify-result.md` is only one signal, not enough on its own to override the spawn evidence.
- Use `scripts/inspect_subagent_progress.py` or the optional `artifacts/mao/subagent-progress_<subagent_id>.json` summary as advisory context only.
- Use `scripts/inspect_worktree_attribution.py` before treating a live worktree blocker as unexpected; direct builder/verifier edits in the active window can be attributed, and descendant-subagent work should only be trusted when explicit lineage evidence is present. Treat weak overlap as uncertain, not descendant proof.
- Safe intervention requires clear failure, an aborted stop, or repeated non-progress after a reasonable wait.
- When in doubt, resume the same subagent first with a narrow status prompt instead of starting overlapping work.

## Routing rollups and analysis

- Hook env for JSONL, path override, rollup toggle, and session budget threshold: see [Configuration — Routing advisory and session budget](configuration.md#routing-advisory-and-session-budget-optional) and commented keys in `.mat.env.sample`. Resolution matches **M1** (`scripts/lib/mat_env.py` via `mat_env_resolve.py`).
- `CURSOR_MAT_ROUTING_ADVISORY_JSONL` defaults **off**; `CURSOR_MAT_ROUTING_ADVISORY_ROLLUP` defaults **on**. Neither replaces file handoffs or MAO gates.
- `scripts/analyze_routing_advisory.py` is for local inspection only; it helps explain reason/tier patterns, completeness, and session rollups, but it is still advisory evidence.
- `scripts/generate_fixture_from_session.sh` normalizes a session into a stable JSON fixture for regression coverage.
- `artifacts/mao/prompt_lint_<session_id>.log` records advisory-only prompt warnings when the prompt is too large, too file-heavy, or loaded with avoid-list docs without a rationale.
- `CURSOR_MAT_SESSION_BUDGET_USD` enables **optional** advisory session budget notes in `docs/session-summary.md` when the best-effort estimated session cost **exceeds** the threshold (requires `session_id` and routing JSONL data). This is **not** a spend cap or enforcement; treat notes as hints, not accounting truth.
- mat-sync, bootstrap, and `update-mat.py` merge workflow keys into **`.mat.env.sample` only** — never auto-write live `.env` or `.mat.env` ([`env-write-contract.md`](env-write-contract.md)).
- Low completeness ratios usually mean optional fields were not emitted, not that the routing decision failed.
- For operational closeout, validate representative fixture-backed runs that include docs-only, cross-file, retry or compaction-heavy, ambiguous planning, and safety-sensitive samples before calling the telemetry healthy.
- When `context_pressure` looks suspicious, compare the advisory record, the prompt shape, and the resulting handoff notes before calling it a false positive.
- Record the compact baseline somewhere reviewable, but do not turn the summary into a claim of routing correctness.

Before any commit, run:

```bash
git status --short
```

Then confirm that session-only or local-only artifacts are not staged accidentally, including:

- `.env`
- `docs/session-summary.md`
- `artifacts/phase1/phase1-verify.log`
- `artifacts/phase1/raw_payloads*`
- temporary SQLite files under `artifacts/phase1/`
- any local audit scratch files created during verification

## Final closeout freshness gate

Before any final "green", merge-ready, push-ready, or `mission_complete` claim, rerun the closeout checks after the last meaningful edit to any of these files:

- `build-result.md`
- `verify-result.md`
- `artifacts/agent-traces/comparison.json`
- `artifacts/agent-traces/comparison.md`
- `docs/session-summary.md` when it exists for the current session

Minimum command set:

```bash
python3 .cursor/scripts/validate_artifacts.py --repo-root . --require-current-plan
python3 scripts/validate_closeout_coherence.py --repo-root .
python3 scripts/validate_planning_artifacts.py --repo-root .
```

If the comparison artifacts only support generic runtime spawns or correlated role attribution, keep that lower proof tier in all closeout wording. Do not rewrite generic evidence as typed builder/verifier proof.

## Planning artifacts validation

`scripts/validate_planning_artifacts.py` enforces planning contracts under `specs/` and substantive `docs/current-plan.md` on the MAT **source** repo (wired in `scripts/phase1-verify.sh` after closeout coherence; adopted sidecar trees print `planning artifacts validation: SKIPPED (adopted sidecar)`).

**Planning Step 0 (SOP, v1):** `/mat-plan` and `/mat-plan-onboarding` document **Step 0 — Deep analysis** before artifact writes. This is doc-test locked via `DeepAnalysisStep0Test` in `tests/test_workflow_docs.py`; **no validator tier** in v1 (opt-in-on-edit N/A). Step 0 is workflow prose only — it does not add a 14th Tier 2 required section.

| Tier | Target | Behavior |
| --- | --- | --- |
| 1 | `planning_mode: plan_onboarding` `tasks.json` | Structural validation against `docs/templates/tasks-schema.json` (stdlib-only keyword subset) |
| 1 | `planning_mode: mat-plan-team` `tasks.json` | Structural validation against `docs/templates/tasks-schema-mat-plan-team.json` (design + execution_plan source artifacts; no `goal`/`spec_refs` on tasks) |
| 1 (skip) | Unknown `planning_mode` | Skipped with `unknown_planning_mode_skipped` notice — no partial checks |
| 2 | Root `specs/<slug>.md` solo `/mat-plan` outputs | 13 required `##` sections in order; Tier 2b validation-loop subsections under `## Testing Strategy` for non-grandfathered specs; Tier 2c `[new]`/`[existing]` tags on every `## Relevant Files / Areas` list bullet for non-grandfathered specs; Tier 2d optional-when-present `## Related plans` with `### back_refs` / `### forward_refs` for non-grandfathered specs; Tier 2e optional-when-present `## Open Decisions` with `OD-###` decision rows for non-grandfathered specs; optional-when-present Task type / Complexity header tags (allowlisted tokens; not YAML frontmatter); skips grandfathered legacy plans, validation-loops grace registry, relevant-files-tag grace registry, related-plans grace registry, open-decisions grace registry, `*-APPROVAL.md` sidecars, and root `.md` when `specs/<slug>/` exists |
| 3 | Onboarding packages | Cross-file traceability (`SPEC-###`, PRD IDs, `depends_on`, `source_artifacts` paths) |
| 4 | Substantive `docs/current-plan.md` | Required `## Amendments` + amendment line format; contract marker syntax in checklist sections (`Implementation steps`, `Acceptance criteria`, `Binary acceptance criteria`); skips missing/placeholder/session-idle plans in **header region only** (first ~25 lines or content before first checklist heading; mirrors MAO `_plan_ready()` semantics) |

**Tier 4 orchestration SOP:** Active substantive plans should declare **`Status: Active orchestration slice`** in the header. Avoid idle phrases (`session idle`, `no active orchestration slice`) in implementation-step or acceptance-criteria body text when possible — advisory hygiene only; header-only skip is canonical.

**Execution plan templates (Slice 5):**

| Template | Tier | Role |
|----------|------|------|
| [`docs/templates/adoption-minimal-current-plan.md`](../templates/adoption-minimal-current-plan.md) | lite | Adoption bootstrap and narrow sprint slices |
| [`docs/templates/execution-plan-template.md`](../templates/execution-plan-template.md) | standard | Orchestrated execution projection (`/mat-plan-team`, `/mat-long-run`) with validation-loop prose |

**Grandfather registry:** `LEGACY_SOLO_PLANS` in `scripts/validate_planning_artifacts.py` — add paths there when a historical solo plan cannot meet the Tier 2 contract yet; remove entries when migrated. **`VALIDATION_LOOPS_GRANDFATHERED_SOLO_PLANS`** — same pattern for Tier 2b validation-loop subsections under `## Testing Strategy`; remove a path when the spec gains both canonical loop subsections or is substantively revised. **`RELEVANT_FILES_TAG_GRANDFATHERED_SOLO_PLANS`** — separate frozenset for Tier 2c `[new]`/`[existing]` tags on `## Relevant Files / Areas` list bullets; remove a path when the spec is substantively revised and bullets are tagged. **`RELATED_PLANS_GRANDFATHERED_SOLO_PLANS`** — separate frozenset for Tier 2d optional `## Related plans` shape; remove a path when the spec gains a valid Related plans section or is substantively revised. **`OPEN_DECISIONS_GRANDFATHERED_SOLO_PLANS`** — separate frozenset for Tier 2e optional `## Open Decisions` shape; remove a path when the spec gains a valid Open Decisions section or is substantively revised. Optional cross-reference: `tasks.json` `open_questions` may cite `OD-###` ids when both exist — no schema change in v1. **Dynamic enumeration (Tier 2c merge):** seed `RELEVANT_FILES_TAG_GRANDFATHERED_SOLO_PLANS` from `git ls-files 'specs/*.md'` (root-level solo plans only) at build time; **exclude** `specs/planf3-polish-mission.md` so it remains the Tier 2c exemplar without grace. **Dynamic enumeration (Tier 2d merge):** seed `RELATED_PLANS_GRANDFATHERED_SOLO_PLANS` from the same `git ls-files 'specs/*.md'` set; **exclude** `specs/planf3-audit-trail-mission.md` so it remains the Tier 2d exemplar without grace. **Dynamic enumeration (Tier 2e merge):** seed `OPEN_DECISIONS_GRANDFATHERED_SOLO_PLANS` from the same `git ls-files 'specs/*.md'` set; **exclude** `specs/planf3-audit-trail-mission.md` so it remains the Tier 2e exemplar without grace. New solo specs after merge must include loop blocks, Relevant Files tags, Related plans shape, and Open Decisions shape immediately when they add those optional sections. Extend `docs/templates/tasks-schema.json` or `docs/templates/tasks-schema-mat-plan-team.json` only with keywords supported by `scripts/lib/planning_schema_validate.py` (document new keywords in this section).

### Living-plan amendments (plan contract v0.1, Slice 2)

Append-only **`## Amendments`** on living markdown plans — **CI-enforced on substantive `docs/current-plan.md` via Tier 4** (`validate_planning_artifacts.py`). Operator guidance for all living plans; see [`docs/architecture/plan-contract.md`](plan-contract.md).

| Rule | Value |
|------|-------|
| Section | `## Amendments` (exact level-2 heading) |
| Format | `- YYYY-MM-DDTHH:MM:SSZ — role — summary` (ISO-8601 UTC) |
| Placement | `docs/current-plan.md` / `plan-summary.md`: **last** section. Solo `specs/<slug>.md`: **second-to-last** before `## Recommended Next Command` |
| Forbidden | Rewrite/delete prior lines; edit timestamps |

**Who may append:**

| Role | May append? | Notes |
|------|-------------|-------|
| Operator / parent orchestrator | Yes | Always, including during orchestration |
| Builder | During active build only | Scope drift; cite triggering checklist item |
| Verifier | No | Read-only; report in `verify-result.md` |
| Planning agents (`/mat-plan`, `/mat-plan-onboarding`) | While authoring, before approval | Same session only |

Grandfathered `LEGACY_SOLO_PLANS` and idle placeholder `docs/current-plan.md` files are not retrofitted until substantively edited (Decision G).

### In-plan status markers (plan contract v0.1, Slice 3)

Contract markers on checklist lines in execution plans — **CI-enforced on substantive `docs/current-plan.md` via Tier 4** (`validate_planning_artifacts.py`). Operator guidance for all execution plans; see [`docs/architecture/plan-contract.md`](plan-contract.md).

| Marker | Meaning | Typical transition |
|--------|---------|-------------------|
| `[]` | Idle / not started | → `[wip]` |
| `[wip]` | In progress | → `[x]` or `[f]` |
| `[x]` | Done for this slice | terminal |
| `[f]` | Failed / blocked (reason required) | → `[wip]` after fix, or append `## Amendments` |

**State machine:** `[] → [wip] → [x]` or `[] → [wip] → [f] → [wip]` (retry).

**Who mutates when:**

| Role | May mutate markers? | Notes |
|------|---------------------|-------|
| Builder | Yes | In-place on active checklist lines during build |
| Parent orchestrator | Yes | May set `[wip]` at slice start when seeding plan |
| Verifier | No | Read-only; **warn-not-fail** in `verify-result.md` when markers disagree with passing build handoff |
| Operator | Yes | Same as parent when not using orchestrator |
| MAO todos | No | Advisory only — `[mao:build] in_progress` ≠ plan-line `[wip]` |

**Authority:** in-plan markers are **advisory**; MAO build→validate gates use `build-result.md` / `verify-result.md` only ([`workflow-artifact-contract.md`](workflow-artifact-contract.md)).

### Plan contract meta-skill (Slice 6)

Procedural encoding of contract v0.1 Decisions A–D (plus Decision E validation-loop SOP) lives in [`.cursor/skills/mat-plan-contract/SKILL.md`](../../.cursor/skills/mat-plan-contract/SKILL.md). The skill **does not replace** slash commands — it cross-references `/mat-plan`, `/mat-plan-onboarding`, `/mat-plan-team`, `/mat-sprint`, and `/mat-long-run`. Planning commands include one-line pointers to the skill. On bootstrap, the full `.cursor/skills/` tree copies via `cursor_copy.dir_contents`; operator summary [`plan-contract.md`](plan-contract.md) packages to `.mat/docs/plan-contract.md`.
