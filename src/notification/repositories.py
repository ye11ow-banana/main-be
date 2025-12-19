from typing import Sequence

from sqlalchemy.dialects.postgresql import insert

from notification import orm
from notification.models import (
    VerificationCodeInDBDTO,
    VerificationCodeDTO,
    MergeVerificationCode,
)
from notification.orm import expires_in_10_minutes
from repository import SQLAlchemyRepository


class VerificationCodeRepository(SQLAlchemyRepository):
    model = orm.VerificationCode

    async def get(
        self, /, returns: Sequence[str] | None = None, **data: str | int
    ) -> VerificationCodeInDBDTO:
        code = await super().get(returns=returns, **data)
        return VerificationCodeInDBDTO.model_validate(code)

    async def add(self, **insert_data) -> VerificationCodeDTO:
        created_code = await super().add(**insert_data)
        return VerificationCodeDTO.model_validate(created_code)

    async def add_or_update(self, obj: MergeVerificationCode) -> None:
        expired_at = expires_in_10_minutes()
        stmt = (
            insert(self.model)
            .values(user_id=obj.user_id, code=obj.code, expired_at=expired_at)
            .on_conflict_do_update(
                index_elements=[self.model.user_id],
                set_={"code": obj.code, "expired_at": expired_at},
            )
        )
        await self._session.execute(stmt)
