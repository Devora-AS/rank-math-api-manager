import os
import re
import unittest
from pathlib import Path


def _repo_root() -> Path:
    """Resolve repo root whether tests live in tests/ or .mat/tests/ (adopted repos)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / ".cursor" / "hooks.json").is_file():
            return parent
    return here.parents[1]


REPO_ROOT = _repo_root()


def _resolve_path(rel_path: str) -> Path:
    """Resolve repo-relative paths; in MAT sidecar adoptions, packaged docs live under `.mat/docs/`."""
    primary = REPO_ROOT / rel_path
    if primary.exists():
        return primary
    if rel_path.startswith("docs/"):
        sidecar = REPO_ROOT / ".mat" / rel_path
        if sidecar.exists():
            return sidecar
    return primary


def _is_mat_sidecar_adoption_layout() -> bool:
    """Prefer explicit `MAT_REPO_LAYOUT=adopted|source`; else detect `.mat/AGENTS.mat.md` (bootstrap sidecar)."""
    env = os.environ.get("MAT_REPO_LAYOUT", "").strip().lower()
    if env == "source":
        return False
    if env == "adopted":
        return True
    return (REPO_ROOT / ".mat" / "AGENTS.mat.md").is_file()


def _read(rel_path: str) -> str:
    return _resolve_path(rel_path).read_text(encoding="utf-8")


def _exists(rel_path: str) -> bool:
    return _resolve_path(rel_path).exists()


class WorkflowCommandDocsTest(unittest.TestCase):
    def test_plan_and_plan_onboarding_command_docs_exist_with_core_guardrails(self):
        if not _exists("docs/guides/planning-commands-guide.md"):
            self.skipTest("planning commands guide not present in this trimmed fixture")

        plan = _read(".cursor/commands/mat-plan.md")
        plan_onboarding = _read(".cursor/commands/mat-plan-onboarding.md")
        planning_guide = _read("docs/guides/planning-commands-guide.md")

        self.assertIn("# MAT Plan", plan)
        self.assertIn("/mat-plan <task description>", plan)
        self.assertIn("Planning only — no implementation.", plan)
        self.assertIn("specs/<slug>.md", plan)
        self.assertIn("solo_plan_only", plan)
        self.assertIn("ready_for_execution_handoff", plan)
        self.assertIn("needs_plan_onboarding", plan)
        self.assertIn("Recommended Next Command", plan)
        self.assertIn("Do not reuse `/mat-plan-team` execution-mode terms", plan)
        self.assertIn("docs/reference/capability-precedence.md", plan)

        self.assertIn("# MAT Plan Onboarding", plan_onboarding)
        self.assertIn("/mat-plan-onboarding <task description>", plan_onboarding)
        self.assertIn(
            "mat-plan-onboarding requires mandatory artifact package: specs/<slug>/prd.md, specs/<slug>/spec.md, specs/<slug>/tasks.json, specs/<slug>/plan-summary.md.",
            plan_onboarding,
        )
        self.assertIn(
            "Each task in tasks.json must trace to spec.md and PRD IDs; spec.md must trace back to prd.md.",
            plan_onboarding,
        )
        self.assertIn(
            "tasks.json must include a per-task execution status field so approved slices can stay aligned with real progress.",
            plan_onboarding,
        )
        self.assertIn("Human approval gate required before any execution handoff.", plan_onboarding)
        self.assertIn(
            "Do not replace docs/current-plan.md with onboarding artifacts; use plan-summary.md to instruct projection.",
            plan_onboarding,
        )
        self.assertIn("docs/reference/capability-precedence.md", plan_onboarding)
        self.assertIn("### Task Status Sync Contract", plan_onboarding)
        self.assertIn("### Guided Discovery Questions", plan_onboarding)
        self.assertIn(
            "After drafting the onboarding package, scan `specs/<slug>/prd.md`, `specs/<slug>/spec.md`, and `specs/<slug>/plan-summary.md` for unresolved open questions before the approval gate.",
            plan_onboarding,
        )
        self.assertIn(
            "Ask unresolved questions in the chat one at a time; after each answer, update the relevant artifact(s) and keep `plan-summary.md` in sync.",
            plan_onboarding,
        )
        self.assertIn(
            "If the user declines to answer, record that explicitly as an open or deferred question in the artifacts before presenting the final approval gate.",
            plan_onboarding,
        )

        self.assertIn("/mat-plan-onboarding", planning_guide)
        self.assertIn("`specs/` is upstream planning truth.", planning_guide)
        self.assertIn("Projection is human/operator-owned", planning_guide)
        self.assertIn("Project one approved execution slice at a time into `docs/current-plan.md`.", planning_guide)
        self.assertIn("if both `specs/<slug>.md` and `specs/<slug>/` exist, the folder package is authoritative", planning_guide)
        self.assertIn("surface unresolved open questions in chat before approval", planning_guide.lower())
        self.assertIn("one question at a time", planning_guide.lower())

    def test_plan_onboarding_templates_and_specimen_lock_traceability_contract(self):
        if not all(
            _exists(path)
            for path in (
                "docs/templates/spec-template.md",
                "docs/templates/tasks-schema.json",
                "specs/plan-and-plan-onboarding-v1/spec.md",
                "specs/plan-and-plan-onboarding-v1/tasks.json",
                "specs/plan-and-plan-onboarding-v1/plan-summary.md",
                "specs/plan-and-plan-onboarding-v1.md",
            )
        ):
            self.skipTest("plan_onboarding templates/specimen not present in this trimmed fixture")

        spec_template = _read("docs/templates/spec-template.md")
        schema = _read("docs/templates/tasks-schema.json")
        specimen_spec = _read("specs/plan-and-plan-onboarding-v1/spec.md")
        specimen_prd = _read("specs/plan-and-plan-onboarding-v1/prd.md")
        specimen_tasks = _read("specs/plan-and-plan-onboarding-v1/tasks.json")
        specimen_summary = _read("specs/plan-and-plan-onboarding-v1/plan-summary.md")
        planning_spec = _read("specs/plan-and-plan-onboarding-v1.md")

        self.assertIn("Stable spec section IDs", spec_template)
        self.assertIn("Use `SPEC-001`, `SPEC-002`, ...", spec_template)
        self.assertIn("Every implementation-significant design section must declare its own `SPEC-###` identifier.", spec_template)
        self.assertIn("TASK-###", spec_template)

        self.assertIn('"const": "plan_onboarding"', schema)
        self.assertNotIn('"plan"', schema)
        self.assertIn('"pattern": "^SPEC-[0-9]{3}$"', schema)
        self.assertIn('"status"', schema)
        self.assertIn('"planned"', schema)
        self.assertIn('"in_progress"', schema)
        self.assertIn('"done"', schema)
        self.assertIn('"blocked"', schema)
        self.assertIn('"deferred"', schema)
        self.assertIn('"status_note"', schema)
        self.assertIn('"last_updated"', schema)

        self.assertIn("### `SPEC-001`", specimen_spec)
        self.assertIn("### `SPEC-002`", specimen_spec)
        self.assertIn("### `SPEC-003`", specimen_spec)
        self.assertIn("### `SPEC-005`", specimen_spec)
        self.assertIn('"spec_ids": [', specimen_tasks)
        self.assertIn('"SPEC-001"', specimen_tasks)
        self.assertIn('"SPEC-002"', specimen_tasks)
        self.assertIn('"SPEC-003"', specimen_tasks)
        self.assertIn('"SPEC-005"', specimen_tasks)
        self.assertIn('"status": "planned"', specimen_tasks)
        self.assertIn('"FR-005"', specimen_tasks)
        self.assertIn('"AC-005"', specimen_tasks)
        self.assertIn("Status: `open | resolved | deferred`", spec_template)

        self.assertIn("Manual projection into `docs/current-plan.md`.", specimen_summary)
        self.assertIn("Only after that projection step should the operator choose `/mat-plan-team` or `/mat-long-run`", specimen_summary)
        self.assertIn("Open questions must be surfaced in chat before approval.", specimen_summary)
        self.assertIn("Projection into `docs/current-plan.md` is human-owned and happens only after written approval.", planning_spec)
        self.assertIn("If both exist, `specs/<slug>/` is authoritative", planning_spec)
        self.assertIn("keep approved task execution status in sync with the active slice", planning_spec)
        self.assertIn("approved execution slices need a deterministic `TASK-###` mapping back to `tasks.json`", specimen_prd)

    def test_sprint_and_lite_command_files_exist_with_core_guardrails(self):
        sprint = _read(".cursor/commands/mat-sprint.md")
        lite = _read(".cursor/commands/mat-lite.md")
        long_run = _read(".cursor/commands/mat-long-run.md")
        subagents_spawn = _read(".cursor/commands/mat-subagents-spawn.md")
        long_run_state = _read("docs/architecture/long-run-state.md")

        self.assertIn("mission_complete", long_run_state)
        self.assertIn("planning_gap", long_run_state)

        self.assertIn("# MAT Long Run", long_run)
        self.assertIn("/mat-long-run <mission description>", long_run)
        self.assertIn("docs/architecture/long-run-state.md", long_run)
        self.assertIn("post-slice mission gate", long_run)
        self.assertIn("planning_gap", long_run)

        self.assertIn("# MAT Subagents Spawn", subagents_spawn)
        self.assertIn("/mat-subagents-spawn <task description>", subagents_spawn)
        self.assertIn("Honesty guardrails", subagents_spawn)
        self.assertIn("wait-before-supersede", subagents_spawn.lower())

        self.assertIn("# MAT Sprint", sprint)
        self.assertIn("/mat-sprint <task description>", sprint)
        self.assertIn("Define a short DoR before editing", sprint)
        self.assertIn("Preflight decision", sprint)
        self.assertIn("builder_plus_verifier", sprint)
        self.assertIn("Onboarding slice sync", sprint)
        self.assertIn("Do not commit unless the user explicitly asks", sprint)
        self.assertIn("Run at least one concrete verification step", sprint)

        self.assertIn("# MAT Lite", lite)
        self.assertIn("/mat-lite <task description>", lite)
        self.assertIn("git diff --check", lite)
        self.assertIn(
            "If the task grows beyond a small bounded change, switch to `/mat-sprint`, `/mat-plan-team`, or `/mat-long-run`",
            lite,
        )
        self.assertIn("Do not commit unless the user explicitly asks for it.", lite)

    def test_command_and_agent_inventories_reference_new_surfaces(self):
        if _is_mat_sidecar_adoption_layout():
            self.skipTest(
                "MAT sidecar adoption uses product-first root; full tables live in .mat/AGENTS.mat.md"
            )
        agents = _read("AGENTS.md")
        readme = _read("README.md")
        components = _read("docs/reference/components.md")
        docs_index = _read("docs/index.md") if _exists("docs/index.md") else ""
        usage = _read("docs/guides/usage-examples-and-cases.md") if _exists("docs/guides/usage-examples-and-cases.md") else ""
        best_practices = _read("docs/guides/best-practices.md") if _exists("docs/guides/best-practices.md") else ""

        self.assertIn("| `/mat-long-run <task>` | Queued multi-slice mission with `docs/architecture/long-run-state.md` and post-slice mission gate |", agents)
        self.assertIn("| `/mat-subagents-spawn <task>` | Decompose work and run parallel Task subagents (parent integrates results; see command doc) |", agents)
        self.assertIn("| `/mat-sprint <task>` | Execute one bounded slice with DoR, implementation, verification, and review |", agents)
        self.assertIn("| `/mat-lite <task>` | Run a lightweight docs/config/quality pass without the full orchestration flow |", agents)
        self.assertIn(
            "| `/mat-plan <task>` | Lightweight solo planning — writes one file: `specs/<slug>.md`; optional `--depth=` thin router to other commands |",
            agents,
        )
        self.assertIn(
            "| `/mat-plan-onboarding <task>` | Heavyweight planning-only onboarding — writes the four-file package under `specs/<slug>/` |",
            agents,
        )
        self.assertIn("| `/mat-wt-check` | Run worktree health and collision checks |", agents)
        self.assertIn("| `/mat-doctor` | Run local diagnostics for workflow readiness |", agents)
        self.assertIn("internal/reference-oriented", agents)
        self.assertIn("not a public packaging target by default", agents)

        self.assertIn("| `/mat-long-run` | Queued multi-slice mission (`docs/architecture/long-run-state.md`, mission gate) |", readme)
        self.assertIn("| `/mat-subagents-spawn` | Parallel Task subagent fan-out with parent integration (see `.cursor/commands/mat-subagents-spawn.md`) |", readme)
        self.assertIn("| `/mat-sprint` | Run one bounded slice end-to-end |", readme)
        self.assertIn("| `/mat-lite` | Run a lightweight docs/config/quality pass |", readme)
        self.assertIn(
            "| `/mat-plan` | Lightweight solo planning — writes one file: `specs/<slug>.md`; optional `--depth=` alias router to other commands |",
            readme,
        )
        self.assertIn(
            "| `/mat-plan-onboarding` | Heavyweight planning-only onboarding — writes the four-file package under `specs/<slug>/` |",
            readme,
        )
        self.assertIn("| `/mat-wt-check` | Run worktree health checks |", readme)
        self.assertIn("| `/mat-doctor` | Run operator diagnostics |", readme)
        self.assertIn("| `test-writer` | Adds focused regression coverage |", readme)
        self.assertIn("| `style-reviewer` | Aligns docs/inventories and removes overclaims |", readme)
        self.assertIn("/mat-plan-onboarding", readme)
        self.assertIn("internal/reference-oriented workflow repo for the maintainer team", readme)
        self.assertIn("not a public packaging target by default", readme)

        self.assertIn(".cursor/commands/mat-plan.md", components)
        self.assertIn(".cursor/commands/mat-plan-onboarding.md", components)
        self.assertIn("docs/guides/planning-commands-guide.md", components)
        self.assertIn(".cursor/commands/mat-long-run.md", components)
        self.assertIn(".cursor/commands/mat-subagents-spawn.md", components)
        self.assertIn("/mat-sprint", _read(".cursor/commands/mat-sprint.md"))
        self.assertIn("/mat-lite", _read(".cursor/commands/mat-lite.md"))
        self.assertIn(".cursor/agents/test-writer.md", components)
        self.assertIn(".cursor/agents/style-reviewer.md", components)
        self.assertIn("internal/reference-oriented", components)

        if docs_index:
            self.assertIn("[planning-commands-guide.md](guides/planning-commands-guide.md)", docs_index)
            self.assertIn("[capability-precedence.md](reference/capability-precedence.md)", docs_index)
        if usage:
            self.assertIn("/mat-plan-onboarding", usage)
            self.assertIn("/mat-plan", usage)
        if best_practices:
            self.assertIn("/mat-plan-onboarding", best_practices)
            self.assertIn("planning truth in `specs/`", best_practices)

    def test_capability_precedence_policy_doc_locks_project_first_routing(self):
        if not _exists("docs/reference/capability-precedence.md"):
            self.skipTest("capability-precedence doc not present in this trimmed fixture")
        cap = _read("docs/reference/capability-precedence.md")
        self.assertIn("# Project-first capability routing (MAT v1)", cap)
        self.assertIn("routing and precedence policy", cap)
        self.assertIn("## Relationship to Cursor", cap)
        self.assertIn("Team Rules", cap)
        self.assertIn("## Precedence (highest first)", cap)
        self.assertIn("## Capability discovery", cap)
        self.assertIn("## Conflict rule", cap)
        self.assertIn("## Authoritative vs advisory", cap)
        self.assertIn("project-local", cap.lower())
        self.assertIn(".mat/", cap)
        self.assertIn("Plugin-provided", cap)
        self.assertIn("Global / user-level", cap)
        self.assertIn("docs/current-plan.md", cap)
        self.assertIn("artifacts/mao/gate.json", cap)
        readme = _read("README.md")
        self.assertIn("docs/reference/capability-precedence.md", readme)
        maintainer = _read("docs/reference/MAINTAINER.md")
        self.assertIn("capability-precedence.md", maintainer)
        components = _read("docs/reference/components.md")
        self.assertIn("capability-precedence.md", components)
        if not _is_mat_sidecar_adoption_layout():
            agents = _read("AGENTS.md")
            self.assertIn("docs/reference/capability-precedence.md", agents)

    def test_model_routing_policy_doc_locks_conservative_adapter_agnostic_policy(self):
        required = (
            "docs/reference/model-routing-policy.md",
            "docs/reference/context-budget-policy.md",
            "docs/schemas/mat-routing-advisory.example.json",
            "README.md",
            "AGENTS.md",
            "docs/index.md",
            "docs/reference/components.md",
            "docs/guides/best-practices.md",
            "docs/reference/MAINTAINER.md",
            "docs/reference/capability-precedence.md",
            ".cursor/agents/parent-orchestrator.md",
            ".cursor/commands/mat-plan-team.md",
            ".cursor/agents/builder.md",
            ".cursor/agents/verifier.md",
            ".cursor/commands/mat-sprint.md",
            ".cursor/commands/mat-long-run.md",
        )
        if not all(_exists(path) for path in required):
            self.skipTest("model routing policy docs not present in this trimmed fixture")

        policy = _read("docs/reference/model-routing-policy.md")
        context_budget = _read("docs/reference/context-budget-policy.md")
        advisory_example = _read("docs/schemas/mat-routing-advisory.example.json")
        readme = _read("README.md")
        agents = _read("AGENTS.md")
        docs_index = _read("docs/index.md")
        components = _read("docs/reference/components.md")
        best_practices = _read("docs/guides/best-practices.md")
        maintainer = _read("docs/reference/MAINTAINER.md")
        cap = _read("docs/reference/capability-precedence.md")
        orchestrator = _read(".cursor/agents/parent-orchestrator.md")
        plan_w_team = _read(".cursor/commands/mat-plan-team.md")
        builder = _read(".cursor/agents/builder.md")
        verifier = _read(".cursor/agents/verifier.md")
        sprint = _read(".cursor/commands/mat-sprint.md")
        long_run = _read(".cursor/commands/mat-long-run.md")

        self.assertIn("# MAT routing policy v1", policy)
        self.assertIn("cheap", policy)
        self.assertIn("standard", policy)
        self.assertIn("strong", policy)
        self.assertIn("multimodal", policy)
        self.assertIn("adapter-agnostic", policy)
        self.assertIn("does not depend on `agent-model-router`", policy)
        self.assertIn("does not describe undocumented Cursor alias-style frontmatter behavior", policy)
        # Cursor Router grounding (S1-router; live docs 2026-08-31)
        self.assertIn("https://cursor.com/docs/cursor-router", policy)
        self.assertIn("Teams and Enterprise", policy)
        self.assertIn("Optimize For", policy)
        self.assertIn("Cost", policy)
        self.assertIn("Balance", policy)
        self.assertIn("Intelligence", policy)
        self.assertIn("auto-smart", policy)
        self.assertIn("optimize_for", policy)
        self.assertIn("`cost`", policy)
        self.assertIn("`balanced`", policy)
        self.assertIn("`intelligence`", policy)
        self.assertIn("Hidden", policy)
        self.assertIn("Grok", policy)
        self.assertIn("MAT does not own Cursor", policy)
        self.assertIn("must not depend on", policy)
        self.assertIn("underlying model", policy)
        self.assertIn("Advisory MAT tier", policy)
        self.assertIn("Automations", policy)
        self.assertIn("ACP", policy)
        self.assertIn("Last updated: 2026-08-31", policy)
        self.assertIn("Telemetry in this slice is advisory only.", policy)
        self.assertIn("provider", policy)
        self.assertIn("routing_reason", policy)
        self.assertIn("context_pressure", policy)
        self.assertIn("session_id", policy)
        self.assertIn("timestamp", policy)
        self.assertIn("The `signal_class` stays `advisory`", policy)
        self.assertIn("artifacts/mao/routing-advisory.jsonl", policy)
        self.assertIn("routing_rollup_<session_id>.json", policy)
        self.assertIn("scripts/analyze_routing_advisory.py", policy)
        self.assertIn("deferred adapter boundary", policy)
        self.assertIn("Where MAT surfaces routing telemetry", policy)
        self.assertIn("Authoritative vs advisory (routing context)", policy)
        self.assertIn("schemas/mat-routing-advisory.example.json", policy)
        self.assertIn("docs/reference/context-budget-policy.md", policy)
        self.assertIn("source_hook", policy)
        self.assertIn("session_id", policy)
        self.assertIn("timestamp", policy)
        self.assertIn("suggested_tier", policy)
        self.assertIn("recommended_escalation", policy)
        self.assertIn("boundary_signals", policy)
        self.assertIn("70 percent", policy)
        self.assertIn("6000 characters", policy)
        self.assertIn("25", policy)

        self.assertIn("# MAT context budget policy v1", context_budget)
        self.assertIn("bounded context", context_budget.lower())
        self.assertIn("artifact-first", context_budget.lower())
        self.assertIn("Soft context-pressure signals", context_budget)
        self.assertIn("Pre-compact / large prompt payloads", context_budget)
        self.assertIn("boundary_signals", context_budget)
        self.assertIn("70 / 6000 / 25", context_budget)
        self.assertIn("Parent orchestrator", context_budget)
        self.assertIn("README.md", context_budget)
        self.assertIn("ROADMAP.md", context_budget)
        self.assertIn("AGENTS.md", context_budget)
        self.assertIn("prompt_lint_<session_id>.log", context_budget)
        self.assertIn("CURSOR_MAT_SESSION_BUDGET_USD", context_budget)
        self.assertIn("never block execution", context_budget)

        self.assertIn("mat_routing_advisory_version", advisory_example)
        self.assertIn('"source_hook"', advisory_example)
        self.assertIn('"timestamp"', advisory_example)
        self.assertIn('"session_id"', advisory_example)
        self.assertIn('"provider"', advisory_example)
        self.assertIn('"routing_tier"', advisory_example)
        self.assertIn('"routing_reason"', advisory_example)
        self.assertIn('"suggested_tier"', advisory_example)
        self.assertIn('"recommended_escalation"', advisory_example)
        self.assertIn("budget_note", advisory_example)
        self.assertIn('"context_pressure"', advisory_example)
        self.assertIn('"payload_size_chars"', advisory_example)
        self.assertIn('"payload_size_bytes"', advisory_example)
        self.assertIn('"retry_count"', advisory_example)
        self.assertIn('"boundary_signals"', advisory_example)
        self.assertIn('"input_tokens"', advisory_example)
        self.assertIn("signal_class", advisory_example)
        self.assertIn("advisory", advisory_example)
        self.assertIn("non_authoritative", advisory_example)

        self.assertIn("Model routing policy", readme)
        self.assertIn("cheap` / `standard` / `strong` policy", readme)
        self.assertIn("routing rollups", readme)
        self.assertIn("prompt lint warnings", readme)
        self.assertIn("session budget notes", readme)
        self.assertIn("representative baselines", readme)
        self.assertIn("docs/reference/model-routing-policy.md", readme)
        self.assertIn("Context budget", readme)
        self.assertIn("docs/reference/context-budget-policy.md", readme)

        self.assertIn("docs/reference/model-routing-policy.md", agents)
        self.assertIn("adapter-agnostic", agents)
        self.assertIn("routing_rollup_<session_id>.json", agents)
        self.assertIn("scripts/analyze_routing_advisory.py", agents)
        self.assertIn("prompt lint warnings", agents)
        self.assertIn("session budget notes", agents)
        self.assertIn("docs/reference/context-budget-policy.md", agents)

        self.assertIn("model-routing-policy.md", docs_index)
        self.assertIn("Conservative MAT routing tiers", docs_index)
        self.assertIn("routing_advisory.md", docs_index)
        self.assertIn("session rollups", docs_index)
        self.assertIn("context-budget-policy.md", docs_index)
        self.assertIn("operational baseline", docs_index)

        self.assertIn("Routing policy", components)
        self.assertIn("docs/reference/model-routing-policy.md", components)
        self.assertIn("routing_advisory.md", components)
        self.assertIn("session rollups", components)
        self.assertIn("context-budget-policy.md", components)
        self.assertIn("routing advisories", components)

        self.assertIn("model-routing-policy.md", best_practices)
        self.assertIn("routing telemetry, rollups, and budget notes are advisory, not workflow truth", best_practices)
        self.assertIn("analyze_routing_advisory.py", best_practices)
        self.assertIn("missing `build-result.md` or `verify-result.md`", best_practices)
        self.assertIn("context-budget-policy.md", best_practices)
        self.assertIn("routing-advisory.jsonl", best_practices)
        self.assertIn("routing_rollup_<session_id>.json", best_practices)
        self.assertIn("prompt lint warnings", best_practices)
        self.assertIn("session budget notes", best_practices)
        self.assertIn("context_pressure_rate", best_practices)
        self.assertIn("closeout validation", best_practices)

        self.assertIn("docs/reference/model-routing-policy.md", maintainer)
        self.assertIn("adapter boundary optional", maintainer)
        self.assertIn("routing_rollup_<session_id>.json", maintainer)
        self.assertIn("analyze_routing_advisory.py", maintainer)
        self.assertIn("generate_fixture_from_session.sh", maintainer)
        self.assertIn("context-budget-policy.md", maintainer)
        self.assertIn("CURSOR_MAT_ROUTING_ADVISORY_JSONL", maintainer)
        self.assertIn("CURSOR_MAT_ROUTING_ADVISORY_ROLLUP", maintainer)
        self.assertIn("CURSOR_MAT_SESSION_BUDGET_USD", maintainer)
        self.assertIn("prompt warnings", maintainer)

        self.assertIn("model-routing-policy.md", cap)
        self.assertIn("conservative MAT routing tiers and advisory budget policy", cap)
        self.assertIn("context-budget-policy.md", cap)

        self.assertIn("docs/reference/model-routing-policy.md", orchestrator)
        self.assertIn("do not invent Cursor alias behavior as a MAT contract", orchestrator)
        self.assertIn("docs/reference/context-budget-policy.md", orchestrator)

        self.assertIn("docs/reference/model-routing-policy.md", plan_w_team)
        self.assertIn("avoid encoding undocumented Cursor alias-style frontmatter behavior as MAT core policy", plan_w_team)
        self.assertIn("docs/reference/context-budget-policy.md", plan_w_team)

        self.assertIn("docs/reference/context-budget-policy.md", builder)
        self.assertIn("docs/reference/context-budget-policy.md", verifier)
        self.assertIn("docs/reference/context-budget-policy.md", sprint)
        self.assertIn("docs/reference/context-budget-policy.md", long_run)

    def test_artifact_contract_doc_and_prompt_examples_stay_aligned(self):
        if not _exists("docs/reference/workflow-artifact-contract.md"):
            self.skipTest("artifact contract doc not present in this trimmed fixture")
        contract = _read("docs/reference/workflow-artifact-contract.md")
        builder = _read(".cursor/agents/builder.md")
        build = _read(".cursor/commands/mat-build.md")
        verifier = _read(".cursor/agents/verifier.md")
        review = _read(".cursor/commands/mat-review.md")
        orchestrator = _read(".cursor/agents/parent-orchestrator.md")
        plan_w_team = _read(".cursor/commands/mat-plan-team.md")
        long_run = _read(".cursor/commands/mat-long-run.md")

        self.assertIn("# Workflow Artifact Contract", contract)
        self.assertIn("## Build Result Contract", contract)
        self.assertIn("## Verify Result Contract", contract)
        self.assertIn("## Closeout (YYYY-MM-DD)", contract)
        self.assertIn("Gate Evidence", contract)
        self.assertIn("Optional Gate Evidence", contract)

        for text in (builder, build):
            self.assertIn("## Closeout (YYYY-MM-DD)", text)
            self.assertIn("## Notes for Verifier", text)
            self.assertIn("docs/reference/workflow-artifact-contract.md", text)

        for text in (verifier, review):
            self.assertIn("## Criteria Review", text)
            self.assertIn("## Closeout (YYYY-MM-DD)", text)
            self.assertIn("docs/reference/workflow-artifact-contract.md", text)

        for text in (orchestrator, plan_w_team, long_run):
            self.assertIn("docs/reference/workflow-artifact-contract.md", text)

        self.assertIn("docs/reference/capability-precedence.md", orchestrator)
        self.assertIn("docs/reference/capability-precedence.md", plan_w_team)

    def test_execution_closeout_contract_and_prompt_defaults_are_explicit(self):
        required = (
            "AGENTS.md",
            "README.md",
            "docs/guides/best-practices.md",
            "docs/architecture/orchestration-workflow.md",
            "docs/architecture/mat-plan-team-spec.md",
            "docs/update-mat/role-prompt-templates.md",
            ".cursor/commands/mat-plan-team.md",
            ".cursor/commands/mat-long-run.md",
            ".cursor/commands/mat-plan-onboarding.md",
            ".cursor/commands/mat-build.md",
            ".cursor/commands/mat-review.md",
            ".cursor/agents/parent-orchestrator.md",
        )
        if not all(_exists(path) for path in required):
            self.skipTest("execution closeout contract docs not present in this trimmed fixture")

        agents = _read("AGENTS.md")
        best_practices = _read("docs/guides/best-practices.md")
        workflow = _read("docs/architecture/orchestration-workflow.md")
        spec = _read("docs/architecture/mat-plan-team-spec.md")
        plan_w_team = _read(".cursor/commands/mat-plan-team.md")
        long_run = _read(".cursor/commands/mat-long-run.md")
        plan_onboarding = _read(".cursor/commands/mat-plan-onboarding.md")
        build = _read(".cursor/commands/mat-build.md")
        review = _read(".cursor/commands/mat-review.md")
        parent = _read(".cursor/agents/parent-orchestrator.md")
        readme = _read("README.md")
        changelog = _read("CHANGELOG.md")
        roadmap = _read("ROADMAP.md")
        update_mat = _read("docs/update-mat/role-prompt-templates.md")

        self.assertIn("fenced `txt` blocks", agents)
        self.assertIn("fenced `txt` blocks", best_practices)
        self.assertIn("fenced `txt` blocks", update_mat)
        self.assertIn("execution-closeout-contract", plan_w_team)
        self.assertIn("execution-closeout-contract", long_run)
        self.assertIn("execution-closeout-contract", plan_onboarding)
        self.assertIn("execution-closeout-contract", build)
        self.assertIn("execution-closeout-contract", review)
        self.assertIn("execution-closeout-contract", readme)
        self.assertIn("execution-closeout-contract", spec)
        self.assertIn("## Execution closeout contract", workflow)
        self.assertIn("README.md", workflow)
        self.assertIn("AGENTS.md", workflow)
        self.assertIn("CHANGELOG.md", workflow)
        self.assertIn("ROADMAP.md", workflow)
        self.assertIn("Commit the final state", workflow)
        self.assertIn("Push when the handoff is meant to leave the branch shared remotely", workflow)
        self.assertIn("Confirm the working tree is clean", workflow)
        self.assertIn("validate_closeout_coherence.py", workflow)
        self.assertIn("git status --short", workflow)
        self.assertIn("CHANGELOG.md", readme)
        self.assertIn("ROADMAP.md", readme)
        self.assertIn("CHANGELOG.md", agents)
        self.assertIn("ROADMAP.md", agents)
        self.assertIn("CHANGELOG.md", best_practices)
        self.assertIn("ROADMAP.md", best_practices)
        self.assertIn("## Now", roadmap)
        self.assertIn("Maintenance Notes", roadmap)
        self.assertIn("no claim of live authoritative todo parity", roadmap)
        self.assertIn("Top-level docs and maintenance guidance", changelog)
        self.assertIn("normal startup", parent.lower())
        self.assertIn("active progress", parent.lower())
        self.assertIn("unclear state", parent.lower())
        self.assertIn("true stall/failure", parent.lower())

    def test_phase2_proof_tiers_and_closeout_gate_wording_stay_aligned(self):
        if not _exists("docs/architecture/mat-plan-team-spec.md") or not _exists("artifacts/agent-traces/README.md"):
            self.skipTest("phase2 proof-tier docs not present in this trimmed fixture")
        spec = _read("docs/architecture/mat-plan-team-spec.md")
        traces = _read("artifacts/agent-traces/README.md")
        orchestrator = _read(".cursor/agents/parent-orchestrator.md")
        maintainer = _read("docs/reference/MAINTAINER.md")
        readme = _read("README.md")

        for text in (spec, traces):
            self.assertIn("policy-required delegation", text)
            self.assertIn("spawn requested", text)
            self.assertIn("generic runtime spawn observed", text)
            self.assertIn("correlated role attribution", text)
            self.assertIn("typed role proved", text)

        for text in (orchestrator, maintainer, readme):
            self.assertIn("final closeout freshness gate", text.lower())
            self.assertIn("validate_closeout_coherence.py", text)

    def test_phase3_verification_ladder_and_escalation_wording_stay_aligned(self):
        required = (
            "docs/pilot/pilot-new/README.md",
            "docs/pilot/pilot-new/step-by-step.md",
            "docs/pilot/pilot-new/success-criteria.md",
            "docs/pilot/pilot-existing/step-by-step.md",
            "docs/guides/best-practices.md",
            ".cursor/commands/mat-sprint.md",
            ".cursor/commands/mat-plan-team.md",
            ".cursor/agents/parent-orchestrator.md",
            ".cursor/agents/builder.md",
            ".cursor/agents/verifier.md",
        )
        if not all(_exists(path) for path in required):
            self.skipTest("phase3 ladder/escalation docs not present in this trimmed fixture")

        ladder = _read("docs/guides/local-app-verification-ladder.md")
        pilot_new_readme = _read("docs/pilot/pilot-new/README.md")
        pilot_new_steps = _read("docs/pilot/pilot-new/step-by-step.md")
        pilot_new_success = _read("docs/pilot/pilot-new/success-criteria.md")
        pilot_existing_steps = _read("docs/pilot/pilot-existing/step-by-step.md")
        best_practices = _read("docs/guides/best-practices.md")
        sprint = _read(".cursor/commands/mat-sprint.md")
        plan_w_team = _read(".cursor/commands/mat-plan-team.md")
        orchestrator = _read(".cursor/agents/parent-orchestrator.md")
        builder = _read(".cursor/agents/builder.md")
        verifier = _read(".cursor/agents/verifier.md")

        self.assertIn("manual/staging", ladder.lower())
        self.assertIn("deterministic local automation", ladder.lower())
        self.assertIn("browser-use", ladder.lower())
        self.assertIn("playwright", ladder.lower())
        self.assertIn("default baseline", ladder.lower())
        self.assertIn("unless deterministic local automation already exists", ladder.lower())

        for text in (pilot_new_readme, pilot_new_steps, pilot_new_success, pilot_existing_steps):
            self.assertIn("local-app-verification-ladder.md", text)
            self.assertIn("manual/staging", text.lower())
            self.assertIn("deterministic local automation", text.lower())

        for text in (best_practices, sprint, plan_w_team, orchestrator, builder, verifier):
            self.assertIn("targeted regression", text.lower())
            self.assertIn("explicit documented exception", text.lower())

        for text in (builder, verifier):
            self.assertIn("hooks", text.lower())
            self.assertIn("validators", text.lower())
            self.assertIn("artifact parsing", text.lower())
            self.assertIn("mao transitions", text.lower())

    def test_phase4_memory_hygiene_and_artifact_taxonomy_stay_aligned(self):
        required = (
            "AGENTS.md",
            "README.md",
            "docs/index.md",
            "docs/reference/MAINTAINER.md",
            ".gitignore",
            "artifacts/agent-traces/README.md",
        )
        if not all(_exists(path) for path in required):
            self.skipTest("phase4 taxonomy docs not present in this trimmed fixture")

        agents = _read("AGENTS.md")
        readme = _read("README.md")
        docs_index = _read("docs/index.md")
        maintainer = _read("docs/reference/MAINTAINER.md")
        gitignore = _read(".gitignore")
        traces = _read("artifacts/agent-traces/README.md")

        self.assertIn("## Durable Repo Facts", agents)
        self.assertIn("## Workspace-Local Operational Facts", agents)
        self.assertIn("## Dated Evidence References", agents)
        self.assertIn("docs/reference/todo-orchestration.md", agents)
        self.assertIn("docs/archive/pilot-report.md", agents)

        for text in (readme, docs_index, maintainer):
            self.assertIn("canonical tracked handoffs", text.lower())
            self.assertIn("tracked distilled evidence", text.lower())
            self.assertIn("local mutable runtime exhaust", text.lower())
            self.assertIn("raw/sensitive captures", text.lower())

        self.assertIn("`docs/current-plan.md`", readme)
        self.assertIn("`docs/current-plan.md`", maintainer)
        self.assertNotIn("docs/current-plan.md", gitignore)
        self.assertIn("artifacts/phase1/phase1-verify.log", gitignore)
        self.assertIn("artifacts/agent-traces/*/", gitignore)
        self.assertIn("comparison.json", traces)
        self.assertIn("comparison.md", traces)
        self.assertIn("local run directories", traces.lower())

    def test_phase5_phase1_verify_log_is_only_local_rerun_evidence(self):
        required = (
            "artifacts/phase1/README.md",
            "artifacts/phase1/phase1-verification-report.md",
            "docs/archive/pilot-report.md",
            "docs/archive/phase1-validation-report.md",
            "docs/guides/troubleshooting.md",
        )
        if not all(_exists(path) for path in required):
            self.skipTest("phase5 phase1 log docs not present in this trimmed fixture")

        phase1_readme = _read("artifacts/phase1/README.md")
        phase1_report = _read("artifacts/phase1/phase1-verification-report.md")
        pilot_report = _read("docs/archive/pilot-report.md")
        validation_report = _read("docs/archive/phase1-validation-report.md")
        troubleshooting = _read("docs/guides/troubleshooting.md")

        self.assertIn("local mutable runtime exhaust", phase1_readme.lower())
        self.assertIn("latest local rerun log", phase1_report.lower())
        self.assertIn("local rerun log", pilot_report.lower())
        self.assertIn("local rerun log", validation_report.lower())
        self.assertIn("latest local rerun log", troubleshooting.lower())
        self.assertNotIn("latest sign-off run is `artifacts/phase1/phase1-verify.log`", validation_report)
        self.assertNotIn("latest sign-off run is `artifacts/phase1/phase1-verify.log`", phase1_report)

    def test_phase5_green_bar_status_docs_stay_honest(self):
        required = ("README.md", "ROADMAP.md")
        if not all(_exists(path) for path in required):
            self.skipTest("phase5 status docs not present in this trimmed fixture")

        readme = _read("README.md")
        roadmap = _read("ROADMAP.md")
        archive = _read("docs/archive/roadmap-completed.md")

        self.assertIn("Phase 5 completed the rollout and green-bar validation pass", readme)
        self.assertIn("workflow is green under the scoped hardening criteria", readme)
        self.assertIn("Phase 5 — Shipped", archive)
        self.assertIn("Green bar — Met", archive)
        self.assertIn("roadmap-completed.md", roadmap)
        self.assertTrue(
            "blocked runtime-limitations stay explicit" in roadmap.lower()
            or "blocked limitations stay explicit" in roadmap.lower()
        )

    def test_continual_learning_hygiene_docs_are_linked(self):
        required = (
            ".cursor/rules/continual-learning-hygiene.mdc",
            "docs/guides/continual-learning-safe-handling.md",
            "README.md",
            "AGENTS.md",
            "docs/reference/MAINTAINER.md",
            "docs/index.md",
        )
        if not all(_exists(path) for path in required):
            self.skipTest("continual-learning hygiene doc set not present in this trimmed fixture")

        rule = _read(".cursor/rules/continual-learning-hygiene.mdc")
        design = _read("docs/guides/continual-learning-safe-handling.md")
        readme = _read("README.md")
        agents = _read("AGENTS.md")
        maintainer = _read("docs/reference/MAINTAINER.md")
        docs_index = _read("docs/index.md")

        self.assertIn("intentional memory maintenance", rule)
        self.assertIn("fresh maintenance session", rule)
        self.assertIn("12 bullets", rule)
        self.assertIn("queue-first memory-maintenance flow", design)
        self.assertIn("fresh chat/session", design)
        self.assertIn("continual-learning-safe-handling.md", readme)
        self.assertIn("continual-learning-safe-handling.md", docs_index)
        self.assertIn("continual-learning AGENTS edits", maintainer)
        self.assertIn("Treat continual-learning `AGENTS.md` edits as intentional memory maintenance", agents)


class LongRunOrchestrationContractTest(unittest.TestCase):
    """Contract tests for docs/prompt-only long-run workflow (approved plan alignment)."""

    def test_long_run_state_has_mandatory_sections_and_all_stop_reasons(self):
        if _is_mat_sidecar_adoption_layout():
            self.skipTest(
                "MAT sidecar adoption may ship a minimal or legacy long-run-state; full contract is MAT-repo scope"
            )
        text = _read("docs/architecture/long-run-state.md")
        for heading in (
            "## Mission",
            "## Scope / hard constraints / non-goals",
            "## Slice preflight decision",
            "## Ordered slice queue",
            "## Active slice",
            "## Completed slices",
            "## Continuation policy",
            "## Stop-reason policy",
            "## Parent mission gate compliance",
        ):
            self.assertIn(heading, text, msg=f"missing section {heading}")
        self.assertIn("do **not** enforce", text.lower())
        self.assertIn("test_workflow_docs.py", text)
        self.assertIn("execution_mode", text)
        self.assertIn("inline", text)
        self.assertIn("builder_plus_verifier", text)
        self.assertIn("parallel_spawn", text)
        self.assertIn("execution_rationale", text)
        self.assertIn("source_task_id", text)
        for reason in (
            "mission_complete",
            "hard_blocker",
            "approval_needed",
            "planning_gap",
            "unexpected_termination",
        ):
            self.assertIn(reason, text, msg=f"stop reason {reason}")

    def test_long_run_command_covers_plan_phase2_requirements(self):
        cmd = _read(".cursor/commands/mat-long-run.md")
        self.assertIn("## Purpose", cmd)
        self.assertIn("## Preflight decision", cmd)
        self.assertIn("## Startup workflow", cmd)
        self.assertIn("## Required artifacts", cmd)
        self.assertIn("## Ordered slice loop", cmd)
        self.assertIn("## Post-slice mission gate", cmd)
        self.assertIn("## Stop conditions", cmd)
        self.assertIn("## Relationship to other commands", cmd)
        self.assertIn("/mat-sprint", cmd)
        self.assertIn("/mat-plan-team", cmd)
        self.assertIn("TASK-###", cmd)
        self.assertIn("tasks.json", cmd)
        # Phase 2: initialize mission state before first builder; slice plan from queue row only
        self.assertRegex(
            cmd.lower(),
            r"before.*first builder|initialize.*before.*builder",
            msg="expected explicit initialize-before-builder dispatch",
        )
        self.assertIn("active", cmd.lower())
        self.assertIn("queued slice", cmd.lower())
        self.assertIn("execution_mode", cmd)
        self.assertIn("builder_plus_verifier", cmd)
        self.assertIn("parallel_spawn", cmd)
        self.assertIn("one-line rationale", cmd)
        self.assertNotIn("slice_execution_mode", cmd)
        # Honesty: no autonomous overclaim
        self.assertIn("autonomous", cmd.lower())
        self.assertIn("Parent mission gate compliance", cmd)

    def test_parent_orchestrator_has_mission_gate_and_slice_vs_mission_rules(self):
        po = _read(".cursor/agents/parent-orchestrator.md")
        self.assertIn("## Task tool mandate (policy)", po)
        self.assertIn("## Long-run missions", po)
        self.assertIn("### Step 0 — Preflight decision", po)
        self.assertIn("### Step 5b — Post-slice mission gate", po)
        self.assertIn("Step 1c — Onboarding task status sync", po)
        self.assertIn("queued slices remain", po)
        self.assertIn("planning_gap", po)
        self.assertIn("not mission complete", po.lower())
        self.assertIn("multi-row backlog", po.lower())
        self.assertIn("wait-before-supersede", po)
        self.assertIn("`build-result.md` by itself is not idle evidence", po)
        self.assertIn("`verify-result.md` by itself is not stall evidence", po)
        self.assertIn("advisory progress helper", po)
        self.assertIn("operator-owned evidence or posture decisions", po)
        self.assertNotIn("slice_execution_mode", po)

    def test_plan_w_team_clarifies_not_default_long_run_without_contract(self):
        pwt = _read(".cursor/commands/mat-plan-team.md")
        self.assertIn("Task", pwt)
        self.assertIn("## Long-run vs single cycle", pwt)
        self.assertIn("## Preflight decision", pwt)
        self.assertIn("/mat-long-run", pwt)
        self.assertIn("docs/architecture/long-run-state.md", pwt)
        self.assertIn("post-slice mission gate", pwt)
        self.assertIn("Step 1c", pwt)
        self.assertIn("builder_plus_verifier", pwt)
        self.assertIn("inline", pwt)
        self.assertIn("delegated multi-agent orchestration command", pwt)
        self.assertIn("default and intended mode", pwt)
        self.assertIn("narrow exception", pwt)
        self.assertIn("not an equal default path", pwt)
        self.assertIn("advisory progress helper", pwt)
        self.assertIn("Missing `build-result.md` alone is not a reason", pwt)

    def test_plan_contract_amendments_append_only_in_commands(self):
        """Slice 2: command docs encode ## Amendments append-only semantics (Decision C)."""
        pwt = _read(".cursor/commands/mat-plan-team.md")
        self.assertIn("## Amendments", pwt)
        self.assertIn("append-only", pwt.lower())
        self.assertIn("YYYY-MM-DDTHH:MM:SSZ", pwt)
        self.assertIn("never rewrite", pwt.lower())

        onboarding = _read(".cursor/commands/mat-plan-onboarding.md")
        self.assertIn("## Amendments", onboarding)
        self.assertIn("append-only", onboarding.lower())
        self.assertIn("verifier append prohibited", onboarding.lower())

        if _exists("docs/reference/MAINTAINER.md"):
            maintainer = _read("docs/reference/MAINTAINER.md")
            self.assertIn("Living-plan amendments", maintainer)
            self.assertIn("Forbidden", maintainer)
            self.assertIn("Rewrite/delete prior lines", maintainer)

        if _exists("docs/templates/adoption-minimal-current-plan.md"):
            template = _read("docs/templates/adoption-minimal-current-plan.md")
            self.assertIn("## Amendments", template)

    def test_plan_contract_status_markers_in_builder_and_commands(self):
        """Slice 3: agent/command docs encode status markers and advisory vs gate distinction (Decision D)."""
        builder = _read(".cursor/agents/builder.md")
        for marker in ("[]", "[wip]", "[x]", "[f]"):
            self.assertIn(marker, builder)
        self.assertIn("gate-authoritative", builder.lower())
        self.assertIn("advisory", builder.lower())
        self.assertIn("in-place", builder.lower())

        pwt = _read(".cursor/commands/mat-plan-team.md")
        self.assertIn("[wip]", pwt)
        self.assertIn("[x]", pwt)
        self.assertIn("[f]", pwt)
        self.assertIn("advisory", pwt.lower())
        self.assertIn("build-result.md", pwt)

        if _exists("docs/reference/MAINTAINER.md"):
            maintainer = _read("docs/reference/MAINTAINER.md")
            self.assertIn("In-plan status markers", maintainer)
            self.assertIn("warn-not-fail", maintainer.lower())

        if _exists("docs/reference/workflow-artifact-contract.md"):
            contract = _read("docs/reference/workflow-artifact-contract.md")
            self.assertIn("In-plan status markers vs gate-authoritative", contract)
            self.assertIn("advisory", contract.lower())

    def test_plan_contract_slice5_execution_template_and_validation_loops(self):
        """Slice 5: standard execution template documents tier mapping and validation-loop prose."""
        template_path = "docs/templates/execution-plan-template.md"
        if not _exists(template_path):
            self.skipTest("execution-plan template not present in this repo layout")
        template = _read(template_path)
        self.assertIn("lite", template.lower())
        self.assertIn("standard", template.lower())
        self.assertIn("onboarding", template.lower())
        self.assertIn("loop until pass", template.lower())
        self.assertIn("docs/architecture/plan-contract.md", template)
        self.assertIn("## Verification plan", template)
        self.assertIn("## Amendments", template)

        if _exists("docs/templates/adoption-minimal-current-plan.md"):
            lite = _read("docs/templates/adoption-minimal-current-plan.md")
            self.assertIn("loop until pass", lite.lower())
            self.assertIn("lite", lite.lower())

        if _exists("docs/guides/planning-commands-guide.md"):
            guide = _read("docs/guides/planning-commands-guide.md")
            self.assertIn("execution-plan-template.md", guide)
            self.assertIn("adoption-minimal-current-plan.md", guide)

    def test_execution_plans_carry_tier2b_loops_without_html_contract(self):
        """S3-planf3: execution projections reuse Tier 2b loops, never living HTML."""
        template_path = "docs/templates/execution-plan-template.md"
        contract_path = "docs/architecture/plan-contract.md"
        sprint_path = ".cursor/commands/mat-sprint.md"
        plan_team_path = ".cursor/commands/mat-plan-team.md"
        required = (template_path, contract_path, sprint_path, plan_team_path)
        missing = [path for path in required if not _exists(path)]
        if missing:
            self.skipTest(
                "execution validation-loop surfaces not present in this repo layout: "
                + ", ".join(missing)
            )

        template = _read(template_path)
        self.assertIn("Tier 2b", template)
        self.assertIn("### Per-phase validation loops (loop until pass)", template)
        self.assertIn("### Global validation commands (before handoff)", template)
        self.assertIn("Phase | Command | Loop until pass", template)

        contract = _read(contract_path)
        self.assertIn("Execution validation loops (Tier 2b discipline)", contract)
        self.assertIn("must carry", contract)
        self.assertIn("Markdown remains the canonical execution contract", contract)
        self.assertIn("must not create or require a living HTML plan", contract)

        sprint = _read(sprint_path)
        self.assertIn("Tier 2b validation-loop discipline", sprint)
        self.assertIn("Per-phase validation loops (loop until pass)", sprint)
        self.assertIn("Global validation commands (before handoff)", sprint)

        plan_team = _read(plan_team_path)
        self.assertIn("Tier 2b validation-loop discipline", plan_team)
        self.assertIn("Per-phase validation loops (loop until pass)", plan_team)
        self.assertIn("Global validation commands (before handoff)", plan_team)
        self.assertIn("must not create or require a living HTML plan", plan_team)

    def test_mat_plan_validation_loops_in_command(self):
        """Tier 2b: /mat-plan command locks canonical validation-loop subsection headings."""
        plan = _read(".cursor/commands/mat-plan.md")
        self.assertIn("### Per-phase validation loops (loop until pass)", plan)
        self.assertIn("### Global validation commands (before handoff)", plan)
        self.assertIn("Phase | Command | Loop until pass", plan)
        self.assertIn("build-result.md", plan)
        self.assertIn("verify-result.md", plan)
        self.assertIn("execution-plan-template.md", plan)
        self.assertIn("specs/mat-plan-validation-loops.md", plan)

    def test_mat_plan_relevant_files_tag_prefix_in_command(self):
        """Tier 2c: /mat-plan command locks [new]/[existing] Relevant Files bullet tags."""
        plan = _read(".cursor/commands/mat-plan.md")
        self.assertIn("## Relevant Files / Areas", plan)
        self.assertIn("[new]", plan)
        self.assertIn("[existing]", plan)
        self.assertIn("case-sensitive", plan.lower())
        self.assertIn("table rows", plan.lower())

    def test_readme_explains_command_triplet(self):
        if _is_mat_sidecar_adoption_layout():
            self.skipTest("MAT sidecar adoption uses a product-first README stub at repo root")
        readme = _read("README.md")
        self.assertIn("**Choosing a command:**", readme)
        self.assertIn("/mat-sprint", readme)
        self.assertIn("/mat-plan-team", readme)
        self.assertIn("/mat-long-run", readme)
        self.assertIn("matching `tasks.json` status synchronized with the active slice", readme)
        self.assertIn("post-slice mission gate", readme)
        self.assertIn("Preflight decision", readme)
        self.assertIn("delegated builder -> verifier orchestration cycle by default", readme)

    def test_docs_readme_toc_links_long_run_state(self):
        if _is_mat_sidecar_adoption_layout():
            self.skipTest("docs/index.md TOC contract is MAT-source scope in adopted repos")
        doc_index = _read("docs/index.md")
        self.assertRegex(doc_index, re.compile(r"^Last updated: \d{4}-\d{2}-\d{2}$", re.MULTILINE))
        self.assertIn("[long-run-state.md](architecture/long-run-state.md)", doc_index)
        self.assertIn("../.cursor/commands/mat-long-run.md", doc_index)
        self.assertIn("parent-orchestrator", doc_index)
        self.assertIn("execution_mode", doc_index)
        self.assertIn("execution_rationale", doc_index)
        self.assertNotIn("slice_execution_mode", doc_index)

    def test_phase4_reassessment_checklist_contract(self):
        if _is_mat_sidecar_adoption_layout():
            self.skipTest("phase4 reassessment checklist is MAT-source packaged doc scope")
        text = _read("docs/archive/phase4-roadmap-reassessment-checklist.md")
        self.assertIn("mao-advisory-go-criteria.md", text)
        self.assertIn("decision-record.md", text)
        self.assertIn("ROADMAP.md", text)
        self.assertIn("G4", text)
        self.assertIn("prepare evidence", text)
        self.assertIn("operator-owned", text)


