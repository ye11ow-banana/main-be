from dependency_injector.wiring import inject
from fastapi import APIRouter, Query, status, HTTPException, UploadFile, File, Form

from calorie.models import (
    TrendFilterDTO,
    TrendItemDTO,
    TrendTypeEnum,
    DaysFilterDTO,
    DayFullInfoDTO,
    DaysFilterSortByEnum,
    IngestResponseDTO,
)
from config.dependencies import TrendServiceDep, ActiveUserDep, DayServiceDep
from models import ResponseDTO, DateRangeDTO, PaginationDTO, NameCodeDTO
from utils import Pagination

router = APIRouter(prefix="/calorie", tags=["Calorie"])


@router.get("/trend/items")
@inject
async def get_trend_items(
    user: ActiveUserDep,
    trend_service: TrendServiceDep,
    trend_filter: TrendFilterDTO = Query(),
) -> ResponseDTO[TrendItemDTO]:
    if trend_filter.type == TrendTypeEnum.WEIGHT:
        items = await trend_service.get_weight_trend(
            user.id, trend_filter.to_date_range()
        )
    else:
        items = await trend_service.get_calorie_trend(
            user.id, trend_filter.to_date_range()
        )
    return ResponseDTO[TrendItemDTO](data=items)


@router.get("/filters/date-range")
@inject
async def get_date_range_filters(
    user: ActiveUserDep, day_service: DayServiceDep
) -> ResponseDTO[DateRangeDTO]:
    date_range = await day_service.get_date_range(user.id)
    return ResponseDTO[DateRangeDTO](data=date_range)


@router.get("/days")
@inject
async def get_days(
    user: ActiveUserDep,
    day_service: DayServiceDep,
    days_filter: DaysFilterDTO = Query(),
) -> ResponseDTO[PaginationDTO[DayFullInfoDTO]]:
    pagination = Pagination(page=days_filter.page)
    days = await day_service.get_paginated_days(user.id, pagination, days_filter)
    return ResponseDTO[PaginationDTO[DayFullInfoDTO]](data=days)


@router.get("/sort_bys")
async def get_sort_bys(_: ActiveUserDep) -> ResponseDTO[NameCodeDTO]:
    results = [
        NameCodeDTO(name="Most recent", code=DaysFilterSortByEnum.MOST_RECENT.value),
        NameCodeDTO(name="Oldest", code=DaysFilterSortByEnum.OLDEST.value),
        NameCodeDTO(
            name="Most calories", code=DaysFilterSortByEnum.MOST_CALORIES.value
        ),
        NameCodeDTO(
            name="Lowest weight", code=DaysFilterSortByEnum.LOWEST_WEIGHT.value
        ),
    ]
    return ResponseDTO[NameCodeDTO](data=results)


@router.post("/ingest")
@inject
async def ingest(
    _: ActiveUserDep,
    day_service: DayServiceDep,
    image: UploadFile = File(...),
    description: str | None = Form(None),
) -> IngestResponseDTO:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Upload an image file"
        )

    return await day_service.process_ingestion_image(
        image_bytes=await image.read(),
        image_mime=image.content_type,
        user_text=description,
    )
