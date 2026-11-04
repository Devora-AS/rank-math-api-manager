# Agents Window operator runbook

- Purpose: Map MAT slices to Cursor Agents Window surfaces (local, worktree, cloud, SSH, multi-workspace) without treating window state as acceptance truth.
- Audience: Operators running `/mat-plan-team`, `/mat-long-run`, `/mat-subagents-spawn`, and `/mat-wt-*`.
- Status: complete
- Last updated: 2026-08-24
- Official reference: [Agents Window](https://cursor.com/docs/agent/agents-window) · [Cloud Agents](https://cursor.com/docs/cloud-agent)

## Authority boundary

| Layer | Role |
|-------|------|
| Canonical | `docs/current-plan.md`, `build-result.md`, `verify-result.md`, `docs/architecture/long-run-state.md` |
| Operator UI | Agents Window tabs, diffs, worktree pickers, cloud/SSH sessions |
| Advisory | Hook events, MAO todos, dashboard panels |

Never mark a slice or mission complete from Agents Window alone. File handoffs stay authoritative ([decision record — Cloud / Agents Window](../decision-record.md#p1-audit--cloud-agents-agents-window)).

## When to use which surface

| MAT need | Prefer | Isolation | Notes |
|----------|--------|-----------|-------|
| Fast interactive Q&A or solo plan | Local Agent / Plan / Ask | Current workspace | `/mat-question`, `/mat-plan*` |
| One writer, one slice | Local Agent | Current workspace | `/mat-sprint`, `/mat-build` |
| Concurrent writers on one repo | Worktree tab + `/mat-wt-create` | Separate git worktree | One active slice per worktree/branch |
| Durable async / heavy compute | Cloud agent | Cloud VM + `.cursor/environment.json` | MAT does **not** auto-provision cloud |
| Environment-bound tooling | SSH remote | Remote host | Keep secrets on the remote; handoffs still in-repo |
| Multi-repo review | Multi-workspace | Explicit repo scopes | No atomic multi-repo mission claim yet |

## Slice → tab checklist

1. Confirm **active slice** in `docs/current-plan.md` (and mission row in `long-run-state.md` when long-running).
2. Choose surface from the table above; open or attach an Agents Window tab for that tree.
3. Run the MAT command (`/mat-plan-team`, `/mat-long-run`, `/mat-subagents-spawn`, …).
4. For parallel streams, isolate with [`/mat-wt-create`](../../.cursor/commands/mat-wt-create.md) / [`/mat-wt-check`](../../.cursor/commands/mat-wt-check.md) before spawning writers.
5. Closeout only after `build-result.md` / `verify-result.md` (and mission gate when applicable) pass — not when the tab shows “done.”

## Local → cloud handoff

1. Ensure plan and acceptance criteria are on disk and committed or otherwise recoverable.
2. Configure `.cursor/environment.json` (install/start) per [Cloud Agents setup](https://cursor.com/docs/cloud-agent/setup). For a single-repo cloud **slice** (branch-per-slice, parent verify, name-only preflight), follow [`cloud-agent-long-run.md`](cloud-agent-long-run.md) and the normative [`specs/cloud-agent-long-run-v1.md`](../../specs/cloud-agent-long-run-v1.md).
3. Start cloud from Agents Window; confirm hooks/commands are available in the cloud checkout.
4. Resume parent gates on returned branch/diff; do not treat cloud “success” as verify PASS.

## Diff / branch closeout

- Review Agents Window diffs as **evidence**, then confirm against `build-result.md` changed paths.
- Prefer one branch (or worktree) per active slice; avoid merging until verify PASS.
- Clean up worktrees with [`/mat-wt-remove`](../../.cursor/commands/mat-wt-remove.md) after merge or abandon.

## Related commands

- [`mat-subagents-spawn`](../../.cursor/commands/mat-subagents-spawn.md) — parallel Task fan-out
- [`mat-long-run`](../../.cursor/commands/mat-long-run.md) — queued multi-slice missions
- [`mat-wt-create`](../../.cursor/commands/mat-wt-create.md) · [`mat-wt-list`](../../.cursor/commands/mat-wt-list.md) · [`mat-wt-check`](../../.cursor/commands/mat-wt-check.md) · [`mat-wt-remove`](../../.cursor/commands/mat-wt-remove.md)
- Agent roster: [`mat-agents.yaml`](../../mat-agents.yaml) · [`specs/agent-roster-v1.md`](../../specs/agent-roster-v1.md)