class PlanContractSlice6MetaSkillTest(unittest.TestCase):
    """Slice 6: mat-plan-contract skill exists, encodes contract semantics, does not replace commands."""

    def test_plan_contract_slice6_meta_skill_and_adoption_packaging(self):
        skill_path = ".cursor/skills/mat-plan-contract/SKILL.md"
        if not _exists(skill_path):
            self.fail(f"missing required skill: {skill_path}")
        skill = _read(skill_path)

        self.assertIn("docs/architecture/plan-contract.md", skill)
        self.assertIn("specs/shared-plan-contract.md", skill)
        self.assertIn("Decision A", skill)
        self.assertIn("Decision B", skill)
        self.assertIn("Decision C", skill)
        self.assertIn("Decision D", skill)
        self.assertIn("Decision E", skill)
        self.assertIn("lite", skill.lower())
        self.assertIn("standard", skill.lower())
        self.assertIn("onboarding", skill.lower())
        self.assertIn("## Amendments", skill)
        self.assertIn("YYYY-MM-DDTHH:MM:SSZ", skill)
        for marker in ("[]", "[wip]", "[x]", "[f]"):
            self.assertIn(marker, skill)
        self.assertIn("loop until pass", skill.lower())
        self.assertIn("does not replace slash commands", skill.lower())

        for cmd in (
            ".cursor/commands/mat-plan.md",
            ".cursor/commands/mat-plan-onboarding.md",
            ".cursor/commands/mat-plan-team.md",
        ):
            text = _read(cmd)
            self.assertIn("mat-plan-contract", text)
            self.assertIn("does not replace", text.lower())

        layout_path = "scripts/adoption/adoption-layout-v1.json"
        if _exists(layout_path):
            layout = _read(layout_path)
            self.assertIn("docs/architecture/plan-contract.md", layout)
            self.assertIn(".mat/docs/plan-contract.md", layout)

        if _exists("docs/reference/components.md"):
            components = _read("docs/reference/components.md")
            self.assertIn("mat-plan-contract", components)

        if _exists("docs/architecture/plan-contract.md"):
            contract = _read("docs/architecture/plan-contract.md")
            self.assertIn("| 6 |", contract)
            self.assertIn("**Done**", contract)
            self.assertIn("mat-plan-contract", contract)


