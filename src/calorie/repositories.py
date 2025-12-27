from datetime import datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from calorie import orm
from calorie.models import TrendItem
from models import DateRangeDTO
from repository import SQLAlchemyRepository


class DayRepository(SQLAlchemyRepository):
    model = orm.Day

    async def get_weight_trend(
        self, user_id: UUID, date_range: DateRangeDTO
    ) -> list[TrendItem]:
        start_dt = datetime.combine(date_range.start_date, time.min)
        end_dt_exclusive = datetime.combine(
            date_range.end_date + timedelta(days=1), time.min
        )
        query = (
            select(self.model.created_at, self.model.body_weight)
            .where(self.model.user_id == user_id)
            .where(self.model.created_at >= start_dt)
            .where(self.model.created_at < end_dt_exclusive)
            .order_by(self.model.created_at)
        )
        days = (await self._session.execute(query)).all()
        return [
            TrendItem(date=created_at.date(), value=body_weight)
            for created_at, body_weight in days
        ]

    async def get_calorie_trend(
        self, user_id: UUID, date_range: DateRangeDTO
    ) -> list[TrendItem]:
        start_dt = datetime.combine(date_range.start_date, time.min)
        end_dt_exclusive = datetime.combine(
            date_range.end_date + timedelta(days=1), time.min
        )
        query = (
            select(self.model)
            .options(
                selectinload(self.model.day_products).selectinload(
                    orm.DayProduct.product
                )
            )
            .where(self.model.user_id == user_id)
            .where(self.model.created_at >= start_dt)
            .where(self.model.created_at < end_dt_exclusive)
            .order_by(self.model.created_at)
        )
        days = (await self._session.execute(query)).scalars().all()
        return [
            TrendItem(
                date=day.created_at.date(), value=self._calculate_total_calories(day)
            )
            for day in days
        ]

    @staticmethod
    def _calculate_total_calories(day: orm.Day) -> Decimal:
        total = Decimal("0")
        for day_product in day.day_products:
            total += (
                day_product.product.calories / Decimal("100")
            ) * day_product.weight
        return total


class ProductRepository(SQLAlchemyRepository):
    model = orm.Product
