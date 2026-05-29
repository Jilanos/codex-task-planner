"""Deterministic feature extraction for task characterization and similarity matching."""

from __future__ import annotations

import re
from typing import Any


_DOMAIN_PATTERNS: dict[str, re.Pattern[str]] = {
    "cli":            re.compile(r"\b(cli|command.?line|entrypoint|argparse|argument)\b", re.I),
    "validation":     re.compile(r"\b(validat\w*|schema|required keys?|constraint)\b", re.I),
    "error_handling": re.compile(r"\b(error\w*|failure\w*|exception|nonzero|non.zero|traceback)\b", re.I),
    "tests":          re.compile(r"\b(tests?|unittest|pytest|coverage|assert)\b", re.I),
    "documentation":  re.compile(r"\b(docs?|documentation|readme|docstring)\b", re.I),
    "packaging":      re.compile(r"\b(packaging|pyproject|setup\.py|install\w*|entry.?point)\b", re.I),
    "persistence":    re.compile(r"\b(database|sqlite|persist\w*|storage|db|dao)\b", re.I),
    "api":            re.compile(r"\b(api|endpoint|route|http|rest|fastapi|flask)\b", re.I),
    "auth":           re.compile(r"\b(auth\w*|login|oauth|token|jwt|session)\b", re.I),
    "security":       re.compile(r"\b(security|secure|secret\w*|vulnerabilit\w*|encrypt)\b", re.I),
    "refactor":       re.compile(r"\b(refactor|cleanup|restructure|reorganize)\b", re.I),
    "migration":      re.compile(r"\b(migrat\w*|upgrade|schema change)\b", re.I),
    "logging":        re.compile(r"\b(logging|log\w*|logger|tracing)\b", re.I),
    "benchmark":      re.compile(r"\b(benchmark\w*|perf test|performance test)\b", re.I),
    "export":         re.compile(r"\b(export\w*|import\w*|serializ\w*|csv|jsonl?)\b", re.I),
    "performance":    re.compile(r"\b(performance|optimi[sz]\w*|latency|throughput|fast)\b", re.I),
    "configuration":  re.compile(r"\b(config\w*|settings?|environment|env var)\b", re.I),
    "concurrency":    re.compile(r"\b(async|await|concurrent|parallel|thread|worker)\b", re.I),
}

_COMPLEXITY_HIGH_TYPES = {"refactor", "migration"}
_COMPLEXITY_MEDIUM_TYPES = {"test", "verification"}


def extract_task_features(
    spec: dict[str, Any],
    request: str,
    dependency_count: int,
) -> dict[str, Any]:
    """Return a deterministic feature vector for a task spec.

    The vector is designed to support cosine or Jaccard similarity
    against a corpus of evaluated tasks for model routing.
    """
    task_type: str = spec.get("task_type", "implementation")
    prompt: str = spec.get("prompt", "")
    acceptance_criteria: list[str] = spec.get("acceptance_criteria", [])
    checks: list[str] = spec.get("checks", [])

    # Detect domains from the task prompt + global request
    combined_text = f"{request} {prompt}"
    active_domains = [
        domain for domain, pattern in _DOMAIN_PATTERNS.items()
        if pattern.search(combined_text)
    ]

    # Convenience booleans for the most routing-relevant dimensions
    domain_set = set(active_domains)
    has_io = "cli" in domain_set or "api" in domain_set
    has_state = "persistence" in domain_set

    complexity = _estimate_complexity(task_type, domain_set, dependency_count)

    return {
        "task_type": task_type,
        "domains": sorted(active_domains),
        # Per-domain flags kept flat for easy vector distance computation
        "has_cli": "cli" in domain_set,
        "has_validation": "validation" in domain_set,
        "has_error_handling": "error_handling" in domain_set,
        "has_tests": "tests" in domain_set,
        "has_docs": "documentation" in domain_set,
        "has_packaging": "packaging" in domain_set,
        "has_persistence": "persistence" in domain_set,
        "has_api": "api" in domain_set,
        "has_auth": "auth" in domain_set,
        "has_security": "security" in domain_set,
        "has_refactor": "refactor" in domain_set,
        "has_migration": "migration" in domain_set,
        "has_logging": "logging" in domain_set,
        "has_benchmark": "benchmark" in domain_set,
        "has_export": "export" in domain_set,
        "has_performance": "performance" in domain_set,
        "has_configuration": "configuration" in domain_set,
        "has_concurrency": "concurrency" in domain_set,
        # Derived semantic flags
        "has_io": has_io,
        "has_state": has_state,
        # Scalar metrics
        "complexity_estimate": complexity,
        "domain_count": len(active_domains),
        "dependency_count": dependency_count,
        "acceptance_criteria_count": len(acceptance_criteria),
        "check_count": len(checks),
        "prompt_word_count": len(prompt.split()),
    }


def _estimate_complexity(task_type: str, domains: set[str], dependency_count: int) -> str:
    if task_type in _COMPLEXITY_HIGH_TYPES:
        return "high"
    domain_count = len(domains)
    if domain_count >= 5 or dependency_count >= 3:
        return "high"
    if domain_count >= 3 or dependency_count >= 1 or task_type in _COMPLEXITY_MEDIUM_TYPES:
        return "medium"
    return "low"
