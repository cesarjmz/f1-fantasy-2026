from __future__ import annotations

from app.core.config import settings
from app.schemas.domain import ChipName
from app.services.seed_data import get_asset

ROUND2_CHIPS = {"limitless", "wildcard"}


def calculate_budget_used(driver_ids: list[int], constructor_ids: list[int]) -> float:
    ids = driver_ids + constructor_ids
    return round(sum(get_asset(asset_id).price_millions for asset_id in ids), 2)


def validate_roster(
    driver_ids: list[int], constructor_ids: list[int], budget_millions: float
) -> tuple[bool, str]:
    if len(driver_ids) != 5:
        return False, "Exactly 5 drivers are required"
    if len(constructor_ids) != 2:
        return False, "Exactly 2 constructors are required"
    if len(set(driver_ids)) != 5 or len(set(constructor_ids)) != 2:
        return False, "Duplicate assets are not allowed"

    used = calculate_budget_used(driver_ids, constructor_ids)
    if used > budget_millions:
        return False, f"Budget exceeded: {used} > {budget_millions}"
    return True, "ok"


def net_transfer_count(
    previous_drivers: list[int],
    previous_constructors: list[int],
    final_drivers: list[int],
    final_constructors: list[int],
) -> tuple[int, list[int], list[int]]:
    previous = set(previous_drivers + previous_constructors)
    final = set(final_drivers + final_constructors)

    out_assets = sorted(list(previous - final))
    in_assets = sorted(list(final - previous))
    transfer_count = len(in_assets)
    return transfer_count, out_assets, in_assets


def transfer_penalty(transfer_count: int) -> int:
    extras = max(0, transfer_count - settings.free_transfers_per_round)
    return extras * settings.transfer_penalty_points


def validate_chip_usage(
    chip: ChipName | None,
    used_chips: list[ChipName],
    round_number: int,
) -> tuple[bool, str]:
    if chip is None:
        return True, "ok"

    if chip in used_chips:
        return False, f"Chip '{chip}' already used this season"

    if chip in ROUND2_CHIPS and round_number < 2:
        return False, f"Chip '{chip}' unlocks from round 2"

    return True, "ok"


def apply_chip_multiplier(
    base_points: float, is_primary_boost: bool, chip: ChipName | None
) -> float:
    if is_primary_boost:
        if chip == "triple_boost":
            return base_points * 3
        return base_points * 2
    return base_points


def apply_no_negative(points: float, chip: ChipName | None) -> float:
    if chip == "no_negative":
        return max(0.0, points)
    return points
