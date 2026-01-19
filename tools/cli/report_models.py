"""Data models and aggregation logic for benchmark reports."""

from __future__ import annotations

import json
import re
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

    # Field-level statistics
    field_matches: dict[str, int] = field(default_factory=dict)
    field_totals: dict[str, int] = field(default_factory=dict)

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
        self.samples.append(sample)

        # Track field-level accuracy
        comparison = sample.get("comparison", {})
        field_matches = comparison.get("field_matches", {})
        for field_name, is_match in field_matches.items():
            self.field_totals[field_name] = self.field_totals.get(field_name, 0) + 1
            if is_match:
                self.field_matches[field_name] = self.field_matches.get(field_name, 0) + 1

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
        """Overall field-level accuracy (matched fields / total fields)."""
        total_matches = sum(self.field_matches.values())
        total_fields = sum(self.field_totals.values())
        return total_matches / total_fields if total_fields else 0.0

    def get_field_accuracy(self, field_name: str) -> float:
        """Get accuracy for a specific field."""
        total = self.field_totals.get(field_name, 0)
        matches = self.field_matches.get(field_name, 0)
        return matches / total if total else 0.0


@dataclass
class MetalAccuracy:
    """Accuracy statistics per metal type."""

    metal: str
    total_images: int = 0
    total_matches: int = 0  # Sum of matched fields
    total_fields: int = 0  # Sum of expected fields
    full_passes: int = 0  # Images with all fields correct

    @property
    def field_accuracy(self) -> float:
        """Percentage of individual fields correctly matched."""
        return self.total_matches / self.total_fields if self.total_fields else 0.0

    @property
    def full_pass_rate(self) -> float:
        """Percentage of images with 100% field accuracy."""
        return self.full_passes / self.total_images if self.total_images else 0.0


@dataclass
class StrategyMetalStats:
    """Statistics for a specific strategy on a specific metal type."""

    strategy_name: str
    metal: str
    total_images: int = 0
    total_matches: int = 0
    total_fields: int = 0
    total_time: float = 0.0
    full_passes: int = 0

    @property
    def field_accuracy(self) -> float:
        """Field-level accuracy for this strategy on this metal."""
        return self.total_matches / self.total_fields if self.total_fields else 0.0

    @property
    def avg_time(self) -> float:
        """Average processing time for this strategy on this metal."""
        return self.total_time / self.total_images if self.total_images else 0.0

    @property
    def full_pass_rate(self) -> float:
        """Percentage of images with all fields correct."""
        return self.full_passes / self.total_images if self.total_images else 0.0


@dataclass
class HybridPotential:
    """Data for evaluating hybrid strategy potential between two models."""

    strategy_a: str
    strategy_b: str
    combined_accuracy: float = 0.0  # Best of both per field
    individual_a_accuracy: float = 0.0
    individual_b_accuracy: float = 0.0
    field_complementarity: dict[str, str] = field(default_factory=dict)  # field -> better strategy
    avg_time_combined: float = 0.0  # Estimated time if using both


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


def extract_metal_from_filename(filename: str) -> str | None:
    """Extract metal type from filename.

    Args:
        filename: Image filename (e.g., 'Gold_01000g_9999_AB123_CS.jpg')

    Returns:
        Metal type or None if not parseable
    """
    # Pattern: Metal_Weight_Fineness_Serial_Producer.ext
    match = re.match(r"^([A-Za-z]+)_\d+[a-z]+_", filename)
    if match:
        metal = match.group(1).lower()
        metal_map = {
            "gold": "Gold",
            "au": "Gold",
            "silver": "Silver",
            "ag": "Silver",
            "platinum": "Platinum",
            "pt": "Platinum",
            "palladium": "Palladium",
            "pd": "Palladium",
        }
        return metal_map.get(metal, metal.capitalize())
    return None


