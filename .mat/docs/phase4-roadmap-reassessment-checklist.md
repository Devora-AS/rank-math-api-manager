# Phase 4 — roadmap reassessment checklist (operator)

**Purpose:** Bounded procedure for the ROADMAP **Current Focus** item *“Reassess blocked runtime limitations only when durable new evidence appears”* ([`ROADMAP.md`](../ROADMAP.md)). This is **operator work**, not something an unattended agent run can complete honestly.

**Last updated:** 2026-03-29

## Preconditions

- You have a **pinned** Cursor version / build (note in the audit header).
- You have read [`docs/decision-record.md`](decision-record.md) **Blocked remainder** and **Go criteria for the advisory slice** (G4–G7 measurement rows).
- Procedures and PASS/INCONCLUSIVE definitions: [`docs/mao-advisory-go-criteria.md`](mao-advisory-go-criteria.md).
- Audit template: [`../artifacts/phase1/mao-advisory-go-criteria-template.md`](../artifacts/phase1/mao-advisory-go-criteria-template.md).

## Checklist

1. **Restate current blocked claims** — From [`ROADMAP.md`](../ROADMAP.md) § *Blocked / Runtime-Limited*, copy the bullets that still apply (no deletion until evidence supports it).

2. **Run or schedule measurement arms** — For each open G4–G7 item you intend to update, follow the matching section in [`docs/mao-advisory-go-criteria.md`](mao-advisory-go-criteria.md) (hook DB query, transcript search, grep for wording, tool vs manual arms). Record **PASS** or **INCONCLUSIVE** honestly.

3. **Prepare evidence** — Agents may prepare evidence summaries, candidate diffs, or a prefilled audit template, but this remains operator-owned work until a human reviews the material.

4. **File a redacted audit** — Add or update a row under `artifacts/phase1/` using the template; include Cursor version and whether `hook_events` / `artifacts/mao/*todo*` files appeared (**including explicit “none”**).

5. **Update `docs/decision-record.md` checkboxes** — Only when you have **dated, cited** evidence from step 2–4. Do **not** check G4–G7 from inference or from another operator’s machine without a new audit row.

6. **Update [`ROADMAP.md`](../ROADMAP.md)** — If posture changes, adjust *Current Focus* / *Near-Term* / *Blocked / Runtime-Limited* with one-line rationale and link to the audit file. Final roadmap or publication/packaging posture changes are operator-owned even when agents prepared the draft. If nothing changed, note “no change” in internal release notes or leave ROADMAP unchanged.

7. **Repo verification** — Before merge: `bash scripts/phase1-verify.sh` and doc tests per [`docs/mao-advisory-go-criteria.md`](mao-advisory-go-criteria.md) G7.

## Honesty boundaries

- **Do not** claim authoritative live Cursor todo parity or a live dashboard todo column.
- **Do not** claim hook-driven subagent spawn from **live** todo state.
- **Do not** treat prepared evidence or drafted wording as runtime authority.
- **INCONCLUSIVE** remains a valid outcome; it advances honesty without proving advisory usefulness.

## Related

- [`specs/phase-4-planning-session.md`](../specs/phase-4-planning-session.md) — Phase 4 direction.
- [`docs/todo-orchestration-runtime-evidence.md`](todo-orchestration-runtime-evidence.md) — What committed artifacts can prove.
