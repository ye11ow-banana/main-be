from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import NoResultFound

from calorie.models import (
    DayCreationDTO,
    DayInDBDTO,
    DayProductCreationDTO,
    UserDayProductCreationDTO,
)
from unitofwork import IUnitOfWork


class DayCreationService:
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow

    async def create(self, data: DayCreationDTO) -> None:
        day_products = self._merge_products(data.products)
        user_to_day_map = await self._get_user_to_day_map(data.date, day_products)
        user_to_products_map = self._get_user_to_products_map(
            day_products, user_to_day_map
        )

        async with self._uow:
            affected_users = set()

            standalone_affected = await self._upsert_standalone_metrics(
                users_with_no_products := (
                        (set(data.user_additional_calories.keys()) | set(data.all_body_weights.keys()))
                        - set(user_to_products_map.keys())
                ),
                data.user_additional_calories,
                data.all_body_weights,
                data.date,
            )
            affected_users |= standalone_affected
            created_affected = await self._create_days(
                data.date,
                user_to_day_map,
                user_to_products_map,
                data.user_additional_calories,
                data.user_body_weight,
            )
            affected_users |= created_affected

            for user_id in affected_users:
                await self._uow.days.update_weight_trend_for_day(user_id, data.date)

            await self._uow.commit()

    async def _get_user_to_day_map(
        self, day_date: date, day_products: list[UserDayProductCreationDTO]
    ) -> dict[UUID, DayInDBDTO | None]:
        user_to_day_map = {}
        for day_product in day_products:
            if day_product.user_id not in user_to_day_map:
                async with self._uow:
                    try:
                        day = await self._uow.days.get_by_date(
                            date_=day_date,
                            user_id=day_product.user_id,
                        )
                    except NoResultFound:
                        day = None
                    user_to_day_map[day_product.user_id] = day
        return user_to_day_map

    async def _create_days(
            self,
            day_date: date,
            user_to_day_map: dict[UUID, DayInDBDTO | None],
            user_to_products_map: dict[UUID, list[DayProductCreationDTO]],
            user_additional_calories: dict[UUID, Decimal],
            user_body_weight: dict[UUID, Decimal],
    ) -> set[UUID]:

        affected_users = set()

        for user_id, day_products in user_to_products_map.items():
            day = user_to_day_map[user_id]
            (
                total_proteins,
                total_carbs,
                total_fats,
                total_calories,
            ) = await self._calculate_totals(day_products)

            additional_calories = user_additional_calories.get(user_id, Decimal("0.0"))
            new_body_weight = user_body_weight.get(user_id)
            total_calories += additional_calories

            if day is None:
                created_at = datetime.combine(day_date, datetime.now().time())
                day = await self._uow.days.add(
                    total_proteins=total_proteins,
                    total_carbs=total_carbs,
                    total_fats=total_fats,
                    total_calories=total_calories,
                    additional_calories=additional_calories,
                    body_weight=new_body_weight,
                    created_at=created_at,
                    user_id=user_id,
                )
                await self._uow.day_products.bulk_add_to_day(day_products, day.id)
            else:
                old_weight = day.body_weight
                day.total_proteins += total_proteins
                day.total_carbs += total_carbs
                day.total_fats += total_fats
                day.total_calories += total_calories
                day.additional_calories += additional_calories

                if new_body_weight is not None:
                    if old_weight != new_body_weight:
                        affected_users.add(user_id)

                    day.body_weight = new_body_weight

                await self._uow.days.update({"id": day.id}, **day.model_dump())
                await self._uow.day_products.bulk_upsert(day_products)

        return affected_users

    async def _upsert_standalone_metrics(
            self,
            user_ids: set[UUID],
            user_additional_calories: dict[UUID, Decimal],
            all_body_weights: dict[UUID, Decimal | None],
            day_date: date
    ) -> set[UUID]:

        affected_users = set()

        for user_id in user_ids:
            additional_calories = user_additional_calories.get(user_id, Decimal("0.0"))
            new_body_weight = all_body_weights.get(user_id)

            try:
                day = await self._uow.days.get_by_date(date_=day_date, user_id=user_id)
            except NoResultFound:
                day = None

            created_at = datetime.combine(day_date, datetime.now().time())

            if day is None:
                await self._uow.days.add(
                    total_calories=additional_calories,
                    additional_calories=additional_calories,
                    body_weight=new_body_weight,
                    created_at=created_at,
                    user_id=user_id,
                )

                if new_body_weight is not None:
                    affected_users.add(user_id)

            else:
                old_weight = day.body_weight

                update_data = {
                    "total_calories": day.total_calories + additional_calories,
                    "additional_calories": day.additional_calories + additional_calories,
                }

                if new_body_weight is not None:
                    if old_weight != new_body_weight:
                        affected_users.add(user_id)

                    update_data["body_weight"] = new_body_weight

                await self._uow.days.update({"id": day.id}, **update_data)

        return affected_users

    async def _calculate_totals(
        self, day_products: list[DayProductCreationDTO]
    ) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        products = await self._uow.products.get_by_ids(
            [dp.product_id for dp in day_products]
        )
        product_map = {product.id: product for product in products}
        total_proteins = Decimal("0.0")
        total_carbs = Decimal("0.0")
        total_fats = Decimal("0.0")
        total_calories = Decimal("0.0")
        for day_product in day_products:
            product = product_map.get(day_product.product_id)
            if product:
                weight_factor = Decimal(day_product.weight) / Decimal("100.0")
                total_proteins += product.proteins * weight_factor
                total_carbs += product.carbs * weight_factor
                total_fats += product.fats * weight_factor
                total_calories += product.calories * weight_factor
        return total_proteins, total_carbs, total_fats, total_calories

    @staticmethod
    def _merge_products(
        data: list[UserDayProductCreationDTO],
    ) -> list[UserDayProductCreationDTO]:
        products = {}
        for day_product in data:
            try:
                obj = products[(day_product.user_id, day_product.product_id)]
            except KeyError:
                products[(day_product.user_id, day_product.product_id)] = day_product
            else:
                obj.weight += day_product.weight
        return list(products.values())

    @staticmethod
    def _get_user_to_products_map(
        day_products: list[UserDayProductCreationDTO],
        user_to_day_map: dict[UUID, DayInDBDTO | None],
    ) -> dict[UUID, list[DayProductCreationDTO]]:
        user_to_products_map = defaultdict(list)
        for day_product in day_products:
            user_to_products_map[day_product.user_id].append(
                DayProductCreationDTO(
                    day_id=getattr(user_to_day_map[day_product.user_id], "id", None),
                    product_id=day_product.product_id,
                    weight=day_product.weight,
                )
            )
        return user_to_products_map
