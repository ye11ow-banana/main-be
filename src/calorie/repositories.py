from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from calorie import orm
from calorie.models import (
    TrendItemDTO,
    DayInDBDTO,
    DaysFilterDTO,
    DaysFilterSortByEnum,
    DayFullInfoDTO,
)
from models import DateRangeDTO
from repository import SQLAlchemyRepository
from utils import Pagination


class DayRepository(SQLAlchemyRepository):
    model = orm.Day

    async def get_full_paginated_info(
        self, user_id: UUID, pagination: Pagination, days_filter: DaysFilterDTO
    ) -> list[DayFullInfoDTO]:
        day_total_calories = (
            select(
                orm.DayProduct.day_id.label("day_id"),
                func.coalesce(
                    func.sum(orm.DayProduct.weight * orm.Product.calories / 100),
                    0,
                ).label("total_calories"),
            )
            .join(orm.Product, orm.Product.id == orm.DayProduct.product_id)
            .group_by(orm.DayProduct.day_id)
            .subquery("day_total_calories")
        )

        query = (
            select(self.model)
            .outerjoin(day_total_calories, day_total_calories.c.day_id == self.model.id)
            .options(
                selectinload(self.model.day_products).selectinload(
                    orm.DayProduct.product
                )
            )
            .where(self.model.user_id == user_id)
        )

        if days_filter.sort_by == DaysFilterSortByEnum.MOST_RECENT:
            query = query.order_by(self.model.created_at.desc())
        elif days_filter.sort_by == DaysFilterSortByEnum.OLDEST:
            query = query.order_by(self.model.created_at.asc())
        elif days_filter.sort_by == DaysFilterSortByEnum.LOWEST_WEIGHT:
            query = query.order_by(self.model.body_weight.asc())
        else:
            query = query.order_by(day_total_calories.c.total_calories.desc())

        start_dt, end_dt_exclusive = (
            days_filter.to_date_range().format_to_exclusive_range()
        )
        query = query.filter(self.model.created_at >= start_dt)
        query = query.filter(self.model.created_at < end_dt_exclusive)

        query = query.offset(pagination.get_offset()).limit(pagination.limit)
        response = await self._session.execute(query)
        results = response.scalars().unique().all()
        return [DayFullInfoDTO.model_validate(result) for result in results]

    async def get_first_and_last(
        self, /, **data: str | int | UUID
    ) -> tuple[DayInDBDTO, DayInDBDTO]:
        query = (
            select(self.model)
            .filter_by(**data)
            .order_by(self.model.created_at.asc())
            .limit(1)
        )
        response = await self._session.execute(query)
        first = response.scalar_one()
        query = (
            select(self.model)
            .filter_by(**data)
            .order_by(self.model.created_at.desc())
            .limit(1)
        )
        response = await self._session.execute(query)
        last = response.scalar_one()
        return DayInDBDTO.model_validate(first), DayInDBDTO.model_validate(last)

    async def get_weight_trend(
        self, user_id: UUID, date_range: DateRangeDTO
    ) -> list[TrendItemDTO]:
        start_dt, end_dt_exclusive = date_range.format_to_exclusive_range()
        query = (
            select(self.model.created_at, self.model.body_weight)
            .where(self.model.user_id == user_id)
            .where(self.model.created_at >= start_dt)
            .where(self.model.created_at < end_dt_exclusive)
            .order_by(self.model.created_at)
        )
        days = (await self._session.execute(query)).all()
        return [
            TrendItemDTO(date=created_at.date(), value=body_weight)
            for created_at, body_weight in days
        ]

    async def get_calorie_trend(
        self, user_id: UUID, date_range: DateRangeDTO
    ) -> list[TrendItemDTO]:
        start_dt, end_dt_exclusive = date_range.format_to_exclusive_range()
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
            TrendItemDTO(
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
