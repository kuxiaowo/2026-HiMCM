"""Shared planning metrics for Questions 1--3; scores are not probabilities.

Compare deployments using the SAME fixed demand vector. None is unknown, and
must never silently become zero. Apply discovery/response at the same spatial
target before aggregating, rather than multiplying two regional averages.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


def _number(value: float, label: str, upper: float | None = None) -> float:
    if value is None or not math.isfinite(value) or value < 0:
        raise ValueError(f"{label} must be a known finite nonnegative value")
    if upper is not None and value > upper:
        raise ValueError(f"{label} must be at most {upper}")
    return float(value)


def target_service_score(discovery: float, response: float) -> float:
    """A two-stage capability index; not an empirically calibrated success rate."""
    return _number(discovery, "discovery", 1) * _number(response, "response", 1)


def aggregate_protection(
    demands: Sequence[float], services: Sequence[float]
) -> dict[str, float | str | None]:
    if len(demands) != len(services):
        raise ValueError("Demand and service records must have matching lengths")
    ds = [_number(v, "demand") for v in demands]
    gs = [_number(v, "service", 1) for v in services]
    total = math.fsum(ds)
    if total == 0:
        return {"status": "not_applicable_no_modeled_demand", "score": None,
                "total_demand": 0.0, "residual_demand": 0.0}
    covered = math.fsum(d * g for d, g in zip(ds, gs))
    return {"status": "complete_for_supplied_scope", "score": 100 * covered / total,
            "total_demand": total, "residual_demand": total - covered}


def compare_fixed_scenario(
    demands: Sequence[float], before: Sequence[float], after: Sequence[float]
) -> dict[str, float | None]:
    baseline = aggregate_protection(demands, before)
    proposed = aggregate_protection(demands, after)
    if baseline["score"] is None:
        return {"score_change": None, "residual_reduction_fraction": None}
    remaining = baseline["residual_demand"]
    return {
        "score_change": proposed["score"] - baseline["score"],
        "residual_reduction_fraction": (
            (remaining - proposed["residual_demand"]) / remaining if remaining else None
        ),
    }


def evaluate_protection_standard(
    demands: Sequence[float | None],
    services: Sequence[float | None],
    *,
    critical_services: Mapping[str, float | None],
    safeguards: Mapping[str, bool | None],
    scope_complete: bool,
    park_target: float = 80,
    critical_target: float = 0.9,
) -> dict:
    """Assess one shift against a declared planning standard.

    Call once per required shift. An average score cannot compensate for a
    failed critical object or a missing priority-habitat safeguard. The caller
    must explicitly declare whether the modeled scope is complete; omission
    of unknown objects must not certify full-park protection. Thresholds are
    team assumptions, not observed probabilities or official standards.
    """
    if len(demands) != len(services):
        raise ValueError("Demand and service records must have matching lengths")
    park_target = _number(park_target, "park_target", 100)
    critical_target = _number(critical_target, "critical_target", 1)
    if type(scope_complete) is not bool:
        raise ValueError("scope_complete must be explicitly True or False")
    unknown, failed = [], []
    for i, (demand, service) in enumerate(zip(demands, services)):
        if demand is None:
            unknown.append(f"demand[{i}]")
        else:
            _number(demand, "demand")
        if service is None:
            unknown.append(f"service[{i}]")
        else:
            _number(service, "service", 1)
    aggregate = None if unknown else aggregate_protection(demands, services)
    score = None if aggregate is None else aggregate["score"]
    if score is None and not unknown:
        unknown.append("no_modeled_demand")
    if score is not None and score + 1e-12 < park_target:
        failed.append("park_score_below_target")
    if not critical_services:
        unknown.append("critical_object_registry_missing")
    for name, service in critical_services.items():
        if service is None:
            unknown.append(f"critical:{name}")
        elif _number(service, "critical_service", 1) + 1e-12 < critical_target:
            failed.append(f"critical:{name}")
    if not safeguards:
        unknown.append("safeguard_registry_missing")
    for name, met in safeguards.items():
        if met is None:
            unknown.append(f"safeguard:{name}")
        elif type(met) is not bool:
            raise ValueError("Safeguards must be True, False, or None")
        elif not met:
            failed.append(f"safeguard:{name}")
    if not scope_complete:
        unknown.append("modeled_scope_incomplete")
    status = "below_standard" if failed else (
        "data_incomplete" if unknown else "meets_planning_standard"
    )
    return {"status": status, "score_for_supplied_demand_scope": score,
            "park_target": park_target, "critical_target": critical_target,
            "failed_conditions": failed, "unknown_fields": unknown,
            "is_empirical_success_probability": False}


def check_metric_semantics() -> dict[str, bool]:
    """Small semantic checks of consequential model behavior, not data calibration."""
    no_response = target_service_score(1, 0) == 0
    unmodeled_is_na = aggregate_protection([0], [1])["score"] is None
    unknown_rejected = False
    try:
        aggregate_protection([None], [1])
    except ValueError:
        unknown_rejected = True
    fixed_comparison = compare_fixed_scenario([3, 1], [.2, .2], [.6, .2])
    fixed_scale = math.isclose(fixed_comparison["score_change"], 30)
    weighted = math.isclose(aggregate_protection([9, 1], [1, 0])["score"], 90)
    # Equal regional discovery and response averages can hide disjoint coverage.
    pointwise = aggregate_protection([1, 1], [target_service_score(1, 0),
                                              target_service_score(0, 1)])
    aligned_coverage_required = pointwise["score"] == 0
    standard_input = dict(demands=[9, 1], services=[8.05 / 9, .95],
                          critical_services={"rhino": .95},
                          safeguards={"priority_habitat": True, "pan_monitoring": True},
                          scope_complete=True)
    valid_standard = evaluate_protection_standard(**standard_input)
    failed_critical = evaluate_protection_standard(
        **dict(standard_input, services=[8.3 / 9, .7], critical_services={"rhino": .7}))
    incomplete_standard = evaluate_protection_standard(
        **dict(standard_input, safeguards={"priority_habitat": None, "pan_monitoring": True}))
    incomplete_scope = evaluate_protection_standard(
        **dict(standard_input, scope_complete=False))
    missing_demand = evaluate_protection_standard(
        **dict(standard_input, demands=[9, None]))
    checks = {"monitoring_without_response_is_not_effective_protection": no_response,
              "zero_demand_is_not_automatic_100_points": unmodeled_is_na,
              "unknown_demand_is_not_silently_zero": unknown_rejected,
              "same_scale_used_for_deployment_comparison": fixed_scale,
              "demand_weighted_aggregation": weighted,
              "discovery_and_response_must_cover_same_targets": aligned_coverage_required,
              "complete_scope_with_all_floors_can_pass": valid_standard["status"] == "meets_planning_standard",
              "high_park_score_cannot_hide_critical_failure": failed_critical["status"] == "below_standard",
              "unknown_safeguard_cannot_certify_protection": incomplete_standard["status"] == "data_incomplete",
              "partial_scope_cannot_certify_full_park": incomplete_scope["status"] == "data_incomplete",
              "unknown_demand_cannot_generate_full_score": missing_demand["status"] == "data_incomplete" and missing_demand["score_for_supplied_demand_scope"] is None}
    if not all(checks.values()):
        raise AssertionError(checks)
    return checks
