from __future__ import annotations

from itertools import combinations
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import COMMON_ERROR_RESPONSES, api_error_detail
from app.db.session import get_db
from app.schemas.domain import (
    AuditBreakdownItem,
    AuditResponse,
    BriefingResponse,
    ChipRecommendationFactor,
    ConstraintsDiagnostics,
    LineupRecommendation,
    LineupHistoryResponse,
    RoundLifecycleResponse,
    OptimizeRequest,
    OptimizeResponse,
    PredictionRow,
    PredictionSortField,
    PriceSnapshot,
    SimulationPredictionsResponse,
    SimulationSummaryResponse,
    SimulationRunRequest,
    SimulationRunResponse,
    SortOrder,
    TransferHistoryResponse,
    ChipUsageResponse,
    TeamSubmissionRequest,
    TeamSubmissionResponse,
    TeamViewResponse,
)
from app.services.repository import (
    ensure_reference_data_seeded,
    ensure_ruleset_seeded,
    get_points_ledger,
    get_team_for_round,
    get_used_chips,
    get_transfer_history,
    get_chip_usage_history,
    get_lineup_history,
    get_round_lifecycle,
    get_asset_prices,
    get_calendar_rounds,
    get_latest_ruleset,
    get_simulation_predictions,
    get_simulation_summary,
    save_simulation_run,
    save_team_submission,
    replace_points_ledger,
    to_team_view,
)
from app.services.cache import CACHE, make_cache_key
from app.services.ruleset import get_current_ruleset
from app.services.scoring import constructor_race_points, driver_race_points
from app.services.seed_data import (
    ALL_ASSETS,
    CONSTRUCTORS,
    DRIVERS,
    ROUNDS_2026,
    get_round,
)
from app.services.simulation import project_asset_points_map
from app.services.team_logic import (
    apply_chip_multiplier,
    apply_no_negative,
    calculate_budget_used,
    net_transfer_count,
    transfer_penalty,
    validate_chip_usage,
    validate_roster,
)

router = APIRouter(prefix="/api/v1", tags=["v1"], responses=COMMON_ERROR_RESPONSES)


def _validate_round_window(
    from_round: int | None,
    to_round: int | None,
) -> None:
    if from_round is not None and to_round is not None and from_round > to_round:
        raise HTTPException(
            status_code=400,
            detail=api_error_detail(
                code="invalid_round_window",
                message="from_round must be less than or equal to to_round",
            ),
        )


@router.get("/calendar")
def calendar(season: int = Query(default=2026), db: Session = Depends(get_db)) -> dict:
    # This endpoint stays deterministic by seeding static reference rows once.
    ensure_reference_data_seeded(
        db=db,
        rounds=ROUNDS_2026,
        assets=ALL_ASSETS,
        season=season,
        round_number=1,
    )
    rounds = [r.model_dump() for r in get_calendar_rounds(db=db, season=season)]
    return {"season": season, "rounds": rounds}


@router.get("/ruleset/current")
def ruleset_current(db: Session = Depends(get_db)) -> dict:
    ensure_ruleset_seeded(db, get_current_ruleset())
    persisted = get_latest_ruleset(db, season=settings.season)
    if persisted is None:
        raise HTTPException(
            status_code=500,
            detail=api_error_detail(
                code="ruleset_missing",
                message="Ruleset missing",
            ),
        )
    return persisted


@router.get("/assets/prices", response_model=PriceSnapshot)
def assets_prices(
    season: int = Query(default=2026),
    round: int = Query(default=1),
    db: Session = Depends(get_db),
) -> PriceSnapshot:
    get_round(round)
    ensure_reference_data_seeded(
        db=db,
        rounds=ROUNDS_2026,
        assets=ALL_ASSETS,
        season=season,
        round_number=round,
    )
    assets = get_asset_prices(db=db, season=season, round_number=round)
    return PriceSnapshot(season=season, round=round, assets=assets)


