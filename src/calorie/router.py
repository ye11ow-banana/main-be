from dependency_injector.wiring import inject
from fastapi import APIRouter, Query

from calorie.models import TrendFilterDTO, TrendItem, TrendTypeEnum
from config.dependencies import TrendServiceDep, ActiveUserDep
from models import ResponseDTO

router = APIRouter(prefix="/calorie", tags=["Calorie"])


@router.get("/trend/items")
@inject
async def get_trend_items(
    user: ActiveUserDep,
    trend_service: TrendServiceDep,
    trend_filter: TrendFilterDTO = Query(),
) -> ResponseDTO[TrendItem]:
    if trend_filter.type == TrendTypeEnum.WEIGHT:
        items = await trend_service.get_weight_trend(
            user.id, trend_filter.to_date_range()
        )
    else:
        items = await trend_service.get_calorie_trend(
            user.id, trend_filter.to_date_range()
        )
    return ResponseDTO[TrendItem](data=items)
