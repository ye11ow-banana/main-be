from dependency_injector.wiring import inject
from fastapi import APIRouter

from config.dependencies import ActiveUserDep, SettingServiceDep
from setting.models import AllSettingsResponseDTO, UpdateSettingsRequestDTO
from src.models import ResponseDTO, SuccessDTO

router = APIRouter(prefix="/settings", tags=["Setting"])


@router.get("")
@inject
async def get_all_settings(
    user: ActiveUserDep, setting_service: SettingServiceDep
) -> ResponseDTO[AllSettingsResponseDTO]:
    settings = await setting_service.get_all_user_settings(user)
    return ResponseDTO[AllSettingsResponseDTO](data=settings)


@router.patch("")
@inject
async def update_settings(
    user: ActiveUserDep,
    setting_service: SettingServiceDep,
    data: UpdateSettingsRequestDTO,
) -> ResponseDTO[SuccessDTO]:
    await setting_service.update_user_settings(user.id, data)
    return ResponseDTO[SuccessDTO](data=SuccessDTO())
