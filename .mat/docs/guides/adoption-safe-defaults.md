# Adoption safe defaults (internal)

- Purpose: One-page **safe-defaults profile** for teams bringing this workflow into a project for the first time.
- Audience: Internal operators and integrators.
- Status: complete
- Last updated: 2026-06-25
- Author: Cursor agent

## 1. Purpose

**What it is:** A conservative baseline—commands, environment posture, and habits—that keeps first adoption predictable and avoids leaning on optional or advisory automation before the team understands it.

**When to use it:** First integration into a repo, a new pilot group, or any situation where consistency matters more than squeezing out advanced features.

**Why it exists:** The workflow ships many **opt-in** hooks, MAO advisory files, and observability paths. Turning them all on at once creates noise, false confidence, and merge risk. Safe defaults keep **file handoffs and explicit operator decisions** in charge until you deliberately escalate.

This repository remains **internal/reference-oriented**; this profile is not a product SLA or a guarantee about Cursor runtime behavior.

## 2. Minimum recommended setup

**Commands:** Prefer **`/mat-sprint`** for the first real change unless you already know you need a full delegated cycle or a multi-slice mission (see §3).

**Environment:** Start from **`.env.sample` → `.env`** (product API keys) and **`.mat.env.sample` → `.mat.env`** (MAT workflow). Treat both as the baseline:

- Keep **`CURSOR_STORE_PROMPTS`**, **`CURSOR_NAME_AGENT`**, and **`CURSOR_VALIDATE_PROMPTS`** **off** in **`.mat.env`** until you explicitly want more logging or prompt enforcement.
- Leave **lifecycle hook capture** (`CURSOR_HOOK_CAPTURE*`) **disabled** in **`.mat.env`** unless you are debugging hooks or collecting evidence for a deliberate audit.
- Leave **MAO optional automation** disabled in **`.mat.env`**: do **not** enable `CURSOR_MAO_HOOK_AUTO_TRANSITION_CAPTURE`, `CURSOR_MAO_VERIFIER_AUTOSTART`, or observability emit flags until you have read [`configuration.md`](../configuration.md) and accept the advisory-only behavior.

**Over-automation:** Do not treat gate files, downstream-readiness snapshots, or dashboard events as **authority** for spawning subagents or skipping parent checks. The parent still owns transitions and dispatch; see [`todo-orchestration.md`](../todo-orchestration-protocol.md).

**Evidence and posture:** Treat **hook evidence, observability DB rows, and advisory JSON** as **hints**. Decisions about “go / no-go / partial ship” stay **operator-owned** (aligned with [`MAINTAINER.md`](../MAINTAINER.md) and [`docs/reference/decision-record.md`](../decision-record.md)).

**Artifact hygiene:** Keep `artifacts/`, `logs/`, and raw capture trees **out of git** unless a policy explicitly requires committed proof. Never commit `.env` or API keys. If you use MAO or phase-1 capture artifacts locally, assume **gitignored** unless your team has a documented exception.

**AGENTS hygiene:** Keep product-owned `AGENTS.md` files intact. The safe default is a small pointer note that references `.mat/AGENTS.mat.md` relative to each file; use the inline fallback only when you intentionally need the delimited MAT block. Run the adoption helper in `--dry-run` mode first if you want to inspect the proposed changes before any backup or write happens.

## 3. Command choice guide

| Situation | Prefer |
| --------- | ------ |
| **One** bounded slice: DoR → implement → verify → short review in this session | **`/mat-sprint`** |
| **One** full **plan → build → verify** cycle with delegated builder and verifier | **`/mat-plan-team`** |
| **Several** ordered slices, **mission state** in [`long-run-state.md`](../long-run-state.md), post-slice **mission gate** | **`/mat-long-run`** |

Rule of thumb: if you are unsure, start with **`/mat-sprint`**. If the work clearly needs separate implementation and verification passes, use **`/mat-plan-team`**. Reserve **`/mat-long-run`** for missions that are honestly multi-slice—not a single cycle dressed up as a “long” task.

## 4. First-run checklist

