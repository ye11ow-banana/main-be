from uuid import UUID

from dependency_injector.wiring import inject
from fastapi import APIRouter, HTTPException, status

from auth.models import UserInfoDTO
from config.dependencies import ActiveUserDep, TeamServiceDep
from social.exceptions import TeamError
from social.models import (
    TeamActionDTO,
    TeamRequestDTO,
    TeamResponseDTO,
)
from src.models import ResponseDTO, SuccessDTO

router = APIRouter(prefix="/social", tags=["Social"])


@router.post("/team/request", status_code=status.HTTP_200_OK)
@inject
async def send_team_request(
    data: TeamRequestDTO,
    user: ActiveUserDep,
    service: TeamServiceDep,
) -> ResponseDTO[TeamResponseDTO]:
    try:
        team = await service.send_request(
            requester_id=user.id,
            addressee_id=data.user_id,
        )
    except TeamError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ResponseDTO(data=TeamResponseDTO.model_validate(team))


@router.post("/team/accept", status_code=status.HTTP_200_OK)
@inject
async def accept_team_request(
    data: TeamActionDTO,
    user: ActiveUserDep,
    service: TeamServiceDep,
) -> ResponseDTO[SuccessDTO]:
    try:
        await service.accept_request(
            team_id=data.team_id,
            user_id=user.id,
        )
    except TeamError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ResponseDTO(data=SuccessDTO())


@router.post("/team/reject", status_code=status.HTTP_200_OK)
@inject
async def reject_team_request(
    data: TeamActionDTO,
    user: ActiveUserDep,
    service: TeamServiceDep,
) -> ResponseDTO[SuccessDTO]:
    try:
        await service.reject_request(
            team_id=data.team_id,
            user_id=user.id,
        )
    except TeamError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ResponseDTO(data=SuccessDTO())


@router.delete("/team/members/{team_member_id}", status_code=status.HTTP_200_OK)
@inject
async def remove_team_member(
    user: ActiveUserDep, service: TeamServiceDep, team_member_id: UUID
) -> ResponseDTO[SuccessDTO]:
    try:
        await service.remove_team_member(user_id=user.id, team_member_id=team_member_id)
    except TeamError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ResponseDTO(data=SuccessDTO())


@router.get("/team/members", status_code=status.HTTP_200_OK)
@inject
async def get_team_members(
    user: ActiveUserDep,
    service: TeamServiceDep,
) -> ResponseDTO[list[UserInfoDTO]]:
    return ResponseDTO(data=await service.get_team_members(user.id))


@router.get("/team/requests", status_code=status.HTTP_200_OK)
@inject
async def get_pending_requests(
    user: ActiveUserDep,
    service: TeamServiceDep,
) -> ResponseDTO[list[TeamResponseDTO]]:
    requests = await service.get_requests(user.id)
    return ResponseDTO(data=requests)
