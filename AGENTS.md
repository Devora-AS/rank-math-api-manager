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
