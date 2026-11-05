# M5 — MAO blocked-bundle reassessment (evidence record)

**Status:** Recorded (docs/evidence only)  
**Slice:** M5 — MAO blocked-bundle reassessment  
**Access window (UTC):** 2026-10-19  
**Related:** [`docs/reference/decision-record.md`](../decision-record.md) (Unblock condition unchanged), [`ROADMAP.md`](../../ROADMAP.md#blocked-by-product--runtime-limitations)

## Three-item MAO blocked bundle (unchanged claims)

Per [`ROADMAP.md` § Blocked by Product / Runtime Limitations](../../ROADMAP.md#blocked-by-product--runtime-limitations):

1. **Live authoritative MAO / Cursor todo parity** — authoritative live Cursor todo truth in the observability dashboard (hook-derived observed todo activity and advisory MAO transitions remain non-authoritative).
2. **Hook-driven subagent auto-spawn from live todo state** — parent evaluation/CLI and advisory `verifier-autostart-intent.json` are not live-todo dispatch; auto-spawn from purported live todo truth stays blocked.
3. **Any claim of live authoritative MAO todo state** — out of scope until product evidence changes.

## Official sources reviewed

| # | URL | Accessed (UTC) | Sections / focus | Finding vs unblock criteria |
|---|-----|----------------|------------------|----------------------------|
| 1 | https://cursor.com/docs/agent/hooks | 2026-10-19 | Overview; `postToolUse` input (`tool_name`, `tool_input`, `tool_output`, `cwd`, `duration`, …); hook event list | Documents **post-execution** hook payloads for tools (including generic tool hooks). **No** documented external **read** or **subscribe** API for live Cursor todo state. `postToolUse` does not expose an authoritative todo query surface for third-party dashboards. **Unblock not met.** |
| 2 | https://cursor.com/docs/cli/acp | 2026-10-19 | Cursor extension methods; `cursor/update_todos`; `cursor/task` | `cursor/update_todos` is a **client notification** (fire-and-forget) to update the **ACP client's** todo list (`merge` flag); not a documented global editor read/replay API. `cursor/task` is a **notification** about subagent task completion (`description`, `prompt`, `subagentType`, optional `agentId`/`durationMs`) — **not** an external spawn RPC for orchestrators. **Unblock not met** for authoritative parity or hook-driven live-todo auto-spawn. |
| 3 | https://cursor.com/docs/agent/subagents | 2026-10-19 | How subagents work; foreground/background; custom `.cursor/agents/` | Subagents are **delegated by the parent Agent** (Task tool / product UI). Docs describe context isolation and parallel work; **no** documented API for hooks or external services to spawn subagents from live todo mutations. **Auto-spawn from live todo state not met.** |
| 4 | https://cursor.com/changelog | 2026-10-19 | Index scan Jul 2026–Oct 2026 (Projects, cloud agents, Environments API, Origin marketplace, Rollouts, remote control, canvases) | **No** changelog entry announcing an external authoritative todo read/subscribe API, hook-accessible live todo mirror, or hook-driven subagent dispatch from todo state since **2026-07-01**. Adjacent features (Projects coordinator, cloud agents, subscriptions) do not satisfy [`decision-record` unblock condition](../decision-record.md#unblock-condition-for-true-parity). **Unblock not met.** |

**Product version note:** This pass is documentation-based; no new operator-machine G4–G7 measurement audit was run in this slice.

## Unblock criteria mapping

| Criterion (decision record) | Result (2026-10-19) |
|-----------------------------|---------------------|
| Documented read endpoint for **authoritative** todo state | **Not found** in hooks or ACP docs reviewed |
| Documented subscription/stream for **authoritative** todo changes | **Not found** |
| Stable guarantees (UI + tool coverage, ordering, latency) suitable for live dashboard parity | **Not documented** |
| External mechanism for hook/dashboard to consume authoritative live todos | **Not documented** |
| Hook-driven subagent auto-spawn from live todo truth | **Still blocked** — `cursor/task` is notification-only; subagent spawn remains parent/product-owned |

## G4–G7 measurement arms

Per slice non-goals: **G4–G7** checkbox state in `docs/archive/mao-advisory-go-criteria.md` (MAT source archive; not sidecar-packaged) and the decision record **unchanged** — no new dated live-operator measurement audit filed in this slice. Status: **deferred / INCONCLUSIVE** for fresh measurement; prior sustaining checks (G1–G3) remain documented in-repo without implying new runtime proof.

## Repo cross-check (`mao_gate.py`)

Read-only review of [`.cursor/hooks/mao_gate.py`](../../.cursor/hooks/mao_gate.py) on HEAD: module docstrings and helpers state **file handoffs remain authoritative**; hooks **do not** call `TodoWrite` or spawn subagents; gate/downstream readiness and todo-write observation are **advisory**. **No doc/code contradiction** requiring a code change for M5.

## Conclusion

**The three-item MAO blocked bundle remains Blocked** as of **2026-10-19**. Official Cursor documentation reviewed above does not introduce an externally supported authoritative todo read/subscribe capability or hook-driven live-todo subagent dispatch. MAT should continue file-based MAO orchestration, parent-owned transitions, and advisory hook/dashboard visibility only — **no live authoritative todo parity claims**.
