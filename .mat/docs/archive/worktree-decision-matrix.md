# Worktree Decision Matrix: Local Worktrees vs Cloud Agents

**Stage:** 5 — Parallel Runtime & Worktrees
**Related Todo:** `design-parallel-runtime`
**Generated:** 2026-03-23
**Last reviewed:** 2026-04-20 (Cursor 3 / bootstrap contract alignment)

---

## Overview

Two practical isolation strategies for parallel work are:

1. **Local Git Worktrees** — You create separate working trees (`git worktree` or Cursor’s explicit `/worktree` / related flows). Each tree has its own branch and files on your machine. **Cursor 3 removed automatic editor-managed worktrees**; nothing here implies the product creates a new git worktree for every parallel agent without an explicit operator step (see `artifacts/fetched/cursor-docs.md` in this repo).
2. **Cursor Cloud Agents** — Agents run in isolated AWS VMs with separate filesystem and networking.

This matrix documents when to use each strategy.

---

## Decision Matrix

| Dimension | Local Worktrees | Cloud Agents |
|-----------|----------------|--------------|
| **Isolation** | Git branch isolation (files) | Full VM isolation (filesystem + process + network) |
| **LSP / Editor feedback** | Limited — official docs note worktrees may lack LSP | Not applicable (headless) |
| **Dependency install** | Via bootstrap script (`bootstrap_worktree.sh`) | Fresh VM with config from AGENTS.md / MCP |
| **File conflicts** | Prevented by separate branches | Not possible (separate VM) |
| **Cost** | Free (local compute) | Cloud compute cost (Cursor plan dependent) |
| **Setup complexity** | Medium — explicit `git worktree` (or `/worktree`) plus `.cursor/worktrees.json` bootstrap | Medium — requires Cloud Agent config |
| **Network access** | Host machine network | Isolated VM network (configurable) |
| **Environment parity** | High (same OS, tools, packages) | Medium (VM may differ from host) |
| **Concurrency** | Up to 8 parallel agents (documented Cursor limit) | Up to 8 parallel agents |
| **Long-running tasks** | Host machine must stay on | Can run without local machine |
| **Computer use** | Not available | Available (screenshot, click, etc.) |
| **MCP support** | Via .cursor/mcp.json | Via .cursor/mcp.json |
| **Best for** | Coding tasks, file operations, testing | Browser automation, long-running, resource-intensive |

---

## Recommendation

### Use Local Worktrees when:

- Running builder/verifier agent pairs on code tasks
- Tasks complete in minutes to an hour
- Environment parity with the host is important
- You want zero cloud cost for routine development
- The task is file-focused (read/write/test code)

### Use Cloud Agents when:

- Tasks require browser automation (computer use)
- Tasks run for hours and you cannot leave your machine on
- You need full process isolation (e.g., running untrusted code)
- You want to parallelize across more than local machine resources

### Phase 1 Default: Local Worktrees

For Phase 1, use local worktrees as the default. Cloud Agents are documented here as an available option but are not required for the pilot.

---

## Local Worktree Configuration

Worktrees are configured in `.cursor/worktrees.json`:

```json
{
  "worktrees": [
    {
      "name": "builder-agent",
      "branch_prefix": "agent/mat-builder",
      "bootstrap": ".cursor/hooks/bootstrap_worktree.sh"
    },
    {
      "name": "verifier-agent",
      "branch_prefix": "agent/verifier",
      "bootstrap": ".cursor/hooks/bootstrap_worktree.sh"
    }
  ]
}
```

**Operator flow:** Create the worktree explicitly, open it in Cursor (or run setup with `ROOT_WORKTREE_PATH` per your `worktrees.json` keys). When bootstrap runs, it copies `.env` when missing, installs dependencies, writes **`.cursor/worktree/runtime.env`** with `OBSERVABILITY_PORT` and `OBSERVABILITY_CLIENT_PORT` (collision-aware seeds from `3001` / `5173` and `cksum(worktree_name) mod 200`), and writes markers under `.cursor/worktree/`.

---

## Bootstrap Process

The bootstrap script (`.cursor/hooks/bootstrap_worktree.sh`) runs in a worktree directory and:

1. Copies `.env` from the project root when missing
2. Writes `.cursor/worktree/runtime.env` with observability port hints (when free ports can be chosen)
3. Installs dependencies (`uv`/`pip` at repo root; `bun`/`npm` in repo root if `package.json` exists, plus `apps/server` and `apps/client` when present)
4. Validates required environment variables (project-specific list; may be empty)
5. Emits a SessionStart event to the observability pipeline (best-effort)
6. Writes worktree marker files (`.cursor/worktree/name`, `bootstrapped_at`, `project_dir`)

---

## LSP Constraint

**Important:** Official Cursor documentation notes that worktrees may not have full LSP support (no integrated linting/type feedback in the editor within worktree agents).

**Mitigation in this architecture:**

- The `post_tool_validate.py` hook runs linting and type-checking explicitly after every file-writing tool call, using CLI tools (ruff, ty, tsc).
- This provides equivalent validation feedback without relying on LSP.
- Do not assume editor-integrated lint indicators will work inside worktree agents.

**Verification step:** Confirm LSP behavior experimentally in Stage 6 (pilot) by running a real parallel agent session and observing whether lint errors surface in the Cursor editor pane.

---

## Manual Parallel Run Checklist

Use this checklist to manually validate parallel worktree isolation (Stage 5 acceptance):

```
[ ] Two separate worktree directories created (check: git worktree list)
[ ] Each worktree has its own .env (not shared) when bootstrap copied from root
[ ] Each worktree bootstrapped independently (check .cursor/worktree/name in each)
[ ] Builder and verifier agents ran in separate worktrees without file conflicts
[ ] Observability server received events from both worktrees (different session IDs)
[ ] build-result.md and verify-result.md were created in the correct worktrees
[ ] Merging worktree branches to main produced no unexpected conflicts
```

---

## Cloud Agent Setup Reference

Cursor 3 routes cloud setup through the **Agents Window** and repo-local environment config — not editor Settings as the sole path.

To configure cloud agents:

1. Open the **Agents Window** in Cursor (agent-first surface for local, cloud, SSH, and multi-workspace).
2. Choose **cloud** and complete **web onboarding**, or add [`.cursor/environment.json`](../../.cursor/environment.json) with `install` / `start` commands (repo file takes precedence over personal/team defaults per Cursor docs).
3. Ensure `.cursor/mcp.json` and root `AGENTS.md` are committed — cloud agents read them like local agents.
4. MAT does **not** auto-provision cloud VMs; this matrix documents operator choice only.

Official references:

- [cursor.com/docs/cloud-agent](https://cursor.com/docs/cloud-agent)
- [cursor.com/docs/agent/agents-window](https://cursor.com/docs/agent/agents-window)
- MAT decision: [`docs/decision-record.md`](../decision-record.md#p1-audit--cloud-agents-agents-window)
