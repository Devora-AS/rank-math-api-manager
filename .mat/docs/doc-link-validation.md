# Internal markdown link validation

**Status:** Maintainer reference — enforced on the MAT **source** tree via `scripts/validate_doc_links.py` and `scripts/phase1-verify.sh`.

## Purpose

Catch broken relative links in operator-facing markdown before they reach CI. The validator resolves `](path)` targets from the **containing file’s directory** (strict relative), matching how Cursor and GitHub render links in nested trees.

## Resolution rules by surface

| Surface | Rule |
|---------|------|
| `docs/**` (non-archive) | Strict relative from the file directory (`../reference/`, `../guides/`, `../../` to repo root). |
| `docs/archive/**` | Same strict relative rules; validated by **`source-archive`** profile (separate from active `docs/`). |
| `.cursor/commands`, `.cursor/agents` | Strict relative — typically `../../docs/reference/...`. |
| `.cursor/skills/<name>/` | Strict relative — use `../../../docs/...`, `../../../specs/...`; sibling skills via `../other-skill/SKILL.md`; `.cursor` assets via `../../commands/...` (not `../../.cursor/...`). |
| `.cursor/rules/*.mdc` | Same as `.cursor/` — e.g. `../../docs/reference/context-budget-policy.md` from `.cursor/rules/`. |
| `packages/mat-workflow/**` | Plugin bundle layout — same depth rules as mirrored `.cursor/` under the package root (not repo-root-only paths). |
| `.mat/docs/**` (adopted sidecar) | Strict relative in the sidecar; repo-root `docs/...` pointers must resolve on the adopted tree or use narrow **`planned_paths`** (no blanket `.mat/docs/**` glob). |
| `http(s)://`, `mailto:`, `#` anchors | **Skipped** — no network or in-page validation. |

Full policy table also lives in active orchestration plans that introduce link slices; this doc is the long-lived reference.

## Allowlists

Some links intentionally target generated, planned, or optional paths. The validator loads `scripts/doc_link_allowlist.json` when present and merges:

- **`planned_paths`** — prefix allowlist for future or irrecoverable historical docs (broken target allowed).
- **`optional_globs`** — fnmatch patterns (default includes gitignored MAO gate filenames referenced from prose; `artifacts/report/**` and `artifacts/phase1/**` for archive citations).
- **`adopted_sidecar_planned_prefixes`** / **`adopted_sidecar_optional_globs`** — merged only for `--profile adopted-sidecar` (MAT source pointers and gitignored paths not shipped in bootstrap fixtures).

Broken links that are **not** allowlisted fail the check. Use `--report` for JSON output.

**Archive note:** After the M7 archive sweep, only genuinely missing historical targets (for example ephemeral agent transcript IDs) remain on `planned_paths`. Do not re-add a blanket `.mat/docs/**` optional glob — that hides real adopted-sidecar defects.

## CLI

```bash
python3 scripts/validate_doc_links.py --repo-root . --profile source
python3 scripts/validate_doc_links.py --repo-root . --profile source-archive
python3 scripts/validate_doc_links.py --repo-root . --profile plugin
python3 scripts/validate_doc_links.py --repo-root . --profile adopted-sidecar
python3 scripts/validate_doc_links.py --repo-root tests/fixtures/adopted_sidecar_link_graph --profile adopted-sidecar
```

| Flag | Meaning |
|------|---------|
| `--profile source` | Active `docs/` (excl. `docs/archive/`), `.cursor/` markdown/mdc, `packages/mat-workflow/`. |
| `--profile source-archive` | `docs/archive/**` only. |
| `--profile plugin` | `packages/mat-workflow/` only. |
| `--profile adopted-sidecar` | `.mat/docs/**`, `.mat/README.md`, adopted `.cursor/{commands,agents,skills,rules}/**`. |
| `--profile adopted-fixture` | `tests/fixtures/doc_links/` (unit tests). |
| `--report` | JSON summary on stdout. |
| `--fail-on-warn` | Do not treat allowlisted missing targets as OK. |

## CI / phase1-verify

On the MAT **source** repository, `scripts/phase1-verify.sh` runs:

```bash
python3 scripts/validate_doc_links.py --repo-root "$ROOT" --profile source
python3 scripts/validate_doc_links.py --repo-root "$ROOT" --profile source-archive
```

**Adopted sidecar** trees:

| Profile | Doc link check |
|---------|----------------|
| `adopted-operational` | **Skip** — use `adopted-contract` for sidecar link validation. |
| `adopted-contract` | Runs `--profile adopted-sidecar` and records `doc_link_validation` pass. |

`scripts/ci/run-adopted-contract-verify.sh` also runs `adopted-sidecar` validation on the bootstrapped fixture before `phase1-verify`.

Bootstrap and `update-mat.py --apply` rewrite copied `.cursor/` and `.mat/docs/` link targets via `scripts/adoption/adopted_link_rewrite.py` (layout-driven `mat_docs` map). The canonical adopted workflow artifact contract file is **`.mat/docs/workflow-artifact-contract.md`** (source: `docs/reference/workflow-artifact-contract.md`). The validator loads the same rewrite module from `scripts/adoption/` for sidecar resolution aliases.

## Boundaries

- Does not validate external URLs, citation-only path strings outside markdown links, or every `README.md` repo-root-absolute style link in one pass.
- Does not replace human review for “source-repo pointer” semantics in adopted `.mat/docs/`.
- Regressions: `tests/test_validate_doc_links.py`, `tests/test_ci_adopted_contract.py`.

## Related

- [`scripts/validate_doc_links.py`](../../scripts/validate_doc_links.py)
- [`scripts/validate_cost_context_hygiene_pack.py`](../../scripts/validate_cost_context_hygiene_pack.py) — complementary policy-string checks for context-budget rule text
- [`docs/reference/verification-profiles.md`](verification-profiles.md) — `doc_link_validation` check per profile
