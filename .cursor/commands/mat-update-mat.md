# MAT Update MAT

Guided orchestrator for refreshing MAT-owned assets in an **adopted** repository. Dry-run first; the updater stays sample-first and auditable. This command does **not** add a new merge engine — it routes operators through existing `bootstrap-workflow-into-repo.sh`, `update-mat.py`, and **`/mat-sync`** with one exact next command at each decision point.

**Production default:** adopted repos with **`.mat/source-config.json` v2** should use **`/mat-sync`** / [`mat-sync-team-runbook.md`](../../.mat/docs/guides/mat-sync-team-runbook.md) (GitHub materialize). **Local `--source` / `$MAT_SOURCE` paths are maintainer dev only** — not the team default.

## Usage

```text
/mat-update-mat
```

Optional context (paste in the same message when helpful):

```text
/mat-update-mat refresh from upstream main in /absolute/path/to/adopted-repo
```

When you draft operator prompts or copied snippets for this command, default to copy-pasteable fenced `txt` blocks unless the user asks for another format.

## Related docs

- [`docs/guides/mat-sync-team-runbook.md`](../../.mat/docs/guides/mat-sync-team-runbook.md) — GitHub-first team runbook for `/mat-sync`
- [`docs/guides/getting-started-existing-projects.md`](../../.mat/docs/getting-started-existing-projects.md) — first adoption vs refresh
- [`docs/update-mat/index.md`](../../.mat/docs/update-mat/index.md) — updater foundation bundle
- [`docs/update-mat/architecture-and-rollout.md`](../../.mat/docs/update-mat/architecture-and-rollout.md) — design and rollout
- [`validation-report.md`](../../validation-report.md) — slice 3 operator checklist
- [`docs/guides/adoption-safe-defaults.md`](../../.mat/docs/guides/adoption-safe-defaults.md) — conservative profile

---

## Safety invariants (always)

- **Dry-run first** — never apply without a reviewed plan JSON.
- **Preserve product `AGENTS.md`** — sidecar helper adds pointers; inline fallback is explicit only.
- **No auto-commit / no auto-PR** — staging stops before commit; operator owns merge and PR.
- **Custom agents preserved** — product-owned `.cursor/agents/` entries are not silently overwritten; true drift fails closed until resolved.
- **Fail-closed on true drift** — conflicts, unmanaged customizations, or missing sidecar prerequisites stop the flow; do not `--apply` past unresolved drift.
- **Isolated staging** — apply uses worktree/branch-like paths; inspect before touching the target root.

---

## Orchestration instructions

You are the **update orchestrator**. Walk the operator through detect → route → plan → approve → verify. After each phase, print **exactly one** recommended next command in a fenced `txt` block. Do not list multiple equally-weighted options — pick the honest branch and one command.

### Step 1 — Detect

Establish **where** MAT lives and **what** the target repo already has.

Check:

| Signal | Meaning |
|--------|---------|
| `.mat/README.md` present | Adopted sidecar layout likely installed |
| `.mat/AGENTS.mat.md` present | Sidecar encyclopedia exists — prerequisite for incremental `update-mat.py` |
| `.cursor/agents/` | Note product custom agents (names not in upstream MAT bundle) — affects conflict risk |
| `MULTI_AGENT_WORKFLOW_ROOT` or sibling checkout | MAT **source** repo path for `--source` / bootstrap |
| Target repo root | Adopted product repo (may equal workspace or a path the operator names) |

Resolve MAT source path (first match wins):

1. Operator-provided absolute path in the message.
2. `MULTI_AGENT_WORKFLOW_ROOT` when set and valid.
3. Sibling heuristic: `../multi-agent-workflow` or `../multi-agent-teams` next to the target when those directories contain `scripts/adoption/update-mat.py`.

Report detect summary in chat (sidecar yes/no, custom agent count if relevant, resolved MAT source).

**Branch — no sidecar yet (first existing-project adoption):**

Use **mat-sync plan → approve** from the MAT source repo (primary). Do not run pristine `update-mat.py` dry-run without sidecar.

```txt
cd "/path/to/multi-agent-teams"   # MAT source
bash scripts/mat-sync.sh --repo-root "<target>" --repository Devora-AS/multi-agent-workflow
# review mat-sync-plan-file=… then:
bash scripts/mat-sync.sh --repo-root "<target>" \
  --approve-plan "<target>/artifacts/mat-sync/latest-plan.json"
```

**`/mat-sync` is not available** inside an un-adopted product repo until first approve installs `.cursor/commands/`. See [`.cursor/commands/mat-adopt.md`](mat-adopt.md) for the installer stub.

**Maintainer/debug fallback** (not team default):