class MatPlanCanvasSkillTest(unittest.TestCase):
    """mat-plan-canvas skill: advisory visualization layer; markdown canonical; no new gates."""

    def test_mat_plan_canvas_skill_contract(self):
        skill_path = ".cursor/skills/mat-plan-canvas/SKILL.md"
        if not _exists(skill_path):
            self.fail(f"missing required skill: {skill_path}")
        skill = _read(skill_path)

        self.assertIn("markdown is canonical", skill.lower())
        self.assertIn("advisory", skill.lower())
        self.assertIn("no write-back", skill.lower())
        self.assertIn("lite", skill.lower())
        self.assertIn("standard", skill.lower())
        self.assertIn("onboarding", skill.lower())
        self.assertIn("sections", skill.lower())
        self.assertIn("stats", skill.lower())
        self.assertIn("tables", skill.lower())
        self.assertIn("cursor.com/docs/agent/tools/canvas", skill)
        self.assertIn("mat-plan-contract", skill)
        self.assertIn("does not replace slash commands", skill.lower())
        self.assertIn("planf3", skill.lower())
        self.assertIn("canary", skill.lower())
        self.assertIn("markdown fallback", skill.lower())
        self.assertIn("no documented public programmatic", skill.lower())
        self.assertNotIn("import only from `cursor/canvas`", skill.lower())
        self.assertNotIn("place `.canvas.tsx`", skill.lower())

        for gate_phrase in (
            "build-result.md",
            "verify-result.md",
            "never substitute",
            "gate-authoritative",
        ):
            self.assertIn(gate_phrase, skill.lower())

        if _exists("docs/reference/components.md"):
            components = _read("docs/reference/components.md")
            self.assertIn("mat-plan-canvas", components)

    def test_canvas_canary_spec_contract(self):
        spec_path = "specs/canvas-canary-v1.md"
        if not _exists(spec_path):
            if _exists(".mat/README.md"):
                self.skipTest("Canvas canary spec is MAT-source scope")
            self.fail(f"missing required spec: {spec_path}")
        spec = _read(spec_path)
        spec_lower = spec.lower()

        for phrase in (
            "https://cursor.com/docs/agent/tools/canvas",
            "canary success",
            "canary failure",
            "markdown fallback",
            "markdown handoffs remain canonical",
            "no public programmatic `.canvas.tsx`",
        ):
            self.assertIn(phrase, spec_lower)

        self.assertIn("build-result.md", spec)
        self.assertIn("verify-result.md", spec)


class MatAdviseProjectApproachSkillTest(unittest.TestCase):
    """advise-project-approach skill: Layer 0 preflight; planning-only; MAT-localized upstream protocol."""

    def test_advise_project_approach_skill_contract(self):
        skill_path = ".cursor/skills/advise-project-approach/SKILL.md"
        if not _exists(skill_path):
            self.fail(f"missing required skill: {skill_path}")
        skill = _read(skill_path)
        skill_lower = skill.lower()

        self.assertIn("THIRD_PARTY", skill)
        self.assertIn("88f1ecc", skill)
        self.assertIn("advise-project-approach", skill_lower)

        for mode in ("pre-build", "mid-build", "post-build"):
            self.assertIn(mode, skill_lower)

        self.assertIn("intake", skill_lower)
        self.assertIn("seven", skill_lower)
        self.assertIn("read-only", skill_lower)
        self.assertIn("planning-only", skill_lower)

        for phrase in (
            "do not rank",
            "stars",
            "prototype",
            "launch",
            "growth",
        ):
            self.assertIn(phrase, skill_lower)

        self.assertIn("specs/<slug>/preflight/landscape.md", skill)
        self.assertIn("candidates.json", skill)
        self.assertIn("novelty-gate.json", skill)

        self.assertIn("scout-report-suggest", skill_lower)
        self.assertIn("mat-prime", skill_lower)
        self.assertIn("does not replace", skill_lower)

        self.assertIn("g3", skill_lower)
        self.assertIn("community research", skill_lower)
        self.assertIn("context-budget-policy", skill_lower)

        for gate_phrase in (
            "build-result.md",
            "verify-result.md",
            "docs/current-plan.md",
        ):
            self.assertIn(gate_phrase, skill_lower)

        if _exists(".cursor/commands/mat-plan.md"):
            mat_plan = _read(".cursor/commands/mat-plan.md")
            self.assertIn("advise-project-approach", mat_plan.lower())

        if _exists("docs/reference/components.md"):
            components = _read("docs/reference/components.md")
            self.assertIn("advise-project-approach", components)


class MatNeuroarxivSkillTest(unittest.TestCase):
    """neuroarxiv skill: Layer 0 Phase B literature scan; G2-gated; bounded Task subagents."""

    def test_neuroarxiv_skill_contract(self):
        skill_path = ".cursor/skills/neuroarxiv/SKILL.md"
        if not _exists(skill_path):
            self.fail(f"missing required skill: {skill_path}")
        skill = _read(skill_path)
        skill_lower = skill.lower()

        self.assertIn("THIRD_PARTY", skill)
        self.assertIn("b5d20ef", skill)
        self.assertIn("neuroarxiv", skill_lower)

        self.assertIn("g2", skill_lower)
        self.assertIn("hard stop", skill_lower)
        self.assertIn("never auto-run", skill_lower)

        for cap_phrase in ("8", "3", "4"):
            self.assertIn(cap_phrase, skill)

        for step in (
            "categorize",
            "fetch",
            "score",
            "cluster",
            "converge",
        ):
            self.assertIn(step, skill_lower)

        self.assertIn("abstract-only", skill_lower)
        self.assertIn("untrusted", skill_lower)
        self.assertIn("prompt injection", skill_lower)

        self.assertIn("specs/<slug>/preflight/arxiv-synthesis.md", skill)
        self.assertIn("arxiv-papers.json", skill)

        self.assertIn("task", skill_lower)
        self.assertIn("claude agent sdk", skill_lower)
        self.assertIn("does not", skill_lower)

        self.assertIn("fetch_arxiv.py", skill)

        for gate_phrase in (
            "build-result.md",
            "verify-result.md",
            "docs/current-plan.md",
        ):
            self.assertIn(gate_phrase, skill_lower)

        if _exists("docs/reference/components.md"):
            components = _read("docs/reference/components.md")
            self.assertIn("neuroarxiv", components)


class MatPreflightGatedSkillTest(unittest.TestCase):
    """mat-preflight-gated skill: Layer 0 orchestrator; Phase A → gate → Phase B; never auto-escalate."""

    def test_mat_preflight_gated_skill_contract(self):
        skill_path = ".cursor/skills/mat-preflight-gated/SKILL.md"
        if not _exists(skill_path):
            self.fail(f"missing required skill: {skill_path}")
        skill = _read(skill_path)
        skill_lower = skill.lower()

        self.assertIn("mat-preflight-gated", skill_lower)
        self.assertIn("planning-only", skill_lower)

        for gate in (
            "existing_sufficient",
            "integrate_and_extend",
            "novel_research_required",
            "inconclusive",
        ):
            self.assertIn(gate, skill)

        for criterion in (
            "closed_scope_denied",
            "technical_mechanism_present",
            "rework_cost_threshold_met",
            "cache_hit",
        ):
            self.assertIn(criterion, skill)

        self.assertIn("never auto-escalate", skill_lower)
        self.assertIn("hard stop", skill_lower)
        self.assertIn("g2", skill_lower)

        self.assertIn(".cursor/skills/advise-project-approach/SKILL.md", skill)
        self.assertIn(".cursor/skills/neuroarxiv/SKILL.md", skill)

        for artifact in (
            "specs/<slug>/preflight/landscape.md",
            "specs/<slug>/preflight/candidates.json",
            "specs/<slug>/preflight/novelty-gate.json",
        ):
            self.assertIn(artifact, skill)

        self.assertIn("specs/_research-cache/", skill)
        self.assertIn("30", skill)

        self.assertIn("relevant files", skill_lower)
        self.assertIn("open decisions", skill_lower)
        self.assertIn("docs/current-plan.md", skill_lower)

        self.assertIn("scout-report-suggest", skill_lower)
        self.assertIn("mat-prime", skill_lower)
        self.assertIn("does not replace", skill_lower)

        for gate_phrase in (
            "build-result.md",
            "verify-result.md",
        ):
            self.assertIn(gate_phrase, skill_lower)

        if _exists("docs/reference/components.md"):
            components = _read("docs/reference/components.md")
            self.assertIn("mat-preflight-gated", components)


