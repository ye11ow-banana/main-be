from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

from auth.exceptions import RegistrationException
from auth.models import UserInCreateDTO, UserInfoDTO
from unitofwork import IUnitOfWork


class RegistrationService:
    def __init__(self, uow: IUnitOfWork):
        self._uof: IUnitOfWork = uow
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def register_user(self, user: UserInCreateDTO) -> UserInfoDTO:
        hashed_password = await self._hash_password(user.password)
        try:
            async with self._uof:
                new_user = await self._create_user(
                    user.username, str(user.email), hashed_password
                )
                await self._uof.commit()
        except IntegrityError:
            raise RegistrationException(
                "User with this username or email already exists"
            )
        return new_user

    async def _create_user(
        self, username: str, email: str, password: str
    ) -> UserInfoDTO:
        return await self._uof.users.add(
            username=username, email=email, hashed_password=password
        )

    async def _hash_password(self, plain_password: str) -> str:
        return self._pwd_context.hash(plain_password)
