from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MergeVerificationCode(BaseModel):
    code: int
    user_id: UUID


class VerificationCodeDTO(MergeVerificationCode):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: int
    expired_at: datetime
    user_id: UUID


class VerificationCodeInDBDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    code: int | None = None
    expired_at: datetime | None = None
    user_id: UUID | None = None

    def to_user_info(self) -> VerificationCodeDTO:
        return VerificationCodeDTO(**self.model_dump())
