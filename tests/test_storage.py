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


if __name__ == "__main__":
    unittest.main()