class MatPreflightResearchIntegrationTest(unittest.TestCase):
    """Slice 4: /mat-preflight-research command, planning guide Layer 0, library catalog, cross-links."""

    _COMMAND_REL = ".cursor/commands/mat-preflight-research.md"
    _GUIDE_REL = "docs/guides/planning-commands-guide.md"
    _LIBRARY_REL = ".cursor/skills/the-library/library.yaml"
    _CROSS_LINK_PATHS = (
        ".cursor/commands/mat-plan.md",
        ".cursor/commands/mat-plan-onboarding.md",
        "docs/guides/mat-advisor-strategy-runbook.md",
    )

    def test_preflight_research_command_delegates_to_gated_skill(self):
        if not _exists(self._COMMAND_REL):
            self.fail(f"missing required command: {self._COMMAND_REL}")
        cmd = _read(self._COMMAND_REL)
        cmd_lower = cmd.lower()

        self.assertIn("/mat-preflight-research", cmd)
        self.assertIn("mat-preflight-gated", cmd_lower)
        self.assertIn(".cursor/skills/mat-preflight-gated/SKILL.md", cmd)
        self.assertIn("planning-only", cmd_lower)
        self.assertIn("never auto-escalate", cmd_lower)
        self.assertIn("g2", cmd_lower)

        for forbidden in (
            "/mat-plan-team",
            "build-result.md",
            "verify-result.md",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertIn(forbidden, cmd_lower)

        for phrase in (
            "do not inline",
            "read and follow",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, cmd_lower)

    def test_planning_guide_layer_0_operator_map(self):
        if not _exists(self._GUIDE_REL):
            self.skipTest(f"{self._GUIDE_REL} not present")
        guide = _read(self._GUIDE_REL)
        guide_lower = guide.lower()

        self.assertIn("## Layer 0", guide)
        self.assertIn("mat-preflight-research", guide_lower)
        self.assertIn("mat-preflight-gated", guide_lower)
        self.assertIn("scout-report-suggest", guide_lower)
        self.assertIn("mat-prime", guide_lower)
        self.assertIn("preflight-escalation-ladder", guide)

    def test_library_yaml_catalog_entries(self):
        if not _exists(self._LIBRARY_REL):
            self.skipTest(f"{self._LIBRARY_REL} not present")
        catalog = _read(self._LIBRARY_REL)
        for skill_id in (
            "advise-project-approach",
            "neuroarxiv",
            "mat-preflight-gated",
        ):
            with self.subTest(skill_id=skill_id):
                self.assertIn(f"id: {skill_id}", catalog)
                self.assertIn("status: active", catalog)
                self.assertIn(f".cursor/skills/{skill_id}/SKILL.md", catalog)

    def test_operator_surfaces_link_preflight_research(self):
        missing = [p for p in self._CROSS_LINK_PATHS if not _exists(p)]
        if missing:
            self.skipTest(f"cross-link paths missing: {missing}")
        for rel in self._CROSS_LINK_PATHS:
            with self.subTest(rel=rel):
                text = _read(rel)
                self.assertTrue(
                    "mat-preflight-research" in text.lower()
                    or "mat-preflight-gated" in text.lower(),
                    msg=f"{rel} missing preflight discoverability cross-link",
                )


class StopValidatorHonestyDocsTest(unittest.TestCase):
    """P0-2: wired `stop_validator.py` vs optional `validators/` utilities; no repo-default overclaim."""

    def test_agents_and_components_document_shipped_stop_vs_optional_validators(self):
        if not _exists("docs/reference/components.md"):
            self.skipTest("components.md not present in this trimmed fixture")
        agents = _read("AGENTS.md")
        if "# AGENTS.md — Cursor-First Agentic Workflow Guide" not in agents:
            self.skipTest(
                "packaged/adoption AGENTS.md stub at resolved repo root — full stop-validator honesty lives in MAT repo AGENTS.md"
            )
        components = _read("docs/reference/components.md")
        for text in (agents, components):
            self.assertIn("stop_validator.py", text)
            self.assertIn("send_event.py", text)
            self.assertIn("validators/", text)
        self.assertIn("additional commands on the shipped `stop` array", agents)
        self.assertIn("Phase 1", agents)
        self.assertIn("permissive", agents.lower())
        self.assertNotIn("blocks stop if required content is missing", agents.lower())
        self.assertNotIn("blocks stop if expected output file was not created", agents.lower())
        self.assertIn("Not wired on shipped `stop`", components)
        self.assertIn("Phase 1 permissive", components)
        self.assertNotIn("Blocks completion if required text is missing", components)
        self.assertNotIn("Blocks completion if expected files are absent", components)

    def test_usage_guide_events_and_features_retain_stop_honesty_boundaries(self):
        """P0-2 follow-up: usage guide + other honesty surfaces stay aligned with shipped `stop`."""
        if not _exists("docs/archive/MULTI_AGENT_USAGE_GUIDE.md"):
            self.skipTest("MULTI_AGENT_USAGE_GUIDE.md not present in this trimmed fixture")
        if not _exists("docs/architecture/events-and-visualization.md") or not _exists("docs/architecture/features-demonstrated.md"):
            self.skipTest("honesty companion docs not present in this trimmed fixture")
        agents = _read("AGENTS.md")
        if "# AGENTS.md — Cursor-First Agentic Workflow Guide" not in agents:
            self.skipTest(
                "packaged/adoption AGENTS.md stub at resolved repo root — full stop-validator honesty tests skipped"
            )
        guide = _read("docs/archive/MULTI_AGENT_USAGE_GUIDE.md")
        events = _read("docs/architecture/events-and-visualization.md")
        features = _read("docs/architecture/features-demonstrated.md")
        g = guide.lower()
        self.assertNotIn("your exit-code-2 validators", g)
        self.assertNotIn("can block agent until acceptance criteria met", g)
        self.assertIn("Shipped `stop` in this repository:", guide)
        self.assertIn("Phase 1 permissive", guide)
        self.assertIn("Optional customization", guide)
        self.assertIn("stop_validator.py", guide)
        self.assertIn("send_event.py", guide)
        self.assertIn("`failClosed` false", guide)
        self.assertIn("honesty boundary:", events)
        self.assertIn("only validator wired on `stop`", events)
        self.assertIn("not on shipped `stop`", features)


class ObservabilitySecurityHonestyDocsTest(unittest.TestCase):
    """P0-3: observability payload preview caps, tool_output honesty, no complete-record overclaim."""

    def test_events_and_visualization_documents_preview_caps_and_tool_output(self):
        if not _exists("docs/architecture/events-and-visualization.md"):
            self.skipTest("events-and-visualization.md not present in this trimmed fixture")
        events = _read("docs/architecture/events-and-visualization.md")
        self.assertIn("Payload preview and secret-handling notes", events)
        self.assertIn("tool_output", events)
        self.assertIn("800", events)
        self.assertIn("65536", events)
        self.assertIn("hook-schema.ts", events)
        self.assertIn("truncated", events.lower())
        self.assertIn("not a redacted audit log", events.lower())
        self.assertIn("do not assume payload previews are complete", events.lower())
        self.assertNotIn("complete record of all tool output", events.lower())
        self.assertNotIn("dashboard previews are complete records", events.lower())

    def test_maintainer_documents_observability_data_handling(self):
        if not _exists("docs/reference/MAINTAINER.md"):
            self.skipTest("MAINTAINER.md not present in this trimmed fixture")
        maintainer = _read("docs/reference/MAINTAINER.md")
        self.assertIn("Observability data handling", maintainer)
        self.assertIn("tool_output", maintainer)
        self.assertIn("truncated", maintainer.lower())
        self.assertIn("OBSERVABILITY_API_TOKEN", maintainer)
        self.assertIn("sensitive local runtime exhaust", maintainer.lower())
        self.assertIn("should not be treated as the full record", maintainer.lower())
        self.assertNotIn("dashboard previews are complete records", maintainer.lower())


class ObservabilityRetentionPolicyDocsTest(unittest.TestCase):
    """P2: observability retention policy doc, honesty strings, and cross-links."""

    def test_retention_policy_exists_with_honesty_strings(self):
        rel = "docs/architecture/observability-retention-policy.md"
        if not _exists(rel):
            self.skipTest("observability-retention-policy.md not present in this trimmed fixture")
        policy = _read(rel)
        self.assertIn("Last updated: 2026-08-24", policy)
        self.assertIn("advisory", policy.lower())
        self.assertIn("800", policy)
        self.assertIn("65536", policy)
        self.assertIn("OBSERVABILITY_DB_PATH", policy)
        self.assertIn("artifacts/phase1", policy)
        self.assertIn("artifacts/mat-runtime", policy)
        self.assertIn("hook_events", policy)
        self.assertIn("hook-schema.ts", policy)
        self.assertIn("truncat", policy.lower())
        self.assertIn("full", policy.lower())
        self.assertIn("sqlite", policy.lower())
        self.assertIn("observability-purge", policy.lower())
        self.assertIn("rfu-7", policy.lower())
        for phrase in (
            "no automatic ttl",
            "no shipped automatic",
            "no server-side event sampling",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, policy.lower())
        self.assertNotIn("automatic purge runs", policy.lower())

    def test_cross_links_from_events_configuration_and_maintainer(self):
        for rel in (
            "docs/architecture/events-and-visualization.md",
            "docs/reference/configuration.md",
            "docs/reference/MAINTAINER.md",
        ):
            if not _exists(rel):
                self.skipTest(f"{rel} not present in this trimmed fixture")
        events = _read("docs/architecture/events-and-visualization.md")
        config = _read("docs/reference/configuration.md")
        maintainer = _read("docs/reference/MAINTAINER.md")
        readme = _read("docs/index.md") if _exists("docs/index.md") else ""
        for text in (events, config, maintainer):
            self.assertIn("observability-retention-policy.md", text)
        if readme:
            self.assertIn("observability-retention-policy.md", readme)
        self.assertIn("OBSERVABILITY_DB_PATH", config)


class MatAdoptionObservabilityAppendixTest(unittest.TestCase):
    """Adoption observability appendix: existence, opt-in honesty, manual rotation, RFU-7 deferral."""

    _APPENDIX_REL = "docs/archive/adoption-observability-appendix.md"
    _LAYOUT_REL = "scripts/adoption/adoption-layout-v1.json"
    _PILOT_REPORT_PATH = "artifacts/report/adoption-observability-pilot-2026-06-23.md"

    def test_appendix_exists_with_honesty_strings(self):
        if not _exists(self._APPENDIX_REL):
            self.skipTest(f"{self._APPENDIX_REL} not present in this trimmed fixture")
        appendix = _read(self._APPENDIX_REL)
        self.assertIn("advisory", appendix.lower())
        self.assertIn("opt-in", appendix.lower())
        for phrase in ("manual rotate", "manual rotation", "rotate and prune", "manual prune"):
            if phrase in appendix.lower():
                break
        else:
            self.fail("appendix must mention manual rotation or rotate/prune")
        no_purge_phrases = (
            "no automatic purge",
            "no automatic ttl",
            "no shipped automatic",
            "no auto-purge",
        )
        self.assertTrue(
            any(p in appendix.lower() for p in no_purge_phrases),
            f"appendix must state no auto-purge/TTL honesty; checked {no_purge_phrases}",
        )
        self.assertIn("observability-retention-policy.md", appendix)
        self.assertTrue(
            "phase-c-rfu-7" in appendix.lower() or "rfu-7" in appendix.lower(),
            "appendix must reference RFU-7 deferral",
        )
        self.assertIn("events.sqlite", appendix)
        self.assertIn("OBSERVABILITY_API_TOKEN", appendix)
        self.assertIn(".mat/docs/archive/adoption-observability-appendix.md", appendix)

    def test_adoption_layout_packages_appendix(self):
        if not _exists(self._LAYOUT_REL):
            self.skipTest(f"{self._LAYOUT_REL} not present")
        layout = _read(self._LAYOUT_REL)
        self.assertIn("docs/archive/adoption-observability-appendix.md", layout)
        self.assertIn(".mat/docs/archive/adoption-observability-appendix.md", layout)

    def test_operator_docs_link_adoption_pilot_report(self):
        """Getting-started, validation-report, and appendix cross-link disposable pilot evidence."""
        paths = (
            "docs/guides/getting-started-existing-projects.md",
            "docs/guides/getting-started-new-projects.md",
            "validation-report.md",
            self._APPENDIX_REL,
        )
        for rel in paths:
            with self.subTest(rel=rel):
                if not _exists(rel):
                    self.skipTest(f"{rel} not present in this trimmed fixture")
                text = _read(rel)
                self.assertIn(self._PILOT_REPORT_PATH, text)
        appendix = _read(self._APPENDIX_REL)
        self.assertIn("## Related evidence", appendix)


class P2OrchestrationStrategyDocsTest(unittest.TestCase):
    """P2 Phase A: worktree wrapper + nested/background subagent strategy in decision-record."""

    _WORKTREE_ANCHOR = "p2-audit--worktree-wrapper-strategy"
    _NESTED_ANCHOR = "p2-audit--nested-and-background-subagents"

    def test_decision_record_p2_sections_with_honesty_strings(self):
        rel = "docs/reference/decision-record.md"
        if not _exists(rel):
            self.skipTest("decision-record.md not present in this trimmed fixture")
        text = _read(rel)
        self.assertIn("P2 Audit — Worktree Wrapper Strategy", text)
        self.assertIn("P2 Audit — Nested and Background Subagents", text)
        self.assertIn("Hybrid defer", text)
        self.assertIn("options matrix", text.lower())
        self.assertIn("/worktree", text)
        self.assertIn("/best-of-n", text)
        self.assertIn("Selective use", text)
        self.assertTrue(
            "file-first" in text.lower() or "file handoff" in text.lower(),
            msg="decision-record must mention file-first or file handoff honesty",
        )
        self.assertIn("advisory", text.lower())
        for phrase in (
            "no live todo spawn",
            "no hook auto-delegation",
            "live todo",
            "hook auto-delegation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), text.lower())
        overclaim_patterns = (
            re.compile(r"hook[- ]driven subagent auto[- ]spawn is shipped", re.IGNORECASE),
            re.compile(r"auto[- ]spawn (?:is|has been) shipped", re.IGNORECASE),
            re.compile(r"live todo spawn is shipped", re.IGNORECASE),
            re.compile(r"hooks (?:now )?spawn (?:builder|verifier) automatically", re.IGNORECASE),
        )
        nested_start = text.lower().find("p2 audit — nested and background subagents")
        self.assertGreater(nested_start, -1)
        nested_block = text[nested_start:]
        for pattern in overclaim_patterns:
            with self.subTest(pattern=pattern.pattern):
                self.assertIsNone(
                    pattern.search(nested_block),
                    msg=f"nested-subagent section overclaims auto-spawn: {pattern.pattern}",
                )

    def test_cross_links_from_roadmap_orchestration_and_audit_report(self):
        for rel in (
            "ROADMAP.md",
            "docs/architecture/orchestration-workflow.md",
            "artifacts/report/mat-audit-report.md",
        ):
            if not _exists(rel):
                self.skipTest(f"{rel} not present in this trimmed fixture")
        roadmap = _read("ROADMAP.md")
        orchestration = _read("docs/architecture/orchestration-workflow.md")
        audit = _read("artifacts/report/mat-audit-report.md")
        archive = _read("docs/archive/roadmap-completed.md")
        for text in (roadmap, orchestration, audit):
            self.assertIn("decision-record.md", text)
            self.assertIn(self._WORKTREE_ANCHOR, text)
            self.assertIn(self._NESTED_ANCHOR, text)
        self.assertTrue(
            "P2OrchestrationStrategyDocsTest" in roadmap
            or "P2OrchestrationStrategyDocsTest" in archive
        )
        self.assertIn("Explicit non-goals", orchestration)
        self.assertIn("**Done**", audit)


# Canonical surfaces for P0-1 worktree contract (aligned with docs/current-plan.md scope).
_WORKTREE_CONTRACT_REL_PATHS = (
    "AGENTS.md",
    "docs/archive/worktree-decision-matrix.md",
    ".cursor/commands/mat-wt-create.md",
    ".cursor/commands/mat-wt-list.md",
    ".cursor/agents/create-worktree-subagent.md",
    ".cursor/worktrees.json",
    ".cursor/hooks/bootstrap_worktree.sh",
    ".cursor/skills/worktree-manager/SKILL.md",
    ".cursor/skills/create-worktree/SKILL.md",
    "docs/reference/MAINTAINER.md",
    "docs/reference/components.md",
    "docs/guides/getting-started-existing-projects.md",
    "docs/guides/getting-started-new-projects.md",
    "docs/reference/configuration.md",
    "docs/guides/quick-start.md",
    "docs/guides/best-practices.md",
    "docs/guides/usage-examples-and-cases.md",
    "docs/archive/MULTI_AGENT_USAGE_GUIDE.md",
    "docs/architecture/features-demonstrated.md",
)

_WORKTREE_MISLEADING_PATTERNS = (
    re.compile(r"Cursor\s+automatically\s+creates\s+a\s+Git\s+worktree", re.IGNORECASE),
    re.compile(r"automatically\s+creates\s+isolated\s+Git\s+worktrees", re.IGNORECASE),
    re.compile(r"Each\s+parallel\s+agent\s+run\s+creates\s+a\s+fresh\s+worktree", re.IGNORECASE),
    re.compile(r"4000\s*\+\s*\(\s*offset\s*\*\s*10", re.IGNORECASE),
    re.compile(r"4000\s*\+\s*offset\s*\*\s*10", re.IGNORECASE),
    re.compile(r"base\s*\+\s*\(\s*offset\s*\*\s*10", re.IGNORECASE),
)


class P1StaleDocsHonestyTest(unittest.TestCase):
    """P1 stale-docs: observability stack honesty, spawn link targets, no snapshot framing."""

    def test_server_readme_describes_shipped_stack_honestly(self):
        if not _exists("apps/server/README.md"):
            self.skipTest("apps/server/README.md not present")
        text = _read("apps/server/README.md")
        self.assertNotIn("partial snapshot", text.lower())
        self.assertNotIn("not included as a full app", text.lower())
        self.assertTrue(
            any(marker in text for marker in ("/ws/events", "apps/client", "start-system.sh")),
            msg="server README should reference shipped stack (/ws/events, apps/client, or start-system.sh)",
        )

    def test_features_demonstrated_does_not_claim_unconfirmed_observability_snapshot(self):
        if not _exists("docs/architecture/features-demonstrated.md"):
            self.skipTest("features-demonstrated.md not present")
        text = _read("docs/architecture/features-demonstrated.md")
        self.assertNotIn(
            "confirmed dependency manifests in this workspace snapshot",
            text.lower(),
        )
        self.assertIn("Full observability stack", text)
        self.assertIn("Client CI gate", text)
        self.assertIn("Runtime review panel", text)
        self.assertIn("MAO visibility panel", text)

    def test_mat_subagents_spawn_related_links_use_mat_prefixed_commands(self):
        rel = ".cursor/commands/mat-subagents-spawn.md"
        if not _exists(rel):
            self.skipTest("mat-subagents-spawn command not present")
        text = _read(rel)
        self.assertIn("[`mat-long-run.md`](mat-long-run.md)", text)
        self.assertIn("[`mat-sprint.md`](mat-sprint.md)", text)
        self.assertNotIn("(long-run.md)", text)
        self.assertNotIn("(sprint.md)", text)
        for target in ("mat-long-run.md", "mat-sprint.md", "mat-plan-team.md"):
            with self.subTest(target=target):
                self.assertTrue(
                    _exists(f".cursor/commands/{target}"),
                    msg=f"Related link target missing: .cursor/commands/{target}",
                )

    def test_mat_subagents_spawn_file_ownership_matrix_s2_parallel(self):
        """S2-parallel: path-class ownership, concurrency budget, parent-mediated only."""
        cmd_rel = ".cursor/commands/mat-subagents-spawn.md"
        teams_rel = "docs/architecture/agent-teams.md"
        if not _exists(cmd_rel):
            self.skipTest("mat-subagents-spawn command not present")
        if not _exists(teams_rel):
            self.skipTest("agent-teams.md not present")

        spawn = _read(cmd_rel)
        teams = _read(teams_rel)

        # AC-1: explicit path-class / ownership matrix
        self.assertIn("## File-ownership / path-class matrix", spawn)
        self.assertIn("Path / glob class", spawn)
        self.assertIn("Primary writer", spawn)
        self.assertIn("Concurrent readers OK?", spawn)
        self.assertIn("Conflict resolution", spawn)
        self.assertIn("build-result.md", spawn)
        self.assertIn("verify-result.md", spawn)
        self.assertIn("docs/current-plan.md", spawn)

        # AC-2: parent-mediated integration; no peer task-board
        self.assertIn("parent-mediated integration", spawn.lower())
        self.assertIn("no peer task-board", spawn.lower())
        self.assertIn("parent-mediated", teams.lower())

        # AC-3: failure-mode handling
        self.assertIn("## Conflict and failure-mode handling", spawn)
        self.assertIn("Failed worker", spawn)
        self.assertIn("Abandoned work", spawn)
        self.assertIn("Duplicate ownership", spawn)

        # AC-4: concurrency budget; no auto worktree-per-Task claim
        self.assertIn("## Concurrency budget", spawn)
        self.assertIn("does not invent a worktree per Task by default", spawn)
        self.assertIn("Do not claim auto worktree-per-Task", spawn)
        self.assertIn("File-ownership matrix", teams)
        self.assertIn("mat-subagents-spawn.md", teams)


# P1 B1 surfaces beyond P0 worktree contract paths (see docs/current-plan.md).
_P1_WORKTREE_HONESTY_REL_PATHS = (
    ".cursor/commands/mat-wt-check.md",
    ".cursor/commands/mat-wt-remove.md",
    "README.md",
    "docs/reference/decision-record.md",
    "docs/architecture/orchestration-workflow.md",
)

# Stop-validator honesty beyond StopValidatorHonestyDocsTest surfaces.
_P1_STOP_VALIDATOR_HONESTY_REL_PATHS = (
    "docs/guides/quick-start.md",
    "docs/archive/pilot-report.md",
    "docs/archive/phase1-validation-report.md",
    "docs/reference/MAINTAINER.md",
)


class P1WorktreeValidatorContractDocsTest(unittest.TestCase):
    """P1 B1: worktree + stop-validator honesty on surfaces beyond P0 contract tests."""

    def test_p1_worktree_surfaces_reject_misleading_patterns_and_hybrid_defer(self):
        if _is_mat_sidecar_adoption_layout():
            self.skipTest("MAT sidecar adoption may omit full worktree doc set at repo root")

        missing = [p for p in _P1_WORKTREE_HONESTY_REL_PATHS if not _exists(p)]
        if missing:
            self.skipTest("P1 worktree honesty paths missing: " + ", ".join(missing))

        for rel in _P1_WORKTREE_HONESTY_REL_PATHS:
            text = _read(rel)
            for pat in _WORKTREE_MISLEADING_PATTERNS:
                with self.subTest(path=rel, pattern=pat.pattern):
                    self.assertIsNone(
                        pat.search(text),
                        msg=f"{rel} matched misleading pattern {pat.pattern!r}",
                    )

        decision = _read("docs/reference/decision-record.md")
        self.assertIn("Hybrid defer", decision)
        self.assertIn("/worktree", decision)
        self.assertIn("/best-of-n", decision)

        readme = _read("README.md")
        self.assertIn("honest boundary", readme.lower())
        self.assertIn("explicit", readme.lower())

        orchestration = _read("docs/architecture/orchestration-workflow.md")
        self.assertIn("p2-audit--worktree-wrapper-strategy", orchestration)
        self.assertIn("operator explicitly created isolation", orchestration.lower())

        for rel in (".cursor/commands/mat-wt-check.md", ".cursor/commands/mat-wt-remove.md"):
            cmd = _read(rel)
            self.assertIn("worktree", cmd.lower())

    def test_p1_stop_validator_surfaces_document_permissive_shipped_stop(self):
        missing = [p for p in _P1_STOP_VALIDATOR_HONESTY_REL_PATHS if not _exists(p)]
        if missing:
            self.skipTest("P1 stop-validator honesty paths missing: " + ", ".join(missing))

        pilot = _read("docs/archive/pilot-report.md")
        self.assertIn("send_event.py", pilot)
        self.assertIn("stop_validator.py", pilot)
        self.assertIn("failClosed", pilot)
        self.assertIn("permissive", pilot.lower())
        self.assertNotIn("blocks completion if required text is missing", pilot.lower())
        self.assertNotIn("blocks stop if required content is missing", pilot.lower())

        quick_start = _read("docs/guides/quick-start.md")
        self.assertIn("explicit git worktree", quick_start.lower())
        self.assertNotIn("blocks completion if", quick_start.lower())
        self.assertNotIn("validators/", quick_start)

        phase1_report = _read("docs/archive/phase1-validation-report.md")
        self.assertNotIn("blocks completion", phase1_report.lower())
        self.assertNotIn("blocks stop if", phase1_report.lower())

        maintainer = _read("docs/reference/MAINTAINER.md")
        self.assertNotIn("validators/ on shipped `stop`", maintainer.lower())
        self.assertNotIn("additional commands on the shipped `stop` array", maintainer.lower())


_MAT_COMMAND_NAMES = (
    "mat-plan",
    "mat-plan-onboarding",
    "mat-plan-update",
    "mat-plan-team",
    "mat-long-run",
    "mat-build",
    "mat-review",
    "mat-subagents-spawn",
    "mat-sprint",
    "mat-lite",
    "mat-wt-create",
    "mat-wt-list",
    "mat-wt-remove",
    "mat-wt-check",
    "mat-doctor",
    "mat-start",
    "mat-update-mat",
    "mat-sync",
    "mat-adopt",
    "mat-git-status",
    "mat-prime",
    "mat-question",
)

_BULK_SKILLS_MIGRATION_PATTERNS = (
    re.compile(r"all commands (?:were|are) migrated to skills", re.IGNORECASE),
    re.compile(r"commands removed in favor of skills only", re.IGNORECASE),
)

_EDITOR_CENTRIC_CLOUD_PATTERNS = (
    re.compile(r"Settings\s*→\s*Cloud Agents", re.IGNORECASE),
    re.compile(r"Open Cursor Settings.*Cloud Agents", re.IGNORECASE),
    re.compile(r"cloud agents in the editor", re.IGNORECASE),
)

_P1_CLOUD_AGENTS_AUDITED_SURFACES = (
    "AGENTS.md",
    "docs/archive/worktree-decision-matrix.md",
    "docs/reference/components.md",
    "docs/reference/configuration.md",
    "docs/reference/technical-stack.md",
)


class P1SkillsCommandsRoutingDocsTest(unittest.TestCase):
    """P1 Phase B B2: skills vs commands routing in decision-record."""

    _ANCHOR = "p1-audit--skills-vs-commands-routing"

    def test_decision_record_p1_skills_commands_section(self):
        rel = "docs/reference/decision-record.md"
        if not _exists(rel):
            self.skipTest("decision-record.md not present in this trimmed fixture")
        text = _read(rel)
        self.assertIn("P1 Audit — Skills vs Commands Routing", text)
        self.assertIn(self._ANCHOR, text)
        self.assertIn("Workflow / command", text)
        self.assertIn("Routing", text)
        self.assertIn("Rationale", text)
        self.assertIn("Migration effort", text)
        for cmd in _MAT_COMMAND_NAMES:
            with self.subTest(command=cmd):
                self.assertIn(f"`{cmd}`", text)
        for skill in ("create-worktree", "worktree-manager", "the-library", "meta-skill"):
            with self.subTest(skill=skill):
                self.assertIn(skill, text)
        self.assertIn("Explicit non-goals", text)

    def test_mat_plan_team_stays_command_and_worktree_skill_cross_ref(self):
        rel = "docs/reference/decision-record.md"
        if not _exists(rel):
            self.skipTest("decision-record.md not present in this trimmed fixture")
        text = _read(rel)
        plan_team_idx = text.find("`mat-plan-team`")
        self.assertGreater(plan_team_idx, -1)
        plan_team_row = text[plan_team_idx : plan_team_idx + 200]
        self.assertIn("Keep as command", plan_team_row)
        self.assertTrue(
            "create-worktree" in text or "worktree-manager" in text,
            msg="decision-record must cross-reference worktree skills",
        )
        planning = _read("docs/guides/planning-commands-guide.md") if _exists("docs/guides/planning-commands-guide.md") else ""
        if planning:
            self.assertIn(self._ANCHOR, planning)

    def test_no_bulk_skills_migration_claim(self):
        rel = "docs/reference/decision-record.md"
        if not _exists(rel):
            self.skipTest("decision-record.md not present in this trimmed fixture")
        text = _read(rel)
        section_start = text.lower().find("p1 audit — skills vs commands routing")
        self.assertGreater(section_start, -1)
        section = text[section_start:]
        self.assertIn("Explicit non-goals", section)
        self.assertIn("No claim that all", section)
        self.assertIn("No bulk", section)
        non_goals_start = section.find("### Explicit non-goals")
        self.assertGreater(non_goals_start, -1)
        prose_before_non_goals = section[:non_goals_start]
        for pattern in _BULK_SKILLS_MIGRATION_PATTERNS:
            with self.subTest(pattern=pattern.pattern):
                self.assertIsNone(
                    pattern.search(prose_before_non_goals),
                    msg="routing prose must not claim bulk command→skill migration",
                )


class P1CloudAgentsAgentsWindowDocsTest(unittest.TestCase):
    """P1 Phase B B3: Cloud Agents / Agents Window Cursor 3 language."""

    _ANCHOR = "p1-audit--cloud-agents-agents-window"

    def test_decision_record_p1_cloud_agents_section(self):
        rel = "docs/reference/decision-record.md"
        if not _exists(rel):
            self.skipTest("decision-record.md not present in this trimmed fixture")
        text = _read(rel)
        self.assertIn("P1 Audit — Cloud Agents and Agents Window", text)
        self.assertIn(self._ANCHOR, text)
        self.assertIn("Agents Window", text)
        self.assertIn(".cursor/environment.json", text)
        self.assertIn("Explicit non-goals", text)
        self.assertIn("MAT does not auto-provision", text)
        self.assertIn("No new cloud automation", text)

    def test_agents_and_worktree_matrix_cursor3_language(self):
        agents_rel = (
            ".mat/AGENTS.mat.md" if _is_mat_sidecar_adoption_layout() else "AGENTS.md"
        )
        for rel in (agents_rel, "docs/archive/worktree-decision-matrix.md"):
            if not _exists(rel):
                self.skipTest(f"{rel} not present in this trimmed fixture")
        agents = _read(agents_rel)
        matrix = _read("docs/archive/worktree-decision-matrix.md")
        for text in (agents, matrix):
            self.assertIn("Agents Window", text)
            self.assertIn(".cursor/environment.json", text)
            self.assertIn(self._ANCHOR, text)
        self.assertIn("cursor.com/docs/cloud-agent", agents)
        self.assertNotIn("Settings → Cloud Agents", agents)
        self.assertNotIn("Settings → Cloud Agents", matrix)

    def test_no_editor_only_cloud_claims(self):
        missing = [p for p in _P1_CLOUD_AGENTS_AUDITED_SURFACES if not _exists(p)]
        if missing:
            self.skipTest("P1 cloud agents audited surfaces missing: " + ", ".join(missing))
        for rel in _P1_CLOUD_AGENTS_AUDITED_SURFACES:
            text = _read(rel)
            for pat in _EDITOR_CENTRIC_CLOUD_PATTERNS:
                with self.subTest(path=rel, pattern=pat.pattern):
                    self.assertIsNone(
                        pat.search(text),
                        msg=f"{rel} matched editor-centric cloud pattern {pat.pattern!r}",
                    )

    def test_audit_report_p1_cloud_row_done(self):
        rel = "artifacts/report/mat-audit-report.md"
        if not _exists(rel):
            self.skipTest("mat-audit-report.md not present in this trimmed fixture")
        text = _read(rel)
        self.assertIn("Cloud Agents / Agents Window refresh", text)
        self.assertIn("**Done**", text)
        self.assertIn(self._ANCHOR, text)
        self.assertIn("P1CloudAgentsAgentsWindowDocsTest", text)


class WorktreeContractDocsTest(unittest.TestCase):
    """Forbid stale auto-worktree and base-4000 port ladder claims on operator-facing paths."""

    def test_worktree_contract_surfaces_reject_stale_claims(self):
        if _is_mat_sidecar_adoption_layout():
            self.skipTest("MAT sidecar adoption may omit full worktree doc set at repo root")

        missing = [p for p in _WORKTREE_CONTRACT_REL_PATHS if not _exists(p)]
        if missing:
            self.skipTest("worktree contract paths missing in this fixture: " + ", ".join(missing))

        for rel in _WORKTREE_CONTRACT_REL_PATHS:
            text = _read(rel)
            for pat in _WORKTREE_MISLEADING_PATTERNS:
                with self.subTest(path=rel, pattern=pat.pattern):
                    self.assertIsNone(
                        pat.search(text),
                        msg=f"{rel} matched misleading pattern {pat.pattern!r}",
                    )

    def test_bootstrap_script_documents_observability_ports(self):
        if not _exists(".cursor/hooks/bootstrap_worktree.sh"):
            self.skipTest("bootstrap_worktree.sh not present")
        text = _read(".cursor/hooks/bootstrap_worktree.sh")
        self.assertIn("OBSERVABILITY_PORT", text)
        self.assertIn("OBSERVABILITY_CLIENT_PORT", text)
        self.assertIn("cksum", text)
        self.assertIn("3001", text)
        self.assertIn("5173", text)

    def test_mat_wt_create_documents_runtime_env_contract(self):
        if not _exists(".cursor/commands/mat-wt-create.md"):
            self.skipTest("mat-wt-create command not present")
        text = _read(".cursor/commands/mat-wt-create.md")
        self.assertIn(".cursor/worktree/runtime.env", text)
        self.assertIn("OBSERVABILITY_PORT", text)
        self.assertIn("bootstrap_worktree.sh", text)


class RFU3NodePinCiTest(unittest.TestCase):
    """Phase C C2 (RFU-3): CI pins Node 22 for apps/client toolchain."""

    def test_phase1_verify_workflow_pins_node_22(self):
        rel = ".github/workflows/phase1-verify.yml"
        if not _exists(rel):
            self.skipTest("phase1-verify workflow not present")
        text = _read(rel)
        self.assertIn("actions/setup-node@v5", text)
        self.assertIn("node-version: 22", text)
        self.assertIn("Vite 8 requires Node 20.19+", text)


def _phase1_verify_client_block() -> str:
    """Extract apps/client block between cd and OK marker in phase1-verify.sh."""
    text = _read("scripts/phase1-verify.sh")
    start = text.find('cd "$ROOT/apps/client"')
    end = text.find("bun observability client: OK")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("apps/client block markers not found in phase1-verify.sh")
    return text[start:end]


class RFU1VitestOnlyCiTest(unittest.TestCase):
    """Phase C C3 (RFU-1): vitest-only client tests in phase1-verify.sh."""

    def test_client_block_uses_vitest_not_bun_test(self):
        if not _exists("scripts/phase1-verify.sh"):
            self.skipTest("phase1-verify.sh not present")
        block = _phase1_verify_client_block()
        self.assertIn("bun run test:vitest", block)
        for line in block.splitlines():
            cmd = line.split("#", 1)[0].strip()
            if cmd == "bun test" or cmd.startswith("bun test "):
                self.fail(f"standalone bun test must not run in client block: {line!r}")


class RFU2FrozenLockfileTest(unittest.TestCase):
    """Phase C C4 (RFU-2): frozen lockfile install in apps/client block."""

    def test_client_block_uses_frozen_lockfile(self):
        if not _exists("scripts/phase1-verify.sh"):
            self.skipTest("phase1-verify.sh not present")
        block = _phase1_verify_client_block()
        self.assertIn("bun install --frozen-lockfile", block)


def _dependabot_types_node_ignore_snippet(text: str) -> str:
    """Return YAML lines for the @types/node ignore list item (empty if missing)."""
    match = re.search(
        r'(?m)^\s*-\s+dependency-name:\s+"@types/node"\s*\n(?:^\s+.+\n)*',
        text,
    )
    return match.group(0) if match else ""


def _maintainer_dependabot_section() -> str:
    """Extract the Dependabot (apps/client) section from MAINTAINER.md."""
    text = _read("docs/reference/MAINTAINER.md")
    start = text.find("## Dependabot (`apps/client`)")
    if start < 0:
        return ""
    rest = text[start + 1 :]
    next_heading = re.search(r"\n## [^\n]+\n", rest)
    end = start + 1 + next_heading.start() if next_heading else len(text)
    return text[start:end]


class RFU4DependabotConfigTest(unittest.TestCase):
    """Phase C C5 (RFU-4): dependabot.yml for apps/client npm only."""

    def test_dependabot_config_exists_and_targets_client_only(self):
        rel = ".github/dependabot.yml"
        if not _exists(rel):
            self.skipTest("dependabot.yml not present")
        text = _read(rel)
        self.assertIn("package-ecosystem: npm", text)
        self.assertIn("directory: /apps/client", text)
        self.assertNotIn("/apps/server", text)
        self.assertIn("interval: weekly", text)
        self.assertIn("groups:", text)

    def test_dependabot_ignores_types_node_semver_major(self):
        rel = ".github/dependabot.yml"
        if not _exists(rel):
            self.skipTest("dependabot.yml not present")
        text = _read(rel)
        self.assertIn("ignore:", text, "dependabot.yml must declare an ignore block")
        snippet = _dependabot_types_node_ignore_snippet(text)
        self.assertTrue(
            snippet,
            'dependabot.yml must include ignore entry for dependency-name: "@types/node"',
        )
        self.assertIn(
            "version-update:semver-major",
            snippet,
            "@types/node ignore must include version-update:semver-major",
        )

    def test_maintainer_dependabot_section_documents_types_node_and_bun_lock(self):
        if not _exists("docs/reference/MAINTAINER.md"):
            self.skipTest("MAINTAINER.md not present")
        section = _maintainer_dependabot_section()
        self.assertTrue(section, "MAINTAINER must have Dependabot (apps/client) section")
        self.assertIn("@types/node", section)
        self.assertIn("bun.lock", section)
        self.assertIn("Node **22**", section)
        self.assertIn("security", section.lower())


class RFU1ClientCiDocsHygieneTest(unittest.TestCase):
    """Phase C C5 doc hygiene: pilot-report matches vitest-only client CI."""

    def test_pilot_report_describes_vitest_only_client_ci(self):
        if not _exists("docs/archive/pilot-report.md"):
            self.skipTest("pilot-report.md not present")
        pilot = _read("docs/archive/pilot-report.md")
        self.assertIn("test:vitest", pilot)
        for line in pilot.splitlines():
            if "apps/client" in line and "bun test" in line:
                self.fail(
                    "apps/client must not be paired with bun test in pilot-report: "
                    f"{line!r}"
                )

    def test_server_readme_documents_vitest_only_client_ci(self):
        rel = "apps/server/README.md"
        if not _exists(rel):
            self.skipTest("apps/server/README.md not present")
        text = _read(rel)
        self.assertIn("test:vitest", text)
        self.assertIn("vitest-only", text)


class MatUpdaterSecurityDocsTest(unittest.TestCase):
    """MAT updater slice 3: dry-run default, approval gate, no auto-commit, no silent AGENTS overwrite."""

    _DOC_PATHS = (
        "docs/reference/MAINTAINER.md",
        "docs/guides/getting-started-existing-projects.md",
        "docs/guides/adoption-safe-defaults.md",
        "validation-report.md",
    )

    def test_updater_security_honesty_strings_across_operator_docs(self):
        missing = [p for p in self._DOC_PATHS if not _exists(p)]
        if missing:
            self.skipTest(f"updater security doc paths missing: {missing}")
        texts = {p: _read(p) for p in self._DOC_PATHS}
        combined = "\n".join(texts.values()).lower()
        self.assertTrue(
            "dry-run" in combined or "dry run" in combined,
            "operator docs must describe dry-run-first default",
        )
        self.assertIn("--approved", combined, "approval gate (--approved) must be documented")
        self.assertTrue(
            "no auto-commit" in combined
            or "stops before commit" in combined
            or "stop before commit" in combined,
            "docs must state updater stops before commit/PR",
        )
        self.assertTrue(
            "no silent" in combined and "agents" in combined
            or "not silently overwrite" in combined
            or "product-owned" in combined,
            "docs must state AGENTS.md is not silently overwritten",
        )
        maintainer = texts["docs/reference/MAINTAINER.md"]
        self.assertIn("MAT updater operator runbook", maintainer)
        self.assertIn("artifacts/update-mat/", maintainer)
        validation = texts["validation-report.md"]
        self.assertIn("Slice 3", validation)
        self.assertIn("Operator checklist", validation)
        self.assertIn("getting-started-existing-projects.md", validation)
        existing = texts["docs/guides/getting-started-existing-projects.md"]
        self.assertIn(".mat/AGENTS.mat.md", existing)
        self.assertTrue(
            "bootstrap before" in existing.lower()
            or "bootstrap first" in existing.lower()
            or "requires bootstrap" in existing.lower(),
            "existing-project guide must state bootstrap before update-mat dry-run",
        )


class MatUpdaterDemoScriptTest(unittest.TestCase):
    """MAT updater operator demo: script exists, executable, honesty strings."""

    _SCRIPT_REL = "scripts/demo/updater-operator-walkthrough.sh"

    def test_demo_script_exists_executable_and_documents_honesty(self):
        script_path = REPO_ROOT / self._SCRIPT_REL
        if not script_path.is_file():
            self.skipTest(f"{self._SCRIPT_REL} not present")
        self.assertTrue(os.access(script_path, os.X_OK), "demo script must be executable")
        text = script_path.read_text(encoding="utf-8")
        required = (
            "dry-run",
            "plan-file=",
            "patch-file=",
            "audit-file=",
            "staging-worktree=",
            "approval required before commit or PR creation",
        )
        for needle in required:
            self.assertIn(needle, text, f"missing honesty string: {needle}")
        self.assertTrue(
            "rev-list --count" in text or "no new commit" in text.lower(),
            "script must assert no auto-commit on target root",
        )
        self.assertIn("demo-walkthrough-latest.md", text)
        self.assertIn("update-mat.py", text)
        self.assertIn("--apply", text)
        self.assertIn("--approved", text)
        self.assertIn("--plan-file", text)


class MatSyncDemoScriptTest(unittest.TestCase):
    """MAT mat-sync demo: script exists, executable, honesty strings."""

    _SCRIPT_REL = "scripts/demo/mat-sync-walkthrough.sh"

    def test_demo_script_exists_executable_and_documents_honesty(self):
        script_path = REPO_ROOT / self._SCRIPT_REL
        if not script_path.is_file():
            self.skipTest(f"{self._SCRIPT_REL} not present")
        self.assertTrue(os.access(script_path, os.X_OK), "demo script must be executable")
        text = script_path.read_text(encoding="utf-8")
        required = (
            "mat-sync.sh",
            "mat-sync-plan-file=",
            "phase verify: doctor",
            "approval required before commit or PR creation",
            "rev-list --count",
        )
        for needle in required:
            self.assertIn(needle, text, f"missing honesty string: {needle}")
        self.assertIn("demo-walkthrough-latest.md", text)
        self.assertIn("--approve-plan", text)


class MatSyncTeamRunbookDocsTest(unittest.TestCase):
    """Slice 4: mat-sync team runbook mandatory sections and GitHub-first cross-links."""

    _RUNBOOK_REL = "docs/guides/mat-sync-team-runbook.md"
    _CROSS_LINK_PATHS = (
        "docs/guides/getting-started-existing-projects.md",
        "docs/update-mat/index.md",
        ".cursor/commands/mat-sync.md",
        ".cursor/commands/mat-update-mat.md",
        "README.md",
        "docs/reference/components.md",
    )

    def test_runbook_exists_with_mandatory_sections(self):
        if not _exists(self._RUNBOOK_REL):
            self.skipTest(f"{self._RUNBOOK_REL} not present")
        text = _read(self._RUNBOOK_REL)
        required_sections = (
            "First adoption / refresh with source-config v2",
            "Pin tag vs SHA",
            "Cache location and refresh",
            "Troubleshooting",
            "true_drift",
            "registry_integrity",
            "Doctor worktrees",
            "whitespace",
            "Wattif-style rebootstrap expectations",
            "Wattif re-upgrade replay",
            "no local MAT path",
        )
        for needle in required_sections:
            with self.subTest(needle=needle):
                self.assertIn(needle, text, f"runbook missing: {needle}")
        self.assertIn("schema_version", text)
        self.assertIn("Devora-AS/multi-agent-workflow", text)
        self.assertIn("maintainer dev only", text.lower())

    def test_operator_surfaces_link_runbook_and_github_first(self):
        missing = [p for p in self._CROSS_LINK_PATHS if not _exists(p)]
        if missing:
            self.skipTest(f"cross-link paths missing: {missing}")
        for rel in self._CROSS_LINK_PATHS:
            with self.subTest(rel=rel):
                text = _read(rel)
                self.assertIn("mat-sync-team-runbook.md", text)
        readme = _read("README.md")
        self.assertTrue(
            "source-config" in readme.lower() and "v2" in readme.lower(),
            "README must document v2 source-config production path",
        )
        mat_sync_cmd = _read(".cursor/commands/mat-sync.md")
        self.assertIn("mat-sync-team-runbook.md", mat_sync_cmd)
        update_mat_cmd = _read(".cursor/commands/mat-update-mat.md")
        self.assertIn("maintainer dev only", update_mat_cmd.lower())


class MatAdvisorStrategyDocsTest(unittest.TestCase):
    """Slice 2: MAT advisor-strategy operator runbook + cross-links."""

    _RUNBOOK_REL = "docs/guides/mat-advisor-strategy-runbook.md"
    _CROSS_LINK_PATHS = (
        "docs/guides/planning-commands-guide.md",
        "docs/index.md",
        ".cursor/agents/parent-orchestrator.md",
        ".cursor/commands/mat-long-run.md",
        "docs/reference/components.md",
    )

    def test_runbook_exists_with_key_guidance(self):
        if not _exists(self._RUNBOOK_REL):
            self.skipTest(f"{self._RUNBOOK_REL} not present")
        text = _read(self._RUNBOOK_REL)
        required = (
            "advisor",
            "parallel",
            "paste-back",
            "non-goals",
            "/mat-long-run",
            "/mat-plan-team",
            "Trace Correlation",
            "git push",
            "hook auto-spawn",
            "MAO live",
        )
        for needle in required:
            with self.subTest(needle=needle):
                self.assertIn(needle, text, f"runbook missing: {needle}")
        self.assertIn("When to use advisor", text)
        self.assertIn("Paste-back checklist", text)
        self.assertIn("Explicit non-goals", text)

    def test_operator_surfaces_link_advisor_runbook(self):
        missing = [p for p in self._CROSS_LINK_PATHS if not _exists(p)]
        if missing:
            self.skipTest(f"cross-link paths missing: {missing}")
        for rel in self._CROSS_LINK_PATHS:
            with self.subTest(rel=rel):
                text = _read(rel)
                self.assertIn("mat-advisor-strategy-runbook.md", text)


class MatPromptTemplatesDocsTest(unittest.TestCase):
    """Slice 3: advisory prompt templates + operator guide (no runtime injection)."""

    _GUIDE_REL = "docs/guides/mat-prompt-templates.md"
    _TEMPLATES = (
        "docs/templates/prompt-builder-handoff.txt",
        "docs/templates/prompt-verifier-handoff.txt",
        "docs/templates/prompt-advisor-pasteback.txt",
    )
    _OPTIONAL_KICKOFF = "docs/templates/prompt-mat-plan-team-kickoff.txt"
    _CROSS_LINK_PATHS = (
        "docs/guides/planning-commands-guide.md",
        "docs/guides/mat-advisor-strategy-runbook.md",
        "docs/index.md",
        "docs/reference/components.md",
    )

    def test_templates_and_guide_exist_with_advisory_posture(self):
        missing = [p for p in self._TEMPLATES if not _exists(p)]
        if missing:
            self.skipTest(f"templates missing: {missing}")
        if not _exists(self._GUIDE_REL):
            self.skipTest(f"{self._GUIDE_REL} not present")
        guide = _read(self._GUIDE_REL)
        for needle in (
            "advisory",
            "Copy-paste",
            "not injected",
            "prompt-builder-handoff.txt",
            "prompt-verifier-handoff.txt",
            "prompt-advisor-pasteback.txt",
            "workflow-artifact-contract",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, guide)
        builder = _read(self._TEMPLATES[0])
        verifier = _read(self._TEMPLATES[1])
        pasteback = _read(self._TEMPLATES[2])
        for rel, text in (
            (self._TEMPLATES[0], builder),
            (self._TEMPLATES[1], verifier),
            (self._TEMPLATES[2], pasteback),
        ):
            with self.subTest(header=rel):
                self.assertTrue(
                    text.lstrip().startswith("#"),
                    f"{rel} should start with a usage header comment",
                )
                self.assertIn("Advisory", text)
                self.assertIn("{{", text)
        self.assertIn("build-result.md", builder)
        self.assertIn("MAO_TASK_CONTEXT_JSON", builder)
        self.assertIn("workflow-artifact-contract.md", builder)
        self.assertIn("verify-result.md", verifier)
        self.assertIn("MAO_TASK_CONTEXT_JSON", verifier)
        self.assertIn("paste-back", pasteback.lower())
        if _exists(self._OPTIONAL_KICKOFF):
            kickoff = _read(self._OPTIONAL_KICKOFF)
            self.assertIn("/mat-plan-team", kickoff)
            self.assertIn("Advisory", kickoff)

    def test_operator_surfaces_link_prompt_templates(self):
        missing = [p for p in self._CROSS_LINK_PATHS if not _exists(p)]
        if missing:
            self.skipTest(f"cross-link paths missing: {missing}")
        for rel in self._CROSS_LINK_PATHS:
            with self.subTest(rel=rel):
                text = _read(rel)
                self.assertTrue(
                    "mat-prompt-templates.md" in text or "prompt-builder-handoff.txt" in text,
                    f"{rel} should link prompt templates guide or template paths",
                )

    def test_roadmap_prompt_optimization_closed(self):
        if not _exists("ROADMAP.md"):
            self.skipTest("ROADMAP.md not present (adopted/minimal trees)")
        roadmap = _read("ROADMAP.md")
        self.assertIn("prompt-optimization", roadmap.lower())
        self.assertRegex(
            roadmap,
            r"- \[x\].*prompt-optimization patterns and reusable prompt templates",
        )
        self.assertIn("MatPromptTemplatesDocsTest", roadmap)


class MatTaskTypeComplexityTagsTest(unittest.TestCase):
    """Slice 4: optional Task type / Complexity tags (no YAML frontmatter; no preflight gates)."""

    @staticmethod
    def _plan_contract_text() -> str | None:
        """Source path or adoption sidecar dest (`.mat/docs/plan-contract.md`)."""
        for rel in (
            "docs/architecture/plan-contract.md",
            ".mat/docs/plan-contract.md",
        ):
            if _exists(rel):
                return _read(rel)
        return None

    def test_mat_plan_documents_optional_tags_and_allowlists(self):
        if not _exists(".cursor/commands/mat-plan.md"):
            self.skipTest("mat-plan command not present")
        cmd = _read(".cursor/commands/mat-plan.md")
        for needle in (
            "Task type",
            "Complexity",
            "chore",
            "feature",
            "refactor",
            "fix",
            "enhancement",
            "simple",
            "medium",
            "complex",
            "YAML frontmatter",
            "preflight",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, cmd)
        plan_contract = self._plan_contract_text()
        if plan_contract is None:
            self.skipTest("plan-contract.md not present (source or .mat/docs sidecar)")
        self.assertIn("tier2_task_type_invalid", plan_contract)
        self.assertIn("tier2_complexity_invalid", plan_contract)
        if _exists(".cursor/skills/mat-plan-contract/SKILL.md"):
            skill = _read(".cursor/skills/mat-plan-contract/SKILL.md")
            self.assertIn("Task type", skill)
        if _exists("docs/guides/planning-commands-guide.md"):
            guide = _read("docs/guides/planning-commands-guide.md")
            self.assertIn("Complexity tags", guide)

    def test_roadmap_task_type_complexity_closed(self):
        if not _exists("ROADMAP.md"):
            self.skipTest("ROADMAP.md not present (adopted/minimal trees)")
        roadmap = _read("ROADMAP.md")
        self.assertRegex(
            roadmap,
            r"- \[x\].*V1-style task type / complexity tags",
        )
        self.assertIn("MatTaskTypeComplexityTagsTest", roadmap)

    def test_roadmap_delivery_and_maturity_legend_documented(self):
        if not _exists("ROADMAP.md"):
            self.skipTest("ROADMAP.md not present (adopted/minimal trees)")
        roadmap = _read("ROADMAP.md")
        self.assertIn("**Delivery state**", roadmap)
        self.assertIn("Shipped features may remain Experimental", roadmap)
        self.assertIn("D2c", roadmap)
        self.assertIn("canonical scope gate", roadmap.lower())
        self.assertNotIn("d2 queued next", roadmap.lower())


class MatAdoptEntryDocsTest(unittest.TestCase):
    """Slice E: /mat-adopt orchestrator entry — 3-step flow and slash honesty."""

    _CMD_REL = ".cursor/commands/mat-adopt.md"
    _CROSS_LINK_PATHS = (
        "docs/guides/mat-sync-team-runbook.md",
        "docs/guides/getting-started-existing-projects.md",
        ".cursor/commands/mat-sync.md",
        "README.md",
        "docs/reference/components.md",
    )

    def test_mat_adopt_command_orchestrator_entry(self):
        if not _exists(self._CMD_REL):
            self.skipTest(f"{self._CMD_REL} not present")
        text = _read(self._CMD_REL)
        self.assertIn("# MAT Adopt", text)
        self.assertIn("/mat-adopt", text)
        self.assertIn("Step 1 — Plan", text)
        self.assertIn("Step 2 — Review preflight", text)
        self.assertIn("Step 3 — Approve", text)
        self.assertIn("plan → review preflight/previews → approve", text)
        self.assertIn("MAT source", text)
        self.assertIn("```txt", text)
        self.assertIn("mat-sync.sh --repo-root", text)
        self.assertIn("`/mat-sync` is not available", text)
        # Orchestration steps: exactly one ```txt block per step (Step 1-3)
        step_boundaries = (
            ("### Step 1 — Plan", "### Step 2 — Review preflight"),
            ("### Step 2 — Review preflight", "### Step 3 — Approve"),
            ("### Step 3 — Approve", "## Maintainer/debug fallback"),
        )
        for start_marker, end_marker in step_boundaries:
            with self.subTest(step=start_marker):
                start = text.find(start_marker)
                self.assertGreater(start, -1, f"missing {start_marker}")
                end = text.find(end_marker, start + len(start_marker))
                section = text[start:end] if end != -1 else text[start:]
                self.assertEqual(
                    section.count("```txt"),
                    1,
                    f"{start_marker} must have exactly one txt block",
                )

    def test_operator_surfaces_reference_mat_adopt_entry(self):
        missing = [p for p in self._CROSS_LINK_PATHS if not _exists(p)]
        if missing:
            self.skipTest(f"cross-link paths missing: {missing}")
        mat_adopt = _read(self._CMD_REL)
        self.assertIn("mat-sync-team-runbook.md", mat_adopt)
        for rel in self._CROSS_LINK_PATHS:
            with self.subTest(rel=rel):
                surface = _read(rel)
                self.assertIn("mat-adopt", surface.lower())
        mat_sync = _read(".cursor/commands/mat-sync.md")
        self.assertIn("First adoption vs refresh (phases)", mat_sync)
        self.assertIn("/mat-adopt", mat_sync)


class ExecutionCommandCloseoutTxtBlocksTest(unittest.TestCase):
    """Slice 3 planf3: execution commands — exactly one txt block per closeout phase."""

    _MAT_PLAN_TEAM = ".cursor/commands/mat-plan-team.md"
    _MAT_LONG_RUN = ".cursor/commands/mat-long-run.md"
    _MAT_SPRINT = ".cursor/commands/mat-sprint.md"
    _MAT_PLAN_UPDATE = ".cursor/commands/mat-plan-update.md"

    def _assert_exactly_one_txt_per_section(
        self,
        text: str,
        boundaries: tuple[tuple[str, str], ...],
    ) -> None:
        for start_marker, end_marker in boundaries:
            with self.subTest(phase=start_marker):
                start = text.find(start_marker)
                self.assertGreater(start, -1, f"missing {start_marker}")
                end = text.find(end_marker, start + len(start_marker))
                section = text[start:end] if end != -1 else text[start:]
                self.assertEqual(
                    section.count("```txt"),
                    1,
                    f"{start_marker} must have exactly one txt block",
                )

    def test_mat_plan_team_closeout_txt_discipline(self):
        if not _exists(self._MAT_PLAN_TEAM):
            self.skipTest(f"{self._MAT_PLAN_TEAM} not present")
        text = _read(self._MAT_PLAN_TEAM)
        self.assertIn("exactly one", text.lower())
        self.assertIn("```txt", text)
        self.assertIn("### Closeout — Plan written complete", text)
        self.assertIn("### Closeout — Build gate passed", text)
        self.assertIn("### Closeout — Verify complete", text)
        self.assertIn("### Closeout — Cycle complete / idle", text)
        self._assert_exactly_one_txt_per_section(
            text,
            (
                (
                    "### Closeout — Plan written complete",
                    "### Closeout — Build gate passed",
                ),
                (
                    "### Closeout — Build gate passed",
                    "### Closeout — Verify complete",
                ),
                (
                    "### Closeout — Verify complete",
                    "### Closeout — Cycle complete / idle",
                ),
                ("### Closeout — Cycle complete / idle", "### Step 0 — To-dos (MAO)"),
            ),
        )

    def test_mat_long_run_closeout_txt_discipline(self):
        if not _exists(self._MAT_LONG_RUN):
            self.skipTest(f"{self._MAT_LONG_RUN} not present")
        text = _read(self._MAT_LONG_RUN)
        self.assertIn("exactly one", text.lower())
        self.assertIn("```txt", text)
        self.assertIn("### Closeout — Mission gate continue", text)
        self.assertIn("### Closeout — Mission gate stop", text)
        self.assertIn("docs/session-summary.md", text)
        self._assert_exactly_one_txt_per_section(
            text,
            (
                (
                    "### Closeout — Plan written complete",
                    "### Closeout — Build gate passed",
                ),
                (
                    "### Closeout — Build gate passed",
                    "### Closeout — Verify complete",
                ),
                (
                    "### Closeout — Verify complete",
                    "### Closeout — Mission gate continue",
                ),
                (
                    "### Closeout — Mission gate continue",
                    "### Closeout — Mission gate stop",
                ),
                (
                    "### Closeout — Mission gate stop",
                    "## Relationship to other commands",
                ),
            ),
        )

    def test_mat_sprint_closeout_txt_discipline(self):
        if not _exists(self._MAT_SPRINT):
            self.skipTest(f"{self._MAT_SPRINT} not present")
        text = _read(self._MAT_SPRINT)
        self.assertIn("exactly one", text.lower())
        self.assertIn("```txt", text)
        self.assertIn("### Closeout — DoR satisfied", text)
        self.assertIn("### Closeout — Sprint review complete", text)
        self._assert_exactly_one_txt_per_section(
            text,
            (
                (
                    "### Closeout — DoR satisfied",
                    "### Closeout — Implement complete",
                ),
                (
                    "### Closeout — Implement complete",
                    "### Closeout — Verify complete",
                ),
                (
                    "### Closeout — Verify complete",
                    "### Closeout — Sprint review complete",
                ),
                (
                    "### Closeout — Sprint review complete",
                    "### Execution plan shape (lite tier)",
                ),
            ),
        )

    def test_mat_plan_update_closeout_txt_discipline(self):
        if not _exists(self._MAT_PLAN_UPDATE):
            self.skipTest(f"{self._MAT_PLAN_UPDATE} not present")
        text = _read(self._MAT_PLAN_UPDATE)
        self.assertIn("exactly one", text.lower())
        self.assertIn("```txt", text)
        self.assertIn("### Closeout — target validated", text)
        self.assertIn("### Closeout — edits applied", text)
        self.assertIn("### Closeout — escalate to onboarding", text)
        self.assertIn("### Closeout — idle / handoff", text)
        self._assert_exactly_one_txt_per_section(
            text,
            (
                (
                    "### Closeout — target validated",
                    "### Closeout — edits applied",
                ),
                (
                    "### Closeout — edits applied",
                    "### Closeout — escalate to onboarding",
                ),
                (
                    "### Closeout — escalate to onboarding",
                    "### Closeout — idle / handoff",
                ),
                (
                    "### Closeout — idle / handoff",
                    "### Recommended Next Command",
                ),
            ),
        )

    def test_planning_commands_guide_execution_closeout_reference(self):
        rel = "docs/guides/planning-commands-guide.md"
        if not _exists(rel):
            self.skipTest(f"{rel} not present")
        guide = _read(rel)
        self.assertIn("Recommended next command (execution commands)", guide)
        self.assertIn("mat-sync.md", guide)
        self.assertIn("mat-update-mat.md", guide)
        self.assertIn("exactly one", guide.lower())

    def test_parent_orchestrator_closeout_pointer(self):
        rel = ".cursor/agents/parent-orchestrator.md"
        if not _exists(rel):
            self.skipTest(f"{rel} not present")
        text = _read(rel)
        self.assertIn("exactly one", text.lower())
        self.assertIn("fenced `txt` block", text)
        self.assertIn("planning-commands-guide.md", text)
        self.assertIn("mat-plan-team.md", text)


class PreflightEscalationLadderDocTest(unittest.TestCase):
    """Slice 2 planf3: preflight escalation ladder — three layers, vocabulary honesty."""

    _LADDER_REL = "docs/architecture/preflight-escalation-ladder.md"
    _LADDER_SIDECAR_FLAT = ".mat/docs/preflight-escalation-ladder.md"
    _COMMAND_RELS = (
        ".cursor/commands/mat-plan.md",
        ".cursor/commands/mat-plan-onboarding.md",
        ".cursor/commands/mat-plan-team.md",
        ".cursor/commands/mat-long-run.md",
        ".cursor/commands/mat-sprint.md",
    )

    def _ladder_text(self) -> str:
        if _exists(self._LADDER_REL):
            return _read(self._LADDER_REL)
        if _exists(self._LADDER_SIDECAR_FLAT):
            return _read(self._LADDER_SIDECAR_FLAT)
        self.fail(f"{self._LADDER_REL} missing (also checked {self._LADDER_SIDECAR_FLAT})")

    def test_preflight_escalation_ladder_canonical_doc(self):
        text = self._ladder_text()
        self.assertIn("solo_plan_only", text)
        self.assertIn("ready_for_execution_handoff", text)
        self.assertIn("needs_plan_onboarding", text)
        self.assertIn("inline", text)
        self.assertIn("builder_plus_verifier", text)
        self.assertIn("parallel_spawn", text)
        self.assertIn("/mat-long-run", text)
        self.assertIn("Do not collapse", text)

    def test_preflight_escalation_ladder_cross_links(self):
        if _is_mat_sidecar_adoption_layout():
            self._ladder_text()
            for rel in self._COMMAND_RELS:
                with self.subTest(rel=rel):
                    if not _exists(rel):
                        self.skipTest(f"{rel} missing in sidecar fixture")
                    self.assertIn("preflight-escalation-ladder.md", _read(rel))
            skill = _read(".cursor/skills/mat-plan-contract/SKILL.md")
            self.assertIn("preflight-escalation-ladder.md", skill)
            sidecar_contract = ".mat/docs/plan-contract.md"
            if _exists(sidecar_contract):
                self.assertIn("preflight-escalation-ladder.md", _read(sidecar_contract))
            return

        self._ladder_text()
        guide = _read("docs/guides/planning-commands-guide.md")
        self.assertIn("preflight-escalation-ladder.md", guide)
        plan_contract = _read("docs/architecture/plan-contract.md")
        self.assertIn("preflight-escalation-ladder.md", plan_contract)
        layout = _read("scripts/adoption/adoption-layout-v1.json")
        self.assertIn("preflight-escalation-ladder.md", layout)
        for rel in self._COMMAND_RELS:
            with self.subTest(rel=rel):
                if not _exists(rel):
                    self.skipTest(f"{rel} missing")
                self.assertIn("preflight-escalation-ladder.md", _read(rel))
        skill = _read(".cursor/skills/mat-plan-contract/SKILL.md")
        self.assertIn("preflight-escalation-ladder.md", skill)


class CIPhase1VerifyCheckoutTest(unittest.TestCase):
    """CI checkout must fetch full git history for legacy fingerprint verification."""

    def test_phase1_verify_workflow_fetches_full_history(self):
        rel = ".github/workflows/phase1-verify.yml"
        if not _exists(rel):
            self.skipTest("phase1-verify workflow not present")
        text = _read(rel)
        self.assertRegex(text, r"fetch-depth:\s*0")
        self.assertIn("mat-legacy-fingerprints", text)


class RelatedPlansOptionalSectionTest(unittest.TestCase):
    """Tier 2d: optional Related plans tail-zone contract."""

    def test_mat_plan_related_plans_in_command(self):
        """Tier 2d: /mat-plan command locks Related plans tail-zone shape."""
        plan = _read(".cursor/commands/mat-plan.md")
        self.assertIn("## Related plans", plan)
        self.assertIn("### back_refs", plan)
        self.assertIn("### forward_refs", plan)
        self.assertIn("repo-root-relative", plan.lower())
        self.assertIn("/mat-plan-update", plan)
        self.assertIn("no automated graph resolver", plan.lower())

    def test_related_plans_docs_and_validator_cross_links(self):
        if not _exists("scripts/validate_planning_artifacts.py"):
            self.skipTest(
                "validate_planning_artifacts.py is MAT-source scope in adopted repos"
            )

        validator = _read("scripts/validate_planning_artifacts.py")
        self.assertIn("RELATED_PLANS_GRANDFATHERED_SOLO_PLANS", validator)
        self.assertIn("tier2_related_plans_missing_back_refs", validator)
        self.assertIn("tier2_related_plans_missing_forward_refs", validator)
        self.assertIn("tier2_related_plans_empty_subsection", validator)
        self.assertIn("tier2_related_plans_unquoted_path", validator)
        self.assertIn("planf3-audit-trail-mission.md", validator)

        template = _read("docs/templates/spec-template.md")
        self.assertIn("## Related plans", template)
        self.assertIn("### back_refs", template)

        onboarding = _read(".cursor/commands/mat-plan-onboarding.md")
        self.assertIn("## Related plans", onboarding)
        self.assertIn("plan-summary.md", onboarding)

        plan_update = _read(".cursor/commands/mat-plan-update.md")
        self.assertIn("back_refs", plan_update)
        self.assertIn("forward_refs", plan_update)

        contract = _read("docs/architecture/plan-contract.md")
        self.assertIn("Tier 2d", contract)
        self.assertIn("RELATED_PLANS_GRANDFATHERED_SOLO_PLANS", contract)

        maintainer = _read("docs/reference/MAINTAINER.md")
        self.assertIn("RELATED_PLANS_GRANDFATHERED_SOLO_PLANS", maintainer)
        self.assertIn("Tier 2d", maintainer)

        guide = _read("docs/guides/planning-commands-guide.md")
        self.assertIn("Tier 2d", guide)
        self.assertIn("### back_refs", guide)

        if _is_mat_sidecar_adoption_layout():
            self.skipTest("root CHANGELOG is product-owned in adopted repos")
        changelog = _read("CHANGELOG.md")
        self.assertIn("cross-plan-refs", changelog)


class OpenDecisionsOptionalSectionTest(unittest.TestCase):
    """Tier 2e: optional Open Decisions tail-zone contract."""

    def test_mat_plan_open_decisions_in_command(self):
        """Tier 2e: /mat-plan command locks Open Decisions tail-zone shape."""
        plan = _read(".cursor/commands/mat-plan.md")
        self.assertIn("## Open Decisions", plan)
        self.assertIn("**OD-", plan)
        self.assertIn("status: `open`", plan)
        self.assertIn("status: `resolved`", plan)
        self.assertIn("status: `deferred`", plan)
        self.assertIn("distinct", plan.lower())
        self.assertIn("Assumptions", plan)
        self.assertIn("Risks and Open Questions", plan)
        self.assertIn("## Related plans", plan)
        self.assertIn("/mat-plan-update", plan)

    def test_open_decisions_docs_and_validator_cross_links(self):
        if not _exists("scripts/validate_planning_artifacts.py"):
            self.skipTest(
                "validate_planning_artifacts.py is MAT-source scope in adopted repos"
            )

        validator = _read("scripts/validate_planning_artifacts.py")
        self.assertIn("OPEN_DECISIONS_GRANDFATHERED_SOLO_PLANS", validator)
        self.assertIn("tier2_open_decisions_malformed_row", validator)
        self.assertIn("tier2_open_decisions_invalid_status", validator)
        self.assertIn("tier2_open_decisions_resolved_missing_provenance", validator)
        self.assertIn("planf3-audit-trail-mission.md", validator)

        template = _read("docs/templates/spec-template.md")
        self.assertIn("## Open Decisions", template)
        self.assertIn("OD-###", template)

        onboarding = _read(".cursor/commands/mat-plan-onboarding.md")
        self.assertIn("one question at a time", onboarding.lower())
        self.assertIn("mirror", onboarding.lower())
        self.assertIn("## Open Decisions", onboarding)
        self.assertIn("plan-summary.md", onboarding)

        plan_update = _read(".cursor/commands/mat-plan-update.md")
        self.assertIn("Open Decisions", plan_update)
        self.assertIn("OD-###", plan_update)

        arch = _read("docs/architecture/open-decisions-optional-tier.md")
        self.assertIn("questionables", arch.lower())
        self.assertIn("one-at-a-time", arch.lower())

        contract = _read("docs/architecture/plan-contract.md")
        self.assertIn("Tier 2e", contract)
        self.assertIn("OPEN_DECISIONS_GRANDFATHERED_SOLO_PLANS", contract)

        maintainer = _read("docs/reference/MAINTAINER.md")
        self.assertIn("OPEN_DECISIONS_GRANDFATHERED_SOLO_PLANS", maintainer)
        self.assertIn("Tier 2e", maintainer)

        guide = _read("docs/guides/planning-commands-guide.md")
        self.assertIn("Tier 2e", guide)
        self.assertIn("OD-###", guide)

        layout = _read("scripts/adoption/adoption-layout-v1.json")
        self.assertIn("open-decisions-optional-tier.md", layout)

        if _is_mat_sidecar_adoption_layout():
            self.skipTest("root CHANGELOG is product-owned in adopted repos")
        changelog = _read("CHANGELOG.md")
        self.assertIn("open-decisions", changelog)


def _extract_planning_step0_block(cmd_text: str) -> str:
    """Return Step 0 prose block from a planning command (mat-plan or onboarding)."""
    match = re.search(
        r"\*\*Step 0\s*[—\-–]\s*Deep analysis.*?(?=\n\d+\.\s|\n###\s|\n##\s|\Z)",
        cmd_text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        match = re.search(
            r"Step 0\s*[—\-–]\s*Deep analysis.*?(?=\n\d+\.\s|\n###\s|\n##\s|\Z)",
            cmd_text,
            re.IGNORECASE | re.DOTALL,
        )
    return match.group(0) if match else ""


class DeepAnalysisStep0Test(unittest.TestCase):
    """Slice 1: Planning Step 0 — deep analysis before artifact writes (SOP-only)."""

    def test_mat_plan_and_onboarding_document_step0(self):
        mat_plan = _read(".cursor/commands/mat-plan.md")
        onboarding = _read(".cursor/commands/mat-plan-onboarding.md")

        for label, cmd_text in (
            ("mat-plan", mat_plan),
            ("mat-plan-onboarding", onboarding),
        ):
            self.assertRegex(
                cmd_text,
                r"Step 0\s*[—\-–]\s*Deep analysis",
                msg=f"{label} missing Step 0 — Deep analysis heading",
            )
            self.assertIn(
                "before any planning artifact writes",
                cmd_text.lower(),
                msg=f"{label} missing before-writes gate phrase",
            )

        for phrase in ("**Restate**", "**Surface**", "**Choose**", "**Decide**"):
            self.assertIn(phrase, mat_plan)
            self.assertIn(phrase, onboarding)

    def test_execution_step0_distinction_in_execution_commands(self):
        team = _read(".cursor/commands/mat-plan-team.md")
        long_run = _read(".cursor/commands/mat-long-run.md")
        combined = team + long_run
        combined_lower = combined.lower()
        self.assertIn(
            "planning step 0",
            combined_lower,
            msg="execution commands must distinguish planning Step 0",
        )
        self.assertIn(
            "execution step 0",
            combined_lower,
            msg="execution commands must name execution Step 0",
        )
        self.assertIn("preflight-escalation-ladder", combined)

    def test_no_ultrathink_or_think_hard_in_planning_commands(self):
        for rel_path in (
            ".cursor/commands/mat-plan.md",
            ".cursor/commands/mat-plan-onboarding.md",
        ):
            cmd_text = _read(rel_path)
            self.assertNotIn("ultrathink", cmd_text.lower(), msg=rel_path)
            self.assertNotIn("think hard", cmd_text.lower(), msg=rel_path)

    def test_step0_sop_only_no_hook_mao_enforcement(self):
        forbidden = (
            "hook enforcement",
            "hooks enforce",
            "mao transition enforcement",
            "todowrite",
            "curator_mao_gate",
        )
        for rel_path in (
            ".cursor/commands/mat-plan.md",
            ".cursor/commands/mat-plan-onboarding.md",
        ):
            step0 = _extract_planning_step0_block(_read(rel_path))
            self.assertTrue(step0, msg=f"{rel_path} Step 0 block not found")
            step0_lower = step0.lower()
            for phrase in forbidden:
                self.assertNotIn(
                    phrase,
                    step0_lower,
                    msg=f"{rel_path} Step 0 must not claim {phrase!r}",
                )

    def test_step0_docs_skill_and_changelog_cross_links(self):
        if _is_mat_sidecar_adoption_layout():
            self.skipTest(
                "root docs/ and CHANGELOG are MAT-source scope in adopted repos"
            )
        if not _exists("scripts/validate_planning_artifacts.py"):
            self.skipTest(
                "validate_planning_artifacts.py is MAT-source scope in adopted repos"
            )

        contract = _read("docs/architecture/plan-contract.md")
        guide = _read("docs/guides/planning-commands-guide.md")
        maintainer = _read("docs/reference/MAINTAINER.md")
        skill = _read(".cursor/skills/mat-plan-contract/SKILL.md")
        template = _read("docs/templates/spec-template.md")

        self.assertIn("Planning Step 0", contract)
        self.assertIn("Deep analysis before writes", guide)
        self.assertIn("DeepAnalysisStep0Test", maintainer)
        self.assertIn("Planning Step 0", skill)
        self.assertIn("step 0 deep analysis", template.lower())

        changelog = _read("CHANGELOG.md")
        self.assertIn("deep-analysis-step0", changelog)


class PlanningDocsInputsTest(unittest.TestCase):
    """Slice 2: Optional planning doc inputs from docs/ and ai_docs/."""

    def test_mat_plan_step2_and_onboarding_step3_optional_doc_inputs(self):
        mat_plan = _read(".cursor/commands/mat-plan.md")
        onboarding = _read(".cursor/commands/mat-plan-onboarding.md")

        self.assertRegex(
            mat_plan,
            r"2\.\s*Research the repo",
            msg="mat-plan missing workflow step 2 — Research the repo",
        )
        self.assertRegex(
            onboarding,
            r"3\.\s*Run guided discovery",
            msg="mat-plan-onboarding missing workflow step 3 — Run guided discovery",
        )

        for label, cmd_text in (
            ("mat-plan", mat_plan),
            ("mat-plan-onboarding", onboarding),
        ):
            self.assertIn(
                "Optional planning doc inputs",
                cmd_text,
                msg=f"{label} missing Optional planning doc inputs subsection",
            )
            self.assertIn(
                "skip-when-absent",
                cmd_text.lower(),
                msg=f"{label} missing skip-when-absent language",
            )
            self.assertIn(
                "optional-when-present",
                cmd_text.lower(),
                msg=f"{label} missing optional-when-present language",
            )
            self.assertIn("ai_docs/", cmd_text, msg=f"{label} missing ai_docs/")
            self.assertIn("docs/", cmd_text, msg=f"{label} missing docs/")
            self.assertNotIn(
                "AI_DOCS/",
                cmd_text,
                msg=f"{label} must use lowercase ai_docs/ not AI_DOCS/",
            )

        self.assertIn(
            "deferred",
            mat_plan.lower(),
            msg="mat-plan must defer literal APP_DOCS/ directory rename",
        )

    def test_context_budget_cross_link_and_no_path_existence_validator(self):
        mat_plan = _read(".cursor/commands/mat-plan.md")
        onboarding = _read(".cursor/commands/mat-plan-onboarding.md")
        combined = mat_plan + onboarding

        self.assertIn("context-budget-policy", combined)
        for label, cmd_text in (
            ("mat-plan", mat_plan),
            ("mat-plan-onboarding", onboarding),
        ):
            marker = "Optional planning doc inputs"
            idx = cmd_text.find(marker)
            self.assertNotEqual(
                idx, -1, msg=f"{label} missing {marker!r} block for scoped check"
            )
            block_lower = cmd_text[idx : idx + 2000].lower()
            for phrase in (
                "path-existence check",
                "path existence validator",
            ):
                self.assertNotIn(
                    phrase,
                    block_lower,
                    msg=f"{label} optional doc inputs must not claim {phrase!r}",
                )

    def test_planning_guide_cross_links_and_changelog(self):
        if _is_mat_sidecar_adoption_layout():
            self.skipTest(
                "root docs/ and CHANGELOG are MAT-source scope in adopted repos"
            )

        guide = _read("docs/guides/planning-commands-guide.md")
        self.assertIn("Planning doc inputs", guide)
        self.assertIn("ai_docs/", guide)
        self.assertIn("docs/", guide)
        self.assertIn("context-budget-policy", guide)
        self.assertIn("mat-prime", guide.lower())
        self.assertIn("docs-scraper", guide.lower())

        mat_prime = _read(".cursor/commands/mat-prime.md")
        self.assertIn("planning-commands-guide", mat_prime)

        docs_scraper = _read(".cursor/agents/docs-scraper.md")
        self.assertIn("planning-commands-guide", docs_scraper)
        self.assertIn("ai_docs/", docs_scraper)

        contract = _read("docs/architecture/plan-contract.md")
        self.assertIn("PlanningDocsInputsTest", contract)
        self.assertIn("optional-when-present", contract.lower())

        config = _read("docs/reference/configuration.md")
        self.assertIn("planning-commands-guide", config)
        self.assertIn("ai_docs/", config)

        changelog = _read("CHANGELOG.md")
        self.assertIn("planning-docs-inputs", changelog)


class PlanMetadataOptionalSectionTest(unittest.TestCase):
    """Tier 4 extension: optional Plan metadata on execution projections."""

    def test_execution_commands_document_plan_metadata(self):
        for rel_path in (
            ".cursor/commands/mat-plan-team.md",
            ".cursor/commands/mat-long-run.md",
            ".cursor/commands/mat-sprint.md",
        ):
            cmd = _read(rel_path)
            self.assertIn("## Plan metadata", cmd)
            self.assertIn("### modified", cmd)
            self.assertIn("### session", cmd)
            self.assertIn("### commit", cmd)
            self.assertIn("append-only", cmd.lower())
            self.assertIn("do not", cmd.lower())
            self.assertIn("auto-write", cmd.lower())

    def test_plan_metadata_docs_and_validator_cross_links(self):
        if not _exists("scripts/validate_planning_artifacts.py"):
            self.skipTest(
                "validate_planning_artifacts.py is MAT-source scope in adopted repos"
            )

        validator = _read("scripts/validate_planning_artifacts.py")
        self.assertIn("tier4_metadata_malformed_entry", validator)
        self.assertIn("tier4_metadata_missing_modified", validator)
        self.assertIn("_validate_tier4_plan_metadata", validator)

        exec_template = _read("docs/templates/execution-plan-template.md")
        self.assertIn("## Plan metadata", exec_template)
        self.assertIn("NOT YAML frontmatter", exec_template)

        lite_template = _read("docs/templates/adoption-minimal-current-plan.md")
        self.assertIn("## Plan metadata", lite_template)

        orchestrator = _read(".cursor/agents/parent-orchestrator.md")
        self.assertIn("## Plan metadata", orchestrator)
        self.assertIn("not", orchestrator.lower())

        contract = _read("docs/architecture/plan-contract.md")
        self.assertIn("audit-only", contract)
        self.assertIn("Tier 4 extension", contract)
        self.assertIn("layer 4 MAO", contract)

        guide = _read("docs/guides/planning-commands-guide.md")
        self.assertIn("Plan metadata", guide)
        self.assertIn("Tier 4", guide)

        fixture = _read("tests/fixtures/planning/plan-metadata-pass.md")
        self.assertIn("### modified", fixture)
        self.assertIn("### session", fixture)
        self.assertIn("### commit", fixture)

        if _is_mat_sidecar_adoption_layout():
            self.skipTest("root CHANGELOG is product-owned in adopted repos")
        changelog = _read("CHANGELOG.md")
        self.assertIn("plan-metadata-header", changelog)


class MatPlanUpdateCommandTest(unittest.TestCase):
    """ROADMAP L107–108: /mat-plan-update planning-only workflow."""

    def test_mat_plan_update_command_and_cross_links(self):
        if not _exists(".cursor/commands/mat-plan-update.md"):
            self.fail(".cursor/commands/mat-plan-update.md missing")

        cmd = _read(".cursor/commands/mat-plan-update.md")
        self.assertIn("# MAT Plan Update", cmd)
        self.assertIn("/mat-plan-update", cmd)
        self.assertIn("Planning only — no implementation.", cmd)
        self.assertIn("## Amendments", cmd)
        self.assertIn("append-only", cmd.lower())
        self.assertIn("escalate_to_onboarding", cmd)
        self.assertIn("re-project", cmd.lower())
        self.assertIn("Recommended Next Command", cmd)
        self.assertIn("Do not auto-edit `docs/current-plan.md`", cmd)

        if not _exists("docs/guides/planning-commands-guide.md"):
            self.skipTest("planning commands guide not present in this trimmed fixture")
        guide = _read("docs/guides/planning-commands-guide.md")
        self.assertIn("/mat-plan-update", guide)

        if not _exists("docs/architecture/preflight-escalation-ladder.md"):
            self.skipTest("preflight escalation ladder not present in this trimmed fixture")
        ladder = _read("docs/architecture/preflight-escalation-ladder.md")
        self.assertIn("/mat-plan-update", ladder)
        self.assertIn("Approved plan drifts slightly", ladder)

        onboarding = _read(".cursor/commands/mat-plan-onboarding.md")
        self.assertIn("/mat-plan-update", onboarding)

        decision = _read("docs/reference/decision-record.md")
        self.assertIn("`mat-plan-update`", decision)
        self.assertIn("`mat-adopt`", decision)

        skill = _read(".cursor/skills/mat-plan-contract/SKILL.md")
        self.assertIn("Decision F — Surgical plan update", skill)

        if _is_mat_sidecar_adoption_layout():
            self.skipTest("MAT sidecar adoption defers root README/AGENTS inventory locks to product repo")
        agents = _read("AGENTS.md")
        self.assertIn("/mat-plan-update", agents)

        readme = _read("README.md")
        self.assertIn("/mat-plan-update", readme)


class MatPlanDepthRouterTest(unittest.TestCase):
    """ROADMAP Next: /mat-plan --depth thin router (2026-07-06)."""

    def test_mat_plan_depth_router_docs(self):
        if not _exists(".cursor/commands/mat-plan.md"):
            self.fail(".cursor/commands/mat-plan.md missing")

        cmd = _read(".cursor/commands/mat-plan.md")
        self.assertIn("## Depth router", cmd)
        self.assertIn("--depth=", cmd)
        self.assertIn("lite", cmd)
        self.assertIn("standard", cmd)
        self.assertIn("onboarding", cmd)
        self.assertIn("team", cmd)
        self.assertIn("long-run", cmd)
        self.assertIn("/mat-sprint", cmd)
        self.assertIn("/mat-plan-onboarding", cmd)
        self.assertIn("/mat-plan-team", cmd)
        self.assertIn("/mat-long-run", cmd)
        self.assertIn("fail closed", cmd.lower())
        explicit_routing = (
            "do not auto-infer" in cmd.lower()
            or "explicit aliases" in cmd.lower()
            or "explicit alias" in cmd.lower()
        )
        self.assertTrue(
            explicit_routing,
            "mat-plan.md must document explicit-only routing (no fuzzy/LLM routing)",
        )
        self.assertIn("Dispatching to", cmd)

        if not _exists("docs/guides/planning-commands-guide.md"):
            self.skipTest("planning commands guide not present in this trimmed fixture")
        guide = _read("docs/guides/planning-commands-guide.md")
        self.assertIn("Depth router", guide)
        self.assertIn("--depth", guide)


class MatUpdaterHardeningDocsTest(unittest.TestCase):
    """mat-updater-hardening slice 4: env merge preview, MAT-tool sample merge, .mat/docs refresh honesty."""

    _DOC_PATHS = (
        "docs/guides/mat-sync-team-runbook.md",
        "docs/guides/getting-started-existing-projects.md",
        ".cursor/commands/mat-sync.md",
        ".cursor/commands/mat-update-mat.md",
        "PANCAKESWAP-BOT-MAT-RUNBOOK.md",
        "CHANGELOG.md",
    )

    def test_updater_hardening_operator_docs(self):
        missing = [p for p in self._DOC_PATHS if not _exists(p)]
        if missing:
            self.skipTest(f"updater hardening doc paths missing: {missing}")
        runbook = _read("docs/guides/mat-sync-team-runbook.md")
        self.assertIn("env_sample_merge_preview", runbook)
        self.assertIn("MAT-tool", runbook)
        self.assertIn("schema v3", runbook.lower())
        self.assertIn("skills", runbook.lower())
        self.assertIn("rules", runbook.lower())
        self.assertIn("does **not** auto-merge live **`.env`**", runbook)

        existing = _read("docs/guides/getting-started-existing-projects.md")
        self.assertIn("env_sample_merge_preview", existing)
        self.assertIn("MAT-tool", existing)
        self.assertIn("not wholesale overwrite", existing.lower())
        self.assertIn(".mat/docs/", existing)
        self.assertIn("does **not** auto-merge live **`.env`**", existing)

        mat_sync = _read(".cursor/commands/mat-sync.md")
        self.assertIn("env_sample_merge_preview", mat_sync)
        self.assertIn("mat_env_sample_merge.py", mat_sync)

        update_mat = _read(".cursor/commands/mat-update-mat.md")
        self.assertIn("env_sample_merge_preview", update_mat)
        self.assertIn(".mat/docs/", update_mat)
        self.assertIn("does **not** touch live **`.env`**", update_mat)

        pancake = _read("PANCAKESWAP-BOT-MAT-RUNBOOK.md")
        self.assertIn("MAT-tool", pancake)
        self.assertIn("does **not** auto-merge live **`.env`**", pancake)
        self.assertNotIn("auto-merge live .env", pancake.lower().replace("**", ""))

        changelog = _read("CHANGELOG.md")
        self.assertIn("mat-updater-hardening", changelog.lower())
        self.assertIn("mat_env_sample_merge.py", changelog)
        self.assertIn("schema v3", changelog.lower())


class OperatorPlaybookDocsTest(unittest.TestCase):
    """O1: mat-operator-playbook shipped habits guide."""

    def test_operator_playbook_surfaces(self):
        playbook_rel = "docs/guides/mat-operator-playbook.md"
        if not _exists(playbook_rel):
            self.skipTest(
                f"{playbook_rel} not present (MAT source-only; adopted fixtures omit full docs/)"
            )
        text = _read(playbook_rel)
        self.assertIn("Files → parent transition check → TodoWrite → dispatch", text)
        self.assertIn("source-full", text)
        self.assertIn("source-python-only", text)
        self.assertIn("adopted-operational", text)
        self.assertIn("adopted-contract", text)
        self.assertIn("**do not block**", text)
        self.assertIn("Codebase Search", text)
        self.assertIn("CURSOR_MAT_POST_TOOL_SCOPED_VALIDATE", text)
        self.assertIn("post_tool_validate.py", text)
        self.assertIn("phase1-verify", text)
        self.assertIn("vue-tsc", text)
        self.assertIn("Does not replace", text)
        self.assertIn("E8b operator map", text)
        self.assertIn("B10. Self-Compact", text)
        self.assertIn("mat-context-gauge.py", text)
        self.assertIn("Tier 2c", text)
        self.assertIn("grandfathered", text.lower())
        for guide in (
            "docs/guides/getting-started-existing-projects.md",
            "docs/guides/quick-start.md",
        ):
            if not _exists(guide):
                self.skipTest(f"{guide} not present")
            self.assertIn("mat-operator-playbook.md", _read(guide))
        contract = _read("docs/reference/env-write-contract.md")
        self.assertIn("mat-operator-playbook.md", contract)


class WorkflowDocsEnvWriteContractTest(unittest.TestCase):
    """M10: env-write contract reference + existing-project guide cross-links."""

    def test_env_write_contract_operator_surfaces(self):
        contract_rel = "docs/reference/env-write-contract.md"
        existing_rel = "docs/guides/getting-started-existing-projects.md"
        if not _exists(contract_rel) or not _exists(existing_rel):
            self.skipTest("M10 env-write contract docs not present")
        contract = _read(contract_rel)
        self.assertIn("test_adopt_env_write_contract", contract)
        self.assertIn("fail closed", contract.lower())
        self.assertIn("scripts/adoption/bootstrap-workflow-into-repo.sh", contract)
        self.assertIn("scripts/setup-dev.sh", contract)
        self.assertIn("M1", contract)
        existing = _read(existing_rel)
        self.assertIn("env-write-contract.md", existing)
        self.assertIn("test_adopt_env_write_contract.py", existing)
        self.assertIn("fail closed", existing.lower())
        changelog = _read("CHANGELOG.md")
        self.assertIn("env-write-contract", changelog.lower())
        self.assertIn("test_adopt_env_write_contract", changelog)


class MatSidecarEnvDocsTest(unittest.TestCase):
    """mat-sidecar-env-v1: sidecar env files, loader, and operator doc honesty."""

    def test_sidecar_env_operator_surfaces(self):
        for rel in (
            "docs/reference/configuration.md",
            "AGENTS.md",
            "CHANGELOG.md",
            "specs/mat-sidecar-env-v1.md",
        ):
            if not _exists(rel):
                self.skipTest(f"{rel} not present")
        config = _read("docs/reference/configuration.md")
        self.assertIn(".mat.env.sample", config)
        self.assertIn("scripts/lib/mat_env.py", config)
        self.assertIn("never auto-merged", config.lower())
        agents = _read("AGENTS.md")
        self.assertIn(".mat.env.sample", agents)
        changelog = _read("CHANGELOG.md")
        self.assertIn("mat-sidecar-env", changelog.lower())
        self.assertIn("mat_env.py", changelog)
        if _exists(".mat.env.sample"):
            mat_sample = _read(".mat.env.sample")
            self.assertIn("MAT-tool", mat_sample)
            self.assertIn("CURSOR_MAT_LOOP_POLICY", mat_sample)
        if _exists(".env.sample"):
            product = _read(".env.sample")
            self.assertIn(".mat.env.sample", product)
            self.assertNotIn("MAT-tool", product)

    def test_readme_quick_start_sidecar_env(self):
        for rel in ("README.md", "docs/guides/quick-start.md"):
            if not _exists(rel):
                self.skipTest(f"{rel} not present")
        readme = _read("README.md")
        self.assertIn("cp .mat.env.sample .mat.env", readme)
        self.assertIn("cp .env.sample .env", readme)
        quick = _read("docs/guides/quick-start.md")
        self.assertIn("cp .mat.env.sample .mat.env", quick)
        self.assertIn("cp .env.sample .env", quick)
        self.assertIn(".mat.env.sample", quick)
        self.assertIn("CURSOR_MAT_LOOP_POLICY", quick)

    def test_neuroarxiv_skill_mat_env_sample(self):
        rel = ".cursor/skills/neuroarxiv/SKILL.md"
        if not _exists(rel):
            self.skipTest(f"{rel} not present")
        text = _read(rel)
        self.assertIn(".mat.env.sample", text)
        self.assertNotIn("in `.env.sample`", text)

    def test_parent_orchestrator_loop_policy_mat_env_sample(self):
        rel = ".cursor/agents/parent-orchestrator.md"
        if not _exists(rel):
            self.skipTest(f"{rel} not present")
        text = _read(rel)
        self.assertIn("CURSOR_MAT_LOOP_POLICY", text)
        self.assertIn(".mat.env.sample", text)
        self.assertNotRegex(text, r"CURSOR_MAT_LOOP_POLICY=1`[^\n]*`\.env\.sample`")

    def test_pancakeswap_runbook_mat_env_sample(self):
        rel = "PANCAKESWAP-BOT-MAT-RUNBOOK.md"
        if not _exists(rel):
            self.skipTest(f"{rel} not present")
        text = _read(rel)
        self.assertIn(".mat.env.sample", text)
        self.assertIn(".mat.env", text)
        self.assertIn("MAT-tool", text)


class MatDiscoveryResearchSkillsSpecTest(unittest.TestCase):
    """Slice 2: lock key phrases in specs/mat-discovery-research-skills.md."""

    def test_discovery_research_skills_spec_key_phrases(self):
        if not _exists("specs/mat-discovery-research-skills.md"):
            self.skipTest("discovery/research skills spec not present in this layout")
        text = _read("specs/mat-discovery-research-skills.md")
        for phrase in (
            "mat-preflight-gated",
            "novel_research_required",
            "88f1ecc",
            "b5d20ef",
            "scout-report-suggest",
            "G2",
        ):
            self.assertIn(phrase, text, msg=f"missing phrase: {phrase}")


class MatDiscoveryResearchSkillsSafetyPackTest(unittest.TestCase):
    """Slice 5: safety/provenance pack — MAINTAINER, configuration, doctor, B13 cross-link."""

    _MAINTAINER_REL = "docs/reference/MAINTAINER.md"
    _CONFIG_REL = "docs/reference/configuration.md"
    _MAT_ENV_SAMPLE_REL = ".mat.env.sample"
    _ENV_SAMPLE_REL = ".env.sample"
    _MAT_DOCTOR_REL = ".cursor/commands/mat-doctor.md"
    _SIDECAR_REL = "docs/guides/sssf-patterns-sidecar.md"

    def test_maintainer_discovery_research_skills_section(self):
        if not _exists(self._MAINTAINER_REL):
            self.skipTest(f"{self._MAINTAINER_REL} not present")
        text = _read(self._MAINTAINER_REL)
        self.assertIn("Discovery & research skills", text)
        for phrase in (
            "inline citations",
            "G2",
            "never auto-escalate",
            "read-only",
            "prompt injection",
            "CURSOR_MAT_NEUROARXIV_REQUIRES_APPROVAL",
            "MAX_NEUROARXIV_PAPERS",
            "MAX_ARXIV_CATEGORIES",
            "artifacts/external-skills/",
            "sssf-patterns-sidecar.md",
            "External skill borrow",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text, msg=f"MAINTAINER missing: {phrase}")
        self.assertIn("--research-skills", text)

    def test_configuration_env_caps_documented(self):
        if not _exists(self._CONFIG_REL):
            self.skipTest(f"{self._CONFIG_REL} not present")
        config = _read(self._CONFIG_REL)
        self.assertIn("Layer 0 preflight", config)
        for var in (
            "CURSOR_MAT_NEUROARXIV_REQUIRES_APPROVAL",
            "MAX_NEUROARXIV_PAPERS",
            "MAX_ARXIV_CATEGORIES",
        ):
            with self.subTest(var=var):
                self.assertIn(var, config)
        self.assertIn("8", config)
        self.assertIn("3", config)
        if _exists(self._MAT_ENV_SAMPLE_REL):
            sample = _read(self._MAT_ENV_SAMPLE_REL)
            for var in (
                "CURSOR_MAT_NEUROARXIV_REQUIRES_APPROVAL",
                "MAX_NEUROARXIV_PAPERS",
                "MAX_ARXIV_CATEGORIES",
            ):
                with self.subTest(env_sample=var):
                    self.assertIn(var, sample)
        if _exists(self._ENV_SAMPLE_REL):
            product_sample = _read(self._ENV_SAMPLE_REL)
            self.assertIn(".mat.env.sample", product_sample)
            self.assertNotIn("MAT-tool", product_sample)

    def test_doctor_research_skills_flag_documented(self):
        if not _exists(self._MAT_DOCTOR_REL):
            self.skipTest(f"{self._MAT_DOCTOR_REL} not present")
        mat_doctor = _read(self._MAT_DOCTOR_REL)
        self.assertIn("--research-skills", mat_doctor)
        self.assertIn("advisory", mat_doctor.lower())
        self.assertIn("validate_research_skills", mat_doctor)


class MatSssfPatternsSidecarDocsTest(unittest.TestCase):
    """Slice 3 (B13): SSSF patterns sidecar guide + docs index discoverability."""

    _GUIDE_REL = "docs/guides/sssf-patterns-sidecar.md"
    _CROSS_LINK_PATHS = (
        "docs/index.md",
        "specs/mat-discovery-research-skills.md",
    )

    def test_sidecar_guide_key_phrases(self):
        if not _exists(self._GUIDE_REL):
            self.skipTest(f"{self._GUIDE_REL} not present")
        text = _read(self._GUIDE_REL)
        for phrase in (
            "sssf-patterns-sidecar",
            "super-simple-software-factory",
            "advise-project-approach",
            "neuroarxiv",
            "file handoffs",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text, msg=f"sidecar guide missing: {phrase}")
        for section in (
            "Borrow",
            "Reject",
            "External skill borrow",
            "workflow-artifact-contract",
            "plan-contract",
            "mat-discovery-research-skills",
        ):
            with self.subTest(section=section):
                self.assertIn(section, text, msg=f"sidecar guide missing section/link: {section}")
        self.assertIn("docs/current-plan.md", text)
        self.assertIn("build-result.md", text)
        self.assertIn("verify-result.md", text)

    def test_operator_surfaces_link_sssf_sidecar(self):
        missing = [p for p in self._CROSS_LINK_PATHS if not _exists(p)]
        if missing:
            self.skipTest(f"cross-link paths missing: {missing}")
        for rel in self._CROSS_LINK_PATHS:
            with self.subTest(rel=rel):
                text = _read(rel)
                self.assertIn("sssf-patterns-sidecar", text)


class MatSssfOperatorPatternsDocsTest(unittest.TestCase):
    """S6-sssf-docs: A7 / B1 / B2 / B6 operator patterns in the SSSF sidecar guide."""

    _GUIDE_REL = "docs/guides/sssf-patterns-sidecar.md"
    _LOOP_POLICY_REL = "docs/reference/loop-policy.md"
    _TEST_WRITER_REL = ".cursor/agents/test-writer.md"
    _VERIFIER_REL = ".cursor/agents/verifier.md"

    def _guide(self) -> str:
        if not _exists(self._GUIDE_REL):
            self.skipTest(f"{self._GUIDE_REL} not present")
        return _read(self._GUIDE_REL)

    def test_a7_adw_ci_sidecar_pattern(self):
        text = self._guide()
        for phrase in (
            "A7",
            "ADW CI sidecar",
            "adws/",
            "adw_quality",
            "adw_build_test",
            "CI-only",
            "scripts/phase1-verify.sh",
            "Cursor parent orchestration unchanged",
            "never spawns subagents",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text, msg=f"A7 section missing: {phrase}")

    def test_b1_phase_primitive_naming_map(self):
        text = self._guide()
        for phrase in (
            "B1",
            "Phase primitive naming",
            "run.phase()",
            "operator lane",
            "subagent lane",
            "hooks + CI lane",
            "vocabulary only",
            "Python does not own the orchestration graph",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text, msg=f"B1 section missing: {phrase}")

    def test_b1_does_not_claim_python_owns_graph(self):
        text = self._guide()
        # Reject-table posture must survive the S6 additions.
        self.assertIn("Python orchestrator owning the graph", text)

    def test_b2_envelope_correction_loops(self):
        text = self._guide()
        for phrase in (
            "B2",
            "Envelope correction",
            "narrow re-prompt",
            "same session",
            "correctable",
            "repair_attempt_limit",
            "Parent owns spawn",
            "loop-policy.md",
            "build-result.md",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text, msg=f"B2 section missing: {phrase}")

    def test_b6_test_writer_vs_verifier_scope(self):
        text = self._guide()
        for phrase in (
            "B6",
            "test loop",
            "review loop",
            "test-writer",
            "verifier",
            "readonly: true",
            "parent serializes",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text, msg=f"B6 section missing: {phrase}")

    def test_b6_does_not_reopen_b3(self):
        text = self._guide()
        self.assertIn("B3", text)
        self.assertIn("does not reopen", text)

    def test_loop_policy_cross_links_envelope_correction(self):
        if not _exists(self._LOOP_POLICY_REL):
            self.skipTest(f"{self._LOOP_POLICY_REL} not present")
        text = _read(self._LOOP_POLICY_REL)
        self.assertIn("sssf-patterns-sidecar", text)
        self.assertIn("Envelope correction", text)

    def test_role_prompts_cross_link_sidecar_loop_separation(self):
        for rel in (self._TEST_WRITER_REL, self._VERIFIER_REL):
            if not _exists(rel):
                self.skipTest(f"{rel} not present")
            with self.subTest(rel=rel):
                text = _read(rel)
                self.assertIn("sssf-patterns-sidecar", text)


class CloudAgentLongRunDocsTest(unittest.TestCase):
    """SLICE-001 D3b/N2: runbook + example env + preflight + normative spec."""

    def test_cloud_agent_long_run_surfaces(self):
        guide_rel = "docs/guides/cloud-agent-long-run.md"
        spec_rel = "specs/cloud-agent-long-run-v1.md"
        example_rel = ".cursor/environment.json.example"
        if not _exists(guide_rel):
            self.skipTest(f"{guide_rel} not present in this trimmed fixture")
        guide = _read(guide_rel)
        for needle in (
            "docs/guides/cloud-agent-long-run.md",
            "scripts/cloud-slice-preflight.py",
            ".cursor/environment.json.example",
            "specs/cloud-agent-long-run-v1.md",
            "orphan",
            "D3a-private",
            "does not auto-provision",
            "d3b/",
            "mat-long-run/",
            "env-var beta",
            "N8",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, guide, f"runbook missing: {needle}")
        self.assertIn("Cloud agent stalled (no commits)", guide)
        self.assertIn("Abandoned branch", guide)
        self.assertIn("Failed Build", guide)
        self.assertIn("Parent lost cloud URL", guide)
        self.assertIn("Handoffs dirty on wrong branch", guide)
        self.assertIn("Secret missing mid-run", guide)
        self.assertIn("cursor-automations.md", guide)

        self.assertTrue(_exists(spec_rel), spec_rel)
        spec = _read(spec_rel)
        self.assertIn("Status:** Normative v1", spec)
        self.assertIn("N8 multi-repo", spec)
        self.assertIn("N6 non-implementation", spec)
        self.assertIn("does not auto-provision", spec)

        self.assertTrue(_exists(example_rel), example_rel)
        example = _read(example_rel)
        self.assertIn("https://www.cursor.com/schemas/environment.schema.json", example)
        self.assertIn("ensure-bun-path.sh", example)
        self.assertNotRegex(example, r"(?i)(sk-|ghp_|github_pat_|xox[baprs]-)")


class MakefileShortcutsDocsTest(unittest.TestCase):
    """B15: quick-start documents Makefile DX wrappers without slash-command replacement."""

    def test_quick_start_documents_makefile_shortcuts(self):
        if not _exists("docs/guides/quick-start.md"):
            self.skipTest("quick-start not present in this trimmed fixture")
        text = _read("docs/guides/quick-start.md")
        self.assertIn("Makefile shortcuts", text)
        self.assertIn("make help", text)
        self.assertIn("do **not** replace Cursor slash commands", text)
        self.assertIn("/mat-plan-team", text)
        self.assertIn("phase1-verify.sh", text)
        self.assertNotRegex(
            text,
            r"Makefile replaces\s+/mat-",
            msg="quick-start must not claim Makefile replaces slash commands",
        )


class MatRunManifestOrchestrationDocsTest(unittest.TestCase):
    """N4 follow-through: orchestration docs reference opt-in run manifest closeout."""

    _DOC_PATHS = (
        ".cursor/agents/parent-orchestrator.md",
        ".cursor/commands/mat-long-run.md",
        "packages/mat-workflow/agents/parent-orchestrator.md",
        "packages/mat-workflow/commands/mat-long-run.md",
    )

    def test_orchestration_surfaces_document_run_manifest_closeout(self):
        missing = [p for p in self._DOC_PATHS if not _exists(p)]
        if missing:
            self.skipTest(f"doc paths missing: {missing}")
        for rel in self._DOC_PATHS:
            with self.subTest(rel=rel):
                text = _read(rel)
                self.assertIn("mat_run_manifest.py", text)
                self.assertIn("CURSOR_MAT_RUN_MANIFEST", text)
                self.assertIn("closeout-write", text)
                self.assertIn("gate_impact", text)

    def test_mat_env_sample_documents_run_manifest_flag(self):
        rel = ".mat.env.sample"
        if not _exists(rel):
            self.skipTest(f"{rel} not present")
        text = _read(rel)
        self.assertIn("CURSOR_MAT_RUN_MANIFEST", text)


class MatEnvSampleSelfCompactTest(unittest.TestCase):
    """Env sample documents Self-Compact and lifecycle MAT keys wired in hooks."""

    _SAMPLE = ".mat.env.sample"

    def test_mat_env_sample_documents_self_compact_and_lifecycle_keys(self) -> None:
        if not _exists(self._SAMPLE):
            self.skipTest(f"{self._SAMPLE} not present")
        text = _read(self._SAMPLE)
        for key in (
            "CURSOR_MAT_SELF_COMPACT_LOG_PRETOOL",
            "CURSOR_BACKUP_TRANSCRIPTS",
            "CURSOR_SAVE_SESSION_STATS",
            "CURSOR_TTS_ANNOUNCE",
            "CURSOR_HOOK_CONTRACT_EMIT_ERROR_OBSERVABILITY",
            "OBSERVABILITY_API_EVENTS_URL",
        ):
            self.assertIn(key, text, msg=f"missing {key} in {self._SAMPLE}")


class MatEnvSampleRoutingBudgetTest(unittest.TestCase):
    """M2: lock routing/budget sample keys and configuration.md operator semantics."""

    _SAMPLE = ".mat.env.sample"
    _CONFIG = "docs/reference/configuration.md"
    _MAINTAINER = "docs/reference/MAINTAINER.md"

    def test_mat_env_sample_documents_routing_and_budget_flags(self):
        if not _exists(self._SAMPLE):
            self.skipTest(f"{self._SAMPLE} not present")
        text = _read(self._SAMPLE)
        for key in (
            "CURSOR_MAT_ROUTING_ADVISORY_JSONL",
            "CURSOR_MAT_ROUTING_ADVISORY_PATH",
            "CURSOR_MAT_ROUTING_ADVISORY_ROLLUP",
            "CURSOR_MAT_SESSION_BUDGET_USD",
        ):
            self.assertIn(key, text)
        self.assertIn("default off", text.lower())
        self.assertIn("advisory only", text.lower())

    def test_configuration_documents_routing_and_budget_section(self):
        if not _exists(self._CONFIG):
            self.skipTest(f"{self._CONFIG} not present")
        config = _read(self._CONFIG)
        self.assertIn("### Routing advisory and session budget (optional)", config)
        self.assertIn("CURSOR_MAT_ROUTING_ADVISORY_JSONL", config)
        self.assertIn("CURSOR_MAT_ROUTING_ADVISORY_PATH", config)
        self.assertIn("CURSOR_MAT_ROUTING_ADVISORY_ROLLUP", config)
        self.assertIn("CURSOR_MAT_SESSION_BUDGET_USD", config)
        self.assertIn("not a spend cap", config.lower())
        self.assertIn(".mat.env.sample` only", config)

    def test_maintainer_agrees_on_routing_budget_semantics(self):
        if not _exists(self._MAINTAINER):
            self.skipTest(f"{self._MAINTAINER} not present")
        maintainer = _read(self._MAINTAINER)
        self.assertIn("Routing advisory and session budget", maintainer)
        self.assertIn("defaults **off**", maintainer)
        self.assertIn("defaults **on**", maintainer)
        self.assertIn("**Not** a spend cap", maintainer)
        self.assertIn(".mat.env.sample` only", maintainer)


class M5BlockedBundleReassessmentTest(unittest.TestCase):
    """M5: blocked-bundle reassessment evidence and decision-record honesty."""

    _EVIDENCE = "docs/evidence/m5-mao-blocked-bundle-reassessment-2026-10-19.md"
    _DECISION = "docs/reference/decision-record.md"

    def test_m5_evidence_and_decision_record_honesty(self):
        if _is_mat_sidecar_adoption_layout():
            self.skipTest("M5 evidence record is MAT-source scope")
        if not _exists(self._EVIDENCE):
            self.fail(f"missing required evidence file: {self._EVIDENCE}")
        evidence = _read(self._EVIDENCE)
        decision = _read(self._DECISION)

        self.assertIn("2026-10-19", evidence)
        self.assertIn("bundle remains Blocked", evidence)
        self.assertIn("no live authoritative todo parity", evidence.lower())
        self.assertIn("https://cursor.com/docs/agent/hooks", evidence)
        self.assertIn("https://cursor.com/docs/cli/acp", evidence)
        self.assertIn("cursor/update_todos", evidence)
        self.assertIn("cursor/task", evidence)

        marker = "### M5 reassessment addendum (2026-10-19)"
        self.assertIn(marker, decision)
        addendum = decision.split(marker, 1)[1].split("## Sign-Off Process", 1)[0]
        self.assertIn(self._EVIDENCE, addendum)
        self.assertIn("still Blocked", addendum)
        self.assertIn("unchanged", addendum.lower())
        self.assertNotIn("live authoritative todo parity shipped", addendum.lower())


class VerifierReadonlyHandoffDocsTest(unittest.TestCase):
    """VERIFY-READONLY-DOC-001: parent-owned verify-result serialization (D2/E2)."""

    _FORBIDDEN_VERIFIER_WRITE_PATTERNS = (
        re.compile(r"(?<!do not )write verify-result\.md", re.IGNORECASE),
        re.compile(r"Produce a structured [`']?verify-result\.md", re.IGNORECASE),
        re.compile(r"verifier writes [`']?verify-result\.md", re.IGNORECASE),
        re.compile(r"produce [`']?verify-result\.md[`']? report", re.IGNORECASE),
    )

    def _assert_no_verifier_write_verify_result_instructions(self, rel: str, text: str) -> None:
        for pattern in self._FORBIDDEN_VERIFIER_WRITE_PATTERNS:
            with self.subTest(path=rel, pattern=pattern.pattern):
                self.assertIsNone(
                    pattern.search(text),
                    f"{rel} should not instruct the verifier to write verify-result.md",
                )

    def test_mat_review_parent_owned_serialization(self):
        if not _exists(".cursor/commands/mat-review.md"):
            self.skipTest("mat-review command not present")
        mat_review = _read(".cursor/commands/mat-review.md")
        self.assertIn("structured verify payload", mat_review)
        self.assertRegex(mat_review, r"parent.{0,60}serializ", re.IGNORECASE)
        self._assert_no_verifier_write_verify_result_instructions(
            ".cursor/commands/mat-review.md", mat_review
        )

    def test_prompt_verifier_handoff_parent_runtime_split(self):
        rel = "docs/templates/prompt-verifier-handoff.txt"
        if not _exists(rel):
            self.skipTest("prompt-verifier-handoff template missing")
        prompt = _read(rel)
        self.assertIn("structured verify payload", prompt)
        self.assertIn("serialize_verify_result", prompt)
        self.assertIn("Do NOT write verify-result.md", prompt)
        self._assert_no_verifier_write_verify_result_instructions(rel, prompt)

    def test_mat_plan_team_step3_and_build_gate_closeout(self):
        if not _exists(".cursor/commands/mat-plan-team.md"):
            self.skipTest("mat-plan-team command not present")
        plan_team = _read(".cursor/commands/mat-plan-team.md")
        self.assertIn("### Step 3 — Delegate to Verifier", plan_team)
        step3 = plan_team.split("### Step 3 — Delegate to Verifier", 1)[1].split(
            "### Step 4", 1
        )[0]
        self.assertIn("structured verify payload", step3)
        self.assertIn("serialize_verify_result", step3)
        self.assertNotIn("produce `verify-result.md`", step3.lower())
        self.assertIn(
            "wait for structured verify payload",
            plan_team.lower(),
        )

    def test_orchestration_workflow_step9_and_sequence_diagram(self):
        rel = "docs/architecture/orchestration-workflow.md"
        if not _exists(rel):
            self.skipTest("orchestration-workflow.md missing")
        orch = _read(rel)
        self.assertIn("structured verify payload", orch)
        self.assertRegex(
            orch,
            r"9\.\s+Verifier[\s\S]{0,400}structured verify payload",
            re.IGNORECASE,
        )
        self.assertIn("serialize verify-result.md", orch.lower())
        self.assertIn("V->>P: structured verify payload", orch)

    def test_verifier_agent_documents_cursor_product_limits(self):
        if not _exists(".cursor/agents/verifier.md"):
            self.skipTest("verifier agent not present")
        verifier = _read(".cursor/agents/verifier.md")
        self.assertIn("## Cursor product limits (readonly subagents)", verifier)
        self.assertIn("Ask-like", verifier)

    def test_archive_orchestration_d2_e2_handoff(self):
        rel = "docs/archive/orchestration.md"
        if not _exists(rel):
            self.skipTest("archive orchestration missing")
        archive = _read(rel)
        self.assertIn("D2/E2", archive)
        self.assertIn("structured verify payload", archive)
        self.assertIn("serialize", archive.lower())
        self._assert_no_verifier_write_verify_result_instructions(rel, archive)

    def test_mat_cursor_improvement_roadmap_e2_overlay(self):
        rel = "mat-cursor-improvement-roadmap.md"
        if not _exists(rel):
            self.skipTest("mat-cursor-improvement-roadmap missing")
        report = _read(rel)
        self.assertIn("Historical status overlay (2026-10-27)", report)
        self.assertIn("VERIFY-READONLY-DOC-001", report)
        self.assertIn("parent serializes handoff", report.lower())


if __name__ == "__main__":
    unittest.main()
