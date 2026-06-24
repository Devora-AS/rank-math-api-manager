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
        if not _exists("docs/planning-commands-guide.md"):
            self.skipTest("planning commands guide not present in this trimmed fixture")

        plan = _read(".cursor/commands/mat-plan.md")
        plan_onboarding = _read(".cursor/commands/mat-plan-onboarding.md")
        planning_guide = _read("docs/planning-commands-guide.md")

        self.assertIn("# MAT Plan", plan)
        self.assertIn("/mat-plan <task description>", plan)
        self.assertIn("Planning only — no implementation.", plan)
        self.assertIn("specs/<slug>.md", plan)
        self.assertIn("solo_plan_only", plan)
        self.assertIn("ready_for_execution_handoff", plan)
        self.assertIn("needs_plan_onboarding", plan)
        self.assertIn("Recommended Next Command", plan)
        self.assertIn("Do not reuse `/mat-plan-team` execution-mode terms", plan)
        self.assertIn("docs/capability-precedence.md", plan)

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
        self.assertIn("docs/capability-precedence.md", plan_onboarding)
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
                "specs/mat-plan-and-plan-onboarding-v1/spec.md",
                "specs/mat-plan-and-plan-onboarding-v1/tasks.json",
                "specs/mat-plan-and-plan-onboarding-v1/plan-summary.md",
                "specs/mat-plan-and-plan-onboarding-v1.md",
            )
        ):
            self.skipTest("plan_onboarding templates/specimen not present in this trimmed fixture")

        spec_template = _read("docs/templates/spec-template.md")
        schema = _read("docs/templates/tasks-schema.json")
        specimen_spec = _read("specs/mat-plan-and-plan-onboarding-v1/spec.md")
        specimen_prd = _read("specs/mat-plan-and-plan-onboarding-v1/prd.md")
        specimen_tasks = _read("specs/mat-plan-and-plan-onboarding-v1/tasks.json")
        specimen_summary = _read("specs/mat-plan-and-plan-onboarding-v1/plan-summary.md")
        planning_spec = _read("specs/mat-plan-and-plan-onboarding-v1.md")

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
        long_run_state = _read("docs/long-run-state.md")

        self.assertIn("mission_complete", long_run_state)
        self.assertIn("planning_gap", long_run_state)

        self.assertIn("# MAT Long Run", long_run)
        self.assertIn("/mat-long-run <mission description>", long_run)
        self.assertIn("docs/long-run-state.md", long_run)
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
        components = _read("docs/components.md")
        docs_index = _read("docs/README.md") if _exists("docs/README.md") else ""
        usage = _read("docs/usage-examples-and-cases.md") if _exists("docs/usage-examples-and-cases.md") else ""
        best_practices = _read("docs/best-practices.md") if _exists("docs/best-practices.md") else ""

        self.assertIn("| `/mat-long-run <task>` | Queued multi-slice mission with `docs/long-run-state.md` and post-slice mission gate |", agents)
        self.assertIn("| `/mat-subagents-spawn <task>` | Decompose work and run parallel Task subagents (parent integrates results; see command doc) |", agents)
        self.assertIn("| `/mat-sprint <task>` | Execute one bounded slice with DoR, implementation, verification, and review |", agents)
        self.assertIn("| `/mat-lite <task>` | Run a lightweight docs/config/quality pass without the full orchestration flow |", agents)
        self.assertIn("| `/mat-plan <task>` | Lightweight solo planning — writes one file: `specs/<slug>.md` |", agents)
        self.assertIn(
            "| `/mat-plan-onboarding <task>` | Heavyweight planning-only onboarding — writes the four-file package under `specs/<slug>/` |",
            agents,
        )
        self.assertIn("| `/mat-wt-check` | Run worktree health and collision checks |", agents)
        self.assertIn("| `/mat-doctor` | Run local diagnostics for workflow readiness |", agents)
        self.assertIn("internal/reference-oriented", agents)
        self.assertIn("not a public packaging target by default", agents)

        self.assertIn("| `/mat-long-run` | Queued multi-slice mission (`docs/long-run-state.md`, mission gate) |", readme)
        self.assertIn("| `/mat-subagents-spawn` | Parallel Task subagent fan-out with parent integration (see `.cursor/commands/mat-subagents-spawn.md`) |", readme)
        self.assertIn("| `/mat-sprint` | Run one bounded slice end-to-end |", readme)
        self.assertIn("| `/mat-lite` | Run a lightweight docs/config/quality pass |", readme)
        self.assertIn("| `/mat-plan` | Lightweight solo planning — writes one file: `specs/<slug>.md` |", readme)
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
        self.assertIn("docs/planning-commands-guide.md", components)
        self.assertIn("`../.cursor/commands/mat-long-run.md`", components)
        self.assertIn("`../.cursor/commands/mat-subagents-spawn.md`", components)
        self.assertIn("`../.cursor/commands/mat-sprint.md`", components)
        self.assertIn("`../.cursor/commands/mat-lite.md`", components)
        self.assertIn("`../.cursor/agents/test-writer.md`", components)
        self.assertIn("`../.cursor/agents/style-reviewer.md`", components)
        self.assertIn("internal/reference-oriented", components)

        if docs_index:
            self.assertIn("[planning-commands-guide.md](planning-commands-guide.md)", docs_index)
            self.assertIn("[capability-precedence.md](capability-precedence.md)", docs_index)
        if usage:
            self.assertIn("/mat-plan-onboarding", usage)
            self.assertIn("/mat-plan", usage)
        if best_practices:
            self.assertIn("/mat-plan-onboarding", best_practices)
            self.assertIn("planning truth in `specs/`", best_practices)

    def test_capability_precedence_policy_doc_locks_project_first_routing(self):
        if not _exists("docs/capability-precedence.md"):
            self.skipTest("capability-precedence doc not present in this trimmed fixture")
        cap = _read("docs/capability-precedence.md")
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
        self.assertIn("docs/capability-precedence.md", readme)
        maintainer = _read("docs/MAINTAINER.md")
        self.assertIn("capability-precedence.md", maintainer)
        components = _read("docs/components.md")
        self.assertIn("capability-precedence.md", components)
        if not _is_mat_sidecar_adoption_layout():
            agents = _read("AGENTS.md")
            self.assertIn("docs/capability-precedence.md", agents)

    def test_model_routing_policy_doc_locks_conservative_adapter_agnostic_policy(self):
        required = (
            "docs/model-routing-policy.md",
            "docs/context-budget-policy.md",
            "docs/schemas/mat-routing-advisory.example.json",
            "README.md",
            "AGENTS.md",
            "docs/README.md",
            "docs/components.md",
            "docs/best-practices.md",
            "docs/MAINTAINER.md",
            "docs/capability-precedence.md",
            ".cursor/agents/parent-orchestrator.md",
            ".cursor/commands/mat-plan-team.md",
            ".cursor/agents/builder.md",
            ".cursor/agents/verifier.md",
            ".cursor/commands/mat-sprint.md",
            ".cursor/commands/mat-long-run.md",
        )
        if not all(_exists(path) for path in required):
            self.skipTest("model routing policy docs not present in this trimmed fixture")

        policy = _read("docs/model-routing-policy.md")
        context_budget = _read("docs/context-budget-policy.md")
        advisory_example = _read("docs/schemas/mat-routing-advisory.example.json")
        readme = _read("README.md")
        agents = _read("AGENTS.md")
        docs_index = _read("docs/README.md")
        components = _read("docs/components.md")
        best_practices = _read("docs/best-practices.md")
        maintainer = _read("docs/MAINTAINER.md")
        cap = _read("docs/capability-precedence.md")
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
        self.assertIn("docs/context-budget-policy.md", policy)
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
        self.assertIn("docs/model-routing-policy.md", readme)
        self.assertIn("Context budget", readme)
        self.assertIn("docs/context-budget-policy.md", readme)

        self.assertIn("docs/model-routing-policy.md", agents)
        self.assertIn("adapter-agnostic", agents)
        self.assertIn("routing_rollup_<session_id>.json", agents)
        self.assertIn("scripts/analyze_routing_advisory.py", agents)
        self.assertIn("prompt lint warnings", agents)
        self.assertIn("session budget notes", agents)
        self.assertIn("docs/context-budget-policy.md", agents)

        self.assertIn("model-routing-policy.md", docs_index)
        self.assertIn("Conservative MAT routing tiers", docs_index)
        self.assertIn("routing_advisory.md", docs_index)
        self.assertIn("session rollups", docs_index)
        self.assertIn("context-budget-policy.md", docs_index)
        self.assertIn("operational baseline", docs_index)

        self.assertIn("Routing policy", components)
        self.assertIn("docs/model-routing-policy.md", components)
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

        self.assertIn("docs/model-routing-policy.md", maintainer)
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

        self.assertIn("docs/model-routing-policy.md", orchestrator)
        self.assertIn("do not invent Cursor alias behavior as a MAT contract", orchestrator)
        self.assertIn("docs/context-budget-policy.md", orchestrator)

        self.assertIn("docs/model-routing-policy.md", plan_w_team)
        self.assertIn("avoid encoding undocumented Cursor alias-style frontmatter behavior as MAT core policy", plan_w_team)
        self.assertIn("docs/context-budget-policy.md", plan_w_team)

        self.assertIn("docs/context-budget-policy.md", builder)
        self.assertIn("docs/context-budget-policy.md", verifier)
        self.assertIn("docs/context-budget-policy.md", sprint)
        self.assertIn("docs/context-budget-policy.md", long_run)

    def test_artifact_contract_doc_and_prompt_examples_stay_aligned(self):
        if not _exists("docs/workflow-artifact-contract.md"):
            self.skipTest("artifact contract doc not present in this trimmed fixture")
        contract = _read("docs/workflow-artifact-contract.md")
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

        for text in (builder, build):
            self.assertIn("## Closeout (YYYY-MM-DD)", text)
            self.assertIn("## Notes for Verifier", text)
            self.assertIn("docs/workflow-artifact-contract.md", text)

        for text in (verifier, review):
            self.assertIn("## Criteria Review", text)
            self.assertIn("## Closeout (YYYY-MM-DD)", text)
            self.assertIn("docs/workflow-artifact-contract.md", text)

        for text in (orchestrator, plan_w_team, long_run):
            self.assertIn("docs/workflow-artifact-contract.md", text)

        self.assertIn("docs/capability-precedence.md", orchestrator)
        self.assertIn("docs/capability-precedence.md", plan_w_team)

    def test_execution_closeout_contract_and_prompt_defaults_are_explicit(self):
        required = (
            "AGENTS.md",
            "README.md",
            "docs/best-practices.md",
            "docs/orchestration-workflow.md",
            "docs/mat-plan-team-spec.md",
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
        best_practices = _read("docs/best-practices.md")
        workflow = _read("docs/orchestration-workflow.md")
        spec = _read("docs/mat-plan-team-spec.md")
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
        self.assertIn("Current Focus", roadmap)
        self.assertIn("Maintenance Notes", roadmap)
        self.assertIn("no claim of live authoritative todo parity", roadmap)
        self.assertIn("Top-level docs and maintenance guidance", changelog)
        self.assertIn("normal startup", parent.lower())
        self.assertIn("active progress", parent.lower())
        self.assertIn("unclear state", parent.lower())
        self.assertIn("true stall/failure", parent.lower())

    def test_phase2_proof_tiers_and_closeout_gate_wording_stay_aligned(self):
        if not _exists("docs/mat-plan-team-spec.md") or not _exists("artifacts/agent-traces/README.md"):
            self.skipTest("phase2 proof-tier docs not present in this trimmed fixture")
        spec = _read("docs/mat-plan-team-spec.md")
        traces = _read("artifacts/agent-traces/README.md")
        orchestrator = _read(".cursor/agents/parent-orchestrator.md")
        maintainer = _read("docs/MAINTAINER.md")
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
            "docs/best-practices.md",
            ".cursor/commands/mat-sprint.md",
            ".cursor/commands/mat-plan-team.md",
            ".cursor/agents/parent-orchestrator.md",
            ".cursor/agents/builder.md",
            ".cursor/agents/verifier.md",
        )
        if not all(_exists(path) for path in required):
            self.skipTest("phase3 ladder/escalation docs not present in this trimmed fixture")

        ladder = _read("docs/local-app-verification-ladder.md")
        pilot_new_readme = _read("docs/pilot/pilot-new/README.md")
        pilot_new_steps = _read("docs/pilot/pilot-new/step-by-step.md")
        pilot_new_success = _read("docs/pilot/pilot-new/success-criteria.md")
        pilot_existing_steps = _read("docs/pilot/pilot-existing/step-by-step.md")
        best_practices = _read("docs/best-practices.md")
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
            "docs/README.md",
            "docs/MAINTAINER.md",
            ".gitignore",
            "artifacts/agent-traces/README.md",
        )
        if not all(_exists(path) for path in required):
            self.skipTest("phase4 taxonomy docs not present in this trimmed fixture")

        agents = _read("AGENTS.md")
        readme = _read("README.md")
        docs_index = _read("docs/README.md")
        maintainer = _read("docs/MAINTAINER.md")
        gitignore = _read(".gitignore")
        traces = _read("artifacts/agent-traces/README.md")

        self.assertIn("## Durable Repo Facts", agents)
        self.assertIn("## Workspace-Local Operational Facts", agents)
        self.assertIn("## Dated Evidence References", agents)
        self.assertIn("docs/todo-orchestration-pilot.md", agents)
        self.assertIn("docs/pilot-report.md", agents)

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
            "docs/pilot-report.md",
            "docs/phase1-validation-report.md",
            "docs/troubleshooting.md",
        )
        if not all(_exists(path) for path in required):
            self.skipTest("phase5 phase1 log docs not present in this trimmed fixture")

        phase1_readme = _read("artifacts/phase1/README.md")
        phase1_report = _read("artifacts/phase1/phase1-verification-report.md")
        pilot_report = _read("docs/pilot-report.md")
        validation_report = _read("docs/phase1-validation-report.md")
        troubleshooting = _read("docs/troubleshooting.md")

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

        self.assertIn("Phase 5 completed the rollout and green-bar validation pass", readme)
        self.assertIn("workflow is green under the scoped hardening criteria", readme)
        self.assertIn("Phase 5 — Shipped", roadmap)
        self.assertIn("Green bar — Met", roadmap)
        self.assertIn("blocked runtime-limitations stay explicit", roadmap.lower())

    def test_continual_learning_hygiene_docs_are_linked(self):
        required = (
            ".cursor/rules/continual-learning-hygiene.mdc",
            "docs/continual-learning-safe-handling.md",
            "README.md",
            "AGENTS.md",
            "docs/MAINTAINER.md",
            "docs/README.md",
        )
        if not all(_exists(path) for path in required):
            self.skipTest("continual-learning hygiene doc set not present in this trimmed fixture")

        rule = _read(".cursor/rules/continual-learning-hygiene.mdc")
        design = _read("docs/continual-learning-safe-handling.md")
        readme = _read("README.md")
        agents = _read("AGENTS.md")
        maintainer = _read("docs/MAINTAINER.md")
        docs_index = _read("docs/README.md")

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
        text = _read("docs/long-run-state.md")
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
        self.assertIn("docs/long-run-state.md", pwt)
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
        doc_index = _read("docs/README.md")
        self.assertRegex(doc_index, re.compile(r"^Last updated: \d{4}-\d{2}-\d{2}$", re.MULTILINE))
        self.assertIn("[long-run-state.md](long-run-state.md)", doc_index)
        self.assertIn("../.cursor/commands/mat-long-run.md", doc_index)
        self.assertIn("parent-orchestrator", doc_index)
        self.assertIn("execution_mode", doc_index)
        self.assertIn("execution_rationale", doc_index)
        self.assertNotIn("slice_execution_mode", doc_index)

    def test_phase4_reassessment_checklist_contract(self):
        text = _read("docs/phase4-roadmap-reassessment-checklist.md")
        self.assertIn("mao-advisory-go-criteria.md", text)
        self.assertIn("decision-record.md", text)
        self.assertIn("ROADMAP.md", text)
        self.assertIn("G4", text)
        self.assertIn("prepare evidence", text)
        self.assertIn("operator-owned", text)


