# Configuration

- Purpose: Document the configurable parts of the workflow, including `.env`, hooks, worktrees, MCP servers, retries, and observability.
- Audience: Maintainers and operators tuning the system for a specific project.
- Prerequisites: Access to `.env`, `.cursor/hooks.json`, `.cursor/worktrees.json`, and `.cursor/mcp.json`.
- Status: complete
- Last updated: 2026-06-25
- Author: Cursor agent (GPT-5.4)

## Missing Prerequisites

- The current workspace snapshot does not show package manifests for the observability apps. Validate the runtime separately before treating the Bun/Vue stack as production-ready.

## Related Files

- [Hook manifest](../../.cursor/hooks.json)
- [Worktree config](../../.cursor/worktrees.json)
- [MCP config](../../.cursor/mcp.json)
- [Environment template (product)](../../.env.sample)
- [MAT workflow template](templates/.mat.env.sample)
- [MAT env loader](../../scripts/lib/mat_env.py)
- [Components](components.md)
- [Pilot report](../archive/pilot-report.md)
- [Artifacts index](artifacts-index.md)

## `.env` and `.mat.env`

**Product** secrets and API keys — start from:

```bash
cp .env.sample .env
```

**MAT workflow** configuration (`CURSOR_*`, `OBSERVABILITY_*`, MAO, loop policy, capture toggles) — start from:

```bash
cp .mat.env.sample .mat.env
```

`.mat.env` is gitignored (like `.env`). MAT bootstrap, mat-sync, and `update-mat.py` merge upstream keys into **`.mat.env.sample` only** (MAT-tool marker block); root `.env.sample` stays product-only. **Live `.env` and `.mat.env` are never auto-merged** — copy new sample keys manually after refresh.

Resolution precedence for hooks (`scripts/lib/mat_env.py`, imported in hooks via [`.cursor/hooks/utils/mat_env_resolve.py`](../../.cursor/hooks/utils/mat_env_resolve.py)): process `os.environ` → `.mat.env` → `.env` (only `CURSOR_*` / `OBSERVABILITY_*` keys) → documented defaults. Wired surfaces include MAO gate toggles, observability POST URLs/tokens, routing advisory paths, session budget notes, loop policy flags, prompt validation, hook capture settings, Stop follow-up / desktop notifications (`stop_validator.py`), session lifecycle flags (`session_start.py`, `session_end.py`), and contract error POST (`hook_contract.py`) — not product API keys (`OPENAI_API_KEY`, etc.).

Key variables (see samples for full lists):

| Variable | Default / example | Purpose |
|----------|-------------------|---------|
| `OBSERVABILITY_SERVER_URL` | `http://localhost:3001/events` | Target for hook event POSTs |
| `CURSOR_DESKTOP_NOTIFICATIONS` | `false` | Enable macOS notifications in `stop_validator.py` |
| `CURSOR_STORE_PROMPTS` | `false` | Persist prompts in `.cursor/data/sessions/` |
| `CURSOR_NAME_AGENT` | `false` | Use Anthropic naming helper in `before_submit_prompt.py` |
| `CURSOR_VALIDATE_PROMPTS` | `false` | Turn on prompt blocking rules |
| `CURSOR_HOOKS_LOG_DIR` | unset | Override default `logs/` location |
| `CURSOR_HOOK_CONTRACT_EMIT_ERROR_OBSERVABILITY` | `0` | Opt-in fail-open POST of structured hook `kind: "error"` envelopes to `/api/events` as `HookContractError` |
| `ENGINEER_NAME` | unset | Personalize optional TTS announcements |
| `ANTHROPIC_API_KEY` | unset | Required for Anthropic helper client |
| `OPENAI_API_KEY` | unset | Required for OpenAI helper client or TTS |
| `ELEVENLABS_API_KEY` | unset | Required for ElevenLabs TTS |

### Lifecycle raw payload capture (optional)

