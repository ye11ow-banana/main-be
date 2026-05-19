from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base, created_at, updated_at, uuidpk

if TYPE_CHECKING:
    from app.orm import App
    from auth.orm import User


class Setting(Base):
    __tablename__ = "settings"
    __table_args__ = (
        UniqueConstraint("app_id", "user_id", name="uq_settings_app_id_user_id"),
    )

    id: Mapped[uuidpk]
    app_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("apps.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    add_day_notes: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default=text("true")
    )
    ai_creates_products: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default=text("true")
    )
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    app: Mapped["App"] = relationship("App", back_populates="settings")
    user: Mapped["User"] = relationship("User", back_populates="settings")
