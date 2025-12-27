from typing import Annotated
from fastapi import HTTPException, status, Request, Depends
from fastapi.security.utils import get_authorization_scheme_param
from dependency_injector.wiring import Provide, inject

from app.services import AppService
from auth.exceptions import AuthenticationException
from auth.models import UserInfoDTO
from auth.services.authentication import JWTAuthenticationService
from auth.services.registration import RegistrationService
from calorie.services.trend import TrendService
from config.containers import Container
from notification.services.email import EmailNotificationService

JWTAuthenticationDep = Annotated[
    JWTAuthenticationService, Depends(Provide[Container.jwt_authentication_service])
]
RegistrationDep = Annotated[
    RegistrationService, Depends(Provide[Container.registration_service])
]
EmailNotificationDep = Annotated[
    EmailNotificationService, Depends(Provide[Container.notification_service])
]


async def use_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


@inject
async def get_authenticated_user(
    jwt_auth_service: JWTAuthenticationDep, token: str = Depends(use_token)
) -> UserInfoDTO:
    try:
        user = await jwt_auth_service.get_current_user(token)
    except AuthenticationException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


AuthenticatedUserDep = Annotated[UserInfoDTO, Depends(get_authenticated_user)]


def active_user(user: AuthenticatedUserDep) -> UserInfoDTO:
    if not user.is_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="User is not verified")
    return user


ActiveUserDep = Annotated[UserInfoDTO, Depends(active_user)]
AppServiceDep = Annotated[AppService, Depends(Provide[Container.app_service])]
TrendServiceDep = Annotated[TrendService, Depends(Provide[Container.trend_service])]