@router.post("/simulations/run", response_model=SimulationRunResponse)
def run_simulation(
    payload: SimulationRunRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> SimulationRunResponse:
    get_round(payload.round)

    ensure_ruleset_seeded(db, get_current_ruleset())
    persisted_ruleset = (
        get_latest_ruleset(db, season=payload.season) or get_current_ruleset()
    )
    projection_cache_key = make_cache_key(
        "projections",
        ruleset_hash=str(persisted_ruleset["hash"]),
        model_version=settings.model_version,
        data_cut=settings.data_cut_label,
        request_params={
            "season": payload.season,
            "round": payload.round,
            "n_sims": payload.n_sims,
        },
    )
    cached_projection = CACHE.get_json(projection_cache_key)
    if cached_projection is not None:
        cached_run_id = str(cached_projection.get("run_id", ""))
        if (
            cached_run_id
            and get_simulation_predictions(db, run_id=cached_run_id) is not None
        ):
            response.headers["X-Cache"] = "HIT"
            return SimulationRunResponse(
                run_id=cached_run_id,
                season=payload.season,
                round=payload.round,
                n_sims=payload.n_sims,
            )

    run_id = str(uuid4())

    projected = project_asset_points_map(
        assets=ALL_ASSETS,
        round_number=payload.round,
        n_sims=payload.n_sims,
    )

    predictions = [
        PredictionRow(
            entity_id=asset.id,
            entity_name=asset.name,
            entity_type=asset.asset_type,
            summary=projected[asset.id],
        )
        for asset in ALL_ASSETS
    ]

    save_simulation_run(
        db=db,
        run_id=run_id,
        season=payload.season,
        round_number=payload.round,
        n_sims=payload.n_sims,
        model_version=settings.model_version,
        predictions=predictions,
    )
    CACHE.set_json(
        projection_cache_key,
        value={"run_id": run_id},
        ttl_seconds=settings.cache_ttl_seconds,
    )
    response.headers["X-Cache"] = "MISS"
    return SimulationRunResponse(
        run_id=run_id, season=payload.season, round=payload.round, n_sims=payload.n_sims
    )


@router.get(
    "/simulations/{run_id}/predictions", response_model=SimulationPredictionsResponse
)
def simulation_predictions(
    run_id: str,
    limit: int | None = Query(default=None, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sort_by: PredictionSortField = Query(default="mean"),
    order: SortOrder = Query(default="desc"),
    db: Session = Depends(get_db),
) -> SimulationPredictionsResponse:
    persisted = get_simulation_predictions(
        db, run_id=run_id, limit=limit, offset=offset, sort_by=sort_by, order=order
    )
    if persisted is None:
        raise HTTPException(
            status_code=404,
            detail=api_error_detail(
                code="simulation_run_not_found",
                message="Unknown run_id",
            ),
        )
    return persisted


@router.get("/simulations/{run_id}/summary", response_model=SimulationSummaryResponse)
def simulation_summary(
    run_id: str, db: Session = Depends(get_db)
) -> SimulationSummaryResponse:
    persisted = get_simulation_summary(db, run_id=run_id)
    if persisted is None:
        raise HTTPException(
            status_code=404,
            detail=api_error_detail(
                code="simulation_run_not_found",
                message="Unknown run_id",
            ),
        )
    return persisted


@router.post("/lineups/submit", response_model=TeamSubmissionResponse)
def submit_lineup(
    payload: TeamSubmissionRequest,
    db: Session = Depends(get_db),
) -> TeamSubmissionResponse:
    get_round(payload.round)
    valid, message = validate_roster(
        payload.drivers,
        payload.constructors,
        budget_millions=settings.starting_budget_millions,
    )
    if not valid:
        raise HTTPException(
            status_code=400,
            detail=api_error_detail(code="invalid_roster", message=message),
        )

    used_chips = get_used_chips(db, user_id=payload.user_id, season=payload.season)
    chip_ok, chip_message = validate_chip_usage(
        payload.chip,
        used_chips=used_chips,
        round_number=payload.round,
    )
    if not chip_ok:
        raise HTTPException(
            status_code=400,
            detail=api_error_detail(code="invalid_chip_usage", message=chip_message),
        )

    previous = get_team_for_round(
        db,
        user_id=payload.user_id,
        season=payload.season,
        round_number=max(1, payload.round - 1),
    )
    if previous is None:
        transfer_count = 0
        in_assets: list[int] = []
        out_assets: list[int] = []
    else:
        transfer_count, out_assets, in_assets = net_transfer_count(
            previous_drivers=previous.drivers,
            previous_constructors=previous.constructors,
            final_drivers=payload.drivers,
            final_constructors=payload.constructors,
        )
    penalty = transfer_penalty(transfer_count)

    budget_used = calculate_budget_used(payload.drivers, payload.constructors)
    team = save_team_submission(
        db=db,
        user_id=payload.user_id,
        season=payload.season,
        round_number=payload.round,
        drivers=payload.drivers,
        constructors=payload.constructors,
        boost_driver_id=payload.boost_driver_id,
        chip=payload.chip,
        budget_used=budget_used,
        transfer_count=transfer_count,
        transfer_penalty_points=penalty,
        in_assets=in_assets,
        out_assets=out_assets,
    )
    return TeamSubmissionResponse(
        team_id=team.id,
        season=team.season,
        round=team.round,
        transfer_count=transfer_count,
        transfer_penalty_points=penalty,
        chip=payload.chip,
    )


@router.get("/lineups/current", response_model=TeamViewResponse)
def current_lineup(
    user_id: str = Query(default="local-user"),
    season: int = Query(default=2026),
    round: int = Query(default=1),
    db: Session = Depends(get_db),
) -> TeamViewResponse:
    team = get_team_for_round(db, user_id=user_id, season=season, round_number=round)
    if team is None:
        raise HTTPException(
            status_code=404,
            detail=api_error_detail(
                code="lineup_not_found",
                message="No submitted lineup for this round",
            ),
        )
    return to_team_view(team)


@router.get("/lineups/transfers", response_model=TransferHistoryResponse)
def lineup_transfer_history(
    user_id: str = Query(default="local-user"),
    season: int = Query(default=2026),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    from_round: int | None = Query(default=None, ge=1),
    to_round: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> TransferHistoryResponse:
    _validate_round_window(from_round=from_round, to_round=to_round)
    return get_transfer_history(
        db=db,
        user_id=user_id,
        season=season,
        limit=limit,
        offset=offset,
        from_round=from_round,
        to_round=to_round,
    )


@router.get("/lineups/chips", response_model=ChipUsageResponse)
def lineup_chip_history(
    user_id: str = Query(default="local-user"),
    season: int = Query(default=2026),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    from_round: int | None = Query(default=None, ge=1),
    to_round: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> ChipUsageResponse:
    _validate_round_window(from_round=from_round, to_round=to_round)
    return get_chip_usage_history(
        db=db,
        user_id=user_id,
        season=season,
        limit=limit,
        offset=offset,
        from_round=from_round,
        to_round=to_round,
    )


@router.get("/lineups/history", response_model=LineupHistoryResponse)
def lineup_history(
    user_id: str = Query(default="local-user"),
    season: int = Query(default=2026),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    from_round: int | None = Query(default=None, ge=1),
    to_round: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> LineupHistoryResponse:
    _validate_round_window(from_round=from_round, to_round=to_round)
    return get_lineup_history(
        db=db,
        user_id=user_id,
        season=season,
        limit=limit,
        offset=offset,
        from_round=from_round,
        to_round=to_round,
    )


@router.get("/lineups/lifecycle", response_model=RoundLifecycleResponse)
def lineup_lifecycle(
    user_id: str = Query(default="local-user"),
    season: int = Query(default=2026),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    from_round: int | None = Query(default=None, ge=1),
    to_round: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> RoundLifecycleResponse:
    _validate_round_window(from_round=from_round, to_round=to_round)
    return get_round_lifecycle(
        db=db,
        user_id=user_id,
        season=season,
        limit=limit,
        offset=offset,
        from_round=from_round,
        to_round=to_round,
    )


@router.get("/lineups/{round_number}", response_model=TeamViewResponse)
def lineup_by_round(
    round_number: int,
    user_id: str = Query(default="local-user"),
    season: int = Query(default=2026),
    db: Session = Depends(get_db),
) -> TeamViewResponse:
    get_round(round_number)
    team = get_team_for_round(
        db, user_id=user_id, season=season, round_number=round_number
    )
    if team is None:
        raise HTTPException(
            status_code=404,
            detail=api_error_detail(
                code="lineup_not_found",
                message="No submitted lineup for this round",
            ),
        )
    return to_team_view(team)


@router.post("/optimize", response_model=OptimizeResponse)
def optimize(payload: OptimizeRequest, response: Response) -> OptimizeResponse:
    get_round(payload.round)
    chip_ok, chip_msg = validate_chip_usage(
        payload.chip, payload.used_chips, payload.round
    )
    if not chip_ok:
        raise HTTPException(
            status_code=400,
            detail=api_error_detail(code="invalid_chip_usage", message=chip_msg),
        )

    optimizer_cache_key = make_cache_key(
        "optimizer",
        ruleset_hash=str(get_current_ruleset()["hash"]),
        model_version=settings.model_version,
        data_cut=settings.data_cut_label,
        request_params={
            "season": payload.season,
            "round": payload.round,
            "budget_millions": payload.budget_millions,
            "risk_mode": payload.risk_mode,
            "chip": payload.chip,
            "used_chips": sorted(payload.used_chips),
        },
    )
    cached_optimize = CACHE.get_json(optimizer_cache_key)
    if cached_optimize is not None:
        response.headers["X-Cache"] = "HIT"
        return OptimizeResponse.model_validate(cached_optimize)

    predictions = project_asset_points_map(
        assets=ALL_ASSETS,
        round_number=payload.round,
        n_sims=max(10_000, settings.default_simulation_count),
    )

    chip_eligible = chip_ok
    free_transfers_assumed = 2

    scored: list[LineupRecommendation] = []
    for drivers in combinations([d.id for d in DRIVERS], 5):
        for constructors in combinations([c.id for c in CONSTRUCTORS], 2):
            valid, _ = validate_roster(
                list(drivers), list(constructors), payload.budget_millions
            )
            if not valid:
                continue

            budget_used = calculate_budget_used(list(drivers), list(constructors))
            all_ids = list(drivers) + list(constructors)
            means = [predictions[a].mean for a in all_ids]
            p10s = [predictions[a].p10 for a in all_ids]
            p90s = [predictions[a].p90 for a in all_ids]

            projected = sum(means)
            rank_reason = "Highest expected value (sum of means)"

            if payload.risk_mode == "max_upside":
                projected = sum(p90s)
                rank_reason = "Highest upside ceiling (sum of p90)"
            elif payload.risk_mode == "min_downside":
                projected = sum(p10s)
                rank_reason = "Best worst-case floor (sum of p10)"
            elif payload.risk_mode == "value_growth":
                projected = sum(means) / max(1.0, budget_used)
                rank_reason = "Best points-per-million efficiency"
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
                rank_reason = f"Chip-adjusted ({payload.chip}) highest projected"

            chip_factors: list[ChipRecommendationFactor] = []
            if payload.chip is not None:
                original_projected = sum(means)
                adjusted = apply_no_negative(projected, payload.chip)
                bonus = round(adjusted - original_projected, 2)
                chip_factors.append(
                    ChipRecommendationFactor(
                        chip=payload.chip,
                        projected_bonus=bonus,
                        reasoning=f"Applying {payload.chip} adds ~{bonus:.1f} pts vs baseline",
                    )
                )
                projected = adjusted
            else:
                projected = apply_no_negative(projected, payload.chip)

            risk_score = round(sum(p90s) - sum(p10s), 2)
            budget_margin = round(payload.budget_millions - budget_used, 2)
            explanation = (
                f"Budget {budget_used:.1f}m ({budget_margin:.1f}m margin), "
                f"projected {projected:.1f} ({payload.risk_mode})"
            )

            constraints = ConstraintsDiagnostics(
                budget_cap=payload.budget_millions,
                budget_used=budget_used,
                budget_margin=budget_margin,
                chip_active=payload.chip,
                chips_already_used=list(payload.used_chips),
                chip_eligible=chip_eligible,
                free_transfers_assumed=free_transfers_assumed,
            )

            scored.append(
                LineupRecommendation(
                    drivers=list(drivers),
                    constructors=list(constructors),
                    projected_points=round(projected, 2),
                    budget_used=budget_used,
                    risk_score=risk_score,
                    explanation=explanation,
                    rank_reason=rank_reason,
                    chip_factors=chip_factors,
                    constraints=constraints,
                )
            )

    scored.sort(key=lambda item: item.projected_points, reverse=True)
    optimize_response = OptimizeResponse(
        season=payload.season,
        round=payload.round,
        risk_mode=payload.risk_mode,
        chip=payload.chip,
        recommendations=scored[:5],
    )
    CACHE.set_json(
        optimizer_cache_key,
        value=optimize_response.model_dump(mode="json"),
        ttl_seconds=settings.cache_ttl_seconds,
    )
    response.headers["X-Cache"] = "MISS"
    return optimize_response


@router.post("/cache/invalidate")
def invalidate_cache(
    namespace: str = Query(default="all", pattern="^(all|projections|optimizer)$"),
) -> dict:
    deleted = CACHE.invalidate_namespace(namespace)
    return {"namespace": namespace, "deleted": deleted}


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
    season: int = Query(default=2026),
    round_number: int = Query(default=1, alias="round"),
    user_id: str = Query(default="local-user"),
    db: Session = Depends(get_db),
) -> AuditResponse:
    team = get_team_for_round(
        db, user_id=user_id, season=season, round_number=round_number
    )
    if team is None:
        raise HTTPException(
            status_code=404,
            detail=api_error_detail(
                code="lineup_not_found",
                message="No submitted lineup to audit",
            ),
        )

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

    replace_points_ledger(
        db=db,
        user_id=user_id,
        season=season,
        round_number=round_number,
        team_id=team.id,
        items=[(item.category, item.points, {}) for item in items],
    )
    persisted_items = get_points_ledger(
        db=db,
        user_id=user_id,
        season=season,
        round_number=round_number,
        team_id=team.id,
    )
    response_items = [
        AuditBreakdownItem(category=row.category, points=row.points)
        for row in persisted_items
    ]
    persisted_total = round(sum(item.points for item in response_items), 2)

    return AuditResponse(
        season=season,
        round=round_number,
        lineup_name=f"{user_id}-round-{round_number}",
        total_points=round(float(persisted_total), 2),
        breakdown=response_items,
    )
