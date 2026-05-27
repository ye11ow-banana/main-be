from dependency_injector.wiring import inject
from fastapi import APIRouter

from config.dependencies import ActiveUserDep, SettingServiceDep
from models import ResponseDTO
from setting.models import AllSettingsResponseDTO

router = APIRouter(prefix="/settings", tags=["Setting"])


@router.get("")
@inject
async def get_all_settings(
    user: ActiveUserDep, setting_service: SettingServiceDep
) -> ResponseDTO[AllSettingsResponseDTO]:
    settings = await setting_service.get_all_user_settings(user)
    return ResponseDTO[AllSettingsResponseDTO](data=settings)
