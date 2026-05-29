# codex-task-planner

`codex-task-planner` is a local, deterministic task planning tool for turning one high-level coding request into structured planning files and harness-ready task files.

It exists to separate planning from execution. The project does not run Codex, does not call an LLM, does not use a database, and does not depend on any existing project. It only writes JSON and JSONL artifacts that another execution harness can consume later.

## What It Does

- Reads a plain-text coding request.
- Reads an execution matrix of models and reasoning efforts.
- Builds a durable plan folder under `.codex-task-planner/plans/`.
- Decomposes the request into small deterministic subtasks.
- Adds global context, local context, dependencies, acceptance criteria, and checks.
- Replicates every task across every model and reasoning effort combination.
- Writes one harness-compatible JSON task file per generated run.

## What It Does Not Do

- It does not execute Codex.
- It does not call OpenAI, Anthropic, or any other LLM provider.
- It does not run generated tasks.
- It does not score results.
- It does not manage remote workspaces.

## Installation

```bash
pip install -e .
```

The project uses a `src/` layout and the Python standard library only.

## CLI Usage

Create a plan:

```bash
codex-task-planner create --request-file examples/requests/simple_request.md --matrix examples/matrices/default.json
```

Inspect a plan:

```bash
codex-task-planner inspect --plan-id PLAN-YYYYMMDD-HHMMSS-abc123
```

Export generated runs:

```bash
codex-task-planner export --plan-id PLAN-YYYYMMDD-HHMMSS-abc123 --format jsonl
```

Validate stored artifacts:

```bash
codex-task-planner validate --plan-id PLAN-YYYYMMDD-HHMMSS-abc123
```

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

Version 0.1 uses keyword and pattern detection. It always creates at least one implementation task and one final verification task.

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

## Tests

Run:

```bash
python -m unittest
```

The test suite uses no network calls.

## Limitations

Deterministic decomposition cannot fully understand project-specific architecture, hidden constraints, or nuanced sequencing. The generated tasks are designed to be practical starting points for a later execution harness, not perfect project plans.

## Future Roadmap

- v0.2: richer deterministic decomposition
- v0.3: optional LLM-based decomposition
- v0.4: integration with a Codex execution harness
- v0.5: supervisor that runs all task and mode combinations
- v0.6: scoring and cost efficiency database
- v0.7: intelligent router that selects the cheapest sufficient execution mode
