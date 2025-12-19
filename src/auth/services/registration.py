from uuid import UUID

from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

from auth.exceptions import RegistrationException, WrongEmailVerificationCodeException
from auth.models import UserInCreateDTO, UserInfoDTO
from unitofwork import IUnitOfWork


class RegistrationService:
    def __init__(self, uow: IUnitOfWork):
        self._uow: IUnitOfWork = uow
        self._pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    async def register_user(self, user: UserInCreateDTO) -> UserInfoDTO:
        hashed_password = await self._hash_password(user.password)
        try:
            async with self._uow:
                new_user = await self._create_user(
                    user.username, str(user.email), hashed_password
                )
                await self._uow.commit()
        except IntegrityError:
            raise RegistrationException(
                "User with this username or email already exists"
            )
        return new_user

    async def apply_code(self, code: int, user_id: UUID) -> None:
        async with self._uow:
            verification_code = await self._uow.verification_codes.get_by_user_id(
                user_id
            )
            if (
                verification_code is None
                or verification_code.code != code
                or verification_code.is_expired()
            ):
                raise WrongEmailVerificationCodeException(code)
            await self._uow.users.verify_user(user_id)
            await self._uow.verification_codes.remove(id=verification_code.id)
            await self._uow.commit()

    async def _create_user(
        self, username: str, email: str, password: str
    ) -> UserInfoDTO:
        return await self._uow.users.add(
            username=username, email=email, hashed_password=password
        )

    async def _hash_password(self, plain_password: str) -> str:
        return self._pwd_context.hash(plain_password)