Hooks read these via **`scripts/lib/mat_env.py`** (process → `.mat.env` → `.env` `CURSOR_*` fallback). Used for audits and stdin field verification.

| Variable | Example | Purpose |
|----------|---------|---------|
| `CURSOR_HOOK_CAPTURE` | `1` | Enable writing selected hook stdin JSON to disk |
| `CURSOR_HOOK_CAPTURE_EVENTS` | `sessionStart,sessionEnd,stop,preCompact` | Comma-separated hook names to capture |
| `CURSOR_HOOK_CAPTURE_DIR` | `artifacts/phase1/raw_payloads-audit` | Output root (relative → repo root; absolute paths allowed) |
| `CURSOR_HOOK_CAPTURE_PER_SESSION` | `1` | Nest files under `<capture-dir>/<sanitized-conversation-id>/` so composer sessions do not mix in one folder |

Details: [`docs/archive/hook-payload-verification.md`](../archive/hook-payload-verification.md), [`docs/guides/troubleshooting.md`](../guides/troubleshooting.md).

### MAT Loop Policy (optional)

Opt-in loop engineering for orchestrated slices. Canonical operator reference: [`loop-policy.md`](loop-policy.md). Runtime: `scripts/mat_loop_policy.py`.

| Variable | Default | Purpose |
|----------|---------|---------|
| `CURSOR_MAT_LOOP_POLICY` | `0` | Set to `1` to enable loop manifest init, parent `evaluate()` after builder attempts, and strict `## Loop Iteration Log` validation in `.cursor/scripts/validate_artifacts.py` for orchestrated non-lite/docs runs |
| `CURSOR_MAT_LOOP_PAUSE` | unset | When set, parent should pause loop progression until cleared (human gate) |
| `CURSOR_MAT_LOOP_EVENTS` | `0` | Set to `1` to append handoff events to `artifacts/loop/events.jsonl` on `docs/current-plan.md` or `build-result.md` writes (PostToolUse; fail-open) |
| `CURSOR_MAT_STOP_VALIDATOR_FOLLOWUP` | `0` | Set to `1` for Stop hook `followup_message` + exit 0 when orchestrated handoffs look incomplete (see [`loop-policy.md`](loop-policy.md) § Stop hook) |
| `CURSOR_MAT_SELF_COMPACT` | `0` | Set to `1` to enable MAT Self-Compact hook extensions (`pre_tool_use`, `pre_compact`, `session_start`, `stop_validator`) and gitignored `artifacts/context-handoff/` updates — see [`.cursor/skills/mat-self-compact/SKILL.md`](../../.cursor/skills/mat-self-compact/SKILL.md) |
| `CURSOR_MAT_SELF_COMPACT_FORCE` | `0` | When `1` **and** self-compact is on: at ≥ force threshold, PreToolUse emits `permission: deny` except writes under `artifacts/context-handoff/` and `python3 scripts/mat-context-gauge.py` |
| `CURSOR_MAT_SELF_COMPACT_NOTICE_PCT` | `55` | Notice tier (PreToolUse `agent_message`) |
| `CURSOR_MAT_SELF_COMPACT_WARNING_PCT` | `70` | Warning tier (aligns with routing advisory 70% boundary) |
| `CURSOR_MAT_SELF_COMPACT_FORCE_PCT` | `85` | Force tier (deny when force lane on) |
| `CURSOR_MAT_SELF_COMPACT_LOG_PRETOOL` | `0` | When `1` **and** `CURSOR_MAT_SELF_COMPACT=1`, append one JSON line per PreToolUse with `context_usage_percent` to `artifacts/context-handoff/pre-tool-context-usage.jsonl` (spike; gitignored) |

**Self-Compact MCP (optional, v2):** stdio server at `scripts/mcp/mat_self_compact_server.py` exposes tools `view_context` and `mat_self_compact`. Requires the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) in the operator environment — not a MAT core dependency:

```bash
# From repository root (example; use a venv or uv as you prefer)
uv run --with mcp python3 scripts/mcp/mat_self_compact_server.py
```

