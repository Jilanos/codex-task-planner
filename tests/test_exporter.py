import json
import unittest

from codex_task_planner.exporter import export_plan
from codex_task_planner.matrix import parse_matrix
from codex_task_planner.planner import create_plan


class ExporterTests(unittest.TestCase):
    def test_export_command_payloads(self):
        matrix = parse_matrix(
            {
                "models": ["m1"],
                "reasoning_efforts": ["low"],
                "default_checks": ["python -m unittest"],
                "workspace_root": "work",
                "output_root": "out",
                "timeout_seconds": 60,
            }
        )
        plan = create_plan("Build a CLI.", matrix)
        as_json = json.loads(export_plan(plan, "json"))
        self.assertEqual(as_json["plan_id"], plan.plan_id)
        as_jsonl = export_plan(plan, "jsonl").strip().splitlines()
        self.assertEqual(len(as_jsonl), len(plan.generated_runs))
        self.assertEqual(json.loads(as_jsonl[0])["run_id"], plan.generated_runs[0].run_id)


if __name__ == "__main__":
    unittest.main()
