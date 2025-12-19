from typing import Sequence
from uuid import UUID

from auth import orm
from auth.models import UserInDBDTO, UserInfoDTO
from repository import SQLAlchemyRepository


class UserRepository(SQLAlchemyRepository):
    model = orm.User

    async def get(
        self, /, returns: Sequence[str] | None = None, **data: str | int
    ) -> UserInDBDTO:
        user = await super().get(returns=returns, **data)
        return UserInDBDTO.model_validate(user)

    async def add(self, **insert_data) -> UserInfoDTO:
        created_user = await super().add(**insert_data)
        return UserInfoDTO.model_validate(created_user)

    async def verify_user(self, user_id: UUID) -> None:
        await self.update({"id": user_id}, is_verified=True)
