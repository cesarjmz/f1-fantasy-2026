from __future__ import annotations

from itertools import combinations
from statistics import median
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query

from app.schemas.domain import (
    AuditBreakdownItem,
    AuditResponse,
    BriefingResponse,
    DistributionSummary,
    LineupRecommendation,
    OptimizeRequest,
    OptimizeResponse,
    PredictionRow,
    PriceSnapshot,
    SimulationPredictionsResponse,
    SimulationRunRequest,
    SimulationRunResponse,
)
from app.services.ruleset import get_current_ruleset
from app.services.scoring import constructor_race_points, driver_race_points
from app.services.seed_data import (
    ALL_ASSETS,
    CONSTRUCTORS,
    DRIVERS,
    ROUNDS_2026,
    get_round,
)
from app.services.team_logic import (
    apply_chip_multiplier,
    apply_no_negative,
    calculate_budget_used,
    validate_chip_usage,
    validate_roster,
)

router = APIRouter(prefix="/api/v1", tags=["v1"])

_SIMULATION_RUNS: dict[str, SimulationPredictionsResponse] = {}


@router.get("/calendar")
def calendar(season: int = Query(default=2026)) -> dict:
    rounds = [r.model_dump() for r in ROUNDS_2026 if r.season == season]
    return {"season": season, "rounds": rounds}


@router.get("/ruleset/current")
def ruleset_current() -> dict:
    return get_current_ruleset()


@router.get("/assets/prices", response_model=PriceSnapshot)
def assets_prices(
    season: int = Query(default=2026), round: int = Query(default=1)
) -> PriceSnapshot:
    get_round(round)
    return PriceSnapshot(season=season, round=round, assets=ALL_ASSETS)


def _project_asset_points(
    asset_id: int, round_number: int, n_sims: int
) -> DistributionSummary:
    # Deterministic seeded projection proxy for MVP: this is replaced by Monte Carlo ingestion models later.
    if asset_id >= 100:
        base = max(20.0, 56.0 - (asset_id - 100) * 4)
    else:
        base = max(8.0, 44.0 - asset_id * 2.5)

    sprint_boost = 1.10 if get_round(round_number).is_sprint else 1.0
    mean = round(base * sprint_boost, 2)
    p10 = round(mean * 0.65, 2)
    p90 = round(mean * 1.35, 2)
    med = round(median([p10, mean, p90]), 2)
    negative_prob = round(max(0.02, 0.18 - (mean / 300.0)), 3)
    if n_sims < 500:
        negative_prob = round(negative_prob + 0.03, 3)

    return DistributionSummary(
        mean=mean, median=med, p10=p10, p90=p90, prob_negative=negative_prob
    )


@router.post("/simulations/run", response_model=SimulationRunResponse)
def run_simulation(payload: SimulationRunRequest) -> SimulationRunResponse:
    get_round(payload.round)
    run_id = str(uuid4())

    predictions = [
        PredictionRow(
            entity_id=asset.id,
            entity_name=asset.name,
            entity_type=asset.asset_type,
            summary=_project_asset_points(asset.id, payload.round, payload.n_sims),
        )
        for asset in ALL_ASSETS
    ]

    _SIMULATION_RUNS[run_id] = SimulationPredictionsResponse(
        run_id=run_id,
        season=payload.season,
        round=payload.round,
        model_version="seeded-v0",
        predictions=predictions,
    )
    return SimulationRunResponse(
        run_id=run_id, season=payload.season, round=payload.round, n_sims=payload.n_sims
    )


@router.get(
    "/simulations/{run_id}/predictions", response_model=SimulationPredictionsResponse
)
def simulation_predictions(run_id: str) -> SimulationPredictionsResponse:
    if run_id not in _SIMULATION_RUNS:
        raise HTTPException(status_code=404, detail="Unknown run_id")
    return _SIMULATION_RUNS[run_id]


