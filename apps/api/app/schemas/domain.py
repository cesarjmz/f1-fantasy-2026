from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


AssetType = Literal["driver", "constructor"]
ChipName = Literal[
    "limitless",
    "wildcard",
    "triple_boost",
    "no_negative",
    "final_fix",
    "autopilot",
]
RiskMode = Literal["max_ev", "max_upside", "min_downside", "value_growth", "chip_aware"]
PredictionSortField = Literal[
    "mean", "median", "p10", "p90", "prob_negative", "entity_name"
]
SortOrder = Literal["asc", "desc"]


class RoundInfo(BaseModel):
    season: int
    round: int
    grand_prix_name: str
    start_date: str
    is_sprint: bool
    lock_at: datetime


class Asset(BaseModel):
    id: int
    name: str
    asset_type: AssetType
    team: str | None = None
    price_millions: float


class PriceSnapshot(BaseModel):
    season: int
    round: int
    assets: list[Asset]


class SimulationRunRequest(BaseModel):
    season: int = 2026
    round: int
    n_sims: int = Field(default=10_000, ge=1)


class DistributionSummary(BaseModel):
    mean: float
    median: float
    p10: float
    p90: float
    prob_negative: float


class PredictionRow(BaseModel):
    entity_id: int
    entity_name: str
    entity_type: AssetType
    summary: DistributionSummary


class SimulationRunResponse(BaseModel):
    run_id: str
    season: int
    round: int
    n_sims: int


class SimulationSummaryEntity(BaseModel):
    entity_id: int
    entity_name: str
    value: float


class SimulationRunSummary(BaseModel):
    entity_count: int
    top_mean: SimulationSummaryEntity
    highest_upside: SimulationSummaryEntity
    highest_negative_risk: SimulationSummaryEntity


class SimulationPredictionsMeta(BaseModel):
    total: int
    limit: int
    offset: int
    returned: int
    has_more: bool
    next_offset: int | None
    sort_by: PredictionSortField
    order: SortOrder


class SimulationPredictionsResponse(BaseModel):
    run_id: str
    season: int
    round: int
    n_sims: int
    model_version: str
    summary: SimulationRunSummary
    meta: SimulationPredictionsMeta
    predictions: list[PredictionRow]


class SimulationSummaryResponse(BaseModel):
    run_id: str
    season: int
    round: int
    n_sims: int
    model_version: str
    summary: SimulationRunSummary


class OptimizeRequest(BaseModel):
    season: int = 2026
    round: int
    budget_millions: float = 100.0
    risk_mode: RiskMode = "max_ev"
    chip: ChipName | None = None
    used_chips: list[ChipName] = Field(default_factory=list)


class ChipRecommendationFactor(BaseModel):
    chip: ChipName
    projected_bonus: float
    reasoning: str


class ConstraintsDiagnostics(BaseModel):
    budget_cap: float
    budget_used: float
    budget_margin: float
    chip_active: ChipName | None
    chips_already_used: list[ChipName]
    chip_eligible: bool
    free_transfers_assumed: int


class LineupRecommendation(BaseModel):
    drivers: list[int]
    constructors: list[int]
    projected_points: float
    budget_used: float
    risk_score: float
    explanation: str
    rank_reason: str
    chip_factors: list[ChipRecommendationFactor]
    constraints: ConstraintsDiagnostics


class OptimizeResponse(BaseModel):
    season: int
    round: int
    risk_mode: RiskMode
    chip: ChipName | None
    recommendations: list[LineupRecommendation]


class BriefingResponse(BaseModel):
    season: int
    round: int
    is_sprint: bool
    lock_at: datetime
    checklist: list[str]
    alerts: list[str]


class AuditBreakdownItem(BaseModel):
    category: str
    points: float


class AuditResponse(BaseModel):
    season: int
    round: int
    lineup_name: str
    total_points: float
    breakdown: list[AuditBreakdownItem]


class TeamSubmissionRequest(BaseModel):
    user_id: str = "local-user"
    season: int = 2026
    round: int
    drivers: list[int]
    constructors: list[int]
    boost_driver_id: int | None = None
    chip: ChipName | None = None


class TeamSubmissionResponse(BaseModel):
    team_id: int
    season: int
    round: int
    transfer_count: int
    transfer_penalty_points: int
    chip: ChipName | None


class TeamViewResponse(BaseModel):
    team_id: int
    user_id: str
    season: int
    round: int
    drivers: list[int]
    constructors: list[int]
    boost_driver_id: int | None
    chip: ChipName | None
    budget_used: float


class PageMeta(BaseModel):
    total: int
    has_more: bool
    next_offset: int | None


class TransferHistoryItem(BaseModel):
    round: int
    transfer_count: int
    penalty_points: int
    in_assets: list[int]
    out_assets: list[int]
    computed_at: datetime


class TransferHistoryResponse(PageMeta):
    user_id: str
    season: int
    items: list[TransferHistoryItem]


class ChipUsageItem(BaseModel):
    chip: ChipName
    round: int
    used_at: datetime


class ChipUsageResponse(PageMeta):
    user_id: str
    season: int
    items: list[ChipUsageItem]


class LineupHistoryItem(BaseModel):
    team_id: int
    round: int
    drivers: list[int]
    constructors: list[int]
    boost_driver_id: int | None
    chip: ChipName | None
    budget_used: float
    submitted_at: datetime


class LineupHistoryResponse(PageMeta):
    user_id: str
    season: int
    items: list[LineupHistoryItem]


class RoundLifecycleItem(BaseModel):
    round: int
    team_id: int
    chip: ChipName | None
    budget_used: float
    transfer_count: int
    transfer_penalty_points: int
    audited_points: float | None
    submitted_at: datetime


class RoundLifecycleResponse(PageMeta):
    user_id: str
    season: int
    items: list[RoundLifecycleItem]


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict | list | str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
