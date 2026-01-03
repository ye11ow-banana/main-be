from dependency_injector.wiring import inject
from fastapi import APIRouter, Query

from calorie.models import (
    TrendFilterDTO,
    TrendItemDTO,
    TrendTypeEnum,
    DaysFilterDTO,
    DayFullInfoDTO,
    DaysFilterSortByEnum,
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
@inject
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
