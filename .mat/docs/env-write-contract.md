# Environment write contract (adoption / update)

- **Purpose:** Operator truth for which MAT routes may touch live `.env` / `.mat.env` vs samples only.
- **Audience:** Maintainers adopting MAT into product repos and CI operators.
- **Status:** complete
- **Last updated:** 2026-10-16

## Summary

MAT **adoption**, **mat-sync**, and **incremental update** paths merge **samples** only. They **must not** create or modify live product **`.env`** or **`.mat.env`**. Regression coverage lives in `tests/test_adopt_env_write_contract.py`; **CI fails closed** on accidental live-env writes on those paths.

**Canonical workflow keys:** `.mat.env.sample` (MAT-tool block between `# ─── MAT-tool ───` … `# ─── /MAT-tool ───`). Root **`.env.sample`** stays product-only; bootstrap may **copy** upstream `.env.sample` when the product repo has **no** `.env.sample` yet — it does not merge MAT keys into live `.env`.

**Runtime reads (honest limit):** Hooks and scripts may read `os.environ`, `.env`, or `load_dotenv` with inconsistent precedence until **[M1](../../ROADMAP.md)** unifies `scripts/lib/mat_env.py`. This document does **not** promise that editing `.mat.env` alone affects every hook today.

**Operator habits:** See [`mat-operator-playbook.md`](../guides/mat-operator-playbook.md) (env section B8) for day-to-day loading and ownership alongside this contract.

## Route table (write behavior)

| Route | Live `.env` / `.mat.env` | Sample / other paths | Notes |
|-------|--------------------------|----------------------|--------|
| `scripts/adoption/bootstrap-workflow-into-repo.sh` (`--mode existing-project`) | **No write** | Merges `.mat.env.sample` when present; copies `.mat.env.sample` or `.env.sample` when missing per layout | See `scripts/adoption/bootstrap-workflow-into-repo.sh` |
| `scripts/mat-sync.sh` detect / plan | **No write** | `env_sample_merge_preview` in plan JSON → `.mat.env.sample` only | Preview only |
| `scripts/mat-sync.sh` approve (rebootstrap / incremental env merge) | **No write** | `apply_env_sample_merge` → `.mat.env.sample` | `mat_env_sample_merge.py` |
| `scripts/adoption/update-mat.py` dry-run / plan | **No write** on product root | Plan may list `.mat.env.sample` merge; staging worktree promotion | Live files on product root untouched |
| `scripts/adoption/update-mat.py` `--apply` + `--approved` | **No write** on product root | Staging worktree receives managed updates | Operator commits from staging branch |
| `scripts/adoption/mat_env_sample_merge.py` | **No write** to live files | Writes `.mat.env.sample` when applied | Shared helper for bootstrap / mat-sync / update-mat |

## Intentional live-env writers (out of adopt regression scope)

These **may** create or copy live env files by design. Documented here; **not** covered by adopt-path fail-closed tests:

| Route | Behavior |
|-------|----------|
| `scripts/setup-dev.sh` | Copies `.env.sample` → `.env` when `.env` missing (MAT **source** dev setup) |
| `.cursor/hooks/bootstrap_worktree.sh` | With `--install --copy-env`, copies root `.env` / `.mat.env` into worktree when missing |
| Operator manual | `cp .mat.env.sample .mat.env` (or similar) after sample merge |

## Read vs write

| Surface | Adoption/update/sync | Runtime hooks (today) |
|---------|----------------------|------------------------|
| `.mat.env.sample` | Merge/copy on adopt paths | Not auto-loaded as live config |
| `.env.sample` | Bootstrap may add if absent; not auto-merged into live `.env` | Reference for operators |
| `.mat.env` | **Never** written by in-scope adopt paths | Partial / inconsistent read until **M1** |
| `.env` | **Never** written by in-scope adopt paths | Product secrets; hook reads vary |

## CI policy

- **`tests/test_adopt_env_write_contract.py`** seeds disposable product trees with synthetic live env content (no real secrets), runs bootstrap / mat-sync / update-mat / merge helpers, and asserts live files are **byte-identical** or **still absent**.
- **`bash scripts/phase1-verify.sh`** runs the full `tests/` unittest discover tranche on the MAT source tree — includes this module.
- **Fail closed:** Any future accidental write to live `.env` or `.mat.env` on in-scope routes should fail CI; do not downgrade to warn-only for this contract.

## Related

- [Getting started in existing projects](../guides/getting-started-existing-projects.md)
- [Configuration](configuration.md) — env file overview
- [MAT sidecar env spec](../../specs/mat-sidecar-env-v1.md)
- ROADMAP **M10** (done), **M1** / **M2** (hook resolution + samples encyclopedia)