```txt
MULTI_AGENT_WORKFLOW_ROOT=<MAT-source> bash scripts/adoption/bootstrap-workflow-into-repo.sh --mode existing-project --non-interactive <target>
```

**Branch — sidecar present; continue to route:**

```txt
# Proceed to Step 2 — Route (no shell command yet; summarize detect findings first)
```

---

### Step 2 — Route

Choose **one** path. Stop and explain when prerequisites are missing.

```text
                    ┌─ No .mat/AGENTS.mat.md ──► First adoption via mat-sync (Step 1 branch)
                    │
Detect complete ─────┼─ Sidecar OK, incremental drift ──► update-mat.py dry-run (Step 3)
                    │
                    └─ Stale layout manifest, heavy unmanaged conflicts,
                       or operator chooses full refresh ──► Re-bootstrap (after dry-run summary)
```

| Route | When | Stop conditions |
|-------|------|-----------------|
| **First adoption (mat-sync)** | No `.mat/AGENTS.mat.md` | Run from MAT source with `--repo-root`; `/mat-sync` unavailable in product repo until approve |
| **Incremental refresh** | Sidecar exists; operator wants upstream drift preview | Unresolved conflicts in dry-run → stop before apply; plan JSON includes **`env_sample_merge_preview`** and **`.mat/docs/`** in `changed_files` when upstream differs |
| **Re-bootstrap** | Dry-run shows stale `adoption-layout-v1.json` footprint, many custom-agent conflicts, or operator explicitly wants manifest-driven full refresh | Preserves root `README.md`, `CHANGELOG.md`, `AGENTS.md` in `--mode existing-project` |

**Branch — first adoption (mat-sync, primary):**

```txt
cd "/path/to/multi-agent-teams"   # MAT source
bash scripts/mat-sync.sh --repo-root "<target>" --repository Devora-AS/multi-agent-workflow
bash scripts/mat-sync.sh --repo-root "<target>" \
  --approve-plan "<target>/artifacts/mat-sync/latest-plan.json"
```

**Branch — first adoption (maintainer/debug bootstrap):**

```txt
MULTI_AGENT_WORKFLOW_ROOT=<MAT-source> bash scripts/adoption/bootstrap-workflow-into-repo.sh --mode existing-project --non-interactive <target>
```

**Branch — incremental refresh (default when sidecar exists):**

```txt
python3 scripts/adoption/update-mat.py --source <MAT-source> --ref main --repo-root <target>
```

**Branch — re-bootstrap (operator choice after reviewing dry-run):**

```txt
MULTI_AGENT_WORKFLOW_ROOT=<MAT-source> bash scripts/adoption/bootstrap-workflow-into-repo.sh --mode existing-project --non-interactive <target>
```

**Branch — stop (missing MAT source or unresolved drift):**

```txt
# STOP — set MULTI_AGENT_WORKFLOW_ROOT or pass --source <absolute-path-to-MAT-source> and resolve dry-run conflicts before apply
```

---

### Step 3 — Plan (dry-run)

Always run **dry-run first** for the incremental path. Default `update-mat.py` invocation is dry-run (no `--apply`).

Operator must review stdout and saved artifacts:

| Field | What to check |
|-------|----------------|
| `plan-file=` | Saved JSON plan — required for `--apply --approved --plan-file` |
| `patch-file=` | Human-readable patch preview |
| `audit-file=` | Audit trail path under `artifacts/update-mat/` when written |
| `legacy_cleanup_preview` | Would-remove / would-quarantine / warn-only legacy command stubs |
| `cursorignore_merge_preview` | When `warn_first` preserved root `.cursorignore`: lines to append on approve (append-only MAT block) |
| `env_sample_merge_preview` | When `.mat.env.sample` is customized: MAT-tool block would change (`path`, `changed`); apply merges markers only — not live `.env` or `.mat.env` |
| `changed_files` | Relative paths that would update on apply — includes **`.mat/docs/`** mappings when upstream docs differ |
| Compatibility snapshot | `mat-footprint-v1.json` preserve paths — product files should not appear as silent overwrites |

Summarize: files to change, conflicts, legacy cleanup, **`.mat.env.sample` MAT-tool merge preview**, **`.mat/docs/`** drift, and whether apply is safe.

**Branch — dry-run clean; ready for human review:**

```txt
# REVIEW — open plan-file from dry-run output; do not apply until operator approves (Step 4)
```

**Branch — dry-run shows conflicts or missing sidecar:**

```txt
# STOP — resolve conflicts manually or choose re-bootstrap; see docs/guides/getting-started-existing-projects.md
```

**Branch — dry-run not yet run (incremental path):**

```txt
python3 scripts/adoption/update-mat.py --source <MAT-source> --ref main --repo-root <target>
```

