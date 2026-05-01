from uuid import UUID
from sqlalchemy import select, or_

from repository import SQLAlchemyRepository
from social import orm
from auth.orm import User


class FriendshipRepository(SQLAlchemyRepository):
    model = orm.Friendship

    async def create(self, requester_id: UUID, addressee_id: UUID):
        friendship = await self.add(
            requester_id=requester_id,
            addressee_id=addressee_id,
            status="pending",
        )
        return friendship

    async def get_friendship(self, user1: UUID, user2: UUID):
        stmt = select(self.model).where(
            or_(
                (self.model.requester_id == user1)
                & (self.model.addressee_id == user2),
                (self.model.requester_id == user2)
                & (self.model.addressee_id == user1),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_user_friends(self, user_id: UUID):
        stmt = select(self.model).where(
            (self.model.status == "accepted")
            & (
                    (self.model.requester_id == user_id)
                    | (self.model.addressee_id == user_id)
            )
        )
        result = await self._session.execute(stmt)

        friendships = result.scalars().all()

        return friendships

    async def get_user_friends_users(self, user_id: UUID):
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
                (self.model.status == "accepted")
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
            & (self.model.status == "pending")
        )
        result = await self._session.execute(stmt)

        friendships = result.scalars().all()

        return friendships