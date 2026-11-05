# Agent instructions (product-first)

This file is **yours**: document how agents should work in *this* repository — stack, conventions, review rules, and safety boundaries.

## Multi-agent workflow (MAT)

This repo uses the Cursor-native multi-agent workflow. The canonical MAT operator reference lives in **`.mat/AGENTS.mat.md`**.

<!-- MAT_WORKFLOW_POINTER -->
## Multi-agent workflow (MAT)

This file stays product-owned. The canonical MAT reference lives in `.mat/AGENTS.mat.md`.
Use the adoption helper's `--inline-fallback` flag only when you need the explicit inline MAT section here.
<!-- /MAT_WORKFLOW_POINTER -->
The **`.mat/docs/`** directory holds packaged workflow documentation copied from the MAT reference repository.

- Orchestration handoffs: `docs/current-plan.md`, `build-result.md`, `verify-result.md` at repo root.
- Long-running missions: `docs/long-run-state.md`.
- Slash commands and hooks: `.cursor/commands/`, `.cursor/hooks/`.
Keep product-specific guidance here; use `.mat/AGENTS.mat.md` for the complete MAT encyclopedia without duplicating it into this file.
<!-- MAT_REFERENCE_NOTE -->
See `.mat/AGENTS.mat.md` for MAT-specific workflow and agent guidance.

## Learned User Preferences

- Do not git push, merge PRs, create tags, or run `gh release create` unless the user explicitly authorizes that step; prepare commands and wait for a clear go-ahead when asked.
- Keep MAT/workflow adoption work on separate branches and PRs from product version WIP; MAT-only diffs must stay free of plugin PHP, composer, and product asset changes.
- Do not run `update-mat.py --apply` or enable the MAT observability apps stack unless the user explicitly approves.
- Prefer fixing PHPCS/CI failures in changed files over expanding baselines; for WordPress test DB setup in CI, mirror local non-interactive reset semantics rather than piping `yes` into installers.
- Treat release packaging and ZIP smoke checks as part of closeout: exclude `.DS_Store`, design-only icon proofs/directions, `.cursor/`, and agent-transcript debris while keeping shipped icon assets.

## Learned Workspace Facts

- MAT is adopted on this repo: tracked `.mat/` sidecar plus `AGENTS.md` pointer; MAT workflow surfaces under `.cursor/agents|commands|hooks|rules|skills` are tracked after mat-sync gitignore merge; private `.cursor/mcp.json`, settings, cache, and hook state stay gitignored.
- Repo-local WordPress skills under `.cursor/skills/` are registered in `.mat/product-extensions.json` and coexist with the MAT bundle; refresh via `/mat-sync` (rebootstrap when routing recommends it).
- Local PHPUnit entrypoint is `./scripts/run-phpunit-local.sh` (Docker MySQL on port 3307); CI `qa.yml` must non-interactively reset `wordpress_test` before `install-wp-tests.sh`.
- Release ZIP build is `scripts/package-plugin.sh`, aligned with `qa.yml` package-smoke and `docs/verification-matrix.md`.
- Adoption health gates are `bash scripts/phase1-verify.sh` and `bash scripts/doctor.sh`; MAT bootstrap/refresh source is the local `multi-agent-teams` checkout via `MULTI_AGENT_WORKFLOW_ROOT`.
