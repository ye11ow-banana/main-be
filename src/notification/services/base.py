import random
from abc import ABC
from uuid import UUID

from notification.models import MergeVerificationCode
from unitofwork import IUnitOfWork


class INotificationService(ABC):
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow

    async def create_verification_code(self, user_id: UUID) -> int:
        code = self._generate_verification_code()
        merge_code = MergeVerificationCode(code=code, user_id=user_id)
        async with self._uow:
            await self._uow.verification_codes.add_or_update(merge_code)
            await self._uow.commit()
        return code

    @staticmethod
    def _generate_verification_code() -> int:
        return random.randint(100000, 999999)
