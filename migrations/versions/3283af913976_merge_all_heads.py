"""merge all heads

Revision ID: 3283af913976
Revises: d8d3b50de011, fa980e857579
Create Date: 2026-05-29 13:06:20.289715

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "3283af913976"
down_revision: Union[str, Sequence[str], None] = ("d8d3b50de011", "af99dc1e7da9")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
