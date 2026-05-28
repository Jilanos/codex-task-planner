"""Identifier generation helpers."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_plan_id(request: str, created_at: datetime | None = None) -> str:
    moment = created_at or utc_now()
    timestamp = moment.strftime("%Y%m%d-%H%M%S")
    digest = hashlib.sha256(f"{moment.isoformat()}\n{request}".encode("utf-8")).hexdigest()[:6]
    return f"PLAN-{timestamp}-{digest}"


def make_task_id(index: int) -> str:
    return f"TASK-{index:03d}"


def make_mode_id(model: str, reasoning_effort: str) -> str:
    safe_model = model.replace("/", "-").replace(" ", "-")
    safe_effort = reasoning_effort.replace("/", "-").replace(" ", "-")
    return f"{safe_model}_{safe_effort}"


def make_run_id(task_id: str, mode_id: str) -> str:
    return f"{task_id}__{mode_id}"
