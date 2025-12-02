from typing import Sequence

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
