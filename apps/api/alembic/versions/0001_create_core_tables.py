"""create core tables

Revision ID: 0001_create_core_tables
Revises:
Create Date: 2026-03-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_create_core_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fantasy_team",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("drivers", sa.JSON(), nullable=False),
        sa.Column("constructors", sa.JSON(), nullable=False),
        sa.Column("boost_driver_id", sa.Integer(), nullable=True),
        sa.Column("chip_used", sa.String(length=32), nullable=True),
        sa.Column("budget_used", sa.Float(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "season", "round", name="uq_team_user_round"),
    )
    op.create_index(
        "ix_fantasy_team_user_id", "fantasy_team", ["user_id"], unique=False
    )
    op.create_index("ix_fantasy_team_season", "fantasy_team", ["season"], unique=False)
    op.create_index("ix_fantasy_team_round", "fantasy_team", ["round"], unique=False)
    op.create_index(
        "ix_fantasy_team_submitted_at", "fantasy_team", ["submitted_at"], unique=False
    )

    op.create_table(
        "fantasy_transfers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("out_assets", sa.JSON(), nullable=False),
        sa.Column("in_assets", sa.JSON(), nullable=False),
        sa.Column("transfer_count", sa.Integer(), nullable=False),
        sa.Column("penalty_points", sa.Integer(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_fantasy_transfers_user_id", "fantasy_transfers", ["user_id"], unique=False
    )
    op.create_index(
        "ix_fantasy_transfers_season", "fantasy_transfers", ["season"], unique=False
    )
    op.create_index(
        "ix_fantasy_transfers_round", "fantasy_transfers", ["round"], unique=False
    )
    op.create_index(
        "ix_fantasy_transfers_computed_at",
        "fantasy_transfers",
        ["computed_at"],
        unique=False,
    )

    op.create_table(
        "fantasy_chip_usage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("chip_name", sa.String(length=32), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "season", "chip_name", name="uq_chip_once_per_season"
        ),
    )
    op.create_index(
        "ix_fantasy_chip_usage_user_id", "fantasy_chip_usage", ["user_id"], unique=False
    )
    op.create_index(
        "ix_fantasy_chip_usage_season", "fantasy_chip_usage", ["season"], unique=False
    )
    op.create_index(
        "ix_fantasy_chip_usage_chip_name",
        "fantasy_chip_usage",
        ["chip_name"],
        unique=False,
    )
    op.create_index(
        "ix_fantasy_chip_usage_round", "fantasy_chip_usage", ["round"], unique=False
    )
    op.create_index(
        "ix_fantasy_chip_usage_used_at", "fantasy_chip_usage", ["used_at"], unique=False
    )

    op.create_table(
        "points_ledger",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("points", sa.Float(), nullable=False),
        sa.Column("meta_json", sa.JSON(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_points_ledger_user_id", "points_ledger", ["user_id"], unique=False
    )
    op.create_index(
        "ix_points_ledger_season", "points_ledger", ["season"], unique=False
    )
    op.create_index("ix_points_ledger_round", "points_ledger", ["round"], unique=False)
    op.create_index(
        "ix_points_ledger_team_id", "points_ledger", ["team_id"], unique=False
    )
    op.create_index(
        "ix_points_ledger_category", "points_ledger", ["category"], unique=False
    )
    op.create_index(
        "ix_points_ledger_computed_at", "points_ledger", ["computed_at"], unique=False
    )

    op.create_table(
        "meeting_rounds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("grand_prix_name", sa.String(length=128), nullable=False),
        sa.Column("start_date", sa.String(length=16), nullable=False),
        sa.Column("is_sprint", sa.Boolean(), nullable=False),
        sa.Column("lock_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("season", "round", name="uq_meeting_round"),
    )
    op.create_index(
        "ix_meeting_rounds_season", "meeting_rounds", ["season"], unique=False
    )
    op.create_index(
        "ix_meeting_rounds_round", "meeting_rounds", ["round"], unique=False
    )

    op.create_table(
        "fantasy_asset_prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("team", sa.String(length=128), nullable=True),
        sa.Column("price_millions", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "season", "round", "asset_id", name="uq_asset_price_per_round"
        ),
    )
    op.create_index(
        "ix_fantasy_asset_prices_season",
        "fantasy_asset_prices",
        ["season"],
        unique=False,
    )
    op.create_index(
        "ix_fantasy_asset_prices_round", "fantasy_asset_prices", ["round"], unique=False
    )
    op.create_index(
        "ix_fantasy_asset_prices_asset_id",
        "fantasy_asset_prices",
        ["asset_id"],
        unique=False,
    )
    op.create_index(
        "ix_fantasy_asset_prices_asset_type",
        "fantasy_asset_prices",
        ["asset_type"],
        unique=False,
    )

    op.create_table(
        "fantasy_ruleset_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("rules_hash", sa.String(length=128), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rules_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_fantasy_ruleset_versions_rules_hash",
        "fantasy_ruleset_versions",
        ["rules_hash"],
        unique=True,
    )
    op.create_index(
        "ix_fantasy_ruleset_versions_season",
        "fantasy_ruleset_versions",
        ["season"],
        unique=False,
    )
    op.create_index(
        "ix_fantasy_ruleset_versions_effective_from",
        "fantasy_ruleset_versions",
        ["effective_from"],
        unique=False,
    )

    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("n_sims", sa.Integer(), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("data_cutoff", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_simulation_runs_run_id", "simulation_runs", ["run_id"], unique=True
    )
    op.create_index(
        "ix_simulation_runs_season", "simulation_runs", ["season"], unique=False
    )
    op.create_index(
        "ix_simulation_runs_round", "simulation_runs", ["round"], unique=False
    )

    op.create_table(
        "simulation_predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("simulation_run_id", sa.Integer(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("entity_name", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("mean", sa.Float(), nullable=False),
        sa.Column("median", sa.Float(), nullable=False),
        sa.Column("p10", sa.Float(), nullable=False),
        sa.Column("p90", sa.Float(), nullable=False),
        sa.Column("prob_negative", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["simulation_run_id"], ["simulation_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "simulation_run_id", "entity_id", name="uq_prediction_run_entity"
        ),
    )
    op.create_index(
        "ix_simulation_predictions_simulation_run_id",
        "simulation_predictions",
        ["simulation_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_simulation_predictions_entity_id",
        "simulation_predictions",
        ["entity_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_points_ledger_computed_at", table_name="points_ledger")
    op.drop_index("ix_points_ledger_category", table_name="points_ledger")
    op.drop_index("ix_points_ledger_team_id", table_name="points_ledger")
    op.drop_index("ix_points_ledger_round", table_name="points_ledger")
    op.drop_index("ix_points_ledger_season", table_name="points_ledger")
    op.drop_index("ix_points_ledger_user_id", table_name="points_ledger")
    op.drop_table("points_ledger")

    op.drop_index("ix_fantasy_chip_usage_used_at", table_name="fantasy_chip_usage")
    op.drop_index("ix_fantasy_chip_usage_round", table_name="fantasy_chip_usage")
    op.drop_index("ix_fantasy_chip_usage_chip_name", table_name="fantasy_chip_usage")
    op.drop_index("ix_fantasy_chip_usage_season", table_name="fantasy_chip_usage")
    op.drop_index("ix_fantasy_chip_usage_user_id", table_name="fantasy_chip_usage")
    op.drop_table("fantasy_chip_usage")

    op.drop_index("ix_fantasy_transfers_computed_at", table_name="fantasy_transfers")
    op.drop_index("ix_fantasy_transfers_round", table_name="fantasy_transfers")
    op.drop_index("ix_fantasy_transfers_season", table_name="fantasy_transfers")
    op.drop_index("ix_fantasy_transfers_user_id", table_name="fantasy_transfers")
    op.drop_table("fantasy_transfers")

    op.drop_index("ix_fantasy_team_submitted_at", table_name="fantasy_team")
    op.drop_index("ix_fantasy_team_round", table_name="fantasy_team")
    op.drop_index("ix_fantasy_team_season", table_name="fantasy_team")
    op.drop_index("ix_fantasy_team_user_id", table_name="fantasy_team")
    op.drop_table("fantasy_team")

    op.drop_index(
        "ix_fantasy_asset_prices_asset_type", table_name="fantasy_asset_prices"
    )
    op.drop_index("ix_fantasy_asset_prices_asset_id", table_name="fantasy_asset_prices")
    op.drop_index("ix_fantasy_asset_prices_round", table_name="fantasy_asset_prices")
    op.drop_index("ix_fantasy_asset_prices_season", table_name="fantasy_asset_prices")
    op.drop_table("fantasy_asset_prices")

    op.drop_index("ix_meeting_rounds_round", table_name="meeting_rounds")
    op.drop_index("ix_meeting_rounds_season", table_name="meeting_rounds")
    op.drop_table("meeting_rounds")

    op.drop_index(
        "ix_simulation_predictions_entity_id", table_name="simulation_predictions"
    )
    op.drop_index(
        "ix_simulation_predictions_simulation_run_id",
        table_name="simulation_predictions",
    )
    op.drop_table("simulation_predictions")

    op.drop_index("ix_simulation_runs_round", table_name="simulation_runs")
    op.drop_index("ix_simulation_runs_season", table_name="simulation_runs")
    op.drop_index("ix_simulation_runs_run_id", table_name="simulation_runs")
    op.drop_table("simulation_runs")

    op.drop_index(
        "ix_fantasy_ruleset_versions_effective_from",
        table_name="fantasy_ruleset_versions",
    )
    op.drop_index(
        "ix_fantasy_ruleset_versions_season", table_name="fantasy_ruleset_versions"
    )
    op.drop_index(
        "ix_fantasy_ruleset_versions_rules_hash", table_name="fantasy_ruleset_versions"
    )
    op.drop_table("fantasy_ruleset_versions")
