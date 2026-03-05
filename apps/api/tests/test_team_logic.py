from app.services.team_logic import (
    net_transfer_count,
    transfer_penalty,
    validate_chip_usage,
)


def test_net_transfers_only_final_state_counts():
    previous_drivers = [1, 2, 3, 4, 5]
    previous_constructors = [101, 102]

    # User may have drafted swaps in between; final team equals previous.
    final_drivers = [1, 2, 3, 4, 5]
    final_constructors = [101, 102]

    transfer_count, out_assets, in_assets = net_transfer_count(
        previous_drivers,
        previous_constructors,
        final_drivers,
        final_constructors,
    )
    assert transfer_count == 0
    assert out_assets == []
    assert in_assets == []


def test_transfer_penalty_after_two_free_transfers():
    assert transfer_penalty(0) == 0
    assert transfer_penalty(2) == 0
    assert transfer_penalty(4) == 20


def test_chip_round_unlock_and_once_per_season():
    ok, _ = validate_chip_usage("limitless", used_chips=[], round_number=1)
    assert not ok

    ok, _ = validate_chip_usage("wildcard", used_chips=[], round_number=2)
    assert ok

    ok, _ = validate_chip_usage("autopilot", used_chips=["autopilot"], round_number=10)
    assert not ok