def aggregate_by_metal(
    payload: list[dict[str, Any]],
    strategy_name: str | None = None,
) -> dict[str, MetalAccuracy]:
    """Aggregate accuracy statistics by metal type.

    Args:
        payload: List of benchmark test results
        strategy_name: Optional filter for specific strategy (None = all strategies combined)

    Returns:
        Dictionary mapping metal names to their accuracy statistics
    """
    aggregates: dict[str, MetalAccuracy] = {}

    for entry in payload:
        filename = Path(entry.get("image", "")).name
        metal = extract_metal_from_filename(filename)

        if not metal:
            continue

        # Initialize metal aggregate if needed
        if metal not in aggregates:
            aggregates[metal] = MetalAccuracy(metal=metal)

        agg = aggregates[metal]
        agg.total_images += 1

        # Count matches across strategies (or specific strategy)
        strategies_to_check = entry.get("results", {})
        if strategy_name:
            strategies_to_check = {
                k: v for k, v in strategies_to_check.items() if k == strategy_name
            }

        for _strat_name, result in strategies_to_check.items():
            comparison = result.get("comparison")
            if comparison:
                matched = comparison.get("matched_fields", 0)
                total = comparison.get("total_expected_fields", 0)
                is_pass = comparison.get("pass", False)

                agg.total_matches += matched
                agg.total_fields += total
                if is_pass:
                    agg.full_passes += 1

    return aggregates


def aggregate_strategy_by_metal(
    payload: list[dict[str, Any]],
) -> dict[str, dict[str, StrategyMetalStats]]:
    """Aggregate statistics per strategy per metal type.

    Returns:
        Nested dict: {strategy_name: {metal: StrategyMetalStats}}
    """
    aggregates: dict[str, dict[str, StrategyMetalStats]] = {}

    for entry in payload:
        filename = Path(entry.get("image", "")).name
        metal = extract_metal_from_filename(filename)

        if not metal:
            continue

        for strategy_name, result in entry.get("results", {}).items():
            # Initialize nested structure
            if strategy_name not in aggregates:
                aggregates[strategy_name] = {}
            if metal not in aggregates[strategy_name]:
                aggregates[strategy_name][metal] = StrategyMetalStats(
                    strategy_name=strategy_name, metal=metal
                )

            stats = aggregates[strategy_name][metal]
            stats.total_images += 1
            stats.total_time += float(result.get("processing_time") or 0.0)

            comparison = result.get("comparison")
            if comparison:
                stats.total_matches += comparison.get("matched_fields", 0)
                stats.total_fields += comparison.get("total_expected_fields", 0)
                if comparison.get("pass", False):
                    stats.full_passes += 1

    return aggregates


def calculate_hybrid_potential(
    payload: list[dict[str, Any]],
    strategy_aggregates: dict[str, StrategyAggregate],
) -> list[HybridPotential]:
    """Calculate potential benefits of combining strategies.

    For each pair of strategies, calculate what accuracy could be achieved
    if we took the best result for each field from either strategy.

    Returns:
        List of HybridPotential sorted by combined accuracy (descending)
    """
    from itertools import combinations

    strategy_names = list(strategy_aggregates.keys())
    if len(strategy_names) < 2:
        return []

    results = []
    fields = ["SerialNumber", "Metal", "Weight", "WeightUnit", "Fineness", "Producer"]

    for strat_a, strat_b in combinations(strategy_names, 2):
        agg_a = strategy_aggregates[strat_a]
        agg_b = strategy_aggregates[strat_b]

        # Calculate combined accuracy (best of each field)
        combined_matches = 0
        total_fields_count = 0
        field_winner = {}

        for fld in fields:
            acc_a = agg_a.get_field_accuracy(fld)
            acc_b = agg_b.get_field_accuracy(fld)

            # Take the better accuracy
            best_acc = max(acc_a, acc_b)
            total_a = agg_a.field_totals.get(fld, 0)
            total_b = agg_b.field_totals.get(fld, 0)
            total = max(total_a, total_b)

            if total > 0:
                combined_matches += best_acc * total
                total_fields_count += total

                if acc_a >= acc_b:
                    field_winner[fld] = strat_a
                else:
                    field_winner[fld] = strat_b

        combined_accuracy = combined_matches / total_fields_count if total_fields_count else 0.0

        hybrid = HybridPotential(
            strategy_a=strat_a,
            strategy_b=strat_b,
            combined_accuracy=combined_accuracy,
            individual_a_accuracy=agg_a.field_accuracy,
            individual_b_accuracy=agg_b.field_accuracy,
            field_complementarity=field_winner,
            avg_time_combined=agg_a.avg_time + agg_b.avg_time,  # Worst case: run both
        )
        results.append(hybrid)

    # Sort by combined accuracy descending
    results.sort(key=lambda x: x.combined_accuracy, reverse=True)
    return results
