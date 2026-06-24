# Adoption observability appendix

- Purpose: Operator-facing **opt-in** guidance for external product repos that adopt MAT and may enable the Bun/Vue observability stack.
- Audience: Teams bootstrapping or refreshing MAT in a product repository (not MAT source maintainers only).
- Status: complete
- Last updated: 2026-06-23
- Author: Cursor agent (builder slice — adoption observability appendix)

## Purpose and advisory posture

This appendix is **advisory only**. It describes honest operator practices for optional observability in adopted repos. It is **not** billing telemetry, **not** an enforced retention contract, and **not** a substitute for canonical file handoffs (`docs/current-plan.md`, `build-result.md`, `verify-result.md`, MAO artifacts under `artifacts/mao/`).

MAT observability in MVP has **no shipped automatic TTL, purge job, or hook redaction**. Disk growth and cleanup are **operator-owned** unless you add external tooling. Do not inherit upstream auto-purge or aggressive redaction defaults in product repos.

## When to enable

Observability is **opt-in**. Safe adoption posture:

- **Defer** the observability apps until the basic agent flow works (slash commands, hooks, plan/build/verify handoffs).
- **Default** to **localhost** and a **single operator** when you first turn the stack on.
- Enable only when you want dashboard visibility or cross-session debugging — not as proof of workflow authority.

See also [`adoption-safe-defaults.md`](adoption-safe-defaults.md) for conservative first-run habits.

## Enablement

When you choose to run the stack in an **adopted** repo:

1. Ensure `apps/server` and `apps/client` were copied from your MAT source (bootstrap does not always copy full app trees — confirm manifests exist before `bun install`).
2. Set `OBSERVABILITY_SERVER_URL` in `.env` (see `.env.sample`).
3. Start the stack:

   ```bash
   /mat-start
   ```

   Or from the repo root:

   ```bash
   bash scripts/start-system.sh
   ```

4. Open the dashboard URL printed by the start script (ports may differ when defaults are in use).

Hooks POST events via `.cursor/hooks/send_event.py` when the server is reachable. Missing or stopped server behavior is fail-open for workflow continuity — handoff files remain canonical.

## Non-local and shared environments

When observability runs beyond **localhost** (team dashboard, LAN/VPN, CI posting to a central server):

- Set **`OBSERVABILITY_API_TOKEN`** on the server and matching client env (`VITE_OBSERVABILITY_API_TOKEN` for the Vue dashboard WebSocket when required).
- Store tokens in secrets managers or CI secrets — **never commit** them.
- **Narrow POST scope** — only trusted runners and operators should POST; review what hook payloads may contain before broad enablement.

