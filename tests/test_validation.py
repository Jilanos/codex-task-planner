import tempfile
import unittest
from pathlib import Path

from codex_task_planner.matrix import parse_matrix
from codex_task_planner.models import Task
from codex_task_planner.planner import create_plan
from codex_task_planner.storage import write_plan
from codex_task_planner.validation import validate_plan


class ValidationTests(unittest.TestCase):
    def test_validate_command_rules_accept_valid_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".codex-task-planner"
            matrix = parse_matrix(
                {
                    "models": ["m1"],
                    "reasoning_efforts": ["low"],
                    "default_checks": ["python -m unittest"],
                    "workspace_root": str(root / "work"),
                    "output_root": str(root / "out"),
                    "timeout_seconds": 60,
                }
            )
            plan = create_plan("Build a CLI with tests.", matrix, root / "plans")
            write_plan(plan, matrix, root)
            self.assertEqual(validate_plan(plan, root), [])

    def test_validation_finds_duplicate_task_ids_and_bad_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".codex-task-planner"
            matrix = parse_matrix(
                {
                    "models": ["m1"],
                    "reasoning_efforts": ["low"],
                    "default_checks": ["python -m unittest"],
                    "workspace_root": str(root / "work"),
                    "output_root": str(root / "out"),
                    "timeout_seconds": 60,
                }
            )
            plan = create_plan("Build a CLI.", matrix, root / "plans")
            duplicate = Task(
                task_id=plan.tasks[0].task_id,
                title="Bad duplicate",
                task_type="implementation",
                estimated_complexity="low",
                dependencies=["TASK-999"],
                prompt="Bad task.",
                local_context={},
                acceptance_criteria=[],
                checks=[],
            )
            bad_plan = type(plan)(
                plan_id=plan.plan_id,
                created_at=plan.created_at,
                request=plan.request,
                global_context=plan.global_context,
                tasks=plan.tasks + [duplicate],
                modes=plan.modes,
                generated_runs=[],
            )
            errors = validate_plan(bad_plan, root)
            self.assertTrue(any("duplicate task ids" in error for error in errors))
            self.assertTrue(any("invalid task dependency" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
