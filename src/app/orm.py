from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column

from database import Base, created_at, uuidpk


class App(Base):
    __tablename__ = "apps"

    id: Mapped[uuidpk]
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    image: Mapped[str] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[created_at]
