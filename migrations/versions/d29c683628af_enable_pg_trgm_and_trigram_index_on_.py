"""enable pg_trgm and trigram index on products.name

Revision ID: d29c683628af
Revises: 382d5b26955c
Create Date: 2026-01-04 19:07:22.328823

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d29c683628af"
down_revision: Union[str, Sequence[str], None] = "382d5b26955c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_products_name_trgm
        ON products
        USING gin (lower(name) gin_trgm_ops);
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_products_name_trgm;")
    op.execute("DROP EXTENSION IF EXISTS fuzzystrmatch;")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm;")
