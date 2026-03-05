from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MeetingRound(Base):
    __tablename__ = "meeting_rounds"
    __table_args__ = (UniqueConstraint("season", "round", name="uq_meeting_round"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    season: Mapped[int] = mapped_column(Integer, index=True)
    round: Mapped[int] = mapped_column(Integer, index=True)
    grand_prix_name: Mapped[str] = mapped_column(String(128))
    start_date: Mapped[str] = mapped_column(String(16))
    is_sprint: Mapped[bool] = mapped_column(Boolean, default=False)
    lock_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FantasyAssetPrice(Base):
    __tablename__ = "fantasy_asset_prices"
    __table_args__ = (
        UniqueConstraint(
            "season", "round", "asset_id", name="uq_asset_price_per_round"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    season: Mapped[int] = mapped_column(Integer, index=True)
    round: Mapped[int] = mapped_column(Integer, index=True)
    asset_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(128))
    asset_type: Mapped[str] = mapped_column(String(32), index=True)
    team: Mapped[str | None] = mapped_column(String(128), nullable=True)
    price_millions: Mapped[float] = mapped_column(Float)
