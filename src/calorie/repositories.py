from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, delete, func, select, update
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
    UserBodyWeightDTO,
)
from repository import SQLAlchemyRepository
from src.models import DateRangeDTO
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
        base_query = (
            select(self.model)
            .options(
                selectinload(self.model.day_products).selectinload(
                    orm.DayProduct.product
                )
            )
            .filter_by(**data)
        )

        first_stmt = base_query.order_by(self.model.created_at.asc()).limit(1)
        first_res = await self._session.execute(first_stmt)
        first = first_res.scalar_one()

        last_stmt = base_query.order_by(self.model.created_at.desc()).limit(1)
        last_res = await self._session.execute(last_stmt)
        last = last_res.scalar_one()

        return (
            DayInDBDTO.model_validate(first),
            DayInDBDTO.model_validate(last),
        )

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

    @staticmethod
    def _date_to_range(date_: date) -> tuple[datetime, datetime]:
        start = datetime.combine(date_, datetime.min.time())
        end = start + timedelta(days=1)
        return start, end

    async def get_calorie_trend(
        self, user_id: UUID, date_range: DateRangeDTO
    ) -> list[TrendItemDTO]:
        start_dt, end_dt_exclusive = date_range.format_to_exclusive_range()
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.created_at >= start_dt)
            .where(self.model.created_at < end_dt_exclusive)
            .where(self.model.total_calories > 0)
            .order_by(self.model.created_at)
        )
        days = (await self._session.execute(query)).scalars().all()
        return [
            TrendItemDTO(date=day.created_at.date(), value=day.total_calories)
            for day in days
        ]

    async def get_trend_adjacent_days(
        self, user_id: UUID, target_date: date
    ) -> tuple[orm.Day | None, orm.Day | None, orm.Day | None]:
        start, end = self._date_to_range(target_date)

        current_day = (
            await self._session.execute(
                select(self.model)
                .where(self.model.user_id == user_id)
                .where(self.model.created_at >= start)
                .where(self.model.created_at < end)
            )
        ).scalar_one_or_none()

        if current_day is None:
            return None, None, None

        previous_day = (
            await self._session.execute(
                select(self.model)
                .where(self.model.user_id == user_id)
                .where(self.model.created_at < current_day.created_at)
                .where(self.model.body_weight.isnot(None))
                .order_by(self.model.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        next_day = (
            await self._session.execute(
                select(self.model)
                .where(self.model.user_id == user_id)
                .where(self.model.created_at > current_day.created_at)
                .where(self.model.body_weight.isnot(None))
                .order_by(self.model.created_at.asc())
                .limit(1)
            )
        ).scalar_one_or_none()

        return previous_day, current_day, next_day

    @staticmethod
    def update_trend(
        previous_day: orm.Day | None,
        current_day: orm.Day | None,
        next_day: orm.Day | None,
    ) -> None:
        if current_day is None or current_day.body_weight is None:
            return

        if previous_day and previous_day.body_weight is not None:
            current_day.trend = current_day.body_weight - previous_day.body_weight
        else:
            current_day.trend = None

        if next_day and next_day.body_weight is not None:
            next_day.trend = next_day.body_weight - current_day.body_weight

    async def get_day_with_products(
        self,
        user_id: UUID,
        target_date: date,
    ) -> DayFullInfoDTO:
        start, end = self._date_to_range(target_date)

        query = (
            select(self.model)
            .options(
                selectinload(self.model.day_products).selectinload(
                    orm.DayProduct.product
                )
            )
            .where(self.model.user_id == user_id)
            .where(self.model.created_at >= start)
            .where(self.model.created_at < end)
        )

        result = await self._session.execute(query)
        day = result.scalar_one_or_none()

        if day is None:
            raise NoResultFound("Day not found")

        return DayFullInfoDTO.model_validate(day)

    async def get_all_by_date(self, date_: date) -> list[UserBodyWeightDTO]:
        start, end = self._date_to_range(date_)

        query = (
            select(self.model.user_id, self.model.body_weight)
            .where(self.model.created_at >= start)
            .where(self.model.created_at < end)
        )

        rows = await self._session.execute(query)

        return [
            UserBodyWeightDTO(user_id=r.user_id, body_weight=r.body_weight)
            for r in rows.mappings()
        ]

    async def get_by_date(self, date_: date, **data: str | int | UUID) -> DayInDBDTO:
        start, end = self._date_to_range(date_)

        query = (
            select(self.model)
            .where(self.model.created_at >= start)
            .where(self.model.created_at < end)
            .filter_by(**data)
        )
        response = await self._session.execute(query)
        row = response.scalars().first()

        if row is None:
            raise NoResultFound(f"No result found for date {date_}")

        return DayInDBDTO.model_validate(row)

    async def get_day_products_by_id(self, day_id: UUID):
        query = (
            select(orm.DayProduct.weight, orm.Product)
            .join(orm.Product)
            .where(orm.DayProduct.day_id == day_id)
        )
        res = await self._session.execute(query)
        return res.all()

    async def get_by_id(self, *, day_id: UUID) -> DayInDBDTO:
        query = (
            select(self.model)
            .options(
                selectinload(self.model.day_products).selectinload(
                    orm.DayProduct.product
                )
            )
            .where(self.model.id == day_id)
        )

        result = await self._session.execute(query)
        day = result.scalar_one_or_none()

        if day is None:
            raise NoResultFound(f"Day not found: {day_id}")

        return DayInDBDTO.model_validate(day)


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
        statement = insert(self.model).values(
            name=product.name_ua,
            proteins=product.per_100g.proteins,
            fats=product.per_100g.fats,
            carbs=product.per_100g.carbs,
            calories=product.per_100g.calories,
        )

        statement = statement.on_conflict_do_nothing(
            index_elements=[self.model.name]
        ).returning(self.model.id)

        result = await self._session.execute(statement)
        inserted_id = result.scalar()

        if not inserted_id:
            query = select(self.model.id).where(self.model.name == product.name_ua)
            existing_result = await self._session.execute(query)
            inserted_id = existing_result.scalar_one()

        return inserted_id

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

    async def delete_product(self, day_id: UUID, product_id: UUID) -> None:
        query = (
            delete(self.model)
            .where(self.model.day_id == day_id)
            .where(self.model.product_id == product_id)
        )
        result = await self._session.execute(query)
        if result.rowcount == 0:
            raise NoResultFound("Day product not found")

    async def update_weight(self, day_id: UUID, product_id: UUID, weight: int) -> None:
        query = (
            update(self.model)
            .where(self.model.day_id == day_id)
            .where(self.model.product_id == product_id)
            .values(weight=weight)
        )
        result = await self._session.execute(query)
        if result.rowcount == 0:
            raise NoResultFound("Day product not found")
