from uuid import UUID

from sqlalchemy import insert, literal, select

from app.orm import App
from repository import SQLAlchemyRepository
from setting import orm


class SettingRepository(SQLAlchemyRepository):
    model = orm.Setting

    async def create_for_active_apps(self, user_id: UUID) -> None:
        stmt = insert(self.model).from_select(
            ["app_id", "user_id"],
            select(App.id, literal(user_id)).where(App.is_active.is_(True)),
            include_defaults=False,
        )
        await self._session.execute(stmt)
