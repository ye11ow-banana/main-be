import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base, uuidpk

if TYPE_CHECKING:
    from auth.orm import User


def expires_in_10_minutes() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=10)


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id: Mapped[uuidpk]
    code: Mapped[int] = mapped_column(nullable=False)
    expired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=expires_in_10_minutes
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="verification_code")
