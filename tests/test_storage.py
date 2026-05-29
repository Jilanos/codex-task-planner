import json
import tempfile
import unittest
from pathlib import Path

from codex_task_planner.matrix import parse_matrix
from codex_task_planner.planner import create_plan
from codex_task_planner.storage import load_plan, write_plan


class StorageTests(unittest.TestCase):
    def test_plan_artifacts_and_harness_task_files_are_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".codex-task-planner"
            matrix = parse_matrix(
                {
                    "models": ["m1"],
                    "reasoning_efforts": ["low", "medium"],
                    "default_checks": ["python -m unittest"],
                    "workspace_root": str(root / "generated_workspaces"),
                    "output_root": str(root / "generated_artifacts"),
                    "timeout_seconds": 60,
                }
            )
            plan = create_plan("Build a CLI with tests.", matrix, root / "plans")
            directory = write_plan(plan, matrix, root)
            self.assertTrue((directory / "plan.json").exists())
            self.assertTrue((directory / "tasks.jsonl").exists())
            self.assertTrue((directory / "generated_runs.jsonl").exists())
            first_task_file = Path(plan.generated_runs[0].task_file)
            self.assertTrue(first_task_file.exists())
            raw = json.loads(first_task_file.read_text(encoding="utf-8"))
            self.assertIn("Global context:", raw["prompt"])
            self.assertIn("Local context:", raw["prompt"])
            loaded = load_plan(plan.plan_id, root)
            self.assertEqual(loaded.plan_id, plan.plan_id)

    def test_harness_task_files_include_features(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".codex-task-planner"
            matrix = parse_matrix(
                {
                    "models": ["m1"],
                    "reasoning_efforts": ["low"],
                    "default_checks": ["python -m unittest"],
                    "workspace_root": str(root / "ws"),
                    "output_root": str(root / "out"),
                    "timeout_seconds": 60,
                }
            )
            plan = create_plan("Build a CLI that validates JSON. Add tests.", matrix, root / "plans")
            write_plan(plan, matrix, root)
            task_file = Path(plan.generated_runs[0].task_file)
            raw = json.loads(task_file.read_text(encoding="utf-8"))
            self.assertIn("features", raw)
            features = raw["features"]
            self.assertIn("task_type", features)
            self.assertIn("domains", features)
            self.assertIn("complexity_estimate", features)

    def test_tasks_jsonl_includes_features(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".codex-task-planner"
            matrix = parse_matrix(
                {
                    "models": ["m1"],
                    "reasoning_efforts": ["low"],
                    "default_checks": [],
                    "workspace_root": str(root / "ws"),
                    "output_root": str(root / "out"),
                    "timeout_seconds": 60,
                }
            )
            plan = create_plan("Build a CLI with validation and tests.", matrix, root / "plans")
            directory = write_plan(plan, matrix, root)
            lines = (directory / "tasks.jsonl").read_text(encoding="utf-8").splitlines()
            for line in lines:
                task = json.loads(line)
                self.assertIn("features", task)
                self.assertIsInstance(task["features"], dict)


if __name__ == "__main__":
    unittest.main()
