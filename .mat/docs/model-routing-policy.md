# MAT routing policy v1

- Purpose: define MAT's conservative, docs-first routing vocabulary and escalation policy without turning MAT into a runtime model router.
- Audience: operators, maintainers, and agents that need a stable policy reference for model-tier decisions.
- Status: complete — stable MAT routing tiers, escalation rules, and advisory telemetry fields.
- Last updated: 2026-08-31

## Scope

This document is the MAT policy layer for routing decisions. It is intentionally adapter-agnostic, does not depend on `agent-model-router`, and does not describe undocumented Cursor alias-style frontmatter behavior as MAT core policy.

MAT owns the policy language, the escalation rules, and the advisory budget notes. **MAT does not own Cursor's runtime model resolution**, and it does not introduce a separate runtime router in this slice. Operators may steer Cursor product surfaces (for example Auto Optimize For modes); MAT tiers remain a docs-first intent vocabulary, not a claim that MAT selects the underlying model.

## Cursor Router grounding (product surface)

Public product docs for Cursor Router (fetched 2026-08-31):

- [Cursor Router](https://cursor.com/docs/cursor-router)
- Related catalog / pricing orientation: [Models](https://cursor.com/docs/models) (and models-and-pricing where linked from product docs)
- Local research excerpt (non-authoritative): [`ai_docs/cursor-router-2026-08-31.md`](../../ai_docs/cursor-router-2026-08-31.md)

**Availability:** Cursor Router (the routing system behind Auto) is documented as available on **Teams and Enterprise** plans. Enterprise may require an admin enable step (router off by default on Enterprise per product docs).

**How operators steer Auto:** Open the model picker, select Auto, and choose a mode under **Optimize For**:

| Optimize For mode | Product intent (from Cursor docs) |
|-------------------|-----------------------------------|
| **Cost** | Prioritizes token spend (documented as previous Auto routing logic). |
| **Balance** | Optimizes for intelligence, speed, and cost. |
| **Intelligence** | Routes toward more capable models for harder tasks, still framed as lower cost than always running a single frontier model. |

Balance and Intelligence are documented to consume usage limits faster than Cost. You can switch modes at any time. Cursor Router classifies each agent request; operators **cannot** hand-pick which underlying model handles a given Auto request, and the model pool changes over time.

**Hidden underlying model (default):** Team settings can display which model Auto routed to at the start of each response, or keep it **Hidden**. Hidden is the default and recommended for Balance and Intelligence so results are judged on merit rather than model name. **Acceptance criteria, verifier gates, and cost attribution in MAT must not depend on a resolved or hidden underlying model ID.** Treat the resolved model as unknown unless an operator explicitly enables display for debugging — even then, model labels in UI/hooks remain environment/product behavior, not workflow truth.

**SDK surface (when using Cursor Agent SDK):** Product docs expose Router as model id `auto-smart` with parameter `optimize_for` set to one of `cost` | `balanced` | `intelligence`. Discover availability via `Cursor.models.list()` before hard-coding. The SDK runs Cursor agent workflows; it is not a raw chat-completions API. MAT does not wrap or own this SDK selection.

**Grok enablement note:** Product docs state that enabling **Cursor Grok** (documented as Cursor Grok 4.5) is a requirement for the router pool to work — the router needs a powerful yet cost-efficient model when it is not calling other frontier models. Blocking too many models can reduce routing quality or disable the router. This is a **team admin / product** concern, not a MAT gate.

**Out of scope for this policy:** Do **not** claim that Automations, ACP, or other undocumented product APIs expose MAT routing tiers or can set Optimize For on MAT's behalf. No speculative Automations/ACP routing APIs are part of MAT policy. Stick to published [cursor.com](https://cursor.com/docs/cursor-router) documentation.

### Advisory MAT tier → Router intent mapping

This mapping is **advisory and plan-dependent**. It helps operators align MAT `cheap` / `standard` / `strong` intent with Cursor Auto Optimize For modes or SDK `optimize_for`. It does **not** mean MAT owns runtime resolution, and it must never be used as acceptance proof via a resolved model ID.

| MAT tier | Recommended Auto Optimize For | SDK `optimize_for` (when using `auto-smart`) | Operator intent |
|----------|-------------------------------|-----------------------------------------------|-----------------|
| `cheap` | **Cost** | `cost` | Prefer spend efficiency for exploration, summarization, and low-risk repetitive edits. |
| `standard` | **Balance** | `balanced` | Default for routine orchestration, builder/verifier work, and mixed cost/quality needs. |
| `strong` | **Intelligence** | `intelligence` | Prefer higher capability for ambiguous, high-impact, or safety-sensitive work. |

Escalate MAT tiers using the rules below even when Cursor Auto is selected; product routing and MAT policy language remain separate layers.

## Routing vocabulary

Use three tiers only:

- `cheap` for exploration, summarization, repetitive low-risk edits, and other tasks where speed and cost matter more than deep reasoning.
- `standard` for routine orchestration, normal builder/verifier work, and the default case when no stronger signal exists.
- `strong` for ambiguous tasks, high-impact changes, safety-sensitive work, or cases that need more deliberate reasoning.

Do not add a fourth MAT tier in this slice. If a future use case justifies more nuance, keep it outside this canonical v1 policy until there is a concrete repo-backed need.

`multimodal` stays deferred unless a concrete repo-backed use case appears.

## Conservative escalation rules

Start with the cheapest honest tier. Escalate only when the current tier is a poor fit, not because a richer tier might be theoretically available.

Escalate from `cheap` to `standard` or `strong` when one or more of these are true:

- the first attempt shows weak fit, missed context, or low-confidence reasoning
- the task fans out into multiple dependent steps
- the task is ambiguous enough that a cheaper tier would likely require rework
- the work has safety, production, or cross-cutting impact
- the cost of retrying a weak tier is higher than paying for the stronger one up front

Escalate from `standard` to `strong` when the task still needs more careful reasoning after ordinary orchestration has been ruled out, or when the impact/risk profile justifies the extra cost.

Do not escalate just to chase completeness. If the task is bounded, routine, and low-risk, keep the lower tier.

## Advisory telemetry and budget surfaces

Telemetry in this slice is advisory only. The smallest useful policy surface is:

- the chosen routing tier
- the reason that tier was chosen
- any budget or cost note that informed the decision
- an explicit note that the data is guidance, not workflow truth

The structured advisory record stays tiny and best-effort. When the runtime can observe
more detail, it may include:

- `timestamp`
- `session_id`
- `source_hook`
- `provider`
- `model`
- `routing_tier`
- `routing_reason`
- `suggested_tier`
- `recommended_escalation`
- `budget_note`
- `context_pressure`
- `context_usage_percent`
- `messages_to_compact`
- `payload_size_chars`
- `payload_size_bytes`
- `boundary_signals`
- `input_tokens`
- `output_tokens`
- `cached_tokens`
- `estimated_cost_usd`
- `signal_class`
- `non_authoritative`

The optional `model` field, when present, is a **best-effort environment label**. Acceptance criteria and cost attribution **must not depend on** a hidden or resolved **underlying model** ID from Cursor Router Auto. Prefer recording MAT `routing_tier`, `routing_reason`, and budget notes; treat missing or unknown resolved model as the normal case under Hidden display defaults.

The `signal_class` stays `advisory`; the pressure or escalation signal belongs in
`routing_reason` and `budget_note`, not in a second workflow-truth channel.

`session_id` is only present when the hook payload exposes one. `timestamp` marks when
the advisory was built, not when a routing decision became authoritative.

The boundary markers use conservative advisory thresholds: context usage at or above
70 percent, payloads at or above 6000 characters, and messages-to-compact at or above
25. `recommended_escalation` is only a hint, and `suggested_tier` is still advisory.

Reason codes stay deliberately small and reviewable: `bounded_low_risk`,
`cross_file_complexity`, `retry_escalation`, `safety_impact`, `context_pressure`, and
`insufficient_signal`.

Budget guidance should stay small and readable. If a later slice needs machine-readable thresholds, keep that artifact tiny and schema-checked instead of turning MAT into a heavy policy engine.

### Authoritative vs advisory (routing context)

| Kind | Role |
|------|------|
| **Authoritative (workflow truth)** | Canonical handoffs: `docs/current-plan.md`, `build-result.md`, `verify-result.md`, and (when used) `docs/architecture/long-run-state.md` — same boundary as [`capability-precedence.md`](capability-precedence.md). |
| **Advisory (routing / cost awareness)** | Human or agent notes about tier, reason, and budget; optional example JSON shape [`schemas/mat-routing-advisory.example.json`](../schemas/mat-routing-advisory.example.json); optional gitignored JSONL artifact at `artifacts/mao/routing-advisory.jsonl`; optional session rollups at `artifacts/mao/routing_rollup_<session_id>.json`; local analysis via `scripts/analyze_routing_advisory.py`; hook-emitted observability events (PostToolUse, Stop, and so on). |

Hooks and the observability stack **do not** record an authoritative MAT routing decision. They may carry model labels or summaries for debugging; those remain **environment and product behavior**, not a replacement for this policy doc or for handoff files.

### Where MAT surfaces routing telemetry (honest inventory)

Operators and agents may record the advisory fields in:

- **`docs/session-summary.md`** — short optional lines for tier, reason, and budget note when useful for the run.
- **Parent chat or run notes** — same fields; still advisory.
- **Optional example JSON** — [`schemas/mat-routing-advisory.example.json`](../schemas/mat-routing-advisory.example.json) documents a minimal portable shape for pasting into summaries or tooling; it is **not** wired as mandatory runtime input in this slice.
- **Optional JSONL emission** — `artifacts/mao/routing-advisory.jsonl` can be appended in a fail-open way when the opt-in hook flag is enabled; the artifact is advisory only and may be absent.
- **Optional session rollups** — `artifacts/mao/routing_rollup_<session_id>.json` can summarize counts and completeness when rollup emission is enabled; the file is advisory only and may be absent.
- **Gitignored MAO / hook artifacts** — for example `artifacts/mao/transition-events.jsonl`, gate files: workflow-oriented, still **not** a substitute for reading `current-plan` / `build-result` / `verify-result`.

Do **not** treat observability event streams or hook payloads as proof of which MAT tier “should” have been used; they are diagnostic and optional.

### Context and cost

For **bounded context** (what to load by default per role), see [`docs/reference/context-budget-policy.md`](context-budget-policy.md). It complements this doc: routing tier is policy; context budget is operational loading discipline.

## Deferred adapter boundary

If `agent-model-router` is ever adopted later, it should remain a deferred adapter boundary outside MAT core and stay optional. That future boundary should translate MAT policy into provider- or editor-specific behavior, not redefine the MAT policy itself.

This slice does not create that adapter, does not vendor that project, and does not claim any Cursor-specific alias behavior as a MAT contract.

## Related docs

- [`docs/reference/capability-precedence.md`](capability-precedence.md) for project-first capability routing and authoritative-vs-advisory boundaries
- [`docs/reference/routing_advisory.md`](routing_advisory.md) for the advisory record shape and safe surfacing rules
- [`docs/reference/context-budget-policy.md`](context-budget-policy.md) for bounded context and artifact-first loading
- [`README.md`](../../README.md) for the top-level workflow orientation (docs index at [`../index.md`](README.md))
- [`AGENTS.md`](../../AGENTS.md) for repo-wide operational guidance
- [`docs/guides/best-practices.md`](../guides/best-practices.md) for day-to-day routing and cost guidance
- [Cursor Router](https://cursor.com/docs/cursor-router) for live Auto Optimize For / SDK `auto-smart` product docs
