from uuid import UUID

from pydantic import BaseModel

from auth.models import UserInfoDTO
from repository import SQLAlchemyRepository
from setting.models import AllSettingsResponseDTO, UpdateSettingsRequestDTO
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

    async def update_user_settings(
        self, user_id: UUID, data: UpdateSettingsRequestDTO
    ) -> None:
        async with self._uow:
            if data.calorie_setting is not None:
                await self._update_user_setting(
                    self._uow.calorie_setting, user_id, data.calorie_setting
                )
            await self._uow.commit()

    @staticmethod
    async def _update_user_setting(
        setting_repo: SQLAlchemyRepository, user_id: UUID, data: BaseModel
    ) -> None:
        update_data = data.model_dump(exclude={"id"}, exclude_unset=True)
        await setting_repo.update(what_to_update={"user_id": user_id}, **update_data)
