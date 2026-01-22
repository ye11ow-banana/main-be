from auth.models import UserInfoDTO
from unitofwork import IUnitOfWork


class UserService:
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow

    async def get_users(self) -> list[UserInfoDTO]:
        async with self._uow:
            users = await self._uow.users.get_all_verified()
            return [UserInfoDTO.model_validate(user) for user in users]
