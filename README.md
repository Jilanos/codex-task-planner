# codex-task-planner

Turn one coding request into structured plan files and harness-ready task files, locally and deterministically.

## Problem

Running a coding agent on a large request works better when the request is split into small tasks and run across several models and reasoning efforts. This tool does the planning step only, for people who build or benchmark an execution harness. It does not run Codex, call an LLM, use a database, or depend on another project. It writes JSON and JSONL files that a harness reads later.

## Features

- Reads a plain-text coding request and a matrix of models and reasoning efforts.
- Writes a durable plan folder under `.codex-task-planner/plans/`.
- Splits the request into small tasks by keyword and pattern detection, with context, dependencies, acceptance criteria and checks.
- Replicates every task across every model and reasoning effort combination.
- Writes one harness task JSON file per generated run.
- Adds a deterministic `features` vector to every task, for similarity matching and model routing.
- Inspects, exports (JSONL) and validates stored plans.

It does not execute tasks, score results, or manage remote workspaces.

## Quick start

Python 3.10 or later, standard library only.

```bash
python -m venv .venv
.venv/bin/pip install -e .
.venv/bin/codex-task-planner create --request-file examples/requests/simple_request.md --matrix examples/matrices/default.json
```

The command prints the plan id and the number of tasks, modes and runs. Then use that id:

```bash
codex-task-planner inspect --plan-id PLAN-YYYYMMDD-HHMMSS-abc123
codex-task-planner export --plan-id PLAN-YYYYMMDD-HHMMSS-abc123 --format jsonl
codex-task-planner validate --plan-id PLAN-YYYYMMDD-HHMMSS-abc123
```

Run the tests:

```bash
python -m unittest
```

The tests use no network calls.

## Tech stack

Python (standard library only), `src/` layout, setuptools, unittest, GitHub Actions for the test run.

## Status

Version 0.2.0. See `CHANGELOG.md`. Decomposition is keyword based: it cannot understand project-specific architecture or hidden constraints. The generated tasks are starting points for a later harness, not finished project plans.

Planned: richer decomposition, optional LLM-based decomposition, integration with a Codex execution harness, a supervisor that runs all combinations, a scoring database, and a router that picks the cheapest sufficient mode.

## Request File Format

A request file is plain text. It should describe the desired coding outcome and can include constraints, testing expectations, documentation requirements, or implementation hints.

Example:

```text
Build a small CLI that validates JSON config files and reports clear errors.

The CLI should accept a file path, parse JSON, validate required keys, print readable error messages, and return nonzero exit codes on failure.

Add tests and documentation.
```

## Matrix File Format

The matrix is JSON:

```json
{
  "models": ["gpt-5.3-codex", "gpt-5.4", "gpt-5.5"],
  "reasoning_efforts": ["low", "medium", "high"],
  "default_checks": ["python -m compileall src tests", "python -m unittest"],
  "workspace_root": ".codex-task-planner/generated_workspaces",
  "output_root": ".codex-task-planner/generated_artifacts",
  "timeout_seconds": 600
}
```

Every task is replicated across the Cartesian product of `models` and `reasoning_efforts`.

## Generated Plan Format

Each plan is written to:

```text
.codex-task-planner/plans/PLAN-YYYYMMDD-HHMMSS-abc123/
```

The folder contains:

```text
plan.json
tasks.jsonl
matrix.json
generated_runs.jsonl
harness_tasks/
```

`plan.json` contains the full normalized plan:

- `plan_id`
- `created_at`
- `request`
- `global_context`
- `tasks`
- `modes`
- `generated_runs`

## Generated Harness Task Format

Each generated harness task is JSON:

```json
{
  "task_id": "TASK-001__gpt-5.3-codex_low",
  "prompt": "Global context:\n...\n\nTask:\n...",
  "model": "gpt-5.3-codex",
  "reasoning_effort": "low",
  "workspace": ".codex-task-planner/generated_workspaces/TASK-001__gpt-5.3-codex_low",
  "checks": ["python -m compileall src tests", "python -m unittest"],
  "output_root": ".codex-task-planner/generated_artifacts",
  "timeout_seconds": 600
}
```

The `prompt` includes global context, task instructions, local context, acceptance criteria, and verification commands.

## Deterministic Decomposition

The planner uses keyword and pattern detection. It always creates at least one implementation task and one final verification task.

Detected request components include:

- CLI
- configuration
- validation
- error handling
- tests
- documentation and README
- packaging
- persistence and database work
- API work
- refactor work
- migration
- logging
- benchmark
- export and import
- authentication
- security
- performance

The current planner intentionally favors predictable output over deep semantic understanding.

## Task Feature Extraction

Every generated task includes a `features` dictionary in `tasks.jsonl` and in each harness task file. The feature vector is deterministic and designed for downstream similarity matching and model routing.

Fields:

| Field | Type | Description |
| --- | --- | --- |
| `task_type` | string | `implementation`, `test`, `documentation`, `packaging`, `verification`, `refactor` |
| `domains` | list[string] | Sorted list of detected domains: `cli`, `validation`, `error_handling`, `tests`, `documentation`, `packaging`, `persistence`, `api`, `auth`, `security`, `refactor`, `migration`, `logging`, `benchmark`, `export`, `performance`, `configuration`, `concurrency` |
| `has_*` | bool | One boolean flag per domain for fast vector distance computation |
| `has_io` | bool | True when `cli` or `api` domain is active |
| `has_state` | bool | True when `persistence` domain is active |
| `complexity_estimate` | string | `low`, `medium`, or `high` based on domain count and dependency count |
| `domain_count` | int | Number of active domains |
| `dependency_count` | int | Number of upstream task dependencies |
| `acceptance_criteria_count` | int | Number of acceptance criteria items |
| `check_count` | int | Number of configured check commands |
| `prompt_word_count` | int | Word count of the task prompt |

The feature vector is used by `codex-task-supervisor recommend` to find the most similar historical tasks and select the model that performed best on them.

## Execution Harness Integration

An external harness can read `generated_runs.jsonl`, then load each referenced `task_file`. Each task file contains the model, reasoning effort, workspace, checks, timeout, output root, and a complete prompt.

The harness is responsible for execution, workspace preparation, Codex invocation, result collection, scoring, retries, and cleanup.

## Validation

Validation checks for:

- duplicate task IDs
- duplicate mode IDs
- invalid task dependencies
- missing generated task files
- invalid generated task file shape
- missing stored `plan.json`

Input loading also reports missing request files, empty requests, invalid matrix files, empty model lists, and empty reasoning effort lists.