Retention and pruning remain **manual** even when auth is enabled. See [`MAINTAINER.md`](MAINTAINER.md#observability-data-handling) for maintainer depth.

## What gets stored

### SQLite `events.sqlite`

The Bun server persists normalized hook events in SQLite:

- **Primary table:** `hook_events` — full JSON in `payload` plus metadata columns.
- **Database path:** `OBSERVABILITY_DB_PATH` environment variable, default filename **`events.sqlite`** relative to the **server process working directory** (often `apps/server/` when started from that directory, or repo root when using `scripts/start-system.sh` — confirm your launch path before deleting files).

### WebSocket preview vs full SQLite rows

Live dashboard streams use compact wire shapes with **truncated** `payload_preview` for most events (default **800** bytes; larger cap for some MAO advisory event types). **SQLite stores full payloads** unless you prune or delete rows yourself.

**Honesty boundary:** dashboard previews are not complete records of stored rows. Export or query SQLite when you need the full payload.

For maintainer-level detail, see [`observability-retention-policy.md`](observability-retention-policy.md).

## Gitignore expectations

Keep local observability exhaust **out of git**. Typical gitignored surfaces in MAT-adopted repos:

| Path / pattern | Role |
| --- | --- |
| `events.sqlite` (and `apps/server/events.sqlite` when created there) | Primary observability SQLite store |
| `artifacts/phase1/` | Hook capture, verify logs, smoke SQLite copies |
| `artifacts/mao/` | MAO gate, transition events, todo observations |
| `artifacts/mat-runtime/` | MAT runtime messaging SQLite |
| Hook capture trees | Under `CURSOR_HOOK_CAPTURE_DIR` when set |

Bootstrap installs stack-appropriate `.cursorignore` templates; merge product-specific ignores rather than committing runtime databases or raw captures.

## Manual rotate and prune

**No automatic purge** runs in the shipped server. Operators rotate and prune explicitly:

1. **Export before delete** — copy `events.sqlite` or run read-only SQL exports when you need an audit trail.
2. **Stop the server** before deleting or replacing the SQLite file to avoid partial writes.
3. **Rotate `events.sqlite`** — rename or move the file, then restart so a fresh database is created at `OBSERVABILITY_DB_PATH` (or the default path).
4. **Clean phase-1 capture** — periodically review `artifacts/phase1/` (including `raw_payloads*` trees when present) and remove stale captures on a schedule you define.

Use **repo-relative paths** in runbooks (for example `apps/server/events.sqlite`, `artifacts/phase1/`).

## Hook capture directories

Optional hook payload capture is controlled by **`CURSOR_HOOK_CAPTURE_DIR`** and related `CURSOR_HOOK_CAPTURE*` flags (see [`configuration.md`](configuration.md)):

- **Repo-relative paths** resolve from the repository root.
- **Leading `/` paths** are filesystem-absolute on the machine running hooks.

Capture trees can grow quickly and may contain sensitive `tool_output`. Keep them **gitignored** and prune on an operator-defined schedule. Capture is **off** in safe-defaults posture until you are deliberately collecting evidence.

## RFU-7 deferral (no upstream auto-TTL or hook redaction)

Server-side retention TTL and hook redaction before POST in `send_event.py` are **deferred** (audit **RFU-7**). Adopted repos should document **opt-in** observability and **manual cleanup** — not inherit always-on TTL or aggressive redaction from upstream by default.

Decision record: [`decision-record.md#phase-c-rfu-7--observability-retention-and-hook-redaction-deferred`](decision-record.md#phase-c-rfu-7--observability-retention-and-hook-redaction-deferred).

## Related policy (maintainer depth)

For growth drivers, sampling honesty, recommended operator practices, and non-goals in the MAT source repo, see [`observability-retention-policy.md`](observability-retention-policy.md).

## Product README checklist

Copy or adapt this block into your product repo README when observability is optional but documented:

```markdown
## MAT observability (optional)

- **Opt-in:** defer until basic `/mat-plan-team` or `/mat-sprint` flow works.
- **Start:** `bash scripts/start-system.sh` or `/mat-start` when `apps/server` and `apps/client` are installed.
- **Storage:** local `events.sqlite` (path depends on launch cwd; see `.mat/docs/adoption-observability-appendix.md`).
- **Gitignore:** `events.sqlite`, `artifacts/phase1/`, `artifacts/mao/`, `artifacts/mat-runtime/`, hook capture dirs.
- **Rotation:** manual only — stop server, backup/export, delete or rename DB, restart. No shipped auto-purge.
- **Shared use:** set `OBSERVABILITY_API_TOKEN`; never commit tokens.
- **Authority:** file handoffs (`build-result.md`, `verify-result.md`) — not dashboard rows alone.
- **Depth:** `.mat/docs/adoption-observability-appendix.md` and `.mat/docs/observability-retention-policy.md` when packaged.
```

## Bootstrap and update packaging

On bootstrap or `update-mat.py` apply, this appendix is copied to **`.mat/docs/adoption-observability-appendix.md`** via [`scripts/adoption/adoption-layout-v1.json`](../scripts/adoption/adoption-layout-v1.json). Product repos with minimal root `docs/` should link from README or operator runbooks to the `.mat/docs/` copy after refresh.

## Related evidence

- [Adoption observability pilot report (2026-06-23)](../artifacts/report/adoption-observability-pilot-2026-06-23.md) — disposable bootstrap + `update-mat.py` dry-run evidence for appendix packaging and `AGENTS.md` preservation.

## Related docs

- [`getting-started-new-projects.md`](getting-started-new-projects.md)
- [`getting-started-existing-projects.md`](getting-started-existing-projects.md)
- [`adoption-safe-defaults.md`](adoption-safe-defaults.md)
- [`configuration.md`](configuration.md)
- [`events-and-visualization.md`](events-and-visualization.md)
- [`update-mat/index.md`](update-mat/index.md)
