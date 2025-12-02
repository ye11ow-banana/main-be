from typing import Annotated

from dependency_injector.wiring import Provide
from fastapi import Depends

from auth.models import UserInfoDTO
from auth.services.authentication import JWTAuthenticationService
from auth.services.registration import RegistrationService
from config.containers import Container

JWTAuthenticationDep = Annotated[
    JWTAuthenticationService, Depends(Provide[Container.jwt_authentication_service])
]
AuthenticatedUserDep = Annotated[
    UserInfoDTO, Depends(Provide[Container.authenticated_user])
]
RegistrationDep = Annotated[
    RegistrationService, Depends(Provide[Container.registration_service])
]
