from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.gameplay import (
    FantasyChipUsage,
    FantasyTeam,
    FantasyTransfer,
    PointsLedgerEntry,
)
from app.models.reference import FantasyAssetPrice, MeetingRound
from app.models.ruleset import FantasyRulesetVersion
from app.models.simulation import SimulationPrediction, SimulationRun
from app.schemas.domain import (
    Asset,
    ChipUsageItem,
    ChipUsageResponse,
    DistributionSummary,
    LineupHistoryItem,
    LineupHistoryResponse,
    PredictionRow,
    PredictionSortField,
    RoundLifecycleItem,
    RoundLifecycleResponse,
    RoundInfo,
    SimulationRunSummary,
    SimulationPredictionsMeta,
    SimulationSummaryResponse,
    SimulationSummaryEntity,
    SimulationPredictionsResponse,
    SortOrder,
    TransferHistoryItem,
    TransferHistoryResponse,
    TeamViewResponse,
)


def _empty_simulation_summary() -> SimulationRunSummary:
    empty_entity = SimulationSummaryEntity(entity_id=0, entity_name="n/a", value=0.0)
    return SimulationRunSummary(
        entity_count=0,
        top_mean=empty_entity,
        highest_upside=empty_entity,
        highest_negative_risk=empty_entity,
    )


def _build_simulation_summary(rows: list[SimulationPrediction]) -> SimulationRunSummary:
    if not rows:
        return _empty_simulation_summary()

    top_mean_row = max(rows, key=lambda row: row.mean)
    highest_upside_row = max(rows, key=lambda row: row.p90)
    highest_negative_row = max(rows, key=lambda row: row.prob_negative)

    return SimulationRunSummary(
        entity_count=len(rows),
        top_mean=SimulationSummaryEntity(
            entity_id=top_mean_row.entity_id,
            entity_name=top_mean_row.entity_name,
            value=top_mean_row.mean,
        ),
        highest_upside=SimulationSummaryEntity(
            entity_id=highest_upside_row.entity_id,
            entity_name=highest_upside_row.entity_name,
            value=highest_upside_row.p90,
        ),
        highest_negative_risk=SimulationSummaryEntity(
            entity_id=highest_negative_row.entity_id,
            entity_name=highest_negative_row.entity_name,
            value=highest_negative_row.prob_negative,
        ),
    )


def ensure_ruleset_seeded(db: Session, ruleset_payload: dict) -> None:
    existing = db.scalar(
        select(FantasyRulesetVersion).where(
            FantasyRulesetVersion.rules_hash == ruleset_payload["hash"]
        )
    )
    if existing is not None:
        return

    row = FantasyRulesetVersion(
        season=ruleset_payload["season"],
        rules_hash=ruleset_payload["hash"],
        effective_from=datetime.fromisoformat(ruleset_payload["effective_from"]),
        rules_json=ruleset_payload,
    )
    db.add(row)
    db.commit()


def get_latest_ruleset(db: Session, season: int) -> dict | None:
    row = db.scalar(
        select(FantasyRulesetVersion)
        .where(FantasyRulesetVersion.season == season)
        .order_by(FantasyRulesetVersion.effective_from.desc())
    )
    if row is None:
        return None
    return row.rules_json


def ensure_reference_data_seeded(
    db: Session,
    rounds: list[RoundInfo],
    assets: list[Asset],
    season: int,
    round_number: int,
) -> None:
    round_exists = db.scalar(
        select(MeetingRound).where(
            MeetingRound.season == season, MeetingRound.round == rounds[0].round
        )
    )
    if round_exists is None:
        db.add_all(
            [
                MeetingRound(
                    season=item.season,
                    round=item.round,
                    grand_prix_name=item.grand_prix_name,
                    start_date=item.start_date,
                    is_sprint=item.is_sprint,
                    lock_at=item.lock_at,
                )
                for item in rounds
            ]
        )

    prices_exist = db.scalar(
        select(FantasyAssetPrice).where(
            FantasyAssetPrice.season == season,
            FantasyAssetPrice.round == round_number,
        )
    )
    if prices_exist is None:
        db.add_all(
            [
                FantasyAssetPrice(
                    season=season,
                    round=round_number,
                    asset_id=asset.id,
                    name=asset.name,
                    asset_type=asset.asset_type,
                    team=asset.team,
                    price_millions=asset.price_millions,
                )
                for asset in assets
            ]
        )
    db.commit()


def get_calendar_rounds(db: Session, season: int) -> list[RoundInfo]:
    rows = db.scalars(
        select(MeetingRound)
        .where(MeetingRound.season == season)
        .order_by(MeetingRound.round.asc())
    ).all()
    return [
        RoundInfo(
            season=row.season,
            round=row.round,
            grand_prix_name=row.grand_prix_name,
            start_date=row.start_date,
            is_sprint=row.is_sprint,
            lock_at=row.lock_at,
        )
        for row in rows
    ]


