from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import NoResultFound

from calorie.models import (
    DayFullInfoDTO,
    DayMeasurementUpdateDTO,
    DaysFilterDTO,
    IngestResponseDTO,
    OpenAIProductCreationDTO,
    OpenAIProductDTO,
    OpenAIProductMatchDTO,
)
from calorie.openai_client.client import CalorieOpenAIClient
from config import settings
from models import DateRangeDTO, PaginationDTO
from unitofwork import IUnitOfWork
from utils import Pagination, this_month_range


class DayService:
    def __init__(self, uow: IUnitOfWork, calorie_openai_client: CalorieOpenAIClient):
        self._uow = uow
        self._calorie_openai_client = calorie_openai_client

    async def update_day(self, day_id: UUID, data: DayMeasurementUpdateDTO) -> None:
        async with self._uow:
            await self._uow.days.update({"id": day_id}, **data.model_dump())
            await self._uow.commit()

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
            count = await self._uow.days.count_in_date_range(
                user_id, days_filter.to_date_range()
            )
        return PaginationDTO(
            page_count=pagination.get_page_count(count),
            total_count=count,
            data=days,
        )

    async def process_ingestion_image(
        self,
        image_bytes: bytes,
        image_mime: str,
        user_text: str | None,
    ) -> IngestResponseDTO:
        image_data = self._calorie_openai_client.image_to_items(
            image_bytes=image_bytes,
            mime=image_mime,
            model=settings.openai.model_vision,
        )

        if user_text := (user_text or "").strip():
            user_text_data = self._calorie_openai_client.user_text_to_items(
                user_text=user_text,
                model=settings.openai.model_text,
            )
            image_data.items.extend(user_text_data.items)
            image_data.warnings += user_text_data.warnings
            image_data.unparsed += user_text_data.unparsed

        resolved, unknown = await self._resolve_raw_names(image_data.items)
        if unknown:
            resolved.extend(await self._process_unknown_products(unknown))

        return IngestResponseDTO(
            products=resolved,
            warnings=image_data.warnings,
            unparsed=image_data.unparsed,
        )

    async def _process_unknown_products(
        self, unknown: list[OpenAIProductDTO]
    ) -> list[OpenAIProductMatchDTO]:
        unique_raw_names = self._get_unique_unknown_product_names(unknown)

        products_to_create = self._calorie_openai_client.unknown_to_nutrition(
            raw_names=unique_raw_names,
            model=settings.openai.model_text,
        ).products

        return await self._process_unknown_to_resolved(unknown, products_to_create)

    async def _process_unknown_to_resolved(
        self,
        unknown: list[OpenAIProductDTO],
        products_to_create: list[OpenAIProductCreationDTO],
    ) -> list[OpenAIProductMatchDTO]:
        unknown_map = defaultdict(list)
        for unknown_item in unknown:
            unknown_item_name = self._normalize_raw_name(unknown_item.raw_name)
            unknown_map[unknown_item_name].append(unknown_item)

        resolved = []
        for product_to_create in products_to_create:
            unknown_items = unknown_map.get(product_to_create.raw_name)
            if not unknown_items:
                continue

            async with self._uow:
                created_product_id = await self._uow.products.add_openai_product(
                    product_to_create
                )
                await self._uow.commit()
                for unknown_item in unknown_items:
                    resolved.append(
                        OpenAIProductMatchDTO(
                            user=unknown_item.user,
                            product_id=created_product_id,
                            name=product_to_create.name_ua,
                            weight=unknown_item.weight,
                            matched_score=Decimal(0),
                        )
                    )

        return resolved

    async def _resolve_raw_names(
        self, items: list[OpenAIProductDTO]
    ) -> tuple[list[OpenAIProductMatchDTO], list[OpenAIProductDTO]]:
        resolved: list[OpenAIProductMatchDTO] = []
        unknown: list[OpenAIProductDTO] = []

        for item in items:
            try:
                item_name = self._normalize_raw_name(item.raw_name)
                async with self._uow:
                    product, score = await self._uow.products.find_by_raw_name(
                        item.user, item_name, item.weight
                    )
            except NoResultFound:
                unknown.append(item)
            else:
                resolved.append(product)

        return resolved, unknown

    def _get_unique_unknown_product_names(
        self, unknown: list[OpenAIProductDTO] = None
    ) -> set[str]:
        unique_raw_names = set()
        for unknown_item in unknown:
            unknown_item_name = self._normalize_raw_name(unknown_item.raw_name)
            if unknown_item_name not in unique_raw_names:
                unique_raw_names.add(unknown_item_name)
        return unique_raw_names

    @staticmethod
    def _normalize_raw_name(raw_name: str) -> str:
        return raw_name.strip().lower()
