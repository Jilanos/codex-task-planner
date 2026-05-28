"""Deterministic rule-based request decomposition."""

from __future__ import annotations

import itertools
import re
import textwrap
from datetime import timezone
from pathlib import Path
from typing import Any

from .ids import make_mode_id, make_plan_id, make_run_id, make_task_id, utc_now
from .models import GeneratedRun, Matrix, Mode, Plan, Task


KEYWORDS = {
    "cli": re.compile(r"\b(cli|command line|command-line|entrypoint)\b", re.I),
    "configuration": re.compile(r"\b(config|configuration|settings)\b", re.I),
    "validation": re.compile(r"\b(validat\w*|schema|required keys?)\b", re.I),
    "error_handling": re.compile(r"\b(errors?|error messages?|failure|failures|nonzero|non-zero)\b", re.I),
    "tests": re.compile(r"\b(tests?|unittest|unit tests?|coverage)\b", re.I),
    "documentation": re.compile(r"\b(documentation|docs?|readme)\b", re.I),
    "packaging": re.compile(r"\b(packaging|package|install|pyproject)\b", re.I),
    "persistence": re.compile(r"\b(database|persistence|persist|storage|sqlite)\b", re.I),
    "api": re.compile(r"\b(api|endpoint|route|http|rest)\b", re.I),
    "refactor": re.compile(r"\b(refactor|cleanup|restructure)\b", re.I),
    "migration": re.compile(r"\b(migration|migrate)\b", re.I),
    "logging": re.compile(r"\b(logging|logs?|logger)\b", re.I),
    "benchmark": re.compile(r"\b(benchmark|benchmarks?)\b", re.I),
    "export": re.compile(r"\b(export|exports?)\b", re.I),
    "import": re.compile(r"\b(import|imports?)\b", re.I),
    "authentication": re.compile(r"\b(authentication|auth|login|oauth)\b", re.I),
    "security": re.compile(r"\b(security|secure|secrets?|vulnerabilit)\b", re.I),
    "performance": re.compile(r"\b(performance|optimi[sz]e|fast|latency)\b", re.I),
}


def load_request(path: str | Path) -> str:
    request_path = Path(path)
    try:
        request = request_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise ValueError(f"request file not found: {request_path}") from exc
    if not request:
        raise ValueError("request file is empty")
    return request


def create_plan(request: str, matrix: Matrix, base_plan_dir: str | Path | None = None) -> Plan:
    request = request.strip()
    if not request:
        raise ValueError("request must not be empty")

    created_at_dt = utc_now()
    created_at = created_at_dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    plan_id = make_plan_id(request, created_at_dt)
    global_context = build_global_context(request)
    tasks = build_tasks(request, matrix.default_checks)
    modes = [
        Mode(
            mode_id=make_mode_id(model, effort),
            model=model,
            reasoning_effort=effort,
            timeout_seconds=matrix.timeout_seconds,
        )
        for model, effort in itertools.product(matrix.models, matrix.reasoning_efforts)
    ]
    plan_dir = Path(base_plan_dir or ".codex-task-planner/plans") / plan_id
    runs = build_generated_runs(tasks, modes, matrix, plan_dir)
    return Plan(
        plan_id=plan_id,
        created_at=created_at,
        request=request,
        global_context=global_context,
        tasks=tasks,
        modes=modes,
        generated_runs=runs,
    )


def build_global_context(request: str) -> dict[str, Any]:
    goal = _first_sentence(request)
    constraints = ["Keep the implementation simple and focused."]
    assumptions = ["The target project is a Python project."]
    if KEYWORDS["tests"].search(request):
        constraints.append("Add tests.")
    if KEYWORDS["documentation"].search(request):
        constraints.append("Add documentation.")
    if KEYWORDS["error_handling"].search(request):
        assumptions.append("Failure paths should return nonzero exit codes where a CLI is involved.")
    if KEYWORDS["configuration"].search(request):
        assumptions.append("Configuration input should be handled with clear validation boundaries.")
    return {
        "project_goal": goal,
        "constraints": constraints,
        "assumptions": assumptions,
    }


