import unittest

from codex_task_planner.matrix import parse_matrix
from codex_task_planner.planner import build_tasks, create_plan, load_request


def matrix():
    return parse_matrix(
        {
            "models": ["m1", "m2"],
            "reasoning_efforts": ["low", "high"],
            "default_checks": ["python -m unittest"],
            "workspace_root": "work",
            "output_root": "out",
            "timeout_seconds": 60,
        }
    )


class PlannerTests(unittest.TestCase):
    def test_request_files_load_correctly(self):
        request = load_request("examples/requests/simple_request.md")
        self.assertIn("validates JSON", request)

    def test_plan_ids_are_generated(self):
        plan = create_plan("Build a CLI.", matrix())
        self.assertRegex(plan.plan_id, r"^PLAN-\d{8}-\d{6}-[a-f0-9]{6}$")

    def test_default_implementation_and_final_verification_tasks_are_generated(self):
        tasks = build_tasks("Build something useful.", ["python -m unittest"])
        self.assertEqual(tasks[0].title, "Create core implementation skeleton")
        self.assertEqual(tasks[-1].title, "Run final verification")

    def test_keywords_create_expected_tasks(self):
        tasks = build_tasks(
            "Build a CLI with validation, clear errors, tests, documentation, persistence, API, refactor, packaging.",
            ["python -m unittest"],
        )
        titles = {task.title for task in tasks}
        self.assertIn("Create CLI entrypoint", titles)
        self.assertIn("Implement validation logic", titles)
        self.assertIn("Add clear error handling", titles)
        self.assertIn("Add focused tests", titles)
        self.assertIn("Write user documentation", titles)
        self.assertIn("Implement persistence boundary", titles)
        self.assertIn("Implement API surface", titles)
        self.assertIn("Refactor targeted code", titles)
        self.assertIn("Add packaging metadata", titles)

    def test_task_dependencies_are_valid(self):
        plan = create_plan("Build a CLI with validation errors tests and documentation.", matrix())
        task_ids = {task.task_id for task in plan.tasks}
        for task in plan.tasks:
            for dependency in task.dependencies:
                self.assertIn(dependency, task_ids)

    def test_all_model_and_reasoning_combinations_are_generated(self):
        plan = create_plan("Build a CLI.", matrix())
        self.assertEqual(len(plan.modes), 4)
        self.assertEqual(len(plan.generated_runs), len(plan.tasks) * 4)


if __name__ == "__main__":
    unittest.main()
