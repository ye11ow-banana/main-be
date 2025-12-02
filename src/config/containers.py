from typing import AsyncGenerator

from dependency_injector import containers, providers
from fastapi import HTTPException, status, Request
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker

from auth.exceptions import AuthenticationException
from auth.models import UserInfoDTO
from auth.services.authentication import JWTAuthenticationService
from auth.services.registration import RegistrationService
from config import settings
from unitofwork import IUnitOfWork, UnitOfWork


async def use_db_engine(
    user: str, password: str, host: str, port: str, db_name: str
) -> AsyncGenerator[AsyncEngine, None]:
    database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"
    engine = create_async_engine(database_url, poolclass=NullPool)
    try:
        yield engine
    finally:
        await engine.dispose()


async def use_uow(async_session_maker: sessionmaker[AsyncSession]) -> IUnitOfWork:
    return UnitOfWork(async_session_maker)


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


async def use_authenticated_user(
    jwt_auth_service: JWTAuthenticationService, token: str
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


class Container(containers.DeclarativeContainer):
    db_engine = providers.Singleton(
        use_db_engine,
        user=settings.db.user,
        password=settings.db.password,
        host=settings.db.host,
        port=settings.db.port,
        db_name=settings.db.db_name,
    )
    async_session_maker = providers.Singleton(
        sessionmaker, db_engine, class_=AsyncSession, expire_on_commit=False
    )
    uow = providers.Singleton(use_uow, async_session_maker)
    jwt_authentication_service = providers.Resource(JWTAuthenticationService, uow=uow)
    registration_service = providers.Resource(RegistrationService, uow=uow)
    authenticated_user = providers.Resource(
        use_authenticated_user,
        jwt_authentication_service,
        jwt_token=use_token,
    )
