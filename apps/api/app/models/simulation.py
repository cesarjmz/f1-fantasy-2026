from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class SimulationRun(Base, TimestampMixin):
    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    season: Mapped[int] = mapped_column(Integer, index=True)
    round: Mapped[int] = mapped_column(Integer, index=True)
    n_sims: Mapped[int] = mapped_column(Integer)
    model_version: Mapped[str] = mapped_column(String(64), default="seeded-v0")
    data_cutoff: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    predictions: Mapped[list[SimulationPrediction]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class SimulationPrediction(Base):
    __tablename__ = "simulation_predictions"
    __table_args__ = (
        UniqueConstraint(
            "simulation_run_id", "entity_id", name="uq_prediction_run_entity"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    simulation_run_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_runs.id"), index=True
    )
    entity_id: Mapped[int] = mapped_column(Integer, index=True)
    entity_name: Mapped[str] = mapped_column(String(128))
    entity_type: Mapped[str] = mapped_column(String(32))
    mean: Mapped[float] = mapped_column(Float)
    median: Mapped[float] = mapped_column(Float)
    p10: Mapped[float] = mapped_column(Float)
    p90: Mapped[float] = mapped_column(Float)
    prob_negative: Mapped[float] = mapped_column(Float)

    run: Mapped[SimulationRun] = relationship(back_populates="predictions")
