from dependency_injector.wiring import inject
from fastapi import APIRouter

from app.models import AppDTO
from config.dependencies import ActiveUserDep, AppServiceDep
from models import ResponseDTO

router = APIRouter(prefix="/apps", tags=["Apps"])


@router.get("")
@inject
async def get_apps(_: ActiveUserDep, app_service: AppServiceDep) -> ResponseDTO[AppDTO]:
    apps = await app_service.get_active()
    return ResponseDTO[AppDTO](data=apps)
