# Subagent orchestration

Use this file when the user asks for a feature, refactor, security review, or multi-step task in the Rank Math API Manager plugin.

## Repository context

- Standalone WordPress plugin repository, not a Bedrock site
- Primary code locations:
  - `rank-math-api-manager.php`
  - `includes/`
  - `assets/`
  - `docs/`
  - `tests/`
  - `.cursor/skills/`
  - `.cursor/agents/`

## Delegation strategy

- Prefer the cheapest adequate path first, then escalate only when task risk, ambiguity, or cross-cutting impact is high.
- Use stronger agents for planning, security review, and final quality review.
- Use implementation-focused agents for coding and debugging.
- Use fast verification-oriented agents for tests, validation, and evidence gathering.
- Avoid over-delegation for simple, single-file, or documentation-only work.

## Task sizing

- Tiny documentation, wording, or single-config edits: work directly or use `developer` only if a subagent is needed.
- Small single-file bug fix: `developer` -> `verifier`
- New feature or significant refactor: `wordpress-master` -> `developer` -> `verifier`
- REST route, auth, webhook, or automation contract work: `api-specialist` -> `developer` -> `verifier`
- Security-sensitive endpoint or admin-flow change: add `security-auditor` before completion
- Data shape, query, transient, or storage design work: `data-architect` and/or `performance-optimizer`

## Default delegation flow

- New feature or significant refactor: `wordpress-master` -> `developer` -> `verifier`
- Small bug fix: `developer` -> `verifier`
- REST route design, auth, or automation contracts: `api-specialist`
- Security-sensitive changes: `security-auditor` after design or implementation
- Performance or data-shape issues: `performance-optimizer` and/or `data-architect`
- Debugging fatals, notices, or broken hooks: `debugger`
- Test selection and execution: `test-runner`
- Pre-merge or audit review: `code-reviewer`

## Parallel patterns

- Endpoint, auth, or payload changes: run `verifier` and `security-auditor` in parallel after implementation when possible.
- Larger refactors: run `verifier` and `code-reviewer` in parallel after implementation when possible.
- Performance or data changes: pair `data-architect` with `performance-optimizer` when both storage and runtime cost are in scope.
- Use parallel review only when agents can work independently without shared edit state.

## When to stop and ask the user

Do not proceed without confirmation when work includes:

- destructive operations such as uninstall cleanup, bulk deletion, or large rollback steps
- authentication model changes that alter how external automations connect
- changes to public API contracts or response payloads
- release/versioning decisions, GitHub release changes, or deployment credentials
- ambiguous product behavior or documentation conflicts
- commit, push, tag, or release actions

## Handoffs

- `wordpress-master` produces a brief plan and definition of done.
- `developer` implements the smallest safe change set and lists verification steps.
- `test-runner` runs the most relevant automated checks available, then adds manual checks when automation is missing.
- `verifier` independently confirms behavior, permissions, and edge cases.
- `security-auditor` reviews authentication, authorization, sanitization, escaping, and data exposure for any endpoint or admin-flow changes.

## Mandatory completion rules

- Do not declare endpoint, auth, or security-sensitive work complete without verification by `verifier`, `test-runner`, or both.
- When route, auth method, request payload, or response shape changes, update docs and examples in the same task.
- When behavior changes, ensure tests are updated or provide explicit manual verification steps if automation is unavailable.
- For risky or public-surface changes, prefer a final `code-reviewer` pass before considering the work ready.

## Fallback routing

- If a plugin-local specialist is missing, use the matching global specialist rather than skipping that review step.
- If no architecture specialist is available, route complex planning through the strongest available review/planning agent before implementation.
- If no performance specialist is available, use `data-architect` for storage/query issues and `verifier` for before/after evidence.

## Quick reference

| User intent | Subagent(s) |
|------------|-------------|
| Plan a feature or refactor | `wordpress-master` |
| Implement plugin code changes | `developer` |
| Verify implementation and edge cases | `verifier` |
| Review REST API routes, auth, or webhook design | `api-specialist` |
| Perform security review | `security-auditor` |
| Run and interpret tests | `test-runner` |
| Investigate warnings, fatals, or regressions | `debugger` |
| Review code quality before shipping | `code-reviewer` |
| Optimize performance or caching | `performance-optimizer`, `data-architect` |

Default sequence for most implementation work: `wordpress-master` -> `developer` -> `verifier`.
