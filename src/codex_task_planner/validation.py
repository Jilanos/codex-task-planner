"""Plan validation for stored artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from .models import Plan
from .storage import plan_dir


class ValidationError(ValueError):
    """Raised when a stored plan is invalid."""


REQUIRED_HARNESS_KEYS = {
    "task_id",
    "prompt",
    "model",
    "reasoning_effort",
    "workspace",
    "checks",
    "output_root",
    "timeout_seconds",
}


def validate_plan(plan: Plan, root: str | Path = ".codex-task-planner") -> list[str]:
    errors: list[str] = []
    task_ids = [task.task_id for task in plan.tasks]
    mode_ids = [mode.mode_id for mode in plan.modes]
    if len(task_ids) != len(set(task_ids)):
        errors.append("duplicate task ids")
    if len(mode_ids) != len(set(mode_ids)):
        errors.append("duplicate mode ids")
    known_tasks = set(task_ids)
    for task in plan.tasks:
        for dependency in task.dependencies:
            if dependency not in known_tasks:
                errors.append(f"invalid task dependency: {task.task_id} depends on {dependency}")
    for run in plan.generated_runs:
        if run.task_id not in known_tasks:
            errors.append(f"generated run references missing task: {run.run_id}")
        if run.mode_id not in mode_ids:
            errors.append(f"generated run references missing mode: {run.run_id}")
        _validate_harness_file(run.task_file, errors)
    expected_plan = plan_dir(plan.plan_id, root) / "plan.json"
    if not expected_plan.exists():
        errors.append(f"missing plan.json: {expected_plan}")
    return errors


def validate_or_raise(plan: Plan, root: str | Path = ".codex-task-planner") -> None:
    errors = validate_plan(plan, root)
    if errors:
        raise ValidationError("; ".join(errors))


def _validate_harness_file(path_value: str, errors: list[str]) -> None:
    path = Path(path_value)
    if not path.exists():
        errors.append(f"missing generated task file: {path}")
        return
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid generated task file JSON: {path}: {exc}")
        return
    missing = REQUIRED_HARNESS_KEYS - set(raw)
    if missing:
        errors.append(f"invalid generated task file shape: {path}: missing {', '.join(sorted(missing))}")
    if not isinstance(raw.get("prompt"), str) or "Global context:" not in raw.get("prompt", ""):
        errors.append(f"invalid generated task file shape: {path}: prompt missing global context")
    if not isinstance(raw.get("checks"), list):
        errors.append(f"invalid generated task file shape: {path}: checks must be a list")
