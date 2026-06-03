"""Add teams table

Revision ID: 23c79ef8479d
Revises: d8d3b50de011
Create Date: 2026-06-03 10:55:57.510545

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "23c79ef8479d"
down_revision: Union[str, Sequence[str], None] = "d8d3b50de011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("requester_id", sa.UUID(), nullable=False),
        sa.Column("addressee_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["requester_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["addressee_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
    )

    op.create_index("ix_teams_id", "teams", ["id"])

    op.create_index(
        "uq_teams_user_pair",
        "teams",
        [
            sa.text("LEAST(requester_id, addressee_id)"),
            sa.text("GREATEST(requester_id, addressee_id)"),
        ],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_teams_user_pair", table_name="teams")
    op.drop_index("ix_teams_id", table_name="teams")
    op.drop_table("teams")