def get_asset_prices(db: Session, season: int, round_number: int) -> list[Asset]:
    rows = db.scalars(
        select(FantasyAssetPrice)
        .where(
            FantasyAssetPrice.season == season,
            FantasyAssetPrice.round == round_number,
        )
        .order_by(FantasyAssetPrice.asset_type.asc(), FantasyAssetPrice.asset_id.asc())
    ).all()
    return [
        Asset(
            id=row.asset_id,
            name=row.name,
            asset_type=row.asset_type,
            team=row.team,
            price_millions=row.price_millions,
        )
        for row in rows
    ]


def save_simulation_run(
    db: Session,
    run_id: str,
    season: int,
    round_number: int,
    n_sims: int,
    model_version: str,
    predictions: list[PredictionRow],
) -> None:
    run = SimulationRun(
        run_id=run_id,
        season=season,
        round=round_number,
        n_sims=n_sims,
        model_version=model_version,
    )
    db.add(run)
    db.flush()

    rows = [
        SimulationPrediction(
            simulation_run_id=run.id,
            entity_id=p.entity_id,
            entity_name=p.entity_name,
            entity_type=p.entity_type,
            mean=p.summary.mean,
            median=p.summary.median,
            p10=p.summary.p10,
            p90=p.summary.p90,
            prob_negative=p.summary.prob_negative,
        )
        for p in predictions
    ]
    db.add_all(rows)
    db.commit()


_PREDICTION_SORT_COLUMNS = {
    "mean": SimulationPrediction.mean,
    "median": SimulationPrediction.median,
    "p10": SimulationPrediction.p10,
    "p90": SimulationPrediction.p90,
    "prob_negative": SimulationPrediction.prob_negative,
    "entity_name": SimulationPrediction.entity_name,
}


def get_simulation_predictions(
    db: Session,
    run_id: str,
    limit: int | None = None,
    offset: int = 0,
    sort_by: PredictionSortField = "mean",
    order: SortOrder = "desc",
) -> SimulationPredictionsResponse | None:
    run = db.scalar(select(SimulationRun).where(SimulationRun.run_id == run_id))
    if run is None:
        return None

    base_stmt = select(SimulationPrediction).where(
        SimulationPrediction.simulation_run_id == run.id
    )
    total = db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0

    sort_col = _PREDICTION_SORT_COLUMNS.get(sort_by, SimulationPrediction.mean)
    order_clause = sort_col.asc() if order == "asc" else sort_col.desc()
    # Secondary sort on id for stable pagination
    ordered_stmt = base_stmt.order_by(order_clause, SimulationPrediction.id.asc())

    page_limit = total if limit is None else limit
    rows = db.scalars(ordered_stmt.offset(offset).limit(page_limit)).all()
    returned = len(rows)
    next_offset = offset + returned
    has_more = next_offset < total

    # Summary uses all rows (unordered)
    all_rows = db.scalars(base_stmt).all() if limit is not None else rows

    predictions = [
        PredictionRow(
            entity_id=row.entity_id,
            entity_name=row.entity_name,
            entity_type=row.entity_type,
            summary=DistributionSummary(
                mean=row.mean,
                median=row.median,
                p10=row.p10,
                p90=row.p90,
                prob_negative=row.prob_negative,
            ),
        )
        for row in rows
    ]

    return SimulationPredictionsResponse(
        run_id=run.run_id,
        season=run.season,
        round=run.round,
        n_sims=run.n_sims,
        model_version=run.model_version,
        summary=_build_simulation_summary(list(all_rows)),
        meta=SimulationPredictionsMeta(
            total=total,
            limit=page_limit,
            offset=offset,
            returned=returned,
            has_more=has_more,
            next_offset=next_offset if has_more else None,
            sort_by=sort_by,
            order=order,
        ),
        predictions=predictions,
    )


def get_simulation_summary(
    db: Session, run_id: str
) -> SimulationSummaryResponse | None:
    run = db.scalar(select(SimulationRun).where(SimulationRun.run_id == run_id))
    if run is None:
        return None

    rows = db.scalars(
        select(SimulationPrediction).where(
            SimulationPrediction.simulation_run_id == run.id
        )
    ).all()

    return SimulationSummaryResponse(
        run_id=run.run_id,
        season=run.season,
        round=run.round,
        n_sims=run.n_sims,
        model_version=run.model_version,
        summary=_build_simulation_summary(rows),
    )


def get_team_for_round(
    db: Session, user_id: str, season: int, round_number: int
) -> FantasyTeam | None:
    return db.scalar(
        select(FantasyTeam).where(
            FantasyTeam.user_id == user_id,
            FantasyTeam.season == season,
            FantasyTeam.round == round_number,
        )
    )


