"""Data models and aggregation logic for benchmark reports."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class StrategyAggregate:
    """Aggregated statistics for a single strategy across multiple runs."""

    name: str
    runs: int = 0
    successes: int = 0
    total_conf: float = 0.0
    total_time: float = 0.0
    latest_error: str | None = None
    samples: list[dict[str, Any]] = field(default_factory=list)
    # Quality metrics
    tests_with_ground_truth: int = 0
    perfect_matches: int = 0
    total_matched_fields: int = 0
    total_expected_fields: int = 0

    def add_sample(self, sample: dict[str, Any]) -> None:
        """Add a single test result to the aggregate statistics."""
        self.runs += 1
        error = sample.get("error")
        confidence = float(sample.get("confidence") or 0.0)
        processing_time = float(sample.get("processing_time") or 0.0)
        self.total_conf += confidence
        self.total_time += processing_time
        if not error:
            self.successes += 1
        else:
            self.latest_error = error

        # Track quality metrics
        comparison = sample.get("comparison")
        if comparison and isinstance(comparison, dict):
            total_fields = comparison.get("total_expected_fields", 0)
            if total_fields > 0:
                self.tests_with_ground_truth += 1
                matched = comparison.get("matched_fields", 0)
                self.total_matched_fields += matched
                self.total_expected_fields += total_fields
                if comparison.get("pass", False):
                    self.perfect_matches += 1

        self.samples.append(sample)

    @property
    def avg_conf(self) -> float:
        """Average confidence across all runs."""
        return self.total_conf / self.runs if self.runs else 0.0

    @property
    def avg_time(self) -> float:
        """Average processing time across all runs."""
        return self.total_time / self.runs if self.runs else 0.0

    @property
    def success_rate(self) -> float:
        """Success rate (successes/total runs)."""
        return self.successes / self.runs if self.runs else 0.0

    @property
    def field_accuracy(self) -> float:
        """Field-level accuracy (matched fields / total expected fields)."""
        return (
            self.total_matched_fields / self.total_expected_fields
            if self.total_expected_fields
            else 0.0
        )

    @property
    def perfect_match_rate(self) -> float:
        """Perfect match rate (all fields correct)."""
        return (
            self.perfect_matches / self.tests_with_ground_truth
            if self.tests_with_ground_truth
            else 0.0
        )


def load_results(data_path: Path) -> list[dict[str, Any]]:
    """Load benchmark results from JSON file.

    Args:
        data_path: Path to JSON results file

    Returns:
        List of test result dictionaries

    Raises:
        FileNotFoundError: If results file doesn't exist
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Results file not found: {data_path}")
    with data_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def aggregate_by_strategy(payload: list[dict[str, Any]]) -> dict[str, StrategyAggregate]:
    """Aggregate results by strategy name.

    Args:
        payload: List of benchmark test results

    Returns:
        Dictionary mapping strategy names to their aggregated statistics
    """
    aggregates: dict[str, StrategyAggregate] = {}
    for entry in payload:
        for strategy_name, strategy_result in entry["results"].items():
            agg = aggregates.setdefault(strategy_name, StrategyAggregate(strategy_name))
            agg.add_sample(strategy_result)
    return aggregates
