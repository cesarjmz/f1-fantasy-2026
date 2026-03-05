from __future__ import annotations

import hashlib
import random

from app.schemas.domain import Asset, DistributionSummary
from app.services.seed_data import get_round


def _base_points(asset_id: int, round_number: int) -> float:
    if asset_id >= 100:
        base = max(20.0, 56.0 - (asset_id - 100) * 4)
    else:
        base = max(8.0, 44.0 - asset_id * 2.5)

    sprint_boost = 1.10 if get_round(round_number).is_sprint else 1.0
    return base * sprint_boost


def _deterministic_rng(asset_id: int, round_number: int, n_sims: int) -> random.Random:
    seed_bytes = f"{asset_id}:{round_number}:{n_sims}".encode("utf-8")
    seed = int(hashlib.sha256(seed_bytes).hexdigest()[:16], 16)
    return random.Random(seed)


def monte_carlo_projection(
    asset_id: int,
    round_number: int,
    n_sims: int,
) -> DistributionSummary:
    n = max(1, n_sims)
    mean_target = _base_points(asset_id=asset_id, round_number=round_number)
    stdev = max(3.5, mean_target * 0.24)

    rng = _deterministic_rng(asset_id=asset_id, round_number=round_number, n_sims=n)
    samples: list[float] = []
    negatives = 0
    for _ in range(n):
        value = max(-20.0, rng.gauss(mean_target, stdev))
        if value < 0:
            negatives += 1
        samples.append(value)

    samples.sort()
    idx_p10 = int((n - 1) * 0.10)
    idx_p90 = int((n - 1) * 0.90)
    idx_med = (n - 1) // 2

    return DistributionSummary(
        mean=round(sum(samples) / n, 2),
        median=round(samples[idx_med], 2),
        p10=round(samples[idx_p10], 2),
        p90=round(samples[idx_p90], 2),
        prob_negative=round(negatives / n, 3),
    )


def project_asset_points_map(
    assets: list[Asset],
    round_number: int,
    n_sims: int,
) -> dict[int, DistributionSummary]:
    return {
        asset.id: monte_carlo_projection(
            asset_id=asset.id,
            round_number=round_number,
            n_sims=n_sims,
        )
        for asset in assets
    }