---

### Step 4 — Approve

Explicit **human approval** required before any mutation.

Rules:

- Apply **only** with `--apply --approved --plan-file <path-from-dry-run>`.
- Operator must confirm they reviewed `plan-file`, `patch-file`, `legacy_cleanup_preview`, and **`env_sample_merge_preview`** when present.
- **`.mat.env.sample` apply** uses **`mat_env_sample_merge.py`** (MAT-tool markers only); does **not** touch live **`.env`** or **`.mat.env`**.
- Incremental apply refreshes **`.mat/docs/`** mappings listed in `changed_files` when upstream differs.
- Nested `AGENTS.md` ambiguity → run `python3 scripts/adoption/manage-agents-sidecars.py --repo-root <target>` before apply when needed.
- **No auto-commit** — inspect `staging-worktree=` output; confirm no new commit on target root.

**Branch — operator approved apply:**

```txt
python3 scripts/adoption/update-mat.py --source <MAT-source> --ref main --repo-root <target> --apply --approved --plan-file <plan.json>
```

**Branch — operator declined or needs more review:**

```txt
# STOP — no apply; re-run dry-run after resolving conflicts or editing target tree
```

**Branch — approval pending (waiting on human):**

```txt
# WAIT — operator must approve before: python3 scripts/adoption/update-mat.py ... --apply --approved --plan-file <plan.json>
```

---

### Step 5 — Verify

After bootstrap, apply staging, or re-bootstrap, verify the adopted tree.

1. Doctor (quick operator diagnostics):

```bash
bash scripts/doctor.sh
```

2. Phase 1 verify from **adopted repo root** (default **adopted_operational** profile when `.mat/README.md` exists — skips `.mat/tests` unless opted in):

```bash
bash scripts/phase1-verify.sh
```

Optional packaged contract tests in adopted repos:

```bash
PHASE1_VERIFY_ADOPTED_CONTRACT_TESTS=1 bash scripts/phase1-verify.sh
```

Report PASS/FAIL and first failing check if any.

**Post-flight — `.cursorignore` (warn_first adoptions):** When dry-run or **`/mat-sync`** plan JSON includes **`cursorignore_merge_preview`**, remind the operator to review missing MAT ignore fragments before approve. Prefer **`bash scripts/mat-sync.sh ... --approve-plan ...`** so the append-only marked merge runs after bootstrap/apply; manual merge from `.mat/docs/templates/*.mat-suggest` remains valid. Second approve is idempotent when the MAT marker block is already present.

**Branch — verify pass; mission slice complete:**

```txt
# DONE — manual commit/PR on target when ready; updater does not commit for you
```

**Branch — verify fail:**

```txt
bash scripts/doctor.sh
```

---

## End-of-pass rule

Every orchestration pass ends with **exactly one** fenced `txt` block containing the single honest next command (or a explicit `STOP` / `WAIT` / `DONE` line when no shell command is correct). Do not leave the operator with parallel equally-valid commands.

---

## Common operator paths (quick reference)

**First existing-project adoption (no sidecar yet) — mat-sync primary:**

```txt
cd "/path/to/multi-agent-teams"   # MAT source
bash scripts/mat-sync.sh --repo-root "<target>" --repository Devora-AS/multi-agent-workflow
bash scripts/mat-sync.sh --repo-root "<target>" \
  --approve-plan "<target>/artifacts/mat-sync/latest-plan.json"
```

**First adoption — maintainer/debug bootstrap (fallback only):**

```txt
MULTI_AGENT_WORKFLOW_ROOT=<MAT-source> bash scripts/adoption/bootstrap-workflow-into-repo.sh --mode existing-project --non-interactive <target>
```

**Incremental refresh (clean dry-run):**

```txt
python3 scripts/adoption/update-mat.py --source <MAT-source> --ref main --repo-root <target>
```

**Re-bootstrap when layout manifest stale or heavy custom-agent surface (operator choice after dry-run summary):**

```txt
MULTI_AGENT_WORKFLOW_ROOT=<MAT-source> bash scripts/adoption/bootstrap-workflow-into-repo.sh --mode existing-project --non-interactive <target>
```

---

## Non-goals (this command)

- No new merge engine — use **`/mat-sync`** / [`scripts/mat-sync.sh`](../../scripts/mat-sync.sh) for the shell state machine wrapper.
- No auto-commit, auto-PR, or silent `AGENTS.md` overwrite.
- Conflict-bucket routing (`product-extensions.json`, `routing_recommendation`) ships in [`update_mat_conflict_routing.py`](../../scripts/adoption/update_mat_conflict_routing.py); use **`/mat-sync`** or this command's dry-run for bucket summaries and rebootstrap vs stop routing.
