"""add rooms table

Revision ID: 202409121230
Revises: 202402071210
Create Date: 2024-09-12 12:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "202409121230"
down_revision: Union[str, None] = "202402071210"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("rooms"):
        op.create_table(
            "rooms",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("room_number", sa.String(length=6), nullable=False),
            sa.Column("title", sa.String(length=100), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=True),
            sa.Column("creator_id", sa.Integer(), nullable=True),
            sa.Column("janus_room_id", sa.String(length=64), nullable=True),
            sa.Column("max_participants", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.ForeignKeyConstraint(["creator_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("rooms")} if inspector.has_table("rooms") else set()
    if "ix_rooms_room_number" not in existing_indexes:
        op.create_index("ix_rooms_room_number", "rooms", ["room_number"], unique=True)
    if "ix_rooms_is_active" not in existing_indexes:
        op.create_index("ix_rooms_is_active", "rooms", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_rooms_is_active", table_name="rooms")
    op.drop_index("ix_rooms_room_number", table_name="rooms")
    op.drop_table("rooms")
