from uuid import UUID

from auth.models import UserInfoDTO
from setting.models import AllSettingsResponseDTO
from unitofwork import IUnitOfWork


class SettingService:
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow

    async def create_for_active_apps(self, new_user_id: UUID) -> None:
        async with self._uow:
            await self._uow.calorie_setting.add(user_id=new_user_id)
            await self._uow.commit()

    async def get_all_user_settings(self, user: UserInfoDTO) -> AllSettingsResponseDTO:
        async with self._uow:
            calorie_setting = await self._uow.calorie_setting.get(
                ("add_day_notes", "ai_creates_products"), user_id=user.id
            )
            return AllSettingsResponseDTO(calorie_setting=calorie_setting)
