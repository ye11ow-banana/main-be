from typing import Sequence

from app import orm
from app.models import AppDTO
from repository import SQLAlchemyRepository


class AppRepository(SQLAlchemyRepository):
    model = orm.App

    async def get_active(
        self, /, returns: Sequence[str] | None = None, **data: str | int
    ) -> list[AppDTO]:
        apps = await super().get_all(returns=returns, is_active=True, **data)
        return [AppDTO.model_validate(app) for app in apps]
