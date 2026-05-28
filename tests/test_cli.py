import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from codex_task_planner.cli import main


class CliTests(unittest.TestCase):
    def test_create_inspect_export_validate_commands_work(self):
        repo = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                request = Path("request.md")
                matrix = Path("matrix.json")
                request.write_text("Build a CLI with validation errors tests and documentation.", encoding="utf-8")
                matrix.write_text(
                    """{
                      "models": ["m1"],
                      "reasoning_efforts": ["low", "high"],
                      "default_checks": ["python -m unittest"],
                      "workspace_root": ".codex-task-planner/generated_workspaces",
                      "output_root": ".codex-task-planner/generated_artifacts",
                      "timeout_seconds": 60
                    }""",
                    encoding="utf-8",
                )

                out = io.StringIO()
                with redirect_stdout(out):
                    self.assertEqual(main(["create", "--request-file", str(request), "--matrix", str(matrix)]), 0)
                plan_id = out.getvalue().splitlines()[0].split()[1]

                inspect_out = io.StringIO()
                with redirect_stdout(inspect_out):
                    self.assertEqual(main(["inspect", "--plan-id", plan_id]), 0)
                self.assertIn("generated_runs:", inspect_out.getvalue())

                export_out = io.StringIO()
                with redirect_stdout(export_out):
                    self.assertEqual(main(["export", "--plan-id", plan_id, "--format", "jsonl"]), 0)
                self.assertIn('"run_id"', export_out.getvalue())

                validate_out = io.StringIO()
                with redirect_stdout(validate_out):
                    self.assertEqual(main(["validate", "--plan-id", plan_id]), 0)
                self.assertIn(f"valid {plan_id}", validate_out.getvalue())
            finally:
                os.chdir(repo)

    def test_missing_request_file_fails(self):
        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["create", "--request-file", "missing.md", "--matrix", "missing.json"])
        self.assertEqual(code, 2)
        self.assertIn("request file not found", err.getvalue())


if __name__ == "__main__":
    unittest.main()
