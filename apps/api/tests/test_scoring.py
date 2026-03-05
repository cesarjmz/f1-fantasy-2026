from app.services.scoring import (
    constructor_race_points,
    driver_qualifying_points,
    driver_race_points,
    pit_stop_band_points,
)


def test_driver_qualifying_points_top10_and_nctime():
    assert driver_qualifying_points(1) == 10
    assert driver_qualifying_points(10) == 1
    assert driver_qualifying_points(11) == 0
    assert driver_qualifying_points(None, status="no time") == -5


def test_driver_race_penalty_for_dsq():
    total, breakdown = driver_race_points(
        finish_position=None,
        start_position=7,
        overtakes=2,
        fastest_lap=False,
        driver_of_day=False,
        status="DSQ",
    )
    assert total == -20
    assert breakdown["finish"] == -20
    assert breakdown["overtakes"] == 0


def test_constructor_race_excludes_dotd_and_adds_pit_bonuses():
    total = constructor_race_points(
        driver_race_points_excluding_dotd=(20, 18),
        fastest_stop_seconds=2.05,
        has_fastest_stop=True,
        has_world_record_stop=True,
    )
    # 20 + 18 + pit(10) + fastest(5) + world record(15)
    assert total == 68


def test_pit_stop_band_points():
    assert pit_stop_band_points(1.95) == 20
    assert pit_stop_band_points(2.15) == 10
    assert pit_stop_band_points(2.35) == 5
    assert pit_stop_band_points(2.80) == 3