Add a **local** `.cursor/mcp.json` entry pointing at that command; the committed template stays empty. See [`docs/security/mcp.md`](../security/mcp.md).
| `CURSOR_MAT_POST_TOOL_SCOPED_VALIDATE` | `1` (scoped on) | Set to `0` to force project-wide `ruff` / `ty` / root `tsc` on every file-writing PostToolUse (legacy behavior). When on (default), `post_tool_validate.py` prefers changed `.py` paths and package `tsc -p` when all changed `.ts`/`.tsx` share one known package (`apps/client`, `apps/server`, or repo-root `tsconfig.json` when present). Falls back to broader checks when the change list is empty, paths are outside the repo, TypeScript packages are mixed, or a package tsconfig is missing. **Trade-off:** faster hook feedback may miss issues only `bash scripts/phase1-verify.sh` catches (`vue-tsc`, Bun server smoke, full-repo ruff). Hooks do not replace CI. |

**Handoff JSONL row shape** (one object per line; also accepted by the observability adapter as advisory `LoopHandoff` when posted to `/events` or `/api/events`):

| Field | Required | Description |
|-------|----------|-------------|
| `event_version` | yes | Schema version string (currently `"1"`) |
| `observed_at` | yes | ISO-8601 UTC timestamp |
| `trigger` | yes | Emitter context (e.g. `post_tool_use`) |
| `handoff` | yes | `build_result` or `current_plan` |
| `changed_paths` | yes | Repo-relative paths written in the triggering tool call |

Example:

```json
{
  "event_version": "1",
  "observed_at": "2026-08-12T12:00:00+00:00",
  "trigger": "post_tool_use",
  "handoff": "build_result",
  "changed_paths": ["build-result.md"]
}
```

API posts use `event_type: "LoopHandoff"` with the same fields under `payload` plus `non_authoritative: true` (fail-open visibility only).

When `CURSOR_MAT_LOOP_POLICY=1`, parents initialize loop manifest state per slice (see [`loop-policy.md`](loop-policy.md) — `scripts/mat-loop-manifest.py init` writes `artifacts/loop/<run-id>/manifest.json` and mirrors `artifacts/loop/manifest.json`); builders should include `## Loop Iteration Log` on `build-result.md` unless the slice is `lite` tier or `docs` class (see plan header or manifest `slice_class`).

### Layer 0 preflight — discovery / research skills (optional)

Operator-opt-in caps for neuroarxiv Phase B. Not required for CI or `phase1-verify.sh` (no network research in gates). Design reference: [`specs/mat-discovery-research-skills.md`](specs/mat-discovery-research-skills.md).

| Variable | Default | Purpose |
|----------|---------|---------|
| `CURSOR_MAT_NEUROARXIV_REQUIRES_APPROVAL` | `1` (documented in `.mat.env.sample`; unset = skill default posture) | When `1`, neuroarxiv treats missing **G2** in-thread approval as a **hard stop** before Phase B |
| `MAX_NEUROARXIV_PAPERS` | `8` | Maximum paper reads (abstract processing) per preflight run — normative cap ≤8 |
| `MAX_ARXIV_CATEGORIES` | `3` | Maximum arXiv categories queried per run — normative cap ≤3 |

Optional fetch helper: `scripts/preflight/fetch_arxiv.py` reads these env vars. Advisory honesty scan: `python3 scripts/validate_research_skills.py --repo-root .` or `bash scripts/doctor.sh --research-skills`.

### Routing advisory and session budget (optional)

Hooks read these through **`scripts/lib/mat_env.py`** (process `os.environ` → `.mat.env` → `.env` with `CURSOR_*` / `OBSERVABILITY_*` keys only). Implementation: [`.cursor/hooks/utils/routing_advisory.py`](../../.cursor/hooks/utils/routing_advisory.py), [`.cursor/hooks/utils/routing_rollup.py`](../../.cursor/hooks/utils/routing_rollup.py), [`.cursor/hooks/utils/context_budget.py`](../../.cursor/hooks/utils/context_budget.py). Deeper operator notes: [`routing_advisory.md`](routing_advisory.md), [`context-budget-policy.md`](context-budget-policy.md).

