from dependency_injector import containers, providers
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker

from app.services import AppService
from auth.services.authentication import JWTAuthenticationService
from auth.services.registration import RegistrationService
from calorie.services.day import DayService
from calorie.services.trend import TrendService
from config import settings
from notification.services.email import EmailNotificationService
from unitofwork import UnitOfWork


def create_db_engine(
    user: str, password: str, host: str, port: str, db_name: str
) -> AsyncEngine:
    database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"
    return create_async_engine(database_url, poolclass=NullPool)


class Container(containers.DeclarativeContainer):
    db_engine = providers.Singleton(
        create_db_engine,
        user=settings.db.user,
        password=settings.db.password,
        host=settings.db.host,
        port=settings.db.port,
        db_name=settings.db.db_name,
    )
    async_session_maker = providers.Singleton(
        sessionmaker,
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    uow = providers.Factory(UnitOfWork, async_session_maker=async_session_maker)
    jwt_authentication_service = providers.Factory(JWTAuthenticationService, uow=uow)
    registration_service = providers.Factory(RegistrationService, uow=uow)
    notification_service = providers.Factory(EmailNotificationService, uow=uow)
    app_service = providers.Factory(AppService, uow=uow)
    trend_service = providers.Factory(TrendService, uow=uow)
    day_service = providers.Factory(DayService, uow=uow)
