# Changelog

## 0.2.0

### Added

- `features.py`: deterministic feature extraction for every generated task.
  Each task now carries a `features` dict with 18 domain flags, boolean
  convenience fields (`has_io`, `has_state`), a `complexity_estimate`, and
  scalar metrics (`domain_count`, `dependency_count`, `prompt_word_count`, …).
- `features` field on the `Task` dataclass (backward-compatible default).
- `features` written to `tasks.jsonl` and to every harness task file so
  downstream tools can use them without re-reading the plan.
- `py.typed` marker for downstream type-checking support.
- `LICENSE` (MIT).

### Changed

- Removed `authors` field from `pyproject.toml`.
- Added `classifiers` and `keywords` to `pyproject.toml`.

## 0.1.0

Initial release. Deterministic keyword-based request decomposition, matrix
replication across model and reasoning-effort combinations, harness task file
generation, plan validation, and export.