- [ ] **Validate environment:** `cp .env.sample .env` and `cp .mat.env.sample .mat.env`, fill only what you need; run **`/mat-doctor`** or `bash scripts/doctor.sh` where available.
- [ ] **Branch hygiene:** work on a **feature branch**; know what you will merge and how CI runs.
- [ ] **Pick session type:** choose **`/mat-sprint`**, **`/mat-plan-team`**, or **`/mat-long-run`** using §3—do not default to the heaviest option.
- [ ] **Capture / artifacts:** confirm **`git status`** will not pick up `artifacts/`, `logs/`, or `.env`; if using hook capture, use a **gitignored** directory and never commit raw payloads by accident.
- [ ] **Baseline verification:** run `bash scripts/phase1-verify.sh` (or your project’s agreed test/lint entrypoint) so you know the repo was healthy before workflow changes.

## 5. Known conservative defaults

These reduce risk for initial adoption (see `.env.sample`, `.mat.env.sample`, and [`configuration.md`](../configuration.md)):

- Prompt storage, LLM agent naming, and prompt validation **off** by default in the sample.
- Desktop notifications **off** unless you turn them on.
- Hook payload capture **off** unless explicitly enabled.
- MAO advisory files and optional observability POSTs are **opt-in**; the canonical workflow still uses **`docs/current-plan.md`**, **`build-result.md`**, and **`verify-result.md`**.

## 6. Escalation guidance

Move beyond safe defaults when the team can **name** what they are turning on and why:

- **Delegated builder + verifier** for a slice: use **`/mat-plan-team`** when inline work is no longer the honest fit.
- **Multi-slice missions:** adopt **`/mat-long-run`** and maintain [`long-run-state.md`](../long-run-state.md) with explicit execution mode and mission gate discipline.
- **AGENTS sidecar refresh:** run `python3 scripts/adoption/manage-agents-sidecars.py --repo-root .` to update root and nested pointers; add `--inline-fallback` only when the explicit inline block is required.
- **MAT refreshes:** use `python3 scripts/adoption/update-mat.py --source <upstream-repo-or-url> --ref <ref>` first in **dry-run** mode (the default), then apply only after you inspect the patch preview, the `scripts/adoption/mat-footprint-v1.json` compatibility snapshot, and the staged worktree path. Apply requires explicit **`--apply --approved --plan-file <plan.json>`** flags — the updater stops before commit or PR creation. Product-owned `AGENTS.md` prose is not silently overwritten; use the sidecar helper when pointer blocks need refresh. Operator checklist: [`validation-report.md`](../../validation-report.md) slice 3; defaults: [`getting-started-existing-projects.md`](getting-started-existing-projects.md). The supporting bundle lives in [`docs/update-mat/`](../update-mat/index.md). **First adoption:** bootstrap before dry-run — pristine dry-run fails without `.mat/AGENTS.mat.md`. WordPress **plugin-only** repos without `wp-config.php` at root may get the `cursorignore-mat-default` template; merge `.mat/docs/templates/cursorignore-mat-wordpress` manually when strict CI hygiene is ready ([rank-math pilot](../../artifacts/report/adoption-rank-math-api-manager-pilot-2026-06-24.md)).
- **MAO gate + transition capture:** enable only after **`CURSOR_MAO_GATE`** and parent-owned checks are understood; treat `capture_transition_decision` and `suggested-todo-mutation.json` as **helpers**, not autonomous control.
- **Observability + emit flags:** add when you want dashboard visibility or cross-session evidence—not as a substitute for reading handoff files. Adopted repos: see [`adoption-observability-appendix.md`](../archive/adoption-observability-appendix.md) for opt-in posture, manual SQLite rotation, gitignored growth surfaces, and RFU-7 deferral (no upstream auto-purge).
- **Parallel worktrees / parallel subagents:** add when isolation or fan-out is justified; avoid parallel runs that duplicate the same implementation work.

If something feels “magic,” assume it is **advisory** until you have read the linked protocol and maintainer notes.

## Related docs

- [`quick-start.md`](quick-start.md)
- [`getting-started-new-projects.md`](getting-started-new-projects.md)
- [`getting-started-existing-projects.md`](getting-started-existing-projects.md)
- [`best-practices.md`](best-practices.md)
- [`configuration.md`](../configuration.md)
