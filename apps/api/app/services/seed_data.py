from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.domain import Asset, ChipName, RoundInfo

SPRINT_ROUNDS_2026 = {2, 3, 5, 9, 13, 18}

ROUNDS_2026: list[RoundInfo] = [
    RoundInfo(
        season=2026,
        round=1,
        grand_prix_name="Australia",
        start_date="2026-03-08",
        is_sprint=False,
        lock_at=datetime(2026, 3, 7, 4, 0, tzinfo=timezone.utc),
    ),
    RoundInfo(
        season=2026,
        round=2,
        grand_prix_name="China",
        start_date="2026-03-22",
        is_sprint=True,
        lock_at=datetime(2026, 3, 20, 4, 0, tzinfo=timezone.utc),
    ),
    RoundInfo(
        season=2026,
        round=3,
        grand_prix_name="Miami",
        start_date="2026-04-05",
        is_sprint=True,
        lock_at=datetime(2026, 4, 3, 4, 0, tzinfo=timezone.utc),
    ),
    RoundInfo(
        season=2026,
        round=4,
        grand_prix_name="Bahrain",
        start_date="2026-04-12",
        is_sprint=False,
        lock_at=datetime(2026, 4, 11, 14, 0, tzinfo=timezone.utc),
    ),
    RoundInfo(
        season=2026,
        round=5,
        grand_prix_name="Canada",
        start_date="2026-05-24",
        is_sprint=True,
        lock_at=datetime(2026, 5, 22, 16, 0, tzinfo=timezone.utc),
    ),
    RoundInfo(
        season=2026,
        round=6,
        grand_prix_name="Monaco",
        start_date="2026-06-07",
        is_sprint=False,
        lock_at=datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc),
    ),
    RoundInfo(
        season=2026,
        round=7,
        grand_prix_name="Austria",
        start_date="2026-06-21",
        is_sprint=False,
        lock_at=datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc),
    ),
    RoundInfo(
        season=2026,
        round=8,
        grand_prix_name="Spain",
        start_date="2026-06-28",
        is_sprint=False,
        lock_at=datetime(2026, 6, 27, 10, 0, tzinfo=timezone.utc),
    ),
    RoundInfo(
        season=2026,
        round=9,
        grand_prix_name="Great Britain",
        start_date="2026-07-05",
        is_sprint=True,
        lock_at=datetime(2026, 7, 3, 10, 0, tzinfo=timezone.utc),
    ),
    RoundInfo(
        season=2026,
        round=10,
        grand_prix_name="Hungary",
        start_date="2026-07-19",
        is_sprint=False,
        lock_at=datetime(2026, 7, 18, 10, 0, tzinfo=timezone.utc),
    ),
    RoundInfo(
        season=2026,
        round=11,
        grand_prix_name="Belgium",
        start_date="2026-08-02",
        is_sprint=False,
        lock_at=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc),
    ),
    RoundInfo(
        season=2026,
        round=12,
        grand_prix_name="Italy",
        start_date="2026-09-06",
        is_sprint=False,
        lock_at=datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc),
    ),
    RoundInfo(
        season=2026,
        round=13,
        grand_prix_name="Netherlands",
        start_date="2026-09-13",
        is_sprint=True,
        lock_at=datetime(2026, 9, 11, 10, 0, tzinfo=timezone.utc),
    ),
    RoundInfo(
        season=2026,
        round=14,
        grand_prix_name="Azerbaijan",
        start_date="2026-09-27",
        is_sprint=False,
        lock_at=datetime(2026, 9, 26, 10, 0, tzinfo=timezone.utc),
    ),
    RoundInfo(
        season=2026,
        round=15,
        grand_prix_name="Singapore",
        start_date="2026-10-11",
        is_sprint=True,
        lock_at=datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc),
    ),
]

DRIVERS: list[Asset] = [
    Asset(
        id=1,
        name="Max Verstappen",
        asset_type="driver",
        team="Red Bull",
        price_millions=30.0,
    ),
    Asset(
        id=2,
        name="Lando Norris",
        asset_type="driver",
        team="McLaren",
        price_millions=27.0,
    ),
    Asset(
        id=3,
        name="Charles Leclerc",
        asset_type="driver",
        team="Ferrari",
        price_millions=26.0,
    ),
    Asset(
        id=4,
        name="Lewis Hamilton",
        asset_type="driver",
        team="Ferrari",
        price_millions=24.0,
    ),
    Asset(
        id=5,
        name="Oscar Piastri",
        asset_type="driver",
        team="McLaren",
        price_millions=23.0,
    ),
    Asset(
        id=6,
        name="George Russell",
        asset_type="driver",
        team="Mercedes",
        price_millions=21.0,
    ),
    Asset(
        id=7,
        name="Fernando Alonso",
        asset_type="driver",
        team="Aston Martin",
        price_millions=18.0,
    ),
    Asset(
        id=8,
        name="Pierre Gasly",
        asset_type="driver",
        team="Alpine",
        price_millions=14.0,
    ),
    Asset(
        id=9, name="Yuki Tsunoda", asset_type="driver", team="RB", price_millions=12.0
    ),
    Asset(
        id=10,
        name="Alex Albon",
        asset_type="driver",
        team="Williams",
        price_millions=11.0,
    ),
]

CONSTRUCTORS: list[Asset] = [
    Asset(id=101, name="Red Bull", asset_type="constructor", price_millions=20.0),
    Asset(id=102, name="McLaren", asset_type="constructor", price_millions=18.0),
    Asset(id=103, name="Ferrari", asset_type="constructor", price_millions=16.0),
    Asset(id=104, name="Mercedes", asset_type="constructor", price_millions=12.0),
    Asset(id=105, name="Aston Martin", asset_type="constructor", price_millions=10.0),
]

ALL_ASSETS = DRIVERS + CONSTRUCTORS

CHIPS: list[ChipName] = [
    "limitless",
    "wildcard",
    "triple_boost",
    "no_negative",
    "final_fix",
    "autopilot",
]


def get_round(round_number: int) -> RoundInfo:
    for round_info in ROUNDS_2026:
        if round_info.round == round_number:
            return round_info
    raise ValueError(f"Unknown round: {round_number}")


def get_asset(asset_id: int) -> Asset:
    for asset in ALL_ASSETS:
        if asset.id == asset_id:
            return asset
    raise ValueError(f"Unknown asset_id: {asset_id}")