All outputs under `artifacts/mao/` and budget notes in `docs/session-summary.md` are **advisory only** — they do not gate MAO transitions, block tools, or enforce spend. mat-sync, bootstrap, and `update-mat.py` merge keys into **`.mat.env.sample` only**; they never create or auto-merge live `.env` or `.mat.env` ([`env-write-contract.md`](env-write-contract.md)).

| Variable | Default | Purpose |
|----------|---------|---------|
| `CURSOR_MAT_ROUTING_ADVISORY_JSONL` | off (`0` / unset) | When enabled (`1` / `true` / `on`), append routing advisory rows to JSONL |
| `CURSOR_MAT_ROUTING_ADVISORY_PATH` | `artifacts/mao/routing-advisory.jsonl` | Override JSONL path (repo-relative or absolute); used when JSONL capture is enabled |
| `CURSOR_MAT_ROUTING_ADVISORY_ROLLUP` | on | Session rollup files `artifacts/mao/routing_rollup_<session_id>.json`; set `0` / `false` / `off` to disable |
| `CURSOR_MAT_SESSION_BUDGET_USD` | unset | Positive USD threshold for **optional** session budget notes only |

**JSONL vs rollup:** JSONL event capture is **opt-in** (default off). Session rollups are **on by default** and summarize advisory records for a session; disable rollups independently of JSONL when you want less disk noise.

**Session budget notes** (`append_session_budget_advisory_note` in `context_budget.py`): not a spend cap or enforcement. A note is written only when (1) `CURSOR_MAT_SESSION_BUDGET_USD` resolves to a positive threshold, (2) a `session_id` is present, (3) routing advisory data can be loaded from the JSONL path (default or `CURSOR_MAT_ROUTING_ADVISORY_PATH`), and (4) the best-effort `estimated_cost_usd_total` for that session **exceeds** the threshold. Estimates may be incomplete when advisories omit cost fields.

Inspect locally: `python3 scripts/analyze_routing_advisory.py` (advisory summaries only).

## `.cursor/hooks.json`

The active hook manifest follows Cursor's current `version + hooks object` shape:

```json
{
  "version": 1,
  "hooks": {
    "beforeSubmitPrompt": [
      {
        "command": "python3 .cursor/hooks/before_submit_prompt.py",
        "failClosed": false
      }
    ],
    "stop": [
      {
        "command": "python3 .cursor/hooks/stop_validator.py",
        "loop_limit": 2,
        "failClosed": false
      }
    ]
  }
}
```

Tuning guidance:

- Increase `loop_limit` only when an auto-retry loop is truly desirable.
- Leave `failClosed` as `false` for observability hooks so telemetry outages do not block work.
- Use `matcher` only when you need event filtering on supported hook types.
- Per current Cursor hook docs, the optional per-script timeout key is `timeout` (seconds), not `timeout_ms`.
- This repo's current `.cursor/hooks.json` does not set explicit per-hook `timeout` values; the manifest relies on Cursor defaults plus script-local subprocess timeouts where needed.

### Hook contract dry-run support

This repo now ships a shared hook contract helper at [`../.cursor/hooks/hook_contract.py`](../../.cursor/hooks/hook_contract.py). Supported scripts accept a manual `--dry-run` flag and emit a structured JSON envelope with:

- `hook_event`
- `script`
- `kind`
- `message`
- `details`
- `retryable`
- `dry_run`

Bounded semantics:

- `--dry-run` is for manual verification and tests; it is not enabled in the checked-in hook manifest.
- Dry-run still reads stdin and may inspect existing files or derive normalized payloads.
- "No side effects" means the hook does not perform network POSTs, write logs/artifacts, spawn validator or notification subprocesses, or enforce a blocking/non-zero decision based on the inspected payload.
- With `CURSOR_HOOK_CONTRACT_EMIT_ERROR_OBSERVABILITY=1`, only non-dry-run `kind: "error"` envelopes are mirrored to observability as `HookContractError`; this does not emit dry-run results and does not create a generic hook result stream.

