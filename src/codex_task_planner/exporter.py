"""Plan export helpers."""

from __future__ import annotations

import json

from .models import Plan


def export_plan(plan: Plan, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(plan.to_dict(), indent=2, sort_keys=True)
    if fmt == "jsonl":
        return "".join(json.dumps(run.to_dict(), sort_keys=True) + "\n" for run in plan.generated_runs)
    raise ValueError(f"unsupported export format: {fmt}")
