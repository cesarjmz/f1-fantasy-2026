from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FantasyTeam(Base):
    __tablename__ = "fantasy_team"
    __table_args__ = (
        UniqueConstraint("user_id", "season", "round", name="uq_team_user_round"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    season: Mapped[int] = mapped_column(Integer, index=True)
    round: Mapped[int] = mapped_column(Integer, index=True)
    drivers: Mapped[list[int]] = mapped_column(JSON)
    constructors: Mapped[list[int]] = mapped_column(JSON)
    boost_driver_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chip_used: Mapped[str | None] = mapped_column(String(32), nullable=True)
    budget_used: Mapped[float] = mapped_column(Float)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class FantasyTransfer(Base):
    __tablename__ = "fantasy_transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    season: Mapped[int] = mapped_column(Integer, index=True)
    round: Mapped[int] = mapped_column(Integer, index=True)
    out_assets: Mapped[list[int]] = mapped_column(JSON)
    in_assets: Mapped[list[int]] = mapped_column(JSON)
    transfer_count: Mapped[int] = mapped_column(Integer)
    penalty_points: Mapped[int] = mapped_column(Integer)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class FantasyChipUsage(Base):
    __tablename__ = "fantasy_chip_usage"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "season", "chip_name", name="uq_chip_once_per_season"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    season: Mapped[int] = mapped_column(Integer, index=True)
    chip_name: Mapped[str] = mapped_column(String(32), index=True)
    round: Mapped[int] = mapped_column(Integer, index=True)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class PointsLedgerEntry(Base):
    __tablename__ = "points_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    season: Mapped[int] = mapped_column(Integer, index=True)
    round: Mapped[int] = mapped_column(Integer, index=True)
    team_id: Mapped[int] = mapped_column(Integer, index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    points: Mapped[float] = mapped_column(Float)
    meta_json: Mapped[dict] = mapped_column(JSON, default={})
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
