"""Dataclasses and JSON helpers for plans, tasks, modes, and generated runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Matrix:
    models: list[str]
    reasoning_efforts: list[str]
    default_checks: list[str]
    workspace_root: str
    output_root: str
    timeout_seconds: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Mode:
    mode_id: str
    model: str
    reasoning_effort: str
    timeout_seconds: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Task:
    task_id: str
    title: str
    task_type: str
    estimated_complexity: str
    dependencies: list[str]
    prompt: str
    local_context: dict[str, Any]
    acceptance_criteria: list[str]
    checks: list[str]
    features: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GeneratedRun:
    run_id: str
    task_id: str
    mode_id: str
    model: str
    reasoning_effort: str
    workspace: str
    checks: list[str]
    output_root: str
    timeout_seconds: int
    task_file: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Plan:
    plan_id: str
    created_at: str
    request: str
    global_context: dict[str, Any]
    tasks: list[Task] = field(default_factory=list)
    modes: list[Mode] = field(default_factory=list)
    generated_runs: list[GeneratedRun] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "created_at": self.created_at,
            "request": self.request,
            "global_context": self.global_context,
            "tasks": [task.to_dict() for task in self.tasks],
            "modes": [mode.to_dict() for mode in self.modes],
            "generated_runs": [run.to_dict() for run in self.generated_runs],
        }
