# MAT Start

Start the observability system.

## Usage

```
/mat-start
```

## Instructions

Run the observability system startup script (Bash; it sources `scripts/lib/ensure-bun-path.sh` so `bun` is found even when `~/.zshrc` was not loaded):

```bash
bash scripts/start-system.sh
```

Run in the **background** in a terminal tab if you want it to keep running while you work: append `&` or use your terminal’s detach.

If `scripts/start-system.sh` does not exist, start the services individually (ensure `PATH` includes `~/.bun/bin` if needed):

```bash
cd apps/server && bun install && bun run dev &
cd apps/client && bun install && bun run dev &
```

Report which services were started and on which ports.

After startup (or if the operator only wants orientation), print the **four primary entry paths** from the command registry — not the full 23-command dump:

```bash
python3 scripts/generate-command-index.py --print-primary
```

Full inventory lives in [`docs/reference/command-index.md`](../../.mat/docs/command-index.md) (generated from `mat-command-registry.yaml`).
