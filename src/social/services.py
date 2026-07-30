from uuid import UUID

from auth.models import UserInfoDTO
from social.exceptions import (
    TeamAlreadyExistsError,
    TeamError,
    TeamNotFoundError,
)
from social.models import TeamResponseDTO, TeamStatus
from unitofwork import IUnitOfWork


class TeamService:
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow

    async def send_request(
        self,
        requester_id: UUID,
        addressee_id: UUID,
    ) -> TeamResponseDTO:
        if requester_id == addressee_id:
            raise TeamError("You cannot send a team request to yourself")

        async with self._uow:
            if not await self._uow.users.exists(addressee_id):
                raise TeamError("Cannot send request")

            if await self._uow.teams.exists_between(requester_id, addressee_id):
                raise TeamAlreadyExistsError("Team already exists")

            team = await self._uow.teams.create(requester_id, addressee_id)
            await self._uow.commit()

            return TeamResponseDTO.model_validate(team)

    async def remove_team_member(self, user_id: UUID, member_user_id: UUID) -> None:
        async with self._uow:
            team = await self._uow.teams.get_team(user_id, member_user_id)

            if not team or team.status != TeamStatus.ACCEPTED:
                raise TeamNotFoundError("Team does not exist")

            await self._uow.teams.remove(id=team.id)
            await self._uow.commit()

    async def accept_request(self, team_id: UUID, user_id: UUID) -> None:
        async with self._uow:
            team = await self._uow.teams.get(id=team_id)

            if not team:
                raise TeamNotFoundError("Team request not found")

            if team.addressee_id != user_id:
                raise TeamError("Not allowed")

            await self._uow.teams.update({"id": team_id}, status=TeamStatus.ACCEPTED)
            await self._uow.commit()

    async def reject_request(self, team_id: UUID, user_id: UUID) -> None:
        async with self._uow:
            team = await self._uow.teams.get(id=team_id)

            if not team:
                raise TeamNotFoundError("Team request not found")

            if team.addressee_id != user_id:
                raise TeamError("Not allowed")

            if team.status != TeamStatus.PENDING:
                raise TeamError("Cannot reject non-pending request")

            await self._uow.teams.remove(id=team_id)
            await self._uow.commit()

    async def get_team_members(self, user_id: UUID) -> list[UserInfoDTO]:
        async with self._uow:
            users = await self._uow.teams.get_user_team_members_users(user_id)
            return [UserInfoDTO.model_validate(u) for u in users]

    async def get_teams(self, user_id: UUID) -> list[TeamResponseDTO]:
        async with self._uow:
            teams = await self._uow.teams.get_user_team_members(user_id)
            return [TeamResponseDTO.model_validate(t) for t in teams]

    async def get_requests(self, user_id: UUID) -> list[TeamResponseDTO]:
        async with self._uow:
            requests = await self._uow.teams.get_pending_requests(user_id)
            return [TeamResponseDTO.model_validate(r) for r in requests]
