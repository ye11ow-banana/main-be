from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload

from calorie import orm
from calorie.models import (
    DayFullInfoDTO,
    DayInDBDTO,
    DaysFilterDTO,
    DaysFilterSortByEnum,
    OpenAIProductCreationDTO,
    OpenAIProductMatchDTO,
    ProductDTO,
    TrendItemDTO,
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

    async def find_by_raw_name(
        self,
        user: str,
        raw_name: str,
        weight: str,
        *,
        min_similarity: float = 0.20,
        use_levenshtein_for_short: bool = True,
    ) -> tuple[OpenAIProductMatchDTO, float]:
        name_lowercase = func.lower(self.model.name)
        sim = func.similarity(name_lowercase, raw_name)
        if use_levenshtein_for_short:
            lev = func.levenshtein(name_lowercase, raw_name)
            lev_score = case(
                (
                    func.length(raw_name) <= 4,
                    case(
                        (lev == 0, 1.0), (lev == 1, 0.75), (lev == 2, 0.50), else_=0.0
                    ),
                ),
                else_=0.0,
            )
            score_expression = (sim * 0.85) + (lev_score * 0.15)
        else:
            score_expression = sim

        score = score_expression.label("score")
        stmt = (
            select(self.model, score_expression.label("score"))
            .where(name_lowercase.op("%")(raw_name))
            .where(sim >= min_similarity)
            .order_by(score.desc())
            .limit(1)
        )

        res = await self._session.execute(stmt)
        row = res.first()
        if row is None:
            raise NoResultFound(f"No product match found for raw_name={raw_name!r}")

        product, score = row[0], float(row[1])

        dto = OpenAIProductMatchDTO(
            user=user,
            product_id=product.id,
            name=product.name,
            weight=weight,
            matched_score=Decimal(str(score)),
        )
        return dto, score

    async def add_openai_product(self, product: OpenAIProductCreationDTO) -> UUID:
        new_model_object = self.model(
            name=product.name_ua,
            proteins=product.per_100g.proteins,
            fats=product.per_100g.fats,
            carbs=product.per_100g.carbs,
            calories=product.per_100g.calories,
        )
        self._session.add(new_model_object)
        await self._session.flush()
        return new_model_object.id

    async def search_by_name(self, q: str, pagination: Pagination) -> list[ProductDTO]:
        query = select(self.model).order_by(self.model.created_at.desc())
        if q:
            query = query.where(self.model.name.ilike(f"%{q}%"))
        query = query.offset(pagination.get_offset()).limit(pagination.limit)
        response = await self._session.execute(query)
        results = response.scalars().all()
        return [ProductDTO.model_validate(product) for product in results]

    async def count_by_name(self, q: str) -> int:
        query = select(func.count()).select_from(self.model)
        if q:
            query = query.where(self.model.name.ilike(f"%{q}%"))
        return (await self._session.execute(query)).scalar()
