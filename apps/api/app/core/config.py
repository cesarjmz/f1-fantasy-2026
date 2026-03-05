import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "F1 Fantasy API"
    season: int = 2026
    max_teams_per_user: int = 3
    starting_budget_millions: float = 100.0
    free_transfers_per_round: int = 2
    transfer_penalty_points: int = 10
    default_simulation_count: int = 10_000
    model_version: str = "seeded-v0"
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))
    data_cut_label: str = os.getenv("DATA_CUT_LABEL", "seeded-2026-03-05")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./f1_fantasy.db")


settings = Settings()
