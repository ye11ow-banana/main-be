"""Change settings table to be 121 with users table

Revision ID: d8d3b50de011
Revises: 265ea30783ec
Create Date: 2026-05-21 15:01:28.540081

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d8d3b50de011"
down_revision: Union[str, Sequence[str], None] = "265ea30783ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        DELETE FROM settings
        USING (
            SELECT ctid
            FROM (
                SELECT
                    settings.ctid,
                    row_number() OVER (
                        PARTITION BY settings.user_id
                        ORDER BY
                            CASE
                                WHEN lower(apps.name) LIKE '%calorie%' THEN 0
                                ELSE 1
                            END,
                            settings.created_at,
                            settings.id
                    ) AS row_num
                FROM settings
                LEFT JOIN apps ON apps.id = settings.app_id
            ) AS ranked_settings
            WHERE ranked_settings.row_num > 1
        ) AS duplicate_settings
        WHERE settings.ctid = duplicate_settings.ctid;
    """)

    op.drop_index(op.f("ix_settings_id"), table_name="settings")
    op.drop_constraint("uq_settings_app_id_user_id", "settings", type_="unique")
    op.drop_constraint("settings_app_id_fkey", "settings", type_="foreignkey")
    op.drop_constraint("settings_user_id_fkey", "settings", type_="foreignkey")
    op.drop_constraint("settings_pkey", "settings", type_="primary")
    op.drop_column("settings", "id")
    op.drop_column("settings", "app_id")
    op.rename_table("settings", "calorie_settings")
    op.create_primary_key("calorie_settings_pkey", "calorie_settings", ["user_id"])
    op.create_foreign_key(
        "calorie_settings_user_id_fkey",
        "calorie_settings",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "calorie_settings_user_id_fkey", "calorie_settings", type_="foreignkey"
    )
    op.drop_constraint("calorie_settings_pkey", "calorie_settings", type_="primary")
    op.rename_table("calorie_settings", "settings")
    op.add_column(
        "settings",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
    )
    op.add_column("settings", sa.Column("app_id", sa.UUID(), nullable=True))
    op.execute("""
        UPDATE settings
        SET app_id = app_choice.id
        FROM (
            SELECT id
            FROM apps
            ORDER BY
                CASE WHEN is_active IS TRUE THEN 0 ELSE 1 END,
                CASE WHEN lower(name) LIKE '%calorie%' THEN 0 ELSE 1 END,
                created_at,
                id
            LIMIT 1
        ) AS app_choice;
    """)
    op.alter_column("settings", "app_id", existing_type=sa.UUID(), nullable=False)
    op.execute("""
        INSERT INTO settings (
            id,
            app_id,
            user_id,
            add_day_notes,
            ai_creates_products,
            created_at,
            updated_at
        )
        SELECT
            gen_random_uuid(),
            apps.id,
            settings.user_id,
            settings.add_day_notes,
            settings.ai_creates_products,
            settings.created_at,
            settings.updated_at
        FROM settings
        JOIN apps ON apps.id <> settings.app_id
        WHERE apps.is_active IS TRUE;
    """)
    op.create_primary_key("settings_pkey", "settings", ["id"])
    op.create_foreign_key(
        "settings_app_id_fkey",
        "settings",
        "apps",
        ["app_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "settings_user_id_fkey",
        "settings",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_settings_app_id_user_id", "settings", ["app_id", "user_id"]
    )
    op.create_index(op.f("ix_settings_id"), "settings", ["id"], unique=False)
