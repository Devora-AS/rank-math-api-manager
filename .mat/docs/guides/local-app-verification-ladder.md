# Local-App Verification Ladder

**Status:** canonical verification order for local-app pilots

**Purpose:** define the default verification order for local applications so pilots do not jump straight to brittle browser automation or close out on vague smoke checks.

## Verification Order

Use this order unless the target repo has an already-trusted deterministic harness that justifies starting at step 2:

1. **Manual/staging baseline**
   - Default baseline for local-app pilots.
   - Confirm the core user/admin flow in a real local or staging environment.
   - Record the exact steps, environment, and observed outcome in `verify-result.md` or the equivalent closeout artifact.

2. **Deterministic local automation**
   - Prefer this next when the target repo already has stable automated checks for the flow.
   - Examples: PHPUnit, integration tests, request-level tests, WP test harnesses, or other repo-native deterministic automation.
   - If the risky path has no such coverage yet, add targeted regression coverage or document an explicit exception.

3. **`browser-use`**
   - Use when browser interaction adds useful evidence and the environment is reachable to the browser tool.
   - Treat it as supporting evidence, not the default baseline.
   - Do not rely on it as the only check for risky workflow or security-sensitive changes when deterministic automation is available or should be added.

4. **Playwright**
   - Use when the target repo already ships a Playwright path or when browser-use is unsuitable for the needed UI coverage.
   - Prefer focused deterministic scenarios over broad flaky smoke suites.
   - Like browser-use, this is a ladder tool, not an implied default for every local-app pilot.

5. **Explicit fallback path**
   - If deterministic automation is not practical in the slice and browser tooling is blocked, document the fallback explicitly.
   - State what was verified manually, what was not automated, why automation was deferred, and what follow-up coverage is still needed.
   - Do not present that fallback as equivalent to targeted regression coverage.

## Default Rule

For local-app pilots, **manual/staging is the default baseline unless deterministic local automation already exists in the target repo**.

Browser-use and Playwright are optional ladder steps. They help gather evidence, but they do not replace the default baseline and they do not remove the need for targeted regression coverage on risky paths.

## Risk Escalation Rule

If a slice touches any of these areas, do not close out on vague or purely smoke-style verification alone:

- hooks
- validators
- artifact parsing
- MAO transitions
- security-sensitive pilot logic

For those changes, require one of:

1. **targeted regression coverage**, or
2. an **explicit documented exception** that explains why the coverage was not added in this slice

The exception must be written in the slice artifacts (`build-result.md`, `verify-result.md`, or the equivalent repo-local handoff), not left as an implicit assumption.
