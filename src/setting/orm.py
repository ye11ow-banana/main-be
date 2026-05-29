from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base, created_at, updated_at

if TYPE_CHECKING:
    from auth.orm import User


class CalorieSetting(Base):
    __tablename__ = "calorie_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    add_day_notes: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default=text("true")
    )
    ai_creates_products: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default=text("true")
    )
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    user: Mapped["User"] = relationship("User", back_populates="calorie_setting")
