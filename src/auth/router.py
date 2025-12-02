from dependency_injector.wiring import inject
from fastapi import APIRouter, HTTPException, status

from auth.exceptions import AuthenticationException, RegistrationException
from auth.models import TokenDTO, UserInCreateDTO, UserInfoDTO, UserInLoginDTO
from config.dependencies import (
    JWTAuthenticationDep,
    AuthenticatedUserDep,
    RegistrationDep,
)
from models import ResponseDTO

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
@inject
async def login(
    user: UserInLoginDTO,
    jwt_auth_service: JWTAuthenticationDep,
) -> ResponseDTO[TokenDTO]:
    try:
        token = await jwt_auth_service.authenticate_user(user)
    except AuthenticationException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return ResponseDTO[TokenDTO](data=token)


@router.get("/users/me")
@inject
async def get_current_user(
    user: AuthenticatedUserDep,
) -> ResponseDTO[UserInfoDTO]:
    return ResponseDTO[UserInfoDTO](data=user)


@router.post("/registration", status_code=status.HTTP_201_CREATED)
@inject
async def register_user(
    user: UserInCreateDTO,
    registration_service: RegistrationDep,
) -> ResponseDTO[UserInfoDTO]:
    try:
        new_user = await registration_service.register_user(user)
    except RegistrationException as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ResponseDTO[UserInfoDTO](data=new_user)
