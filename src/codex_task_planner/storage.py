"""File persistence for plans and generated harness task files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import GeneratedRun, Matrix, Plan, Task
from .planner import render_harness_prompt

DEFAULT_ROOT = Path(".codex-task-planner")


def plan_dir(plan_id: str, root: str | Path = DEFAULT_ROOT) -> Path:
    return Path(root) / "plans" / plan_id


def write_plan(plan: Plan, matrix: Matrix, root: str | Path = DEFAULT_ROOT) -> Path:
    directory = plan_dir(plan.plan_id, root)
    harness_dir = directory / "harness_tasks"
    harness_dir.mkdir(parents=True, exist_ok=True)
    _write_json(directory / "plan.json", plan.to_dict())
    _write_json(directory / "matrix.json", matrix.to_dict())
    _write_jsonl(directory / "tasks.jsonl", [task.to_dict() for task in plan.tasks])
    _write_jsonl(directory / "generated_runs.jsonl", [run.to_dict() for run in plan.generated_runs])
    task_lookup = {task.task_id: task for task in plan.tasks}
    for run in plan.generated_runs:
        task = task_lookup[run.task_id]
        _write_json(Path(run.task_file), build_harness_task(plan, task, run))
    return directory


def load_plan(plan_id_value: str, root: str | Path = DEFAULT_ROOT) -> Plan:
    from .models import GeneratedRun, Mode, Task

    path = plan_dir(plan_id_value, root) / "plan.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"plan not found: {plan_id_value}") from exc
    return Plan(
        plan_id=raw["plan_id"],
        created_at=raw["created_at"],
        request=raw["request"],
        global_context=raw["global_context"],
        tasks=[Task(**task) for task in raw["tasks"]],
        modes=[Mode(**mode) for mode in raw["modes"]],
        generated_runs=[GeneratedRun(**run) for run in raw["generated_runs"]],
    )


def load_matrix_snapshot(plan_id_value: str, root: str | Path = DEFAULT_ROOT) -> Matrix:
    path = plan_dir(plan_id_value, root) / "matrix.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return Matrix(**raw)


def build_harness_task(plan: Plan, task: Task, run: GeneratedRun) -> dict[str, object]:
    return {
        "task_id": run.run_id,
        "prompt": render_harness_prompt(plan, task),
        "model": run.model,
        "reasoning_effort": run.reasoning_effort,
        "workspace": run.workspace,
        "checks": run.checks,
        "output_root": run.output_root,
        "timeout_seconds": run.timeout_seconds,
    }


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    path.write_text(content, encoding="utf-8")
