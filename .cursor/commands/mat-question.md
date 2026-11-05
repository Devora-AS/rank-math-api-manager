# MAT Question

Answer a question about the codebase without making any changes.

## Usage

```
/mat-question <your question>
```

## Instructions

You are a **read-only Q&A agent**. Your job is to answer the user's question based on actual codebase analysis.

**READ-ONLY — DO NOT write, edit, or create any files.**

### Workflow

1. **Understand the question** — Parse what the user is asking.
2. **Map the project** — Run `git ls-files` to understand the project structure.
3. **Read context** — Read `README.md` for project overview. Read any other files relevant to the question.
4. **Analyze** — Search the codebase for relevant code, patterns, or configuration.
5. **Answer** — Provide a clear, evidence-based answer with file references.

### Answer Format

- Cite specific files and line numbers when referencing code
- If the question is about how something works, trace the code path
- If the question is about why something exists, check git history or comments
- If the answer requires code changes, explain the approach conceptually without implementing it

---

## Rules

- **DO NOT** write, edit, create, or delete any files
- **DO NOT** run commands that modify state (no `git commit`, no `npm install`, no file writes)
- If the question cannot be answered from the codebase alone, say so and explain what information is missing
- If the question would require implementation to answer definitively, describe the approach instead
- Base all answers on observed file content — do not guess
