from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PointsModelConfig:
    prior_rate_per_minute: float = 0.65
    prior_minutes: float = 12.0
    max_poisson_terms: int = 250


def _poisson_tail_prob(lam: float, k: int, max_terms: int) -> float:
    if k <= 0:
        return 1.0
    if lam <= 0:
        return 0.0
    terms = min(k, max_terms)
    cumulative = 0.0
    for i in range(terms):
        cumulative += math.exp(-lam) * (lam ** i) / math.factorial(i)
    if k > max_terms:
        mean = lam
        variance = lam
        if variance <= 0:
            return 0.0
        z = (k - 0.5 - mean) / math.sqrt(variance)
        return max(0.0, min(1.0, 1.0 - _normal_cdf(z)))
    return max(0.0, min(1.0, 1.0 - cumulative))


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2)))


def estimate_break_probabilities(
    current_points: float,
    minutes_played: float,
    remaining_minutes: float,
    season_high: float,
    all_time_high: float,
    config: PointsModelConfig | None = None,
) -> dict[str, float]:
    if config is None:
        config = PointsModelConfig()
    if minutes_played <= 0 or remaining_minutes <= 0:
        return {"season_high": 0.0, "all_time": 0.0}

    prior_alpha = config.prior_rate_per_minute * config.prior_minutes
    prior_beta = config.prior_minutes
    posterior_alpha = prior_alpha + max(0.0, current_points)
    posterior_beta = prior_beta + minutes_played
    rate_per_minute = posterior_alpha / posterior_beta
    lam = rate_per_minute * remaining_minutes

    season_needed = max(0, math.ceil(season_high - current_points))
    all_time_needed = max(0, math.ceil(all_time_high - current_points))

    season_prob = _poisson_tail_prob(lam, season_needed, config.max_poisson_terms)
    all_time_prob = _poisson_tail_prob(lam, all_time_needed, config.max_poisson_terms)

    return {
        "season_high": season_prob,
        "all_time": all_time_prob,
    }
