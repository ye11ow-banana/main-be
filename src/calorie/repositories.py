from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload

from calorie import orm
from calorie.models import (
    DayFullInfoDTO,
    DayInDBDTO,
    DayProductCreationDTO,
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
        query = (
            select(self.model)
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
            query = query.order_by(self.model.total_calories.desc())

        start_dt, end_dt_exclusive = (
            days_filter.to_date_range().format_to_exclusive_range()
        )
        query = query.filter(self.model.created_at >= start_dt)
        query = query.filter(self.model.created_at < end_dt_exclusive)

        query = query.offset(pagination.get_offset()).limit(pagination.limit)
        response = await self._session.execute(query)
        results = response.scalars().unique().all()
        return [DayFullInfoDTO.model_validate(result) for result in results]

    async def count_in_date_range(self, user_id: UUID, date_range: DateRangeDTO) -> int:
        start_dt, end_dt_exclusive = date_range.format_to_exclusive_range()
        query = (
            select(func.count())
            .where(self.model.user_id == user_id)
            .where(self.model.created_at >= start_dt)
            .where(self.model.created_at < end_dt_exclusive)
        )
        return (await self._session.execute(query)).scalar()

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
            .where(self.model.body_weight.isnot(None))
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
            .where(self.model.user_id == user_id)
            .where(self.model.created_at >= start_dt)
            .where(self.model.created_at < end_dt_exclusive)
            .order_by(self.model.created_at)
        )
        days = (await self._session.execute(query)).scalars().all()
        return [
            TrendItemDTO(date=day.created_at.date(), value=day.total_calories)
            for day in days
        ]

    async def get_by_date(self, date_: date, **data: str | int | UUID) -> DayInDBDTO:
        start = datetime.combine(date_, datetime.min.time())
        end = start + timedelta(days=1)
        query = (
            select(self.model)
            .where(self.model.created_at >= start)
            .where(self.model.created_at < end)
            .filter_by(**data)
        )
        response = await self._session.execute(query)
        return DayInDBDTO.model_validate(response.scalar_one())

    async def add(self, **insert_data) -> DayInDBDTO:
        new_model_object = self.model(**insert_data)
        self._session.add(new_model_object)
        await self._session.flush()
        return DayInDBDTO.model_validate(new_model_object)


class ProductRepository(SQLAlchemyRepository):
    model = orm.Product

    async def get_by_ids(self, id_list: list[UUID]) -> list[ProductDTO]:
        query = select(self.model).where(self.model.id.in_(id_list))
        response = await self._session.execute(query)
        return [ProductDTO.model_validate(row) for row in response.scalars()]

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


class DayProductRepository(SQLAlchemyRepository):
    model = orm.DayProduct

    async def bulk_add_to_day(
        self, products: list[DayProductCreationDTO], day_id: UUID
    ) -> None:
        data = [product.model_dump() | {"day_id": day_id} for product in products]
        await self.bulk_add(data)

    async def bulk_upsert(self, products: list[DayProductCreationDTO]) -> None:
        items = [product.model_dump() for product in products]
        stmt = insert(self.model).values(items)

        excluded = stmt.excluded

        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=[self.model.day_id, self.model.product_id],
            set_={"weight": self.model.weight + excluded.weight},
        )

        await self._session.execute(upsert_stmt)
