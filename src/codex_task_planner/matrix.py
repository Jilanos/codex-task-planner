"""Execution matrix loading and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Matrix


class MatrixError(ValueError):
    """Raised when an execution matrix is invalid."""


def load_matrix(path: str | Path) -> Matrix:
    matrix_path = Path(path)
    try:
        raw = json.loads(matrix_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MatrixError(f"matrix file not found: {matrix_path}") from exc
    except json.JSONDecodeError as exc:
        raise MatrixError(f"invalid matrix JSON: {exc}") from exc
    return parse_matrix(raw)


def parse_matrix(raw: dict[str, Any]) -> Matrix:
    required = [
        "models",
        "reasoning_efforts",
        "default_checks",
        "workspace_root",
        "output_root",
        "timeout_seconds",
    ]
    missing = [key for key in required if key not in raw]
    if missing:
        raise MatrixError(f"matrix missing required keys: {', '.join(missing)}")

    models = _string_list(raw["models"], "models")
    reasoning_efforts = _string_list(raw["reasoning_efforts"], "reasoning_efforts")
    default_checks = _string_list(raw["default_checks"], "default_checks")
    if not models:
        raise MatrixError("matrix models must not be empty")
    if not reasoning_efforts:
        raise MatrixError("matrix reasoning_efforts must not be empty")
    if not isinstance(raw["workspace_root"], str) or not raw["workspace_root"].strip():
        raise MatrixError("matrix workspace_root must be a nonempty string")
    if not isinstance(raw["output_root"], str) or not raw["output_root"].strip():
        raise MatrixError("matrix output_root must be a nonempty string")
    if not isinstance(raw["timeout_seconds"], int) or raw["timeout_seconds"] <= 0:
        raise MatrixError("matrix timeout_seconds must be a positive integer")

    return Matrix(
        models=models,
        reasoning_efforts=reasoning_efforts,
        default_checks=default_checks,
        workspace_root=raw["workspace_root"],
        output_root=raw["output_root"],
        timeout_seconds=raw["timeout_seconds"],
    )


def _string_list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list):
        raise MatrixError(f"matrix {name} must be a list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise MatrixError(f"matrix {name} must contain only nonempty strings")
    return list(value)