def build_tasks(request: str, checks: list[str]) -> list[Task]:
    task_specs: list[dict[str, Any]] = []
    task_specs.append(_implementation_spec(request))

    ordered_components = [
        ("cli", _cli_spec),
        ("validation", _validation_spec),
        ("error_handling", _error_spec),
        ("persistence", _persistence_spec),
        ("api", _api_spec),
        ("refactor", _refactor_spec),
        ("packaging", _packaging_spec),
        ("tests", _tests_spec),
        ("documentation", _documentation_spec),
    ]
    seen_titles = {task_specs[0]["title"]}
    for key, factory in ordered_components:
        if KEYWORDS[key].search(request):
            spec = factory()
            if spec["title"] not in seen_titles:
                task_specs.append(spec)
                seen_titles.add(spec["title"])

    task_specs.append(_verification_spec())
    tasks: list[Task] = []
    for index, spec in enumerate(task_specs, start=1):
        task_id = make_task_id(index)
        dependencies = _resolve_dependencies(spec, tasks)
        tasks.append(
            Task(
                task_id=task_id,
                title=spec["title"],
                task_type=spec["task_type"],
                estimated_complexity=spec["estimated_complexity"],
                dependencies=dependencies,
                prompt=spec["prompt"],
                local_context=spec["local_context"],
                acceptance_criteria=spec["acceptance_criteria"],
                checks=list(checks),
            )
        )
    return tasks


def build_generated_runs(tasks: list[Task], modes: list[Mode], matrix: Matrix, plan_dir: Path) -> list[GeneratedRun]:
    runs = []
    for task, mode in itertools.product(tasks, modes):
        run_id = make_run_id(task.task_id, mode.mode_id)
        runs.append(
            GeneratedRun(
                run_id=run_id,
                task_id=task.task_id,
                mode_id=mode.mode_id,
                model=mode.model,
                reasoning_effort=mode.reasoning_effort,
                workspace=str(Path(matrix.workspace_root) / run_id),
                checks=list(task.checks),
                output_root=matrix.output_root,
                timeout_seconds=mode.timeout_seconds,
                task_file=str(plan_dir / "harness_tasks" / f"{run_id}.json"),
            )
        )
    return runs


def render_harness_prompt(plan: Plan, task: Task) -> str:
    criteria = "\n".join(f"- {item}" for item in task.acceptance_criteria)
    constraints = "\n".join(f"- {item}" for item in plan.global_context["constraints"])
    assumptions = "\n".join(f"- {item}" for item in plan.global_context["assumptions"])
    local_context = "\n".join(f"- {key}: {value}" for key, value in task.local_context.items())
    return textwrap.dedent(
        f"""
        Global context:
        Project goal: {plan.global_context["project_goal"]}
        Constraints:
        {constraints}
        Assumptions:
        {assumptions}

        Task:
        {task.prompt}

        Local context:
        {local_context}

        Acceptance criteria:
        {criteria}

        Verification commands:
        {chr(10).join(f"- {check}" for check in task.checks)}
        """
    ).strip()


def _resolve_dependencies(spec: dict[str, Any], tasks: list[Task]) -> list[str]:
    if spec.get("depends_on_previous") and tasks:
        return [tasks[-1].task_id]
    if spec["task_type"] in {"test", "documentation", "packaging", "verification"} and tasks:
        return [tasks[-1].task_id]
    return []


def _first_sentence(request: str) -> str:
    compact = " ".join(request.split())
    match = re.search(r"(.+?[.!?])(?:\s|$)", compact)
    return match.group(1) if match else compact


def _implementation_spec(request: str) -> dict[str, Any]:
    return {
        "title": "Create core implementation skeleton",
        "task_type": "implementation",
        "estimated_complexity": "low",
        "prompt": "Create the smallest coherent implementation skeleton needed to satisfy the requested feature.",
        "local_context": {
            "scope": "Core implementation structure only.",
            "expected_files": ["src/", "tests/"],
            "out_of_scope": ["Release automation", "external service calls", "large refactors"],
        },
        "acceptance_criteria": [
            "The project has a clear implementation entry point.",
            "The code is organized so later tasks can extend it cleanly.",
            "No network calls or LLM calls are introduced.",
        ],
    }


def _cli_spec() -> dict[str, Any]:
    return {
        "title": "Create CLI entrypoint",
        "task_type": "implementation",
        "estimated_complexity": "low",
        "prompt": "Implement a CLI entrypoint that accepts the required command arguments and returns clear exit codes.",
        "local_context": {"scope": "CLI argument parsing and process exit behavior.", "expected_files": ["src/", "tests/"], "out_of_scope": ["Shell completion", "interactive prompts"]},
        "acceptance_criteria": ["A CLI entrypoint exists.", "The CLI accepts the requested arguments.", "The CLI exits with code 0 on success and nonzero on failure."],
        "depends_on_previous": True,
    }


def _validation_spec() -> dict[str, Any]:
    return {
        "title": "Implement validation logic",
        "task_type": "implementation",
        "estimated_complexity": "medium",
        "prompt": "Implement deterministic validation logic for the requested inputs and required fields.",
        "local_context": {"scope": "Validation rules and return values.", "expected_files": ["src/", "tests/"], "out_of_scope": ["Full JSON schema engine", "remote validation"]},
        "acceptance_criteria": ["Valid input is accepted.", "Missing or malformed required data is rejected.", "Validation behavior is deterministic and covered by checks."],
        "depends_on_previous": True,
    }


