# MAT Doctor

Run a local operator diagnostics workflow.

## Usage

```text
/mat-doctor
```

Optional full pass:

```text
/mat-doctor --full
```

Advisory quality-command honesty (fake-green pattern scan):

```text
/mat-doctor --quality-commands
```

Advisory discovery/research skill honesty (no fake-green research):

```text
/mat-doctor --research-skills
```

Advisory rules-precedence collision hints (Team Rules not repo-readable):

```text
/mat-doctor --rules-precedence
```

Adoption provenance summary (mat-sync plan SHA, layout hash, capability baseline — no secrets):

```text
/mat-doctor --adoption
```

MAO generated-artifact status (advisory vocabulary — not live todo authority):

```text
/mat-doctor --mao
```

Four primary entry paths from the command registry (progressive disclosure):

```text
/mat-doctor --commands
```

Advisory N4 run manifest listing and stale hash check (not a verify gate):

```text
/mat-doctor --run-manifest
```

## Instructions

1. Run the standard checks:

```bash
bash scripts/doctor.sh
```

2. If the user requested `--full`, run:

```bash
bash scripts/doctor.sh --full
```

3. If the user requested `--quality-commands`, run:

```bash
bash scripts/doctor.sh --quality-commands
```

This mode is **advisory only** (always exits 0 unless the validator crashes). It scans MAT-owned verify paths (`scripts/phase1-verify.sh`, `.cursor/hooks/post_tool_validate.py`, `scripts/doctor.sh`) for heuristic fake-green patterns such as success echoes without a preceding real command, `lint_ok` true on skip paths, or placeholder comments near success exits. WARN lines include `file:line` hints.

4. If the user requested `--research-skills`, run:

```bash
bash scripts/doctor.sh --research-skills
```

This mode is **advisory only** (always exits 0 unless `validate_research_skills.py` crashes). It scans MAT discovery/research skills (`.cursor/skills/neuroarxiv/`, `advise-project-approach/`, `mat-preflight-gated/`) and recent handoffs for heuristic fake-green research patterns: missing G2 / never auto-escalate guardrails, caps exceeded in skill prose (>8 papers or >3 categories), or PASS claims for preflight/research without `specs/<slug>/preflight/` artifacts on disk.

5. If the user requested `--rules-precedence`, run:

```bash
bash scripts/doctor.sh --rules-precedence
```

This mode is **advisory only** (always exits 0 unless `rules_precedence_diagnostic.py` crashes). It scans locally observable project rules, nested `AGENTS.md`, `.mat/` pointers, and best-effort plugin-cache MAT rules for duplicate/shadow hints. It always notes that Dashboard Team Rules are not readable from the repo and writes `artifacts/doctor/rules-precedence-last.json`. See [`docs/reference/capability-precedence.md`](../../.mat/docs/capability-precedence.md).

6. If the user requested `--adoption`, run:

```bash
bash scripts/doctor.sh --adoption
```

7. If the user requested `--mao`, run:

```bash
bash scripts/doctor.sh --mao
```

8. If the user requested `--commands`, run:

```bash
bash scripts/doctor.sh --commands
```

This prints the four primary entry paths from `mat-command-registry.yaml` (progressive disclosure — not the full command dump).

9. If the user requested `--run-manifest`, run:

```bash
bash scripts/doctor.sh --run-manifest
```

This mode is **advisory only** (always exits 0 unless the diagnostic crashes). It lists recent manifests under `artifacts/mat-runs/` and runs `mat_run_manifest.py check` per run. WARN lines indicate stale hashes (`gate_impact: none`) — not verify FAIL.

10. Report:
   - PASS/FAIL result
   - first failing check (if any)
   - one concrete next command to fix or continue

## Rules

- Prefer `scripts/doctor.sh` as the source of truth.
- Keep output actionable and compact.
