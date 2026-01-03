from uuid import UUID

from sqlalchemy.exc import NoResultFound

from calorie.models import DaysFilterDTO, DayFullInfoDTO
from models import DateRangeDTO, PaginationDTO
from unitofwork import IUnitOfWork
from utils import this_month_range, Pagination


class DayService:
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow

    async def get_date_range(self, user_id: UUID) -> DateRangeDTO:
        async with self._uow:
            try:
                first_day, last_day = await self._uow.days.get_first_and_last(
                    user_id=user_id
                )
            except NoResultFound:
                start, end = this_month_range()
                return DateRangeDTO(start_date=start, end_date=end)
            return DateRangeDTO(
                start_date=first_day.created_at.date(),
                end_date=last_day.created_at.date(),
            )

    async def get_paginated_days(
        self, user_id: UUID, pagination: Pagination, days_filter: DaysFilterDTO
    ) -> PaginationDTO[DayFullInfoDTO]:
        async with self._uow:
            days = await self._uow.days.get_full_paginated_info(
                user_id, pagination, days_filter
            )
        self.calculate_totals(days)
        return PaginationDTO(
            page_count=pagination.get_page_count(len(days)),
            total_count=len(days),
            data=days,
        )

    @staticmethod
    def calculate_totals(days: list[DayFullInfoDTO]) -> None:
        for day in days:
            for product in day.products:
                day.total_proteins += product.proteins
                day.total_fats += product.fats
                day.total_carbs += product.carbs
                day.total_calories += product.calories
