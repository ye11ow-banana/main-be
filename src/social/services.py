from uuid import UUID

from auth.models import UserInfoDTO
from social.models import FriendResponseDTO
from unitofwork import IUnitOfWork


class FriendshipService:
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow

    async def send_request(self, requester_id: UUID, addressee_id: UUID):
        async with self._uow:

            if requester_id == addressee_id:
                raise ValueError("You cannot send friend request to yourself")

            user = await self._uow.users.get(id=addressee_id)
            if not user:
                raise ValueError("User not found")

            existing = await self._uow.friendships.get_friendship(
                requester_id, addressee_id
            )
            if existing:
                raise ValueError("Friendship already exists")

            friendship = await self._uow.friendships.create(
                requester_id, addressee_id
            )

            await self._uow.commit()
            return friendship

    async def remove_friend(self, user_id: UUID, friend_id: UUID):
        async with self._uow:
            friendship = await self._uow.friendships.get_friendship(
                user_id, friend_id
            )

            if not friendship or friendship.status != "accepted":
                raise ValueError("Friendship does not exist")

            await self._uow.friendships.remove(id=friendship.id)
            await self._uow.commit()

    async def remove_friendship(self, user_id: UUID, friendship_id: UUID):
        async with self._uow:
            friendship = self._uow.friendships.get(id=friendship_id)

            if not friendship or friendship.status != "accepted":
                raise ValueError("Friendship does not exist")

            await self._uow.friendships.remove(id=friendship.id)
            await self._uow.commit()

    async def accept_request(self, friendship_id: UUID, user_id: UUID):
        async with self._uow:
            friendship = await self._uow.friendships.get(id=friendship_id)

            if not friendship:
                raise ValueError("Friend request not found")

            if friendship.addressee_id != user_id:
                raise ValueError("Not allowed")

            await self._uow.friendships.update(
                {"id": friendship_id}, status="accepted"
            )
            await self._uow.commit()

    async def reject_request(self, friendship_id: UUID, user_id: UUID):
        async with self._uow:
            friendship = await self._uow.friendships.get(id=friendship_id)

            if not friendship:
                raise ValueError("Friend request not found")

            if friendship.addressee_id != user_id:
                raise ValueError("Not allowed")

            await self._uow.friendships.remove(id=friendship_id)
            await self._uow.commit()

    async def get_friends(self, user_id: UUID):
        async with self._uow:
            friends = await self._uow.friendships.get_user_friends_users(user_id)

            return [
                UserInfoDTO.model_validate(f)
                for f in friends
            ]

    async def get_friendships(self, user_id: UUID):
        async with self._uow:
            friendships = await self._uow.friendships.get_user_friends(user_id)

            return [
                FriendResponseDTO.model_validate(f)
                for f in friendships
            ]

    async def get_requests(self, user_id: UUID):
        async with self._uow:
            requests = await self._uow.friendships.get_pending_requests(user_id)

            return [
                FriendResponseDTO.model_validate(r)
                for r in requests
            ]