class StopValidatorHonestyDocsTest(unittest.TestCase):
    """P0-2: wired `stop_validator.py` vs optional `validators/` utilities; no repo-default overclaim."""

    def test_agents_and_components_document_shipped_stop_vs_optional_validators(self):
        if not _exists("docs/components.md"):
            self.skipTest("components.md not present in this trimmed fixture")
        agents = _read("AGENTS.md")
        if "# AGENTS.md — Cursor-First Agentic Workflow Guide" not in agents:
            self.skipTest(
                "packaged/adoption AGENTS.md stub at resolved repo root — full stop-validator honesty lives in MAT repo AGENTS.md"
            )
        components = _read("docs/components.md")
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
        if not _exists("docs/MULTI_AGENT_USAGE_GUIDE.md"):
            self.skipTest("MULTI_AGENT_USAGE_GUIDE.md not present in this trimmed fixture")
        if not _exists("docs/events-and-visualization.md") or not _exists("docs/features-demonstrated.md"):
            self.skipTest("honesty companion docs not present in this trimmed fixture")
        agents = _read("AGENTS.md")
        if "# AGENTS.md — Cursor-First Agentic Workflow Guide" not in agents:
            self.skipTest(
                "packaged/adoption AGENTS.md stub at resolved repo root — full stop-validator honesty tests skipped"
            )
        guide = _read("docs/MULTI_AGENT_USAGE_GUIDE.md")
        events = _read("docs/events-and-visualization.md")
        features = _read("docs/features-demonstrated.md")
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
        if not _exists("docs/events-and-visualization.md"):
            self.skipTest("events-and-visualization.md not present in this trimmed fixture")
        events = _read("docs/events-and-visualization.md")
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
        if not _exists("docs/MAINTAINER.md"):
            self.skipTest("MAINTAINER.md not present in this trimmed fixture")
        maintainer = _read("docs/MAINTAINER.md")
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
        rel = "docs/observability-retention-policy.md"
        if not _exists(rel):
            self.skipTest("observability-retention-policy.md not present in this trimmed fixture")
        policy = _read(rel)
        self.assertIn("Last updated: 2026-06-22", policy)
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
            "docs/events-and-visualization.md",
            "docs/configuration.md",
            "docs/MAINTAINER.md",
        ):
            if not _exists(rel):
                self.skipTest(f"{rel} not present in this trimmed fixture")
        events = _read("docs/events-and-visualization.md")
        config = _read("docs/configuration.md")
        maintainer = _read("docs/MAINTAINER.md")
        readme = _read("docs/README.md") if _exists("docs/README.md") else ""
        for text in (events, config, maintainer):
            self.assertIn("observability-retention-policy.md", text)
        if readme:
            self.assertIn("observability-retention-policy.md", readme)
        self.assertIn("OBSERVABILITY_DB_PATH", config)