Supported scripts:

| Script | Dry-run behavior | Side effects suppressed |
|--------|------------------|-------------------------|
| `.cursor/hooks/before_submit_prompt.py` | Reports prompt-handling decisions, including optional validation outcomes | No prompt log write, no session-data write, and no runtime prompt-control output |
| `.cursor/hooks/session_start.py` | Reports environment status and the exit code it would request | No payload capture file write, no session-start log write, and no observability POST |
| `.cursor/hooks/session_end.py` | Reports shutdown handling, including stats/TTS toggles | No payload capture file write, no session-end log write, no stats write, and no TTS subprocess |
| `.cursor/hooks/post_tool_use_failure.py` | Reports failed-tool payload details it would log | No session log directory write |
| `.cursor/hooks/after_file_edit.py` | Reports formatter selection and commands for the edited file | No formatter subprocesses and no file-edit log write |
| `.cursor/hooks/pre_compact.py` | Reports compaction metadata and whether backup would run | No payload capture file write, no pre-compact log write, and no transcript backup |
| `.cursor/hooks/send_event.py` | Normalizes the hook payload and reports the event it would POST | No payload capture file write and no observability POST |
| `.cursor/hooks/pre_tool_use.py` | Reports whether the tool would be blocked | No debug log write and no blocking exit |
| `.cursor/hooks/post_tool_validate.py` | Reports whether validation would run, changed files, and detected project types | No MAO artifact writes and no lint/type-check subprocesses |
| `.cursor/hooks/subagent_start.py` | Reports parsed MAO/worktree context for the subagent start payload | No session log write and no nested `send_event.py` subprocess |
| `.cursor/hooks/stop_validator.py` | Reports missing artifact checks and the exit code it would request | No desktop notification and no stop-enforcement exit |

## Optional Post-Edit Lint Recipe

This repo already ships two complementary post-edit paths:

- `afterFileEdit` via [`after_file_edit.py`](../../.cursor/hooks/after_file_edit.py): quick file-local formatting/fixing after a successful edit.
- `postToolUse` via [`post_tool_validate.py`](../../.cursor/hooks/post_tool_validate.py): scoped lint/type-check after file-writing tools when safe (see `CURSOR_MAT_POST_TOOL_SCOPED_VALIDATE` above), plus MAO gate/readiness refresh for canonical handoff files.

Current built-in behavior:

- Python edits: `afterFileEdit` runs `ruff format` and then `ruff check --fix` on the edited file.
- JS/TS edits: `afterFileEdit` runs `prettier --write` on the edited file.
- Broader validation still belongs in `postToolUse`, not `afterFileEdit`.

Recommended recipe:

1. Keep `afterFileEdit` for fast file-local formatting and fixers.
2. Keep `postToolUse` for repo-wide or multi-file validation that should happen only after successful write tools.
3. Do not add the same heavy lint/type-check command to both hooks unless duplicate work is explicitly desired.

Practical rule of thumb:

- Good in `afterFileEdit`: formatters and fast file-scoped autofixes.
- Good in `postToolUse`: changed-file or package-scoped lint/type-check (with broader fallback), handoff-file evaluation, observability side effects.
- Avoid in both: the same full `ruff`, `tsc`, or equivalent expensive repo-wide pass.

Minimal adaptation example:

```json
{
  "afterFileEdit": [
    {
      "command": "python3 .cursor/hooks/after_file_edit.py",
      "failClosed": false
    }
  ],
  "postToolUse": [
    {
      "command": "python3 .cursor/hooks/post_tool_validate.py",
      "failClosed": false
    }
  ]
}
```

