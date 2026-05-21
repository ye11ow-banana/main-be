"""recalculate trends

Revision ID: 265ea30783ec
Revises: 26e004ae4c79
Create Date: 2026-04-14 16:20:27.481315

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "265ea30783ec"
down_revision: Union[str, Sequence[str], None] = "c4a7d8e9f012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE days d
        SET trend = sub.trend
        FROM (
            SELECT
                id,
                body_weight - LAG(body_weight) OVER (
                    PARTITION BY user_id
                    ORDER BY created_at
                ) AS trend
            FROM days
            WHERE body_weight IS NOT NULL
        ) AS sub
        WHERE d.id = sub.id;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
