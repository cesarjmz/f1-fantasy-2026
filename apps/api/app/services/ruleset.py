from __future__ import annotations

from datetime import datetime, timezone

RULESET = {
    "season": 2026,
    "hash": "2026-rules-v1",
    "effective_from": datetime(2026, 1, 1, tzinfo=timezone.utc),
    "roster": {"drivers": 5, "constructors": 2, "budget_millions": 100.0},
    "transfers": {"free_per_round": 2, "penalty_per_extra": 10, "net_transfers": True},
    "chips": {
        "once_per_season": True,
        "one_per_week": True,
        "round_2_unlock": ["limitless", "wildcard"],
    },
    "scoring": {
        "qualifying_driver": {
            **{str(i): 11 - i for i in range(1, 11)},
            "nc": -5,
            "dsq": -5,
            "no_time": -5,
        },
        "sprint_driver": {
            **{str(i): 9 - i for i in range(1, 9)},
            "nc": -10,
            "dsq": -10,
            "no_time": -10,
        },
        "race_driver": {
            "1": 25,
            "2": 18,
            "3": 15,
            "4": 12,
            "5": 10,
            "6": 8,
            "7": 6,
            "8": 4,
            "9": 2,
            "10": 1,
            "nc": -20,
            "dsq": -20,
            "no_time": -20,
        },
        "progression_bonus": {
            "none_q2": -1,
            "one_q2": 1,
            "both_q2": 3,
            "one_q3": 5,
            "both_q3": 10,
        },
        "event_bonuses": {
            "position_gain": 1,
            "position_loss": -1,
            "overtake": 1,
            "fastest_lap": 10,
            "driver_of_day": 10,
        },
        "pit_stop_bands": [
            {"max": 1.99, "points": 20},
            {"min": 2.00, "max": 2.19, "points": 10},
            {"min": 2.20, "max": 2.49, "points": 5},
            {"min": 2.50, "max": 2.99, "points": 3},
            {"min": 3.00, "max": 3.49, "points": 1},
        ],
        "pit_stop_fastest_bonus": 5,
        "pit_stop_record_bonus": 15,
        "constructor_dsq_penalty": -20,
    },
}


def get_current_ruleset() -> dict:
    return RULESET