class MatAdoptionObservabilityAppendixTest(unittest.TestCase):
    """Adoption observability appendix: existence, opt-in honesty, manual rotation, RFU-7 deferral."""

    _APPENDIX_REL = "docs/adoption-observability-appendix.md"
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
        self.assertIn(".mat/docs/adoption-observability-appendix.md", appendix)

    def test_adoption_layout_packages_appendix(self):
        if not _exists(self._LAYOUT_REL):
            self.skipTest(f"{self._LAYOUT_REL} not present")
        layout = _read(self._LAYOUT_REL)
        self.assertIn("docs/adoption-observability-appendix.md", layout)
        self.assertIn(".mat/docs/adoption-observability-appendix.md", layout)

    def test_operator_docs_link_adoption_pilot_report(self):
        """Getting-started, validation-report, and appendix cross-link disposable pilot evidence."""
        paths = (
            "docs/getting-started-existing-projects.md",
            "docs/getting-started-new-projects.md",
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
        rel = "docs/decision-record.md"
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
            "docs/orchestration-workflow.md",
            "artifacts/report/mat-audit-report.md",
        ):
            if not _exists(rel):
                self.skipTest(f"{rel} not present in this trimmed fixture")
        roadmap = _read("ROADMAP.md")
        orchestration = _read("docs/orchestration-workflow.md")
        audit = _read("artifacts/report/mat-audit-report.md")
        for text in (roadmap, orchestration, audit):
            self.assertIn("decision-record.md", text)
            self.assertIn(self._WORKTREE_ANCHOR, text)
            self.assertIn(self._NESTED_ANCHOR, text)
        self.assertIn("P2OrchestrationStrategyDocsTest", roadmap)
        self.assertIn("Explicit non-goals", orchestration)
        self.assertIn("**Done**", audit)