If you customize this split for another repo, prefer changing formatter lists in `after_file_edit.py` or write-tool detection in `post_tool_validate.py` instead of layering the same expensive command in both places.

## `.cursor/worktrees.json`

This repository currently uses `../.cursor/worktrees.json` as a project configuration file for named worktree roles, bootstrap references, and optional cloud-agent guidance metadata:

```json
{
  "worktrees": [
    {
      "name": "builder-agent",
      "branch_prefix": "agent/mat-builder",
      "bootstrap": ".cursor/hooks/bootstrap_worktree.sh",
      "env_copy": true
    }
  ],
  "optional_cloud_agent_templates": [
    {
      "name": "cloud-builder-agent",
      "intended_role": "builder"
    }
  ],
  "runtime_checks": {
    "health_script": "scripts/check-worktrees.sh",
    "doctor_script": "scripts/doctor.sh"
  }
}
```

Important note:

- This file documents workflow intent and bootstrap policy for this repo.
- Cursor's documented native worktree initialization keys are `setup-worktree-unix`, `setup-worktree-windows`, and `setup-worktree`.
- If you want first-class Cursor-managed worktree setup, extend or replace this file with the documented keys while preserving the role metadata you need.
- Entries under `optional_cloud_agent_templates` are documentation metadata only; they do not auto-provision cloud agents. Operators configure cloud via the Agents Window and `.cursor/environment.json` per [cursor.com/docs/cloud-agent](https://cursor.com/docs/cloud-agent) and [`decision-record.md`](decision-record.md#p1-audit--cloud-agents-agents-window).

Example native-style add-on:

```json
{
  "setup-worktree-unix": [
    "export ROOT_WORKTREE_PATH=\"${ROOT_WORKTREE_PATH:-$PWD}\"",
    "bash .cursor/hooks/bootstrap_worktree.sh --metadata-only \"${WORKTREE_LABEL:-$(basename \"$PWD\")}\""
  ]
}
```

Pass a stable **worktree label** as the first non-flag argument to `bootstrap_worktree.sh` (often the directory or branch name) so `runtime.env` port hints hash consistently.

**Bootstrap modes (E10):**

```bash
bash .cursor/hooks/bootstrap_worktree.sh --metadata-only "<label>"   # default: markers only
bash .cursor/hooks/bootstrap_worktree.sh --install --copy-env "<label>"
bash .cursor/hooks/bootstrap_worktree.sh --check "<label>"
```

See [`.cursor/worktrees.json.example`](../../.cursor/worktrees.json.example) for native `setup-worktree*` keys with metadata-only default and the Cursor **25** worktree cap note.

## `.cursor/mcp.json`

Operator security posture (local vs cloud, approval, prompt injection, provenance): [`docs/security/mcp.md`](../security/mcp.md). MCP is optional — MAT has no core dependency on it.

The current file is a placeholder plus notes. Add real MCP servers as needed:

```json
{
  "mcpServers": {
    "example-server": {
      "command": "npx",
      "args": ["-y", "@some/mcp-server"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

Guidance:

- Keep secrets in `.env`, not in committed JSON.
- Prefer `${ENV_VAR}` substitution.
- Future **Cursor To-dos + hooks** orchestration does not require extra MCP entries by default; see [`docs/reference/decision-record.md`](decision-record.md).

## Optional Context Hub (`chub`)

[`chub`](https://github.com/andrewyng/context-hub) is an optional CLI for fetching curated, versioned docs and skills for agents. In this repo, treat it as a **CLI-first helper**, not a built-in dependency.

Quick install:

```bash
npm install -g @aisuite/chub
```

Core agent loop:

```bash
chub search openai
chub get openai/chat-api --lang py
chub annotate openai/chat-api "Project note or gotcha"
```

Useful facts for operators:

- `chub search` finds docs or skills by query or exact ID.
- `chub get` fetches the entry content, with `--lang`, `--file`, `--full`, and `-o/--output` for language selection, incremental fetch, or saving to disk.
- `chub annotate` stores local notes that appear on future `chub get` calls.
- Local annotations live under `~/.chub/annotations/`.
- Main config lives at `~/.chub/config.yaml`.

Telemetry caveat:

- Upstream docs currently describe anonymous telemetry as enabled by config unless you opt out.
- Set `telemetry: false` in `~/.chub/config.yaml` if that better fits your environment.

Example config shape:

```yaml
sources:
  - name: community
    url: https://cdn.aichub.org/v1
source: "official,maintainer,community"
refresh_interval: 21600
telemetry: false
```

How it fits this repo:

- Use `chub` when an agent needs current external docs without pasting large reference blocks into prompts.
- If you want repo-local markdown copies of fetched references, use [`../.cursor/agents/docs-scraper.md`](../../.cursor/agents/docs-scraper.md) to save web docs into `ai_docs/` (planning convention: [`planning-commands-guide.md`](../guides/planning-commands-guide.md#planning-doc-inputs-docs--ai_docs)).
- This repo does **not** currently ship a vetted Context Hub MCP server entry in [`.cursor/mcp.json`](../../.cursor/mcp.json). Keep that file optional unless you adopt and validate a real bridge or wrapper yourself.

## Timeouts, Retries, And Observability Tuning

For payload preview truncation, sensitive SQLite exhaust, and shared-environment auth expectations, see [Payload preview and secret-handling notes](../architecture/events-and-visualization.md#payload-preview-and-secret-handling-notes) and [Observability data handling](MAINTAINER.md#observability-data-handling). For retention, growth surfaces, and manual cleanup guidance (advisory only — no shipped auto-purge), see [Observability data retention and sampling policy](../architecture/observability-retention-policy.md).

| Setting | Where | Effect |
|---------|-------|--------|
| `OBSERVABILITY_DB_PATH` | Bun server env ([`hook-db.ts`](../../apps/server/src/hook-db.ts)) | SQLite file for `hook_events` (default `events.sqlite` in server CWD); grows until operator rotates or deletes; see retention policy |
| `loop_limit` | `.cursor/hooks.json` | Limits automatic re-entry on hook-driven retries |
| Builder retry count | `.cursor/agents/parent-orchestrator.md` | Stops endless implementation loops |
| Verifier retry count | `.cursor/agents/parent-orchestrator.md` | Limits re-validation loops |
| HTTP timeout | `.cursor/hooks/send_event.py` | Prevents observability POSTs from hanging the agent |
| HITL timeout | `.cursor/hooks/utils/hitl.py` | Controls how long a human-response request waits |
| TTS timeout | `.cursor/hooks/session_end.py`, `.cursor/hooks/stop_validator.py` | Keeps notifications from blocking shutdown |

## Validation Steps

1. Open Cursor and confirm there is no `Invalid hooks.json` error.
2. Submit a simple prompt and verify a new `logs/<session_id>/user_prompts.json` file appears.
3. Trigger a file edit and confirm `afterFileEdit` behavior.
4. Trigger a failed tool use and confirm `post_tool_use_failure.json` is written.
5. If the observability server is enabled, confirm `send_event.py` can POST successfully.
6. Run `bash scripts/check-worktrees.sh --strict` for local worktree collision/health checks.
7. Run `bash scripts/doctor.sh` for an operator-level readiness report (or `--full` for full verification).

## Practical Example

Temporarily enable prompt logging and macOS notifications:

```bash
export CURSOR_STORE_PROMPTS=true
export CURSOR_DESKTOP_NOTIFICATIONS=true
```

Then run a small agent task in Cursor and inspect:

```bash
ls logs
```

## Acceptance Checklist

- [ ] `.env.sample`, `.cursor/hooks.json`, `.cursor/worktrees.json`, and `.cursor/mcp.json` are all covered here.
- [ ] Retry and timeout controls are identified by file.
- [ ] The distinction between workflow-specific worktree config and native Cursor worktree config is clear.
- [ ] A reviewer can follow the validation steps without contradictory instructions.
