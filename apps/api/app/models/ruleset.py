from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FantasyRulesetVersion(Base):
    __tablename__ = "fantasy_ruleset_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    season: Mapped[int] = mapped_column(Integer, index=True)
    rules_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True
    )
    rules_json: Mapped[dict] = mapped_column(JSON)