# Canonical surfaces for P0-1 worktree contract (aligned with docs/current-plan.md scope).
_WORKTREE_CONTRACT_REL_PATHS = (
    "AGENTS.md",
    "docs/worktree-decision-matrix.md",
    ".cursor/commands/mat-wt-create.md",
    ".cursor/commands/mat-wt-list.md",
    ".cursor/agents/create-worktree-subagent.md",
    ".cursor/worktrees.json",
    ".cursor/hooks/bootstrap_worktree.sh",
    ".cursor/skills/worktree-manager/SKILL.md",
    ".cursor/skills/create-worktree/SKILL.md",
    "docs/MAINTAINER.md",
    "docs/components.md",
    "docs/getting-started-existing-projects.md",
    "docs/getting-started-new-projects.md",
    "docs/configuration.md",
    "docs/quick-start.md",
    "docs/best-practices.md",
    "docs/usage-examples-and-cases.md",
    "docs/MULTI_AGENT_USAGE_GUIDE.md",
    "docs/features-demonstrated.md",
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
        if not _exists("docs/features-demonstrated.md"):
            self.skipTest("features-demonstrated.md not present")
        text = _read("docs/features-demonstrated.md")
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


# P1 B1 surfaces beyond P0 worktree contract paths (see docs/current-plan.md).
_P1_WORKTREE_HONESTY_REL_PATHS = (
    ".cursor/commands/mat-wt-check.md",
    ".cursor/commands/mat-wt-remove.md",
    "README.md",
    "docs/decision-record.md",
    "docs/orchestration-workflow.md",
)

# Stop-validator honesty beyond StopValidatorHonestyDocsTest surfaces.
_P1_STOP_VALIDATOR_HONESTY_REL_PATHS = (
    "docs/quick-start.md",
    "docs/pilot-report.md",
    "docs/phase1-validation-report.md",
    "docs/MAINTAINER.md",
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

        decision = _read("docs/decision-record.md")
        self.assertIn("Hybrid defer", decision)
        self.assertIn("/worktree", decision)
        self.assertIn("/best-of-n", decision)

        readme = _read("README.md")
        self.assertIn("honest boundary", readme.lower())
        self.assertIn("explicit", readme.lower())

        orchestration = _read("docs/orchestration-workflow.md")
        self.assertIn("p2-audit--worktree-wrapper-strategy", orchestration)
        self.assertIn("operator explicitly created isolation", orchestration.lower())

        for rel in (".cursor/commands/mat-wt-check.md", ".cursor/commands/mat-wt-remove.md"):
            cmd = _read(rel)
            self.assertIn("worktree", cmd.lower())

    def test_p1_stop_validator_surfaces_document_permissive_shipped_stop(self):
        missing = [p for p in _P1_STOP_VALIDATOR_HONESTY_REL_PATHS if not _exists(p)]
        if missing:
            self.skipTest("P1 stop-validator honesty paths missing: " + ", ".join(missing))

        pilot = _read("docs/pilot-report.md")
        self.assertIn("send_event.py", pilot)
        self.assertIn("stop_validator.py", pilot)
        self.assertIn("failClosed", pilot)
        self.assertIn("permissive", pilot.lower())
        self.assertNotIn("blocks completion if required text is missing", pilot.lower())
        self.assertNotIn("blocks stop if required content is missing", pilot.lower())

        quick_start = _read("docs/quick-start.md")
        self.assertIn("explicit git worktree", quick_start.lower())
        self.assertNotIn("blocks completion if", quick_start.lower())
        self.assertNotIn("validators/", quick_start)

        phase1_report = _read("docs/phase1-validation-report.md")
        self.assertNotIn("blocks completion", phase1_report.lower())
        self.assertNotIn("blocks stop if", phase1_report.lower())

        maintainer = _read("docs/MAINTAINER.md")
        self.assertNotIn("validators/ on shipped `stop`", maintainer.lower())
        self.assertNotIn("additional commands on the shipped `stop` array", maintainer.lower())


_MAT_COMMAND_NAMES = (
    "mat-plan",
    "mat-plan-onboarding",
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
    "docs/worktree-decision-matrix.md",
    "docs/components.md",
    "docs/configuration.md",
    "docs/technical-stack.md",
)


class P1SkillsCommandsRoutingDocsTest(unittest.TestCase):
    """P1 Phase B B2: skills vs commands routing in decision-record."""

    _ANCHOR = "p1-audit--skills-vs-commands-routing"

    def test_decision_record_p1_skills_commands_section(self):
        rel = "docs/decision-record.md"
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
        rel = "docs/decision-record.md"
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
        planning = _read("docs/planning-commands-guide.md") if _exists("docs/planning-commands-guide.md") else ""
        if planning:
            self.assertIn(self._ANCHOR, planning)

    def test_no_bulk_skills_migration_claim(self):
        rel = "docs/decision-record.md"
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
        rel = "docs/decision-record.md"
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
        for rel in ("AGENTS.md", "docs/worktree-decision-matrix.md"):
            if not _exists(rel):
                self.skipTest(f"{rel} not present in this trimmed fixture")
        agents = _read("AGENTS.md")
        matrix = _read("docs/worktree-decision-matrix.md")
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
        self.assertIn("actions/setup-node@v4", text)
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


class RFU1ClientCiDocsHygieneTest(unittest.TestCase):
    """Phase C C5 doc hygiene: pilot-report matches vitest-only client CI."""

    def test_pilot_report_describes_vitest_only_client_ci(self):
        if not _exists("docs/pilot-report.md"):
            self.skipTest("pilot-report.md not present")
        pilot = _read("docs/pilot-report.md")
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
        "docs/MAINTAINER.md",
        "docs/getting-started-existing-projects.md",
        "docs/adoption-safe-defaults.md",
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
        maintainer = texts["docs/MAINTAINER.md"]
        self.assertIn("MAT updater operator runbook", maintainer)
        self.assertIn("artifacts/update-mat/", maintainer)
        validation = texts["validation-report.md"]
        self.assertIn("Slice 3", validation)
        self.assertIn("Operator checklist", validation)
        self.assertIn("getting-started-existing-projects.md", validation)
        existing = texts["docs/getting-started-existing-projects.md"]
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


class CIPhase1VerifyCheckoutTest(unittest.TestCase):
    """CI checkout must fetch full git history for legacy fingerprint verification."""

    def test_phase1_verify_workflow_fetches_full_history(self):
        rel = ".github/workflows/phase1-verify.yml"
        if not _exists(rel):
            self.skipTest("phase1-verify workflow not present")
        text = _read(rel)
        self.assertRegex(text, r"fetch-depth:\s*0")
        self.assertIn("mat-legacy-fingerprints", text)


if __name__ == "__main__":
    unittest.main()
