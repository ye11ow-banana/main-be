from typing import Sequence
from uuid import UUID

from sqlalchemy import exists, or_, select

from auth import orm
from auth.models import UserInDBDTO, UserInfoDTO
from repository import SQLAlchemyRepository


class UserRepository(SQLAlchemyRepository):
    model = orm.User

    async def get(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> UserInDBDTO:
        user = await super().get(returns=returns, **data)
        return UserInDBDTO.model_validate(user)

    async def add(self, **insert_data) -> UserInfoDTO:
        created_user = await super().add(**insert_data)
        return UserInfoDTO.model_validate(created_user)

    async def verify_user(self, user_id: UUID) -> None:
        await self.update({"id": user_id}, is_verified=True)

    async def get_by_username_or_email(
        self, username_or_email: str
    ) -> UserInDBDTO | None:
        stmt = select(self.model).where(
            or_(
                self.model.username == username_or_email,
                self.model.email == username_or_email,
            )
        )
        user = (await self._session.execute(stmt)).scalar_one_or_none()

        if not user:
            return None

        return UserInDBDTO.model_validate(user)

    async def exists(self, user_id: UUID) -> bool:
        stmt = select(exists().where(self.model.id == user_id))
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_all_verified(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> list[UserInDBDTO]:
        users = await self.get_all(returns=returns, **data | {"is_verified": True})
        return [UserInDBDTO.model_validate(user) for user in users]
