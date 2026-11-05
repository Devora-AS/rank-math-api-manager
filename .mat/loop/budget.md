# MAT loop budgets (operator template)

Default per-`slice_class` budgets for MAT loop policy v0. Mirrors `docs/reference/loop-policy.md` and `scripts/mat_loop_policy.py` (`DEFAULT_BUDGETS`). Unknown `slice_class` falls back to **feature**.

Manifest `budgets` may override individual keys (`max_attempts`, `max_tool_calls`, `max_wall_min`).

## Budget table

| slice_class | max_attempts | max_tool_calls | max_wall_min |
|-------------|--------------|----------------|--------------|
| `small_fix` | 3 | 80 | 45 |
| `feature` | 5 | 200 | 120 |
| `refactor` | 4 | 150 | 90 |
| `docs` | 2 | 40 | 30 |
| `adoption` | 3 | 120 | 90 |
| `long_run` | 5 | 250 | 180 |

## Exhaustion → stop

`evaluate()` returns **stop** when any of:

- `attempts >= max_attempts`
- `counters.tool_calls >= max_tool_calls`
- `counters.wall_min >= max_wall_min`
- `manifest.terminal == true`

## Initialize manifest

```bash
python3 scripts/mat-loop-manifest.py init \
  --run-id <run-id> --slice-id <slice-id> --slice-class feature
```

Opt-in policy: set `CURSOR_MAT_LOOP_POLICY=1`. Diagnostic: `bash scripts/doctor.sh --loop-policy` (advisory; MAT source tree).
