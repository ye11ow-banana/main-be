from uuid import UUID

from calorie.models import TrendItem
from models import DateRangeDTO
from unitofwork import IUnitOfWork


class TrendService:
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow

    async def get_weight_trend(
        self, user_id: UUID, date_range: DateRangeDTO
    ) -> list[TrendItem]:
        async with self._uow:
            return await self._uow.days.get_weight_trend(user_id, date_range)

    async def get_calorie_trend(
        self, user_id: UUID, date_range: DateRangeDTO
    ) -> list[TrendItem]:
        async with self._uow:
            return await self._uow.days.get_calorie_trend(user_id, date_range)
