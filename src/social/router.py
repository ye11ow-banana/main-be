from dependency_injector.wiring import inject
from fastapi import APIRouter, HTTPException, status

from config.dependencies import ActiveUserDep, FriendshipServiceDep
from src.models import ResponseDTO, SuccessDTO
from social.models import (
    FriendRequestDTO,
    FriendResponseDTO,
    FriendshipActionDTO,
)

from auth.models import UserInfoDTO

router = APIRouter(prefix="/social", tags=["Social"])


@router.post("/friends/request", status_code=status.HTTP_200_OK)
@inject
async def send_friend_request(
    data: FriendRequestDTO,
    user: ActiveUserDep,
    service: FriendshipServiceDep,
) -> ResponseDTO[FriendResponseDTO]:
    try:
        friendship = await service.send_request(
            requester_id=user.id,
            addressee_id=data.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ResponseDTO(data=FriendResponseDTO.model_validate(friendship))


@router.post("/friends/accept", status_code=status.HTTP_200_OK)
@inject
async def accept_friend_request(
    data: FriendshipActionDTO,
    user: ActiveUserDep,
    service: FriendshipServiceDep,
) -> ResponseDTO[SuccessDTO]:
    try:
        await service.accept_request(
            friendship_id=data.friendship_id,
            user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ResponseDTO(data=SuccessDTO())


@router.post("/friends/reject", status_code=status.HTTP_200_OK)
@inject
async def reject_friend_request(
    data: FriendshipActionDTO,
    user: ActiveUserDep,
    service: FriendshipServiceDep,
) -> ResponseDTO[SuccessDTO]:
    try:
        await service.reject_request(
            friendship_id=data.friendship_id,
            user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ResponseDTO(data=SuccessDTO())

@router.delete("/friends/remove", status_code=status.HTTP_200_OK)
@inject
async def remove_friend(
    data: FriendshipActionDTO,
    user: ActiveUserDep,
    service: FriendshipServiceDep,
) -> ResponseDTO[SuccessDTO]:
    try:
        await service.remove_friend(
            user_id=user.id,
            friend_id=data.friendship_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ResponseDTO(data=SuccessDTO())


@router.get("/friends", status_code=status.HTTP_200_OK)
@inject
async def get_friends(
    user: ActiveUserDep,
    service: FriendshipServiceDep,
) -> ResponseDTO[list[UserInfoDTO]]:
    return ResponseDTO(data=await service.get_friends(user.id))

@router.get("/friendships", status_code=status.HTTP_200_OK)
@inject
async def get_friends(
    user: ActiveUserDep,
    service: FriendshipServiceDep,
) -> ResponseDTO[list[FriendResponseDTO]]:
    return ResponseDTO(data=await service.get_friendships(user.id))


@router.get("/friends/requests", status_code=status.HTTP_200_OK)
@inject
async def get_pending_requests(
    user: ActiveUserDep,
    service: FriendshipServiceDep,
) -> ResponseDTO[list[FriendResponseDTO]]:
    requests = await service.get_requests(user.id)
    return ResponseDTO(data=requests)