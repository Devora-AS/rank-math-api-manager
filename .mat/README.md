# `.mat/` — Multi-agent workflow (MAT) sidecar

This directory holds **MAT-packaged** material for this repository: reference documentation and workflow contract tests copied from the MAT source repo. It keeps product documentation at the repo root separate from workflow manuals.

- **`.mat/docs/`** — packaged workflow documentation (components, getting started, MAO protocol, [workflow-artifact-contract.md](docs/workflow-artifact-contract.md) for `build-result.md` / `verify-result.md` section contracts, etc.).
- **`.mat/tests/`** — workflow contract tests (`unittest`); run with `python3 -m unittest discover -s .mat/tests -p 'test_*.py' -v`.
- **`.mat/AGENTS.mat.md`** — full MAT operator reference from the source `AGENTS.md`.
- **`.mat/vendor/README-MAT.md`** — optional attribution copy of the MAT source `README.md`.

Entrypoints at repo root: **`scripts/phase1-verify.sh`**, **`.cursor/`** (hooks, commands, agents).

`phase1-verify.sh` detects this sidecar (presence of this file) and then: validates workflow markdown with **optional** `build-result.md` / `verify-result.md` when those handoffs are absent, skips closeout posture checks until `artifacts/agent-traces/comparison.json` exists, runs **`python3 -m unittest discover -s .mat/tests`** (not the product’s `tests/` tree), and skips the Bun observability smoke when `apps/server` is not packaged.

For product narrative, use the root **`README.md`** and your application docs — not this tree.
