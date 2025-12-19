from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base, created_at, uuidpk

if TYPE_CHECKING:
    from notification.orm import VerificationCode


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuidpk]
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(length=1024), nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[created_at]

    verification_code: Mapped["VerificationCode"] = relationship(
        "VerificationCode", back_populates="user"
    )
