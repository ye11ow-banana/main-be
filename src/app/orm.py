from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base, created_at, uuidpk

if TYPE_CHECKING:
    from setting.orm import Setting


class App(Base):
    __tablename__ = "apps"

    id: Mapped[uuidpk]
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    image: Mapped[str] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[created_at]

    settings: Mapped[list["Setting"]] = relationship(
        "Setting", back_populates="app", cascade="all, delete-orphan"
    )
