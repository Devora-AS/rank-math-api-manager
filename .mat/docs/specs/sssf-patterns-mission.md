# SSSF-inspired patterns mission (A11, discovery spec, B13, C-A2, A1, B9)

**Task type:** `feature`
**Complexity:** `complex`
**Preflight:** `ready_for_execution_handoff`
**Source:** ROADMAP.md Next section (2026-08-21)

---

## Mission goal

Ship six related SSSF-inspired stable items: SPDX LICENSE (A11), discovery/research skills design spec, SSSF patterns sidecar guide (B13), optional gate evidence in build handoffs (C-A2), doctor quality-command honesty (A1), and placeholder quality-command banner (B9). Commit after each verified slice; no push until operator approves.

## Global constraints

- File handoffs remain authoritative; no live MAO auto-orchestration.
- MIT SPDX identifier (user-approved; SSSF reference).
- Discovery spec: combined wrapper name `mat-preflight-gated`; inline citations only for provenance minimum.
- A1 and B9 ship together in final slice (paired).
- `bash scripts/phase1-verify.sh` must exit 0 after slice 6.

## Ordered slice queue

| # | Slice id | Scope | execution_mode |
|---|----------|-------|----------------|
| 1 | `slice-1-spdx-license` | LICENSE (MIT) + README license section | `builder_plus_verifier` |
| 2 | `slice-2-discovery-spec` | `specs/mat-discovery-research-skills.md` | `builder_plus_verifier` |
| 3 | `slice-3-sssf-sidecar` | `docs/guides/sssf-patterns-sidecar.md` | `builder_plus_verifier` |
| 4 | `slice-4-gate-evidence` | workflow-artifact-contract + artifact_contract.py + prompts + tests | `builder_plus_verifier` |
| 5 | `slice-5-quality-honesty` | doctor `--quality-commands` + hook advisory banner (A1+B9) | `builder_plus_verifier` |
| 6 | `slice-6-roadmap-closeout` | ROADMAP checkboxes, docs inventory, full phase1-verify | `builder_plus_verifier` |

## Resolved operator decisions

- Combined wrapper skill directory: **`mat-preflight-gated`**
- Minimum provenance: **inline citations only** (no per-task manifest.json requirement)
- Neuroarxiv promotion deferred until A11 lands (satisfied by slice order)

## Global acceptance

- [x] All six slices verified PASS
- [x] ROADMAP Next items A11, discovery spec, B13, C-A2, A1, B9 marked done
- [x] `bash scripts/phase1-verify.sh` exit 0

## Amendments

- 2026-08-21T19:37:00Z — orchestrator — Mission initialized from operator `/mat-long-run` request.