def get_used_chips(db: Session, user_id: str, season: int) -> list[str]:
    rows = db.scalars(
        select(FantasyChipUsage).where(
            FantasyChipUsage.user_id == user_id,
            FantasyChipUsage.season == season,
        )
    ).all()
    return [row.chip_name for row in rows]


def get_transfer_history(
    db: Session,
    user_id: str,
    season: int,
    limit: int,
    offset: int = 0,
    from_round: int | None = None,
    to_round: int | None = None,
) -> TransferHistoryResponse:
    stmt = select(FantasyTransfer).where(
        FantasyTransfer.user_id == user_id,
        FantasyTransfer.season == season,
    )
    if from_round is not None:
        stmt = stmt.where(FantasyTransfer.round >= from_round)
    if to_round is not None:
        stmt = stmt.where(FantasyTransfer.round <= to_round)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    rows = db.scalars(
        stmt.order_by(FantasyTransfer.round.desc(), FantasyTransfer.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    next_offset = offset + len(rows)
    has_more = next_offset < total
    return TransferHistoryResponse(
        user_id=user_id,
        season=season,
        total=total,
        has_more=has_more,
        next_offset=next_offset if has_more else None,
        items=[
            TransferHistoryItem(
                round=row.round,
                transfer_count=row.transfer_count,
                penalty_points=row.penalty_points,
                in_assets=row.in_assets,
                out_assets=row.out_assets,
                computed_at=row.computed_at,
            )
            for row in rows
        ],
    )


def get_chip_usage_history(
    db: Session,
    user_id: str,
    season: int,
    limit: int,
    offset: int = 0,
    from_round: int | None = None,
    to_round: int | None = None,
) -> ChipUsageResponse:
    stmt = select(FantasyChipUsage).where(
        FantasyChipUsage.user_id == user_id,
        FantasyChipUsage.season == season,
    )
    if from_round is not None:
        stmt = stmt.where(FantasyChipUsage.round >= from_round)
    if to_round is not None:
        stmt = stmt.where(FantasyChipUsage.round <= to_round)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    rows = db.scalars(
        stmt.order_by(FantasyChipUsage.round.asc(), FantasyChipUsage.id.asc())
        .offset(offset)
        .limit(limit)
    ).all()
    next_offset = offset + len(rows)
    has_more = next_offset < total

    return ChipUsageResponse(
        user_id=user_id,
        season=season,
        total=total,
        has_more=has_more,
        next_offset=next_offset if has_more else None,
        items=[
            ChipUsageItem(chip=row.chip_name, round=row.round, used_at=row.used_at)
            for row in rows
        ],
    )


def get_lineup_history(
    db: Session,
    user_id: str,
    season: int,
    limit: int,
    offset: int = 0,
    from_round: int | None = None,
    to_round: int | None = None,
) -> LineupHistoryResponse:
    stmt = select(FantasyTeam).where(
        FantasyTeam.user_id == user_id,
        FantasyTeam.season == season,
    )
    if from_round is not None:
        stmt = stmt.where(FantasyTeam.round >= from_round)
    if to_round is not None:
        stmt = stmt.where(FantasyTeam.round <= to_round)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    rows = db.scalars(
        stmt.order_by(FantasyTeam.round.desc(), FantasyTeam.submitted_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    next_offset = offset + len(rows)
    has_more = next_offset < total

    return LineupHistoryResponse(
        user_id=user_id,
        season=season,
        total=total,
        has_more=has_more,
        next_offset=next_offset if has_more else None,
        items=[
            LineupHistoryItem(
                team_id=row.id,
                round=row.round,
                drivers=row.drivers,
                constructors=row.constructors,
                boost_driver_id=row.boost_driver_id,
                chip=row.chip_used,
                budget_used=row.budget_used,
                submitted_at=row.submitted_at,
            )
            for row in rows
        ],
    )


def get_round_lifecycle(
    db: Session,
    user_id: str,
    season: int,
    limit: int,
    offset: int = 0,
    from_round: int | None = None,
    to_round: int | None = None,
) -> RoundLifecycleResponse:
    stmt = select(FantasyTeam).where(
        FantasyTeam.user_id == user_id,
        FantasyTeam.season == season,
    )
    if from_round is not None:
        stmt = stmt.where(FantasyTeam.round >= from_round)
    if to_round is not None:
        stmt = stmt.where(FantasyTeam.round <= to_round)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    teams = db.scalars(
        stmt.order_by(FantasyTeam.round.desc(), FantasyTeam.submitted_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    items: list[RoundLifecycleItem] = []
    for team in teams:
        transfer = db.scalar(
            select(FantasyTransfer)
            .where(
                FantasyTransfer.user_id == user_id,
                FantasyTransfer.season == season,
                FantasyTransfer.round == team.round,
            )
            .order_by(FantasyTransfer.id.desc())
        )
        transfer_count = transfer.transfer_count if transfer is not None else 0
        transfer_penalty = transfer.penalty_points if transfer is not None else 0

        ledger_points = db.scalars(
            select(PointsLedgerEntry.points).where(
                PointsLedgerEntry.user_id == user_id,
                PointsLedgerEntry.season == season,
                PointsLedgerEntry.round == team.round,
                PointsLedgerEntry.team_id == team.id,
            )
        ).all()
        audited_points = round(float(sum(ledger_points)), 2) if ledger_points else None

        items.append(
            RoundLifecycleItem(
                round=team.round,
                team_id=team.id,
                chip=team.chip_used,
                budget_used=team.budget_used,
                transfer_count=transfer_count,
                transfer_penalty_points=transfer_penalty,
                audited_points=audited_points,
                submitted_at=team.submitted_at,
            )
        )

    next_offset = offset + len(items)
    has_more = next_offset < total
    return RoundLifecycleResponse(
        user_id=user_id,
        season=season,
        total=total,
        has_more=has_more,
        next_offset=next_offset if has_more else None,
        items=items,
    )


def save_team_submission(
    db: Session,
    user_id: str,
    season: int,
    round_number: int,
    drivers: list[int],
    constructors: list[int],
    boost_driver_id: int | None,
    chip: str | None,
    budget_used: float,
    transfer_count: int,
    transfer_penalty_points: int,
    in_assets: list[int],
    out_assets: list[int],
) -> FantasyTeam:
    existing = get_team_for_round(
        db, user_id=user_id, season=season, round_number=round_number
    )
    if existing is not None:
        existing.drivers = drivers
        existing.constructors = constructors
        existing.boost_driver_id = boost_driver_id
        existing.chip_used = chip
        existing.budget_used = budget_used
        existing.submitted_at = datetime.now(timezone.utc)
        team = existing
    else:
        team = FantasyTeam(
            user_id=user_id,
            season=season,
            round=round_number,
            drivers=drivers,
            constructors=constructors,
            boost_driver_id=boost_driver_id,
            chip_used=chip,
            budget_used=budget_used,
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(team)
        db.flush()

    transfer = FantasyTransfer(
        user_id=user_id,
        season=season,
        round=round_number,
        out_assets=out_assets,
        in_assets=in_assets,
        transfer_count=transfer_count,
        penalty_points=transfer_penalty_points,
        computed_at=datetime.now(timezone.utc),
    )
    db.add(transfer)

    if chip is not None:
        existing_chip = db.scalar(
            select(FantasyChipUsage).where(
                FantasyChipUsage.user_id == user_id,
                FantasyChipUsage.season == season,
                FantasyChipUsage.chip_name == chip,
            )
        )
        if existing_chip is None:
            db.add(
                FantasyChipUsage(
                    user_id=user_id,
                    season=season,
                    chip_name=chip,
                    round=round_number,
                    used_at=datetime.now(timezone.utc),
                )
            )

    db.commit()
    db.refresh(team)
    return team


def replace_points_ledger(
    db: Session,
    user_id: str,
    season: int,
    round_number: int,
    team_id: int,
    items: list[tuple[str, float, dict]],
) -> None:
    existing = db.scalars(
        select(PointsLedgerEntry).where(
            PointsLedgerEntry.user_id == user_id,
            PointsLedgerEntry.season == season,
            PointsLedgerEntry.round == round_number,
            PointsLedgerEntry.team_id == team_id,
        )
    ).all()
    for row in existing:
        db.delete(row)

    db.add_all(
        [
            PointsLedgerEntry(
                user_id=user_id,
                season=season,
                round=round_number,
                team_id=team_id,
                category=category,
                points=points,
                meta_json=meta,
                computed_at=datetime.now(timezone.utc),
            )
            for category, points, meta in items
        ]
    )
    db.commit()


def get_points_ledger(
    db: Session, user_id: str, season: int, round_number: int, team_id: int
) -> list[PointsLedgerEntry]:
    return db.scalars(
        select(PointsLedgerEntry)
        .where(
            PointsLedgerEntry.user_id == user_id,
            PointsLedgerEntry.season == season,
            PointsLedgerEntry.round == round_number,
            PointsLedgerEntry.team_id == team_id,
        )
        .order_by(PointsLedgerEntry.id.asc())
    ).all()


def to_team_view(team: FantasyTeam) -> TeamViewResponse:
    return TeamViewResponse(
        team_id=team.id,
        user_id=team.user_id,
        season=team.season,
        round=team.round,
        drivers=team.drivers,
        constructors=team.constructors,
        boost_driver_id=team.boost_driver_id,
        chip=team.chip_used,
        budget_used=team.budget_used,
    )
