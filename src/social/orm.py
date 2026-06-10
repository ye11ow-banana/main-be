from __future__ import annotations

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base, created_at, updated_at, uuidpk
from social.models import TeamStatus

if TYPE_CHECKING:
    from auth.orm import User  # noqa: F401


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuidpk]

    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    addressee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[StrEnum] = mapped_column(
        String, default=TeamStatus.PENDING, nullable=False
    )

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    requester = relationship(
        "User",
        foreign_keys="Team.requester_id",
        back_populates="sent_team_requests",
    )

    addressee = relationship(
        "User",
        foreign_keys="Team.addressee_id",
        back_populates="received_team_requests",
    )

Team.__table_args__ = (
    Index(
        "uq_team_unordered_pair",
        func.least(Team.requester_id, Team.addressee_id),
        func.greatest(Team.requester_id, Team.addressee_id),
        unique=True,
    ),
)