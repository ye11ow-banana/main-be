from typing import Sequence
from uuid import UUID

from repository import SQLAlchemyRepository
from setting import orm
from setting.models import CalorieSettingDTO


class CalorieSettingRepository(SQLAlchemyRepository):
    model = orm.CalorieSetting

    async def get(
        self, /, returns: Sequence[str] | None = None, **data: str | int | UUID
    ) -> CalorieSettingDTO:
        row = await super().get(returns, **data)
        return CalorieSettingDTO.model_validate(row)
