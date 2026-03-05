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


class SimulationPredictionsResponse(BaseModel):
    run_id: str
    season: int
    round: int
    model_version: str
    predictions: list[PredictionRow]


class OptimizeRequest(BaseModel):
    season: int = 2026
    round: int
    budget_millions: float = 100.0
    risk_mode: RiskMode = "max_ev"
    chip: ChipName | None = None
    used_chips: list[ChipName] = Field(default_factory=list)


class LineupRecommendation(BaseModel):
    drivers: list[int]
    constructors: list[int]
    projected_points: float
    budget_used: float
    risk_score: float
    explanation: str


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
