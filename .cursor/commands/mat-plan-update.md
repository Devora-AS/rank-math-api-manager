# MAT Plan Update

Apply a surgical, planning-only amendment to an existing planning artifact — append-only `## Amendments` lines without re-running full onboarding or rewriting whole specs.

## Usage

```text
/mat-plan-update <target-path> — <amendment summary>
```

Example:

```text
/mat-plan-update specs/my-feature.md — narrow scope to API-only slice; defer UI to follow-up
```

## Instructions

**Plan contract skill:** For amendments, drift rules, and projection semantics, see [`.cursor/skills/mat-plan-contract/SKILL.md`](../skills/mat-plan-contract/SKILL.md) (does not replace this command).

You are a solo planning agent. Apply **minimal** edits to an **existing** planning file only. Do not implement product code in this command.

### Guardrails

- Planning only — no implementation.
- Do not create `build-result.md`, `verify-result.md`, or MAO execution handoffs.
- Do not auto-edit `docs/current-plan.md` — even when it is the active execution plan (see **Drift / re-projection** below).
- Do not rewrite or delete prior `## Amendments` lines — append only.
- Do not reuse `/mat-plan-team` execution-mode terms here. `/mat-plan-update` is planning-depth / command-depth only.
- **Preflight escalation:** see [`docs/architecture/preflight-escalation-ladder.md`](../../.mat/docs/preflight-escalation-ladder.md) (planning depth and command depth layers).
- For how project-local specs relate to global/plugin defaults when planning, see [`docs/reference/capability-precedence.md`](../../.mat/docs/capability-precedence.md).

### Supported targets

| Target path | Role | Notes |
|-------------|------|-------|
| `specs/<slug>.md` | Solo lightweight plan | Primary target; ensure `## Amendments` exists or add it before appending |
| `specs/<slug>/plan-summary.md` | Onboarding bridge | Preferred package target for execution handoff drift; amend optional `## Related plans` `### back_refs` / `### forward_refs` bullets here when continuity links drift; amend optional `## Open Decisions` `OD-###` row status in-place (same id) with append-only `## Amendments` cite |
| `specs/<slug>/spec.md` | Optional (defer) | Use only when the amendment is clearly spec-scoped; prefer `plan-summary.md` for slice-level drift |
| `specs/<slug>/prd.md` | Optional (defer) | Product-intent changes that affect multiple specs — prefer onboarding re-run when traceability breaks |

When both `specs/<slug>.md` and `specs/<slug>/` exist, the **folder package** remains authoritative for heavyweight planning and execution handoff; update the package file that owns the drift (usually `plan-summary.md`), not the solo file alone.

### Amendment protocol (append-only)

1. Ensure the target has a `## Amendments` section (create it if missing; on solo plans, place it second-to-last, immediately before `## Recommended Next Command`).
2. Append **exactly one** new bullet per invocation:

   ```markdown
   - YYYY-MM-DDTHH:MM:SSZ — role — summary
   ```

   Use ISO-8601 UTC timestamps. Never rewrite or delete prior amendment lines.

3. Apply **minimal** in-body edits only where the amendment summary requires concrete text changes (scope bullets, acceptance criteria, risks, optional `## Open Decisions` `OD-###` row status or body for the same id, etc.).
4. Do not expand scope into a full re-authoring pass — that is `/mat-plan` or `/mat-plan-onboarding` territory.

**Open Decisions amendments:** When updating decision status, edit the matching `OD-###` row in-place (same id; do not delete prior ids) and append one `## Amendments` line citing the decision id. Allowed status tokens: `open`, `resolved`, `deferred` (lowercase, backtick-wrapped).

### Drift / re-projection rule

When `docs/current-plan.md` is **active** (substantive orchestration slice in flight) and planning truth in `specs/` drifts:

1. Update the **planning artifact** first with `/mat-plan-update` (this command).
2. **Do not** edit `docs/current-plan.md` inside this command.
3. After the planning amendment, the **operator** re-projects the approved slice into `docs/current-plan.md` (human/operator-owned), then resumes execution with `/mat-plan-team` or `/mat-long-run`.

If execution already diverged materially, treat re-projection as mandatory before continuing build/verify — markers and MAO todos do not substitute for planning truth.

### Preflight classification

After reading the target, classify the work as one of:

- `surgical_amendment` — bounded edit + one append-only amendment line is sufficient.
- `escalate_to_onboarding` — scope, traceability, or cross-file package integrity requires `/mat-plan-onboarding` (or a fresh `/mat-plan`) instead of in-place surgery.

If `escalate_to_onboarding`, stop before destructive edits; explain why and recommend the heavier command.

### Workflow

1. **Validate target** — confirm the path exists, is a supported planning artifact, and is writable in-repo.
2. **Read context** — load only the target and the smallest set of sibling package files needed to apply the amendment honestly.
3. **Classify** — `surgical_amendment` vs `escalate_to_onboarding`.
4. **Apply minimal edits** — change only sections the amendment summary requires.
5. **Append amendment line** — one ISO bullet under `## Amendments`.
6. **Check drift** — if `docs/current-plan.md` appears active, state the re-projection rule explicitly in the closeout (do not edit that file here).
7. **Closeout** — print exactly one fenced `txt` block for the honest branch (see below) and finish with `## Recommended Next Command` in chat.

### Closeout — target validated

When the target path is valid and classification is `surgical_amendment`:

```txt
# Apply minimal in-place planning edits and append one ISO amendment line — do not touch docs/current-plan.md
```

### Closeout — edits applied

When the amendment and body edits are saved:

```txt
# If docs/current-plan.md is active, operator re-projects from updated planning truth before resuming /mat-plan-team or /mat-long-run
```

### Closeout — escalate to onboarding

When classification is `escalate_to_onboarding`:

```txt
# Escalate to /mat-plan-onboarding — surgical update insufficient for traceability or package integrity
```

### Closeout — idle / handoff

When no execution handoff is pending and the living plan is planning-only:

```txt
# Planning amendment complete — continue human refinement or project when ready; no implementation in this command
```

After each major phase above, print **exactly one** recommended next command in a fenced `txt` block. Reference: [`docs/guides/planning-commands-guide.md`](../../.mat/docs/guides/planning-commands-guide.md#recommended-next-command-execution-commands) for execution-command closeouts (different pattern).

### Recommended Next Command

End the user-visible summary with a **Recommended Next Command** section that chooses **one** honest path:

- continue human refinement on the same planning file
- run `/mat-plan-update` again for another surgical amendment
- escalate to `/mat-plan-onboarding` when package/traceability needs grew
- **re-project** into `docs/current-plan.md` when planning is approved and execution should resume (operator-owned; not automatic)
- start execution with `/mat-plan-team` or `/mat-long-run` only **after** projection when an approved slice is ready

Do not start implementation from this command.
