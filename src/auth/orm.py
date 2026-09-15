from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base, created_at, uuidpk

if TYPE_CHECKING:
    from calorie.orm import Day
    from notification.orm import VerificationCode
    from setting.orm import CalorieSetting
    from social.orm import Team


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuidpk]
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(length=1024), nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[created_at]

    sent_team_requests: Mapped[list["Team"]] = relationship(
        "Team",
        foreign_keys="Team.requester_id",
        back_populates="requester",
        cascade="all, delete-orphan",
    )

    received_team_requests: Mapped[list["Team"]] = relationship(
        "Team",
        foreign_keys="Team.addressee_id",
        back_populates="addressee",
        cascade="all, delete-orphan",
    )

    verification_code: Mapped["VerificationCode"] = relationship(
        "VerificationCode", back_populates="user"
    )
    days: Mapped[list["Day"]] = relationship("Day", back_populates="user")
    calorie_setting: Mapped["CalorieSetting"] = relationship(
        "CalorieSetting", back_populates="user", cascade="all, delete-orphan"
    )
