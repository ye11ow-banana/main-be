from uuid import UUID

from sqlalchemy.exc import NoResultFound

from models import DateRangeDTO
from unitofwork import IUnitOfWork
from utils import this_month_range


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
