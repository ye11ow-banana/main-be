from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import ColumnElement

from auth.orm import User
from database import Base
from repository import SQLAlchemyRepository
from social import orm
from social.exceptions import TeamAlreadyExistsError
from social.models import TeamStatus


class TeamRepository(SQLAlchemyRepository):
    model = orm.Team

    async def create(
        self,
        requester_id: UUID,
        addressee_id: UUID,
    ) -> Base:
        try:
            return await self.add(
                requester_id=requester_id,
                addressee_id=addressee_id,
                status=TeamStatus.PENDING,
            )
        except IntegrityError as e:
            raise TeamAlreadyExistsError("Team already exists") from e

    async def get_team(
        self,
        user1: UUID,
        user2: UUID,
    ) -> orm.Team | None:
        stmt = select(self.model).where(self._pair_expr(user1, user2))
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def exists_between(
        self,
        user1: UUID,
        user2: UUID,
    ) -> bool:
        stmt = select(exists().where(self._pair_expr(user1, user2)))
        result = await self._session.execute(stmt)
        return bool(result.scalar() or False)

    async def get_user_team_members(
        self,
        user_id: UUID,
    ) -> Sequence[orm.Team]:
        stmt = select(self.model).where(
            (self.model.status == TeamStatus.ACCEPTED)
            & (
                (self.model.requester_id == user_id)
                | (self.model.addressee_id == user_id)
            )
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_user_team_members_users(
        self,
        user_id: UUID,
    ) -> Sequence[User]:
        stmt = (
            select(User)
            .join(
                self.model,
                (
                    (self.model.requester_id == User.id)
                    | (self.model.addressee_id == User.id)
                ),
            )
            .where(
                (self.model.status == TeamStatus.ACCEPTED)
                & (
                    (self.model.requester_id == user_id)
                    | (self.model.addressee_id == user_id)
                )
                & (User.id != user_id)
            )
        )

        result = await self._session.execute(stmt)
        return result.scalars().unique().all()

    async def get_pending_requests(
        self,
        user_id: UUID,
    ) -> Sequence[orm.Team]:
        stmt = select(self.model).where(
            (self.model.addressee_id == user_id)
            & (self.model.status == TeamStatus.PENDING)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    def _pair_expr(
        self,
        user1: UUID,
        user2: UUID,
    ) -> ColumnElement[bool]:
        return (
            (self.model.requester_id == user1) & (self.model.addressee_id == user2)
        ) | ((self.model.requester_id == user2) & (self.model.addressee_id == user1))
