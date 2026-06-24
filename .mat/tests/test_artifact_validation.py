from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
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
VALIDATOR_PATH = REPO_ROOT / ".cursor" / "scripts" / "validate_artifacts.py"
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "phase1-verify.sh"

_MODULE_NAME = "validate_artifacts_test_harness"
_SPEC = importlib.util.spec_from_file_location(_MODULE_NAME, VALIDATOR_PATH)
assert _SPEC and _SPEC.loader
_VALIDATOR = importlib.util.module_from_spec(_SPEC)
sys.modules[_MODULE_NAME] = _VALIDATOR
_SPEC.loader.exec_module(_VALIDATOR)


def _load_artifact_contract_module():
    import importlib.util

    mod_path = REPO_ROOT / ".cursor" / "hooks" / "artifact_contract.py"
    name = "_artifact_contract_test"
    spec = importlib.util.spec_from_file_location(name, mod_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_current_plan() -> str:
    return textwrap.dedent(
        """\
        # Current plan

        ## DoR

        - Work the current slice only.

        ## Non-goals

        - No unrelated edits.
        """
    )


def _minimal_build_result() -> str:
    return textwrap.dedent(
        """\
        # Build Result

        ## Task
        Validate the slice.

        ## Status
        PASS

        ## Changes Made
        - `docs/workflow-artifact-contract.md`: defines the canonical contract.

        ## Acceptance Criteria
        - Criterion 1: PASS — contract sections are present

        ## Linting / Type-Check
        PASS

        ## Issues / Blockers
        None

        ## Notes for Verifier
        Inspect the shared contract consumers.

        ## Closeout (2026-03-29)

        Ready for verification.
        """
    )


def _minimal_verify_result() -> str:
    return textwrap.dedent(
        """\
        # Verify Result

        ## Plan
        docs/current-plan.md

        ## Builder Result
        build-result.md

        ## Status
        PASS

        ## Criteria Review

        ### Criterion 1: contract sections are present
        **Result:** PASS
        **Evidence:** `docs/workflow-artifact-contract.md` lists the required sections.

        ## Issues Found
        None

        ## Recommendations
        None

        ## Closeout (2026-03-29)

        Verified.
        """
    )


def _minimal_long_run_state(last_updated: str = "2026-03-29") -> str:
    return textwrap.dedent(
        f"""\
        # Long-run mission state

        **Last updated:** {last_updated}

        ## Mission

        - **Goal:** Keep the validator deterministic.
        - **execution_mode:** `long-run`

        ## Parent mission gate compliance

        - [ ] Capture the parent decision.
        """
    )


class ValidateArtifactsTest(unittest.TestCase):
    def test_valid_minimal_artifacts_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "docs" / "current-plan.md", _minimal_current_plan())
            _write(root / "build-result.md", _minimal_build_result())
            _write(root / "verify-result.md", _minimal_verify_result())
            _write(root / "docs" / "long-run-state.md", _minimal_long_run_state())

            result = _VALIDATOR.validate_paths(_VALIDATOR.default_repo_paths(root))

            self.assertTrue(result.ok(), msg=_VALIDATOR.format_issues(result))

    def test_optional_handoff_artifacts_skips_missing_build_verify(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "docs" / "current-plan.md", _minimal_current_plan())
            _write(root / "docs" / "long-run-state.md", _minimal_long_run_state())
            paths = _VALIDATOR.default_repo_paths(root)
            paths.pop("build_result", None)
            paths.pop("verify_result", None)

            result = _VALIDATOR.validate_paths(paths)

            self.assertTrue(result.ok(), msg=_VALIDATOR.format_issues(result))

    def test_cli_optional_handoff_allows_missing_handoffs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "docs" / "current-plan.md", _minimal_current_plan())
            _write(root / "docs" / "long-run-state.md", _minimal_long_run_state())

            completed = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR_PATH),
                    "--repo-root",
                    str(root),
                    "--require-current-plan",
                    "--optional-handoff-artifacts",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stdout + completed.stderr)

    def test_missing_required_file_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "docs" / "long-run-state.md"

            result = _VALIDATOR.validate_paths({"long_run_state": missing})

            self.assertFalse(result.ok())
            self.assertEqual(
                [(issue.code, issue.message) for issue in result.issues],
                [("missing", "file does not exist")],
            )

    def test_current_plan_requires_non_goals(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = Path(temp_dir) / "docs" / "current-plan.md"
            _write(
                plan,
                "# Current plan\n\n## DoR\n\n- Missing non-goals on purpose.\n",
            )

            result = _VALIDATOR.validate_paths({"current_plan": plan})

            self.assertFalse(result.ok())
            self.assertIn(("non_goals", "missing '## Non-goals' subsection"), {
                (issue.code, issue.message) for issue in result.issues
            })

    def test_current_plan_requires_closeout_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = Path(temp_dir) / "docs" / "current-plan.md"
            _write(plan, _minimal_current_plan())

            result = _VALIDATOR.validate_paths(
                {"current_plan": plan},
                require_current_plan_closeout=True,
            )

            self.assertFalse(result.ok())
            self.assertIn(("closeout_section", "missing '## Closeout' subsection"), {
                (issue.code, issue.message) for issue in result.issues
            })

    def test_trailing_whitespace_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = Path(temp_dir) / "docs" / "current-plan.md"
            _write(
                plan,
                "# Current plan\n\n## Non-goals\n\n- This line has trailing spaces.   \n",
            )

            result = _VALIDATOR.validate_paths({"current_plan": plan})

            self.assertFalse(result.ok())
            self.assertIn(("trailing_whitespace", "line 5: trailing whitespace"), {
                (issue.code, issue.message) for issue in result.issues
            })

    def test_long_run_requires_mission_execution_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            long_run = Path(temp_dir) / "docs" / "long-run-state.md"
            _write(
                long_run,
                textwrap.dedent(
                    """\
                    # Long-run mission state

                    **Last updated:** 2026-03-29

                    ## Mission

                    - **Goal:** Missing execution mode on purpose.

                    ## Parent mission gate compliance

                    - [ ] Gate entry exists.
                    """
                ),
            )

            result = _VALIDATOR.validate_paths({"long_run_state": long_run})

            self.assertFalse(result.ok())
            self.assertIn(
                (
                    "execution_mode",
                    "missing mission-level **execution_mode:** `short-run` or `long-run`",
                ),
                {(issue.code, issue.message) for issue in result.issues},
            )

    def test_long_run_accepts_parenthetical_mission_gate_heading(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            long_run = Path(temp_dir) / "docs" / "long-run-state.md"
            _write(
                long_run,
                textwrap.dedent(
                    """\
                    # Long-run mission state

                    **Last updated:** 2026-03-29

                    ## Mission

                    - **Goal:** Accept current repo heading style.
                    - **execution_mode:** `long-run`

                    ## Parent mission gate compliance (per verifier PASS)

                    - [ ] Gate entry exists.
                    """
                ),
            )

            result = _VALIDATOR.validate_paths({"long_run_state": long_run})

            self.assertTrue(result.ok(), msg=_VALIDATOR.format_issues(result))

    def test_long_run_rejects_bad_last_updated_format(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            long_run = Path(temp_dir) / "docs" / "long-run-state.md"
            _write(long_run, _minimal_long_run_state(last_updated="2026/03/29"))

            result = _VALIDATOR.validate_paths({"long_run_state": long_run})

            self.assertFalse(result.ok())
            self.assertIn(("last_updated", "missing '**Last updated:** YYYY-MM-DD' line"), {
                (issue.code, issue.message) for issue in result.issues
            })

    def test_long_run_freshness_check_is_optional(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            long_run = Path(temp_dir) / "docs" / "long-run-state.md"
            _write(long_run, _minimal_long_run_state(last_updated="2020-01-01"))

            result = _VALIDATOR.validate_paths(
                {"long_run_state": long_run},
                today=_VALIDATOR.date(2026, 3, 29),
                enforce_fresh_last_updated=True,
            )

            self.assertFalse(result.ok())
            self.assertIn(("last_updated_stale", "Last updated is older than 30 days"), {
                (issue.code, issue.message) for issue in result.issues
            })

    def test_build_or_verify_requires_iso_closeout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            build_result = Path(temp_dir) / "build-result.md"
            _write(
                build_result,
                "# Build Result\n\n## Closeout (2026-3-29)\n\nBad date format.\n",
            )

            result = _VALIDATOR.validate_paths({"build_result": build_result})

            self.assertFalse(result.ok())
            self.assertIn(
                ("closeout_subsection", "missing '## Closeout (YYYY-MM-DD)' subsection"),
                {(issue.code, issue.message) for issue in result.issues},
            )

    def test_build_result_requires_rich_contract_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            build_result = Path(temp_dir) / "build-result.md"
            _write(
                build_result,
                textwrap.dedent(
                    """\
                    # Build Result

                    ## Task
                    Validate the slice.

                    ## Status
                    PASS

                    ## Closeout (2026-03-29)

                    Ready for verification.
                    """
                ),
            )

            result = _VALIDATOR.validate_paths({"build_result": build_result})

            self.assertFalse(result.ok())
            issue_codes = {issue.code for issue in result.issues}
            self.assertTrue(
                {
                    "changes_made",
                    "acceptance_criteria",
                    "linting_type_check",
                    "issues_blockers",
                    "notes_for_verifier",
                }.issubset(issue_codes),
                msg=_VALIDATOR.format_issues(result),
            )

    def test_verify_result_requires_plan_builder_and_criteria_review_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            verify_result = Path(temp_dir) / "verify-result.md"
            _write(
                verify_result,
                textwrap.dedent(
                    """\
                    # Verify Result

                    ## Status
                    PASS

                    ## Closeout (2026-03-29)

                    Verified.
                    """
                ),
            )

            result = _VALIDATOR.validate_paths({"verify_result": verify_result})

            self.assertFalse(result.ok())
            issue_codes = {issue.code for issue in result.issues}
            self.assertTrue(
                {"plan", "builder_result", "criteria_review", "issues_found", "recommendations"}.issubset(
                    issue_codes
                ),
                msg=_VALIDATOR.format_issues(result),
            )

    def test_build_result_rejects_unresolved_acceptance_criterion_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            build_result = Path(temp_dir) / "build-result.md"
            _write(
                build_result,
                textwrap.dedent(
                    """\
                    # Build Result

                    ## Task
                    Validate the slice.

                    ## Status
                    PASS

                    ## Changes Made
                    - `docs/workflow-artifact-contract.md`: draft contract text

                    ## Acceptance Criteria
                    - [ ] Criterion 1

                    ## Linting / Type-Check
                    PASS

                    ## Issues / Blockers
                    None

                    ## Notes for Verifier
                    Inspect acceptance parsing.

                    ## Closeout (2026-03-29)

                    Ready for verification.
                    """
                ),
            )

            result = _VALIDATOR.validate_paths({"build_result": build_result})

            self.assertFalse(result.ok())
            self.assertIn(
                ("acceptance_criteria_format", "Acceptance Criteria bullets must include PASS, FAIL, or PARTIAL"),
                {(issue.code, issue.message) for issue in result.issues},
            )

    def test_malformed_json_fence_is_reported_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            long_run = Path(temp_dir) / "docs" / "long-run-state.md"
            _write(
                long_run,
                textwrap.dedent(
                    """\
                    # Long-run mission state

                    **Last updated:** 2026-03-29

                    ## Mission

                    - **Goal:** Test JSON validation.
                    - **execution_mode:** `long-run`

                    ```json
                    {"broken":
                    ```

                    ## Parent mission gate compliance

                    - [ ] Gate entry exists.
                    """
                ),
            )

            result = _VALIDATOR.validate_paths({"long_run_state": long_run})

            self.assertFalse(result.ok())
            self.assertIn(
                (
                    "json_parse",
                    "JSON fence starting at line 10 is invalid: Expecting value (line 1, column 11)",
                ),
                {(issue.code, issue.message) for issue in result.issues},
            )

    def test_phase1_verify_script_returns_nonzero_for_invalid_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_copy = Path(temp_dir) / "repo"
            shutil.copytree(
                REPO_ROOT,
                repo_copy,
                ignore=shutil.ignore_patterns(
                    ".git",
                    "__pycache__",
                    "*.pyc",
                    "node_modules",
                    ".venv",
                    ".uv",
                    ".cursor/data",
                    ".cursor/worktree",
                    "artifacts/phase1",
                ),
            )

            _write(repo_copy / "verify-result.md", _minimal_verify_result())
            _write(
                repo_copy / "docs" / "current-plan.md",
                "# Current plan\n\n## DoR\n\n- Deliberately invalid for the script test.\n",
            )

            env = os.environ.copy()
            env["PHASE1_VERIFY_SKIP_UNITTEST"] = "1"
            env["PHASE1_VERIFY_SKIP_BUN"] = "1"
            env["PHASE1_VERIFY_SKIP_CLIENT"] = "1"

            completed = subprocess.run(
                ["bash", str(repo_copy / "scripts" / "phase1-verify.sh")],
                cwd=repo_copy,
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0, msg=completed.stdout + completed.stderr)
            self.assertIn("missing '## Non-goals' subsection", completed.stdout + completed.stderr)


class ValidateCloseoutCoherenceProfileTest(unittest.TestCase):
    def test_missing_comparison_fails_without_adopted_marker(self) -> None:
        closeout_path = REPO_ROOT / "scripts" / "validate_closeout_coherence.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            completed = subprocess.run(
                [sys.executable, str(closeout_path), "--repo-root", str(root)],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("comparison_json_missing", completed.stdout + completed.stderr)

    def test_missing_comparison_skips_with_mat_sidecar_readme(self) -> None:
        closeout_path = REPO_ROOT / "scripts" / "validate_closeout_coherence.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".mat").mkdir(parents=True)
            (root / ".mat" / "README.md").write_text(
                "# `.mat/` — Multi-agent workflow (MAT) sidecar\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(closeout_path), "--repo-root", str(root)],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stdout + completed.stderr)
            self.assertIn("SKIPPED", completed.stdout)


class WorkflowArtifactContractPathTest(unittest.TestCase):
    def test_resolve_workflow_artifact_contract_prefers_root_docs(self) -> None:
        ac = _load_artifact_contract_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "docs").mkdir(parents=True)
            (root / "docs" / "workflow-artifact-contract.md").write_text("root", encoding="utf-8")
            (root / ".mat" / "docs").mkdir(parents=True)
            (root / ".mat" / "docs" / "workflow-artifact-contract.md").write_text(
                "sidecar", encoding="utf-8"
            )
            resolved = ac.resolve_workflow_artifact_contract_doc(root)
            self.assertIsNotNone(resolved)
            assert resolved is not None
            self.assertEqual(resolved.read_text(encoding="utf-8"), "root")

    def test_resolve_workflow_artifact_contract_falls_back_to_mat_docs(self) -> None:
        ac = _load_artifact_contract_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".mat" / "docs").mkdir(parents=True)
            (root / ".mat" / "docs" / "workflow-artifact-contract.md").write_text(
                "sidecar", encoding="utf-8"
            )
            resolved = ac.resolve_workflow_artifact_contract_doc(root)
            self.assertIsNotNone(resolved)
            assert resolved is not None
            self.assertEqual(resolved.read_text(encoding="utf-8"), "sidecar")

    def test_resolve_workflow_artifact_contract_none_when_missing(self) -> None:
        ac = _load_artifact_contract_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertIsNone(ac.resolve_workflow_artifact_contract_doc(root))


if __name__ == "__main__":
    unittest.main()