def _error_spec() -> dict[str, Any]:
    return {
        "title": "Add clear error handling",
        "task_type": "implementation",
        "estimated_complexity": "low",
        "prompt": "Add readable error handling for invalid inputs, parse failures, and expected failure modes.",
        "local_context": {"scope": "User-facing error messages and failure paths.", "expected_files": ["src/", "tests/"], "out_of_scope": ["Internationalization", "telemetry"]},
        "acceptance_criteria": ["Failure messages explain what went wrong.", "Expected errors do not produce tracebacks for users.", "Failure paths return nonzero exit codes where applicable."],
        "depends_on_previous": True,
    }


def _tests_spec() -> dict[str, Any]:
    return {
        "title": "Add focused tests",
        "task_type": "test",
        "estimated_complexity": "low",
        "prompt": "Add focused unit tests for successful behavior, validation failures, and expected error paths.",
        "local_context": {"scope": "Unit tests for requested behavior.", "expected_files": ["tests/"], "out_of_scope": ["Network tests", "slow end-to-end suites"]},
        "acceptance_criteria": ["Tests cover success cases.", "Tests cover failure cases.", "The configured test command passes."],
    }


def _documentation_spec() -> dict[str, Any]:
    return {
        "title": "Write user documentation",
        "task_type": "documentation",
        "estimated_complexity": "low",
        "prompt": "Document the feature, usage examples, failure behavior, and verification commands.",
        "local_context": {"scope": "README or project documentation.", "expected_files": ["README.md", "docs/"], "out_of_scope": ["Hosted documentation site"]},
        "acceptance_criteria": ["Usage is documented.", "Examples are included.", "Known limitations or failure behavior are documented."],
    }


def _packaging_spec() -> dict[str, Any]:
    return {
        "title": "Add packaging metadata",
        "task_type": "packaging",
        "estimated_complexity": "low",
        "prompt": "Add or update packaging metadata so the project can be installed and invoked locally.",
        "local_context": {"scope": "Local package metadata and console entry points.", "expected_files": ["pyproject.toml"], "out_of_scope": ["Publishing to package indexes"]},
        "acceptance_criteria": ["The project can be installed locally.", "Console entry points are declared if needed.", "Packaging metadata remains minimal."],
    }


def _persistence_spec() -> dict[str, Any]:
    return {
        "title": "Implement persistence boundary",
        "task_type": "implementation",
        "estimated_complexity": "medium",
        "prompt": "Implement the minimal local persistence or database boundary required by the request.",
        "local_context": {"scope": "Storage interface and local persistence behavior.", "expected_files": ["src/", "tests/"], "out_of_scope": ["Hosted databases", "distributed storage"]},
        "acceptance_criteria": ["Data can be saved and loaded locally.", "Persistence errors are handled clearly.", "Storage behavior is covered by tests."],
        "depends_on_previous": True,
    }


def _api_spec() -> dict[str, Any]:
    return {
        "title": "Implement API surface",
        "task_type": "implementation",
        "estimated_complexity": "medium",
        "prompt": "Implement the requested API surface with deterministic request and response behavior.",
        "local_context": {"scope": "API routes or callable interface.", "expected_files": ["src/", "tests/"], "out_of_scope": ["External hosting", "authentication unless explicitly requested"]},
        "acceptance_criteria": ["The requested API surface exists.", "Valid requests return expected results.", "Invalid requests produce clear errors."],
        "depends_on_previous": True,
    }


def _refactor_spec() -> dict[str, Any]:
    return {
        "title": "Refactor targeted code",
        "task_type": "refactor",
        "estimated_complexity": "high",
        "prompt": "Refactor the targeted code while preserving externally visible behavior.",
        "local_context": {"scope": "Requested refactor only.", "expected_files": ["src/", "tests/"], "out_of_scope": ["Unrelated style churn", "feature changes"]},
        "acceptance_criteria": ["Existing behavior is preserved.", "Code organization is clearer.", "Tests or checks confirm no regression."],
        "depends_on_previous": True,
    }


def _verification_spec() -> dict[str, Any]:
    return {
        "title": "Run final verification",
        "task_type": "verification",
        "estimated_complexity": "low",
        "prompt": "Run the configured verification commands and fix any small issues required for them to pass.",
        "local_context": {"scope": "Final checks only.", "expected_files": ["src/", "tests/", "README.md"], "out_of_scope": ["New feature work"]},
        "acceptance_criteria": ["All configured checks pass.", "Generated or changed files are internally consistent.", "No hidden execution assumptions remain."],
    }
