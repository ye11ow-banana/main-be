from app.models import AppDTO
from unitofwork import IUnitOfWork


class AppService:
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow

    async def get_active(self) -> list[AppDTO]:
        async with self._uow:
            return await self._uow.apps.get_active()
