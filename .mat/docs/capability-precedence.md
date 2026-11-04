# Project-first capability routing (MAT v1)

- **Purpose:** Define **MAT’s routing and precedence policy** — how MAT **coexists** with project-local, MAT-packaged, plugin, and global Cursor capabilities without becoming a second orchestrator.
- **Audience:** Operators, integrators, and agents working in mixed environments (global skills, project rules, marketplace plugins, adopted `.mat/` sidecars).
- **Status:** complete — stable project-first precedence policy. This is **MAT workflow guidance**; it does **not** enforce Cursor’s actual asset-loading or rules-merge behavior (see [Relationship to Cursor’s rules system](#relationship-to-cursors-rules-system)).
- **Last updated:** 2026-09-15

## Why this exists

Repositories often have **several** capability sources at once: checked-in `.cursor/` assets, a **`.mat/`** sidecar after adoption, user-global skills, and plugin-provided commands or MCP servers. MAT’s **orchestration** story stays file-handoff-centric; this document adds a **single** explicit policy for *which guidance should win* for **repo-specific** behavior.

MAT does **not** replace Cursor’s native resolution for skills or plugins. It **documents** expected operator and agent behavior: prefer what the **repository** declares before generic defaults.

For MAT's conservative routing tiers and cost-aware policy, see [`model-routing-policy.md`](model-routing-policy.md); it stays separate from runtime loading and any future adapter boundary. For **bounded context** (what agents should load by default), see [`context-budget-policy.md`](context-budget-policy.md).

## Relationship to Cursor’s rules system

Cursor’s product documentation describes **rules precedence for the Agent (Chat)** as **Team Rules → Project Rules → User Rules**, with **earlier sources taking precedence** when rules conflict. That is **Cursor’s** merge order — MAT does not reimplement or override it.

MAT’s numbered list below is **MAT’s own policy** for orchestration and repo workflow: prefer **checked-in project** `.cursor/` and root `AGENTS.md` for **repo-specific** MAT behavior before **user-global** defaults. That is **directionally aligned** with treating **Project Rules** as more authoritative than **User Rules** for work in this repository, but MAT must not claim **identity** with Cursor’s engine. **Team Rules** (organization-level) may still apply first in Cursor — treat that as consistent with the “Higher-priority constraints” paragraph under [Precedence (highest first)](#precedence-highest-first) (policy and safety outrank convenience).

**Authoritative for MAT workflow** remains the canonical **file handoffs** (`docs/current-plan.md`, `build-result.md`, `verify-result.md`, MAO protocol). **Advisory** remains hook/gate artifacts and this routing doc for **human/agent** choices — not a second runtime source of truth.

## Precedence (highest first)

Use this order when deciding **what applies to workflow and repo-specific behavior** in this working tree:

1. **Project-local repo guidance** — Files under **`.cursor/`** (for example `rules/`, `commands/`, `agents/`, `skills/`, `mcp.json`, `hooks.json`) and the repo’s root **`AGENTS.md`** (product narrative). Executable **`scripts/`** at repo root are part of project-native automation when present.
2. **Repo-local MAT reference (`.mat/` sidecar)** — Packaged MAT manuals, `.mat/AGENTS.mat.md`, and `.mat/docs/` in **adopted** repos. This is **MAT reference and parity** with upstream; it does **not** silently override active project `.cursor/` policy. Teams may merge or mirror deliberately.
3. **Plugin-provided** capabilities — Skills, rules, agents, commands, or MCP integrations from Cursor plugins. Use when they add value; treat them as **subordinate** to checked-in project policy when the **same concern** is defined in-repo (project wins for repo-specific behavior).
4. **Global / user-level** skills, rules, and commands — Generic fallbacks when the repo does not define a local override.

**Higher-priority constraints:** Platform, organizational, or **safety** policies (for example security rules mandated by IT, or blocking hooks) outrank convenience defaults. MAT does not define those systems; agents must obey them when they apply.

## Capability discovery

- **Filesystem-first:** If it exists under **`.cursor/`** in the repo, it is a **declared** project capability for this codebase.
- **MAT sidecar:** After adoption, look under **`.mat/docs/`** and **`.mat/AGENTS.mat.md`** for full MAT reference without merging it blindly into product docs. Product-owned `AGENTS.md` files keep a small pointer note only; nested or monorepo `AGENTS.md` files are treated the same way and point back to the repo-root sidecar relative to their own location.
- **No deep stack inference in MAT core:** Framework-specific behavior (WordPress, Next.js + Sanity, Python, and so on) should be expressed with **project-local** rules, skills, and commands — not with a large MAT profile matrix.
- **Optional machine-readable manifests** (for example a `capabilities` JSON under `.mat/`) are **deferred** to a later slice; v1 is documentation and conventions only.

## Routing narrative (agents and operators)

- **Prefer project-native** slash commands, agents, and rules when names exist under **`.cursor/`** — they encode **this repo’s** contract.
- **Use MAT defaults** from this repository (or `.mat/` copies) when describing orchestration patterns (parent/mat-builder/verifier, MAO handoffs) that are not overridden locally.
- **Global and plugin** capabilities are acceptable **fallbacks** for generic tasks (formatting helpers, broad skills) when they do not contradict checked-in project rules.
- **MCP and tools:** Project **`.cursor/mcp.json`** (or equivalent) describes servers for **this** repo; document required servers in `AGENTS.md` or README when they are part of the team contract. MCP stays optional and advisory — operator security posture in [`docs/security/mcp.md`](../security/mcp.md).

## Conflict rule

When **project-local** guidance disagrees with **global or plugin** defaults on **repo-specific** behavior, **project-local wins**. Resolve residual ambiguity deliberately (human review or explicit rule updates). When **safety or platform** policy conflicts with a repo convention, **safety/platform** wins.

MAT remains **additive**: it does not intercept tool calls or maintain a parallel orchestration state.

## Doctor diagnostic

Advisory operator scan for locally observable rule/guidance collisions (not a Cursor merge simulator):

```bash
bash scripts/doctor.sh --rules-precedence
# or: make doctor-rules
```

- **Scanner:** `scripts/rules_precedence_diagnostic.py` — reads project `.cursor/rules/*.mdc`, root/nested `AGENTS.md` (depth-limited), `.mat/` pointer files when present, and best-effort `~/.cursor/plugins/cache/**/mat-workflow/**/rules/*.mdc`.
- **Limits:** Dashboard **Team Rules** and most **User Rules** are **not** readable from the repo; the report always emits an `INFO` for that gap. The scanner does **not** override Team Rules, fail CI on collisions, or claim identity with Cursor’s Team → Project → User merge order.
- **Artifact:** gitignored `artifacts/doctor/rules-precedence-last.json` (plus optional `report-events.jsonl` append). Exit 0 unless the process crashes.
- **Policy reference:** this document; maintainer note in [`MAINTAINER.md`](MAINTAINER.md#project-first-capability-routing).

## Authoritative vs advisory

| Kind | Role |
|------|------|
| **Authoritative (workflow truth)** | Canonical handoff files such as **`docs/current-plan.md`**, **`build-result.md`**, **`verify-result.md`**, and (when used) **`docs/architecture/long-run-state.md`** — plus MAO parent-owned transitions as documented. |
| **Advisory** | Hook-written **`artifacts/mao/gate.json`**, downstream readiness snapshots, todo-write observations, plugin hints — useful for preflight, **not** a substitute for reading handoff files. |
| **Routing / discovery (this doc)** | **Advisory policy** for choosing which repo-local vs global capabilities to trust first; Cursor’s runtime remains the implementation of last resort for what loads where. |

## Compatibility

- **Product-first `.mat/` adoption:** Root `AGENTS.md` stays product-owned; `.mat/` holds extended MAT reference, and the adoption helper manages the small pointer note or explicit inline fallback without overwriting product text — see [getting-started-new-projects.md](../guides/getting-started-new-projects.md) and [getting-started-existing-projects.md](../guides/getting-started-existing-projects.md).
- **Upstream MAT development repo:** May have no `.mat/` sidecar; precedence still applies to **`.cursor/`** and root **`AGENTS.md`**.

## Related

- [AGENTS.md](../../AGENTS.md) — agent roles, MAO, roadmap
- [model-routing-policy.md](model-routing-policy.md) — conservative MAT routing tiers and advisory budget policy
- [context-budget-policy.md](context-budget-policy.md) — bounded context and artifact-first loading discipline
- [Orchestration workflow](orchestration-workflow.md)
- [Todo orchestration protocol](todo-orchestration-protocol.md)
- [specs/project-first-capability-router-v1.md](../../specs/project-first-capability-router-v1.md) — planning source
