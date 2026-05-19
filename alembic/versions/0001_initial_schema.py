"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("hashed_password", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_points", sa.Integer(), nullable=True, default=0),
        sa.Column("lifetime_pnl_usd", sa.Float(), nullable=True, default=0.0),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "tables",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("sb_usd", sa.Float(), nullable=False),
        sa.Column("bb_usd", sa.Float(), nullable=False),
        sa.Column("ante_usd", sa.Float(), nullable=True, default=0.0),
        sa.Column("game_type", sa.String(10), nullable=True, default="cash"),
        sa.Column("max_players", sa.Integer(), nullable=True, default=6),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tables_id", "tables", ["id"])

    op.create_table(
        "game_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("table_id", sa.Integer(), sa.ForeignKey("tables.id"), nullable=False),
        sa.Column("start_stack_usd", sa.Float(), nullable=False),
        sa.Column("start_stack_bb", sa.Float(), nullable=False),
        sa.Column("current_stack_usd", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=True, default="active"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_game_sessions_id", "game_sessions", ["id"])

    op.create_table(
        "hands",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("game_sessions.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("played_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hero_position", sa.String(10), nullable=False),
        sa.Column("villain_position", sa.String(10), nullable=False),
        sa.Column("hero_cards", sa.String(20), nullable=False),
        sa.Column("board", sa.String(30), nullable=True, default=""),
        sa.Column("street", sa.String(10), nullable=False),
        sa.Column("pot_type", sa.String(5), nullable=False),
        sa.Column("hero_role", sa.String(10), nullable=False),
        sa.Column("preflop_spot", sa.String(10), nullable=False),
        sa.Column("pot_usd", sa.Float(), nullable=True),
        sa.Column("recommended_action", sa.String(20), nullable=False),
        sa.Column("recommended_size", sa.Float(), nullable=True),
        sa.Column("equity", sa.Float(), nullable=False),
        sa.Column("ev_best_bb", sa.Float(), nullable=False),
        sa.Column("ev_comps_json", sa.JSON(), nullable=False),
        sa.Column("mix_json", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("user_action", sa.String(20), nullable=False),
        sa.Column("stack_before_usd", sa.Float(), nullable=False),
        sa.Column("stack_after_usd", sa.Float(), nullable=False),
        sa.Column("net_usd", sa.Float(), nullable=False),
        sa.Column("net_bb", sa.Float(), nullable=False),
        sa.Column("aligned", sa.Boolean(), nullable=True, default=False),
        sa.Column("ev_loss_bb", sa.Float(), nullable=True, default=0.0),
        sa.Column("points_earned", sa.Integer(), nullable=True, default=0),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hands_id", "hands", ["id"])

    op.create_table(
        "rebuys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("game_sessions.id"), nullable=False),
        sa.Column("rebuy_usd", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("rebuys")
    op.drop_table("hands")
    op.drop_table("game_sessions")
    op.drop_table("tables")
    op.drop_table("users")
