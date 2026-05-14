from uuid import UUID

from auth.models import UserInfoDTO
from social.models import TeamResponseDTO, TeamStatus
from unitofwork import IUnitOfWork


class TeamService:
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow

    async def send_request(self, requester_id: UUID, addressee_id: UUID):
        async with self._uow:
            if requester_id == addressee_id:
                raise ValueError("You cannot send a team request to yourself")

            user = await self._uow.users.get(id=addressee_id)
            if not user:
                raise ValueError("User not found")

            existing = await self._uow.teams.get_team(requester_id, addressee_id)
            if existing:
                raise ValueError("Team already exists")

            team = await self._uow.teams.create(requester_id, addressee_id)

            await self._uow.commit()
            return team

    async def remove_team_member(self, user_id: UUID, team_member_id: UUID):
        async with self._uow:
            team = await self._uow.teams.get_team(user_id, team_member_id)

            if not team or team.status != TeamStatus.ACCEPTED:
                raise ValueError("Team does not exist")

            await self._uow.teams.remove(id=team.id)
            await self._uow.commit()

    async def leave_team(self, user_id: UUID, team_id: UUID):
        async with self._uow:
            team = self._uow.teams.get(id=team_id)

            if not team or team.status != TeamStatus.ACCEPTED:
                raise ValueError("Team does not exist")

            await self._uow.teams.remove(id=team.id)
            await self._uow.commit()

    async def accept_request(self, team_id: UUID, user_id: UUID):
        async with self._uow:
            team = await self._uow.teams.get(id=team_id)

            if not team:
                raise ValueError("Team request not found")

            if team.addressee_id != user_id:
                raise ValueError("Not allowed")

            await self._uow.teams.update({"id": team_id}, status=TeamStatus.ACCEPTED)
            await self._uow.commit()

    async def reject_request(self, team_id: UUID, user_id: UUID):
        async with self._uow:
            team = await self._uow.teams.get(id=team_id)

            if not team:
                raise ValueError("Team request not found")

            if team.addressee_id != user_id:
                raise ValueError("Not allowed")

            await self._uow.teams.remove(id=team_id)
            await self._uow.commit()

    async def get_team_members(self, user_id: UUID):
        async with self._uow:
            team_members = await self._uow.teams.get_user_team_members_users(user_id)

            return [UserInfoDTO.model_validate(t) for t in team_members]

    async def get_teams(self, user_id: UUID):
        async with self._uow:
            teams = await self._uow.teams.get_user_team_members(user_id)

            return [TeamResponseDTO.model_validate(t) for t in teams]

    async def get_requests(self, user_id: UUID):
        async with self._uow:
            requests = await self._uow.teams.get_pending_requests(user_id)

            return [TeamResponseDTO.model_validate(r) for r in requests]
