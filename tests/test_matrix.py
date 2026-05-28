import json
import tempfile
import unittest
from pathlib import Path

from codex_task_planner.matrix import MatrixError, load_matrix, parse_matrix


class MatrixTests(unittest.TestCase):
    def test_matrix_files_load_correctly(self):
        matrix = load_matrix(Path("examples/matrices/default.json"))
        self.assertEqual(matrix.models[0], "gpt-5.3-codex")
        self.assertEqual(matrix.reasoning_efforts, ["low", "medium", "high"])

    def test_invalid_matrix_files_fail_clearly(self):
        with self.assertRaisesRegex(MatrixError, "models must not be empty"):
            parse_matrix(
                {
                    "models": [],
                    "reasoning_efforts": ["low"],
                    "default_checks": [],
                    "workspace_root": "work",
                    "output_root": "out",
                    "timeout_seconds": 10,
                }
            )

    def test_invalid_json_fails_clearly(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "matrix.json"
            path.write_text("{bad", encoding="utf-8")
            with self.assertRaisesRegex(MatrixError, "invalid matrix JSON"):
                load_matrix(path)


if __name__ == "__main__":
    unittest.main()
