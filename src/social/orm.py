from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base, created_at, uuidpk
from social.models import TeamStatus

if TYPE_CHECKING:
    pass


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuidpk]

    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    addressee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[str] = mapped_column(
        String, default=TeamStatus.PENDING, nullable=False
    )

    created_at: Mapped[created_at]

    requester = relationship(
        "User",
        foreign_keys=[requester_id],
        back_populates="sent_team_requests",
    )

    addressee = relationship(
        "User",
        foreign_keys=[addressee_id],
        back_populates="received_team_requests",
    )
