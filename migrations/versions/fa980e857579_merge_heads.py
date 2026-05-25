"""merge heads

Revision ID: fa980e857579
Revises: 265ea30783ec, af99dc1e7da9
Create Date: 2026-05-22 13:10:57.365410

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "fa980e857579"
down_revision: Union[str, Sequence[str], None] = ("265ea30783ec", "af99dc1e7da9")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
