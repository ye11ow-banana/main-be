"""Backfill settings for existing users

Revision ID: c4a7d8e9f012
Revises: b8d9a6f2c1e4
Create Date: 2026-05-19 00:00:01.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4a7d8e9f012"
down_revision: Union[str, Sequence[str], None] = "b8d9a6f2c1e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        INSERT INTO settings (app_id, user_id)
        SELECT apps.id, users.id
        FROM apps
        CROSS JOIN users
        WHERE apps.is_active IS TRUE
        ON CONFLICT ON CONSTRAINT uq_settings_app_id_user_id DO NOTHING;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    pass
