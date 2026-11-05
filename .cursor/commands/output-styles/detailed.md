# Detailed Output Style

Use this style when the user asks for deeper explanation, trade-offs, architecture context, or a walkthrough that should be understandable without opening every file.

## Goals

- Explain both the outcome and the reasoning behind it.
- Preserve important caveats and trade-offs.
- Help the reader understand how the pieces connect.

## Default Shape

- Use short titled sections when they improve scanning.
- Start with the high-level result before details.
- Group information by topic or user-facing outcome, not by every touched file.
- Use bullets for comparisons, steps, or discrete findings; use paragraphs for explanation.

## Do

- Explain why a change was made, not just what changed.
- Call out assumptions, constraints, and rejected alternatives when relevant.
- Include focused code or command examples when they teach something.
- Mention verification and any residual gaps.

## Avoid

- Turning every answer into a changelog.
- Copying large code blocks when a short excerpt or summary is enough.
- Over-explaining trivial edits.
- Hiding the final outcome under too much background.

## Good Fits

- Multi-file refactors
- Design decisions
- Debugging writeups
- Feature handoffs

## Suggested Sections

1. Result
2. Key changes
3. Verification
4. Risks or follow-ups

## Example

```md
## Result
The dashboard now uses a normalized `project_label` end-to-end, so filters and event cards no longer rely on ad-hoc path parsing in the client.

## Key changes
- Added shared normalization on the server and included `project_label` in the wire payload.
- Updated the client to trust the wire value first and derive it only as a fallback.
- Added targeted tests for fetched records and websocket events.

## Verification
`bun test src`, `bun test`, and `bun run build` all passed.
```
