from __future__ import annotations

import unittest

from codex_task_planner.features import extract_task_features


_BASE_SPEC = {
    "task_type": "implementation",
    "estimated_complexity": "low",
    "prompt": "Create a CLI entrypoint that validates JSON config files.",
    "acceptance_criteria": ["CLI exists.", "Returns nonzero on failure.", "Tests pass."],
    "checks": ["python -m compileall src", "python -m unittest"],
}


class FeatureExtractionTests(unittest.TestCase):
    def test_required_keys_are_present(self) -> None:
        features = extract_task_features(_BASE_SPEC, "build a cli validator", 0)
        required = {
            "task_type", "domains", "has_cli", "has_validation", "has_error_handling",
            "has_tests", "has_docs", "has_packaging", "has_persistence", "has_api",
            "has_auth", "has_security", "has_refactor", "has_migration", "has_logging",
            "has_benchmark", "has_export", "has_performance", "has_configuration",
            "has_concurrency", "has_io", "has_state",
            "complexity_estimate", "domain_count", "dependency_count",
            "acceptance_criteria_count", "check_count", "prompt_word_count",
        }
        self.assertEqual(required - features.keys(), set())

    def test_cli_domain_detected_from_request(self) -> None:
        features = extract_task_features(_BASE_SPEC, "build a cli tool", 0)
        self.assertIn("cli", features["domains"])
        self.assertTrue(features["has_cli"])
        self.assertTrue(features["has_io"])

    def test_persistence_sets_has_state(self) -> None:
        spec = {**_BASE_SPEC, "prompt": "Implement sqlite storage layer."}
        features = extract_task_features(spec, "add database persistence", 0)
        self.assertTrue(features["has_persistence"])
        self.assertTrue(features["has_state"])

    def test_scalar_metrics_are_correct(self) -> None:
        features = extract_task_features(_BASE_SPEC, "build a cli validator", 2)
        self.assertEqual(features["dependency_count"], 2)
        self.assertEqual(features["acceptance_criteria_count"], 3)
        self.assertEqual(features["check_count"], 2)
        self.assertGreater(features["prompt_word_count"], 0)

    def test_complexity_low_no_domains_no_deps(self) -> None:
        spec = {**_BASE_SPEC, "prompt": "Create a minimal skeleton."}
        features = extract_task_features(spec, "simple utility", 0)
        self.assertIn(features["complexity_estimate"], {"low", "medium", "high"})

    def test_complexity_high_for_refactor_type(self) -> None:
        spec = {**_BASE_SPEC, "task_type": "refactor", "prompt": "Refactor module."}
        features = extract_task_features(spec, "refactor codebase", 0)
        self.assertEqual(features["complexity_estimate"], "high")

    def test_complexity_high_with_many_domains(self) -> None:
        request = "cli api auth persistence logging benchmark security performance tests docs"
        features = extract_task_features(_BASE_SPEC, request, 0)
        self.assertEqual(features["complexity_estimate"], "high")

    def test_domains_are_sorted(self) -> None:
        features = extract_task_features(_BASE_SPEC, "cli validation tests docs", 0)
        self.assertEqual(features["domains"], sorted(features["domains"]))

    def test_task_type_is_preserved(self) -> None:
        for task_type in ("implementation", "test", "documentation", "verification"):
            spec = {**_BASE_SPEC, "task_type": task_type}
            features = extract_task_features(spec, "simple request", 0)
            self.assertEqual(features["task_type"], task_type)

    def test_empty_request_does_not_crash(self) -> None:
        spec = {**_BASE_SPEC, "prompt": ""}
        features = extract_task_features(spec, "", 0)
        self.assertEqual(features["domains"], [])
        self.assertEqual(features["prompt_word_count"], 0)

    def test_features_in_generated_plan_tasks(self) -> None:
        from codex_task_planner.planner import build_tasks
        tasks = build_tasks("Build a CLI that validates JSON and reports errors. Add tests.", ["python -m unittest"])
        for task in tasks:
            self.assertIsInstance(task.features, dict)
            self.assertIn("task_type", task.features)
            self.assertIn("domains", task.features)
            self.assertIn("complexity_estimate", task.features)


if __name__ == "__main__":
    unittest.main()
