from __future__ import annotations

from app.services.ruleset import get_current_ruleset


def _status_key(status: str | None) -> str | None:
    if status is None:
        return None
    normalized = status.strip().lower().replace(" ", "_")
    aliases = {"dnf": "nc", "not_classified": "nc", "disqualified": "dsq"}
    return aliases.get(normalized, normalized)


def points_by_finish(
    table: dict[str, int], finish_position: int | None, status: str | None = None
) -> int:
    key = _status_key(status)
    if key in table:
        return int(table[key])
    if finish_position is None:
        return 0
    return int(table.get(str(finish_position), 0))


def driver_qualifying_points(
    finish_position: int | None, status: str | None = None
) -> int:
    table = get_current_ruleset()["scoring"]["qualifying_driver"]
    return points_by_finish(table, finish_position, status)


def driver_sprint_points(
    finish_position: int | None,
    start_position: int | None,
    overtakes: int,
    fastest_lap: bool,
    driver_of_day: bool,
    status: str | None = None,
) -> tuple[int, dict[str, int]]:
    scoring = get_current_ruleset()["scoring"]
    points = points_by_finish(scoring["sprint_driver"], finish_position, status)
    breakdown = {"finish": points}

    if status is None:
        delta = 0
        if start_position and finish_position:
            delta = start_position - finish_position
        breakdown["position_delta"] = delta * scoring["event_bonuses"]["position_gain"]
        breakdown["overtakes"] = overtakes * scoring["event_bonuses"]["overtake"]
        breakdown["fastest_lap"] = (
            scoring["event_bonuses"]["fastest_lap"] if fastest_lap else 0
        )
        breakdown["driver_of_day"] = (
            scoring["event_bonuses"]["driver_of_day"] if driver_of_day else 0
        )
    else:
        breakdown["position_delta"] = 0
        breakdown["overtakes"] = 0
        breakdown["fastest_lap"] = 0
        breakdown["driver_of_day"] = 0

    total = sum(breakdown.values())
    return total, breakdown


def driver_race_points(
    finish_position: int | None,
    start_position: int | None,
    overtakes: int,
    fastest_lap: bool,
    driver_of_day: bool,
    status: str | None = None,
) -> tuple[int, dict[str, int]]:
    scoring = get_current_ruleset()["scoring"]
    points = points_by_finish(scoring["race_driver"], finish_position, status)
    breakdown = {"finish": points}

    if status is None:
        delta = 0
        if start_position and finish_position:
            delta = start_position - finish_position
        breakdown["position_delta"] = delta * scoring["event_bonuses"]["position_gain"]
        breakdown["overtakes"] = overtakes * scoring["event_bonuses"]["overtake"]
        breakdown["fastest_lap"] = (
            scoring["event_bonuses"]["fastest_lap"] if fastest_lap else 0
        )
        breakdown["driver_of_day"] = (
            scoring["event_bonuses"]["driver_of_day"] if driver_of_day else 0
        )
    else:
        breakdown["position_delta"] = 0
        breakdown["overtakes"] = 0
        breakdown["fastest_lap"] = 0
        breakdown["driver_of_day"] = 0

    total = sum(breakdown.values())
    return total, breakdown


def constructor_qualifying_points(
    driver_points: tuple[int, int],
    q2_count: int,
    q3_count: int,
    disqualified_drivers: int = 0,
) -> int:
    scoring = get_current_ruleset()["scoring"]
    total = sum(driver_points)
    progression = scoring["progression_bonus"]

    if q3_count == 2:
        total += progression["both_q3"]
    elif q3_count == 1:
        total += progression["one_q3"]
    elif q2_count == 2:
        total += progression["both_q2"]
    elif q2_count == 1:
        total += progression["one_q2"]
    else:
        total += progression["none_q2"]

    total += (
        disqualified_drivers
        * get_current_ruleset()["scoring"]["qualifying_driver"]["dsq"]
    )
    return total


def pit_stop_band_points(fastest_stop_seconds: float) -> int:
    bands = get_current_ruleset()["scoring"]["pit_stop_bands"]
    for band in bands:
        min_v = band.get("min", float("-inf"))
        max_v = band.get("max", float("inf"))
        if min_v <= fastest_stop_seconds <= max_v:
            return int(band["points"])
    return 0


def constructor_race_points(
    driver_race_points_excluding_dotd: tuple[int, int],
    fastest_stop_seconds: float,
    has_fastest_stop: bool,
    has_world_record_stop: bool,
    disqualified_drivers: int = 0,
) -> int:
    scoring = get_current_ruleset()["scoring"]
    total = sum(driver_race_points_excluding_dotd)
    total += pit_stop_band_points(fastest_stop_seconds)
    if has_fastest_stop:
        total += scoring["pit_stop_fastest_bonus"]
    if has_world_record_stop:
        total += scoring["pit_stop_record_bonus"]
    total += disqualified_drivers * scoring["constructor_dsq_penalty"]
    return total
