from collections import defaultdict
from datetime import date, datetime
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
        day_products = self._calculate_totals(data.products)
        user_to_day_map = await self._get_user_to_day_map(data.date, day_products)
        user_to_products_map = self._get_user_to_products_map(
            day_products, user_to_day_map
        )
        async with self._uow:
            await self._create_days(data.date, user_to_day_map, user_to_products_map)
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
    ) -> None:
        for user_id, products in user_to_products_map.items():
            day = user_to_day_map[user_id]
            if day is None:
                created_at = datetime.combine(day_date, datetime.now().time())
                day = await self._uow.days.add(created_at=created_at, user_id=user_id)
                await self._uow.day_products.bulk_add_to_day(products, day.id)
            else:
                await self._uow.day_products.bulk_upsert(products)

    @staticmethod
    def _calculate_totals(
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
                    day_id=user_to_day_map[day_product.user_id].id,
                    product_id=day_product.product_id,
                    weight=day_product.weight,
                )
            )
        return user_to_products_map
