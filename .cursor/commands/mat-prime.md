# MAT Prime

Load codebase context and provide a summary of the project.

## Usage

```
/mat-prime
```

## Instructions

You are a **codebase context loader**. Your job is to rapidly understand the project and summarize it for the user.

Optional planning-time doc reads during `/mat-plan` / `/mat-plan-onboarding` are separate from mat-prime — see [`docs/guides/planning-commands-guide.md`](../../.mat/docs/guides/planning-commands-guide.md#planning-doc-inputs-docs--ai_docs).

### Workflow

1. **Map the project structure** — Run `git ls-files` to get a full listing of tracked files.
2. **Read key documentation** — Read these files if they exist:
   - `README.md`
   - `AGENTS.md`
   - All files in `docs/` directory
   - All files in `ai_docs/` directory (if present)
   - `package.json`, `pyproject.toml`, `Cargo.toml`, or other dependency manifests
   - `.cursor/hooks.json`
3. **Identify conventions** — Note the tech stack, directory conventions, naming patterns, and agent/hook setup.
4. **Summarize** — Provide a structured summary to the user.

### Summary Format

```
## Project: <name>

### Purpose
<one-paragraph description>

### Tech Stack
- <language/runtime>
- <frameworks>
- <key dependencies>

### Directory Structure
<concise tree of important directories with descriptions>

### Key Files
- `file`: <purpose>

### Agent/Hook Setup
<summary of any agent definitions, hooks, or automation>

### Development Commands
- `<command>`: <what it does>

### Open Questions
- <anything unclear from the docs>
```

---

## Rules

- Read-only operation — do NOT modify any files
- Prioritize breadth over depth — understand the whole project, don't deep-dive into implementation
- If `ai_docs/` exists, treat those files as important context documents
- Keep the summary concise but complete enough to orient a new contributor
