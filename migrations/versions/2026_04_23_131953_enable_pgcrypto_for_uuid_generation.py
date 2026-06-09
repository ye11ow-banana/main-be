"""enable pgcrypto for uuid generation

Revision ID: 3112835c5adc
Revises: 26e004ae4c79
Create Date: 2026-04-23 13:19:53.769070

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3112835c5adc"
down_revision: Union[str, Sequence[str], None] = "26e004ae4c79"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN id SET DEFAULT gen_random_uuid();
    """)

    op.execute("""
        ALTER TABLE days
        ALTER COLUMN id SET DEFAULT gen_random_uuid();
    """)

    op.execute("""
        ALTER TABLE products
        ALTER COLUMN id SET DEFAULT gen_random_uuid();
    """)

    op.execute("""
        ALTER TABLE apps
        ALTER COLUMN id SET DEFAULT gen_random_uuid();
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE users
        ALTER COLUMN id DROP DEFAULT;
    """)

    op.execute("""
        ALTER TABLE days
        ALTER COLUMN id DROP DEFAULT;
    """)

    op.execute("""
        ALTER TABLE products
        ALTER COLUMN id DROP DEFAULT;
    """)

    op.execute("""
        ALTER TABLE apps
        ALTER COLUMN id DROP DEFAULT;
    """)