@router.post("/optimize", response_model=OptimizeResponse)
def optimize(payload: OptimizeRequest) -> OptimizeResponse:
    get_round(payload.round)
    chip_ok, chip_msg = validate_chip_usage(
        payload.chip, payload.used_chips, payload.round
    )
    if not chip_ok:
        raise HTTPException(status_code=400, detail=chip_msg)

    predictions = {
        asset.id: _project_asset_points(asset.id, payload.round, n_sims=10_000)
        for asset in ALL_ASSETS
    }

    scored: list[LineupRecommendation] = []
    for drivers in combinations([d.id for d in DRIVERS], 5):
        for constructors in combinations([c.id for c in CONSTRUCTORS], 2):
            valid, _ = validate_roster(
                list(drivers), list(constructors), payload.budget_millions
            )
            if not valid:
                continue

            budget_used = calculate_budget_used(list(drivers), list(constructors))
            means = [predictions[a].mean for a in list(drivers) + list(constructors)]
            p10s = [predictions[a].p10 for a in list(drivers) + list(constructors)]
            p90s = [predictions[a].p90 for a in list(drivers) + list(constructors)]

            projected = sum(means)
            if payload.risk_mode == "max_upside":
                projected = sum(p90s)
            elif payload.risk_mode == "min_downside":
                projected = sum(p10s)
            elif payload.risk_mode == "value_growth":
                projected = sum(means) / max(1.0, budget_used)
            elif payload.risk_mode == "chip_aware" and payload.chip in {
                "triple_boost",
                "autopilot",
            }:
                best = max(means)
                projected = (
                    projected
                    - best
                    + apply_chip_multiplier(
                        best, is_primary_boost=True, chip=payload.chip
                    )
                )

            projected = apply_no_negative(projected, payload.chip)
            risk_score = round(sum(p90s) - sum(p10s), 2)
            explanation = f"Budget {budget_used:.1f}m, projected {projected:.1f} ({payload.risk_mode})"

            scored.append(
                LineupRecommendation(
                    drivers=list(drivers),
                    constructors=list(constructors),
                    projected_points=round(projected, 2),
                    budget_used=budget_used,
                    risk_score=risk_score,
                    explanation=explanation,
                )
            )

    scored.sort(key=lambda item: item.projected_points, reverse=True)
    return OptimizeResponse(
        season=payload.season,
        round=payload.round,
        risk_mode=payload.risk_mode,
        chip=payload.chip,
        recommendations=scored[:5],
    )


@router.get("/briefing", response_model=BriefingResponse)
def briefing(
    season: int = Query(default=2026), round: int = Query(default=1)
) -> BriefingResponse:
    round_info = get_round(round)
    checklist = [
        "Confirm sprint format and extra scoring session",
        "Re-check penalties and steward notes before lock",
        "Re-run optimizer after latest weather update",
        "Validate chip eligibility and one-chip-per-week rule",
        "Check transfer count using net-transfer final-state logic",
    ]
    alerts = []
    if round_info.is_sprint:
        alerts.append(
            "Sprint weekend detected: consider 3x Boost or Limitless scenario"
        )
    return BriefingResponse(
        season=season,
        round=round,
        is_sprint=round_info.is_sprint,
        lock_at=round_info.lock_at,
        checklist=checklist,
        alerts=alerts,
    )


@router.get("/audit/lineup", response_model=AuditResponse)
def audit_lineup(
    season: int = Query(default=2026), round: int = Query(default=1)
) -> AuditResponse:
    race_total, race_breakdown = driver_race_points(
        finish_position=2,
        start_position=5,
        overtakes=3,
        fastest_lap=True,
        driver_of_day=False,
    )
    constructor_total = constructor_race_points(
        driver_race_points_excluding_dotd=(22, 16),
        fastest_stop_seconds=2.18,
        has_fastest_stop=True,
        has_world_record_stop=False,
        disqualified_drivers=0,
    )

    items = [
        AuditBreakdownItem(category=f"driver_race_{k}", points=v)
        for k, v in race_breakdown.items()
    ]
    items.append(
        AuditBreakdownItem(category="constructor_race_total", points=constructor_total)
    )
    total = race_total + constructor_total

    return AuditResponse(
        season=season,
        round=round,
        lineup_name="Seeded audit lineup",
        total_points=round(float(total), 2),
        breakdown=items,
    )
