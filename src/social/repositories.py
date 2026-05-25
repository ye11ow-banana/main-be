from uuid import UUID

from sqlalchemy import exists, select

from auth.orm import User
from repository import SQLAlchemyRepository
from social import orm
from social.models import TeamStatus


class TeamRepository(SQLAlchemyRepository):
    model = orm.Team

    async def create(self, requester_id: UUID, addressee_id: UUID):
        team = await self.add(
            requester_id=requester_id,
            addressee_id=addressee_id,
            status=TeamStatus.PENDING,
        )
        return team

    async def get_team(self, user1: UUID, user2: UUID):
        stmt = select(self.model).where(
            (
                (self.model.requester_id == user1) & (self.model.addressee_id == user2)
                | (self.model.requester_id == user2)
                & (self.model.addressee_id == user1)
            )
        )

        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def exists_between(self, user1: UUID, user2: UUID) -> bool:
        stmt = select(
            exists().where(
                (self.model.requester_id == user1) & (self.model.addressee_id == user2)
                | (self.model.requester_id == user2)
                & (self.model.addressee_id == user1)
            )
        )

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_user_team_members(self, user_id: UUID):
        stmt = select(self.model).where(
            (self.model.status == TeamStatus.ACCEPTED)
            & (
                (self.model.requester_id == user_id)
                | (self.model.addressee_id == user_id)
            )
        )
        result = await self._session.execute(stmt)

        team_members = result.scalars().all()

        return team_members

    async def get_user_team_members_users(self, user_id: UUID):
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
        return result.scalars().all()

    async def get_pending_requests(self, user_id: UUID):
        stmt = select(self.model).where(
            (self.model.addressee_id == user_id)
            & (self.model.status == TeamStatus.PENDING)
        )
        result = await self._session.execute(stmt)

        teams = result.scalars().all()

        return teams
