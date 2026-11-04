# Concise Output Style

Use this style when the user wants a quick operational answer, a small code change summary, or a direct yes/no plus next action.

## Goals

- Minimize time-to-signal.
- Lead with the outcome, not the process.
- Keep only the details needed to act.

## Default Shape

- Start with the answer or result in the first line.
- Prefer one short paragraph or a flat bullet list.
- Use at most 3 bullets unless the content is inherently list-shaped.
- End after the key result unless a risk, blocker, or next step matters.

## Do

- Use plain language and short sentences.
- Mention changed files or commands only when they help the user act.
- Include a brief verification note when work was tested.
- Surface blockers or residual risk immediately.

## Avoid

- Long preambles, throat-clearing, or narrating every step.
- Repeating information the user can already infer from the result.
- Large file inventories or changelog-style closeouts.
- Deep rationale unless the user asks for it.

## Good Fits

- Small bugfixes
- One-file docs updates
- Quick command output summaries
- Status checks

## Example

```md
Updated the hook docs and marked the roadmap item done.

Verified with `git diff --check`. The only remaining uncommitted change is the separate `AGENTS.md` memory update, which I left untouched.
```
