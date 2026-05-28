"""Command line interface for codex-task-planner."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from .exporter import export_plan
from .matrix import MatrixError, load_matrix
from .planner import create_plan, load_request
from .storage import load_plan, write_plan
from .validation import validate_plan


def _configure_logging(level: str | None) -> None:
    raw = level or os.environ.get("CODEX_TASK_PLANNER_LOG", "WARNING")
    logging.basicConfig(
        level=getattr(logging, raw.upper(), logging.WARNING),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stderr,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-task-planner")
    parser.add_argument("--log-level", default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="create a new durable plan")
    create.add_argument("--request-file", required=True)
    create.add_argument("--matrix", required=True)

    inspect = subparsers.add_parser("inspect", help="inspect an existing plan")
    inspect.add_argument("--plan-id", required=True)

    export = subparsers.add_parser("export", help="export generated runs")
    export.add_argument("--plan-id", required=True)
    export.add_argument("--format", choices=["json", "jsonl"], default="jsonl")

    validate = subparsers.add_parser("validate", help="validate an existing plan")
    validate.add_argument("--plan-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.log_level)
    try:
        if args.command == "create":
            request = load_request(args.request_file)
            matrix = load_matrix(args.matrix)
            plan = create_plan(request, matrix)
            directory = write_plan(plan, matrix)
            print(f"created {plan.plan_id}")
            print(f"plan_dir {directory}")
            print(f"tasks {len(plan.tasks)}")
            print(f"modes {len(plan.modes)}")
            print(f"generated_runs {len(plan.generated_runs)}")
            print("CODEX_TASK_PLANNER_RESULT " + json.dumps({
                "plan_id": plan.plan_id,
                "plan_dir": str(directory),
                "tasks": len(plan.tasks),
                "modes": len(plan.modes),
                "generated_runs": len(plan.generated_runs),
            }, sort_keys=True))
            return 0
        if args.command == "inspect":
            plan = load_plan(args.plan_id)
            print(f"plan_id: {plan.plan_id}")
            print(f"created_at: {plan.created_at}")
            print(f"tasks: {len(plan.tasks)}")
            print(f"modes: {len(plan.modes)}")
            print(f"generated_runs: {len(plan.generated_runs)}")
            for task in plan.tasks:
                print(f"- {task.task_id}: {task.title} [{task.task_type}]")
            return 0
        if args.command == "export":
            print(export_plan(load_plan(args.plan_id), args.format), end="")
            return 0
        if args.command == "validate":
            plan = load_plan(args.plan_id)
            errors = validate_plan(plan)
            if errors:
                for error in errors:
                    print(f"error: {error}", file=sys.stderr)
                return 1
            print(f"valid {plan.plan_id}")
            return 0
    except (ValueError, MatrixError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
