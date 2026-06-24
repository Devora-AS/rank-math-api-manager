# cursorignore-mat-shared.inc
# Reusable block for MAT stack templates. When editing, sync copies in
# `cursorignore-mat-default` and per-stack templates. Not installed at repo root
# as-is; copied into `cursorignore-mat-*` files.

# Dependencies & build outputs
node_modules/
dist/
build/
out/
.next/
.nuxt/
.turbo/
coverage/
htmlcov/

# Caches & compiled artifacts
.cache/
__pycache__/
*.py[cod]
.ruff_cache/
.mypy_cache/
.pytest_cache/
.tox/
*.egg-info/

# Logs & local env (never index secrets)
*.log
.env
.env.*
!.env.sample

# Large generated / vendor trees (extend per repo)
artifacts/run-traces/

# ─── Escape hatch ─────────────────────────────────────────────────────────────
# Tight ignores save tokens and reduce accidental secret exposure. When a slice
# truly needs a path listed here, remove or narrow the relevant lines in
# `.cursorignore` for that work, document why, and restore strict patterns afterward.